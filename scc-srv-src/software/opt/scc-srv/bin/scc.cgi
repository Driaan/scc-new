#!/bin/sh

# Shell script to handle SCC web server actions.
# Copyright (C) 2001-2004 Open Challenge B.V.
# Copyright (C) 2004-2005 OpenEyeT Professional Services.
# Copyright (C) 2005-2018 QNH.
# Copyright (C) 2019 Siem Korteweg.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.
# If not, write to the Free Software Foundation,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# Contact information: https://sourceforge.net/projects/sysconfcollect/support

# SCC-release: 1.19.44
# ID:          $Id: scc.cgi 6217 2019-03-22 18:46:12Z siemkorteweg $


ProgName=${0##*/};			export ProgName

set -u

export SCC_BIN=/opt/scc-srv/bin
export SCC_CONF=/var/opt/scc-srv/conf
export SCC_DATA=/var/opt/scc-srv/data
export SCC_WWW=${SCC_DATA}/www
export SCC_TMP=/tmp

PATH=/sbin:/usr/sbin:/usr/bin:/bin:${SCC_BIN};		export PATH

export SCC_LOG=${SCC_DATA}/log/scc.cgi.log
logging=
if [ -w ${SCC_LOG} ]
then
	logging="yes"
fi
log_date=$(date '+%Y-%m-%d:%H.%M.%S')

export TMPDIR=${SCC_TMP}
export TMP=${SCC_TMP}

export SHELL=/bin/sh
export LANG=C

if [ -d /usr/xpg4/bin ]
then
	PATH=/usr/xpg4/bin:${PATH}
fi

SYNTAX="Syntax error, use: ${ProgName} <realm>"

if [ $# -ne 1 ]
then
	echo "${SYNTAX}" >&2
	exit 1
fi
realm="${1}"

scc_web_path_dir=""
if [ -f ${SCC_CONF}/scc.conf ]
then
	scc_web_path_dir="$(sed -n 's/^SCC_WEB_PATH=//p' ${SCC_CONF}/scc.conf)"
fi
web_realm_dir="${scc_web_path_dir}/${realm}"
HOME_URL="<A HREF=\"${web_realm_dir}/index.html\">Home</A>&nbsp;&nbsp;&nbsp;&nbsp;"

export TOP_URL='<A HREF="#TOP">Top</A>&nbsp;&nbsp;&nbsp;&nbsp;'

logo_tag=""
if [ -f ./custom/scc-logo.png ]
then
	logo_tag="<IMG SRC=\"${web_realm_dir}/custom/scc-logo.png\" ALT=HelpInfo>"
fi

group=${SCC_TMP}/scc-cgi-class-$$;		export group
TMP_FILE_1=${SCC_TMP}/scc-cgi-tmp1-$$;		export TMP_FILE_1
TMP_FILE_2=${SCC_TMP}/scc-cgi-tmp2-$$;		export TMP_FILE_2

trap 'rm -f ${group} ${TMP_FILE_1} ${TMP_FILE_2}' 0
trap "exit 2" 1 2 3 15

# Generate header of the resulting HTML page
# Argument (optional, default value is "System Configuration Collector: ${realm}):
#	title
# Environment variables:
#	${web_realm_dir}
#	${realm}
header()
{
	title="System Configuration Collector: ${realm}"
	if [ $# -eq 1 ]
	then
		title="${1}"
	fi

	cat <<-EndOfTxt
		<!DOCTYPE HTML>
		<HTML lang="en">
		<HEAD>
			<META HTTP-EQUIV="content-type" CONTENT="text/html; charset=UTF-8">
			<LINK HREF="${web_realm_dir}/custom/style.css" REL="stylesheet" TYPE="text/css">
			<LINK HREF="${web_realm_dir}/custom/favicon.ico" REL="shortcut icon" TYPE="image/x-icon">
			<TITLE>${title}</TITLE>
		</HEAD>
		<BODY>
	EndOfTxt
}

# Terminate html page
# Argument:
#	none
trailer()
{
	echo "</BODY>"
	echo "</HTML>"
}

# Generate page with a single meesage.
# Argument:
#	message
report_msg()
{
	header

	echo "<P class=\"header\">${1}</P>"

	trailer
}

# Generate CSV from statistics of runs of a single host.
# Read logbook data from stdin, refer to scc-log for structure of logbook.
gen_csv()
{
	awk	-F:	'BEGIN		{
						print "Date,Time,Runtime,Changes"
					}
			/:runtime::/	{
						#2011-05-17:12.27.17:runtime::18
						if ( data_to_display > 0 )
						{
							printf( "%s,%s,%s,%s\n", prev_date, prev_time, prev_runtime, "0" )
						}
						prev_date = $1
						prev_time = $2
						prev_runtime = $5
						data_to_display = 1
						next
					}
			/:count::/	{
						#2011-05-17:12.27.17:count::4
						printf( "%s,%s,%s,%s\n", prev_date, prev_time, prev_runtime, $5 )
						data_to_display = 0
					}
			END		{
						if ( prev_runtime >= 0 )
						{
							printf( "%s,%s,%s,%s\n", prev_date, prev_time, prev_runtime, "0" )
						}
					}' -
}

# Generate the page with the statistics of a host.
# Arguments:
#	realm_path
#	host
gen_stats_page()
{
	export realm_path=${1}
	export host=${2}

	gen_csv <scc.${host}.log >scc.${host}.csv

	awk -F, '{
			printf( "%s %s %10.10s %10.10s\n", $1, $2, $3, $4 )
		}' scc.${host}.csv >scc.${host}.all_data
	all_cnt=$(( $(wc -l <scc.${host}.csv) - 1 ))
	recent_cnt=30
	recent_limit=50
	set $(awk '{ if ( NR == 2 ) start = $1; end = $1} END { print start, end }' scc.${host}.all_data)
	all_start=${1}
	all_end=${2}

	cnt=$(wc -l <scc.${host}.all_data)
	if [ ${cnt} -gt ${recent_limit} ]
	then
		(
			head -n 1 scc.${host}.all_data
			tail -n ${recent_cnt} scc.${host}.all_data
		) >scc.${host}.recent_data

		set $(awk '{ if ( NR == 2 ) start = $1; end = $1} END { print start, end }' scc.${host}.recent_data)
		recent_start=${1}
		recent_end=${2}
	fi

	plot_exe="$(which gnuplot 2>/dev/null)"

	if [ -x "${plot_exe}" -a ${all_cnt} -gt 3 ]
	then
		while read type category column title
		do
			if [ -f scc.${host}.${type}_data ]
			then
				scc_plot=scc_$$.plt
				cat >${scc_plot} <<-_EOF_
					set xdata time
					set timefmt "%Y-%m-%d %H.%M.%S"
					set title "${title} of SCC on host ${host}" 
					set xlabel "Date" 
					set ylabel "${title}" 
					set yrange [0:]
					set key off
					set terminal png enhanced size ${SCC_STATS_X_RES},${SCC_STATS_Y_RES} 
					set output 'scc.${host}.${type}_${category}.png'
					plot "scc.${host}.${type}_data"  using 1:${column} with lines
				_EOF_

				${plot_exe} ${scc_plot} >/dev/null 2>/dev/null
				rm -f ./${scc_plot} scc.${host}.${type}_${category}
			fi
		done <<-_X_
			all	runtime	3 Runtime (s)
			recent	runtime 3 Runtime (s)
			all	changes 4 Changes (lines)
			recent	changes 4 Changes (lines)
		_X_
		rm -f scc.${host}.*_data
	fi

	header "Statictics of host ${host}"
	cat <<-_EOF_
			<H1 id="TOP">Statistics: ${host}</H1>
			<P class=header>
			<A HREF="${realm_path}/index.html">Home</A>&nbsp;&nbsp;&nbsp;&nbsp;
			Source data
			</P>
			<P>Source data is available in <A HREF="${realm_path}/scc.${host}.csv">CSV</A> format.</P>

	_EOF_

	if [ -x "${plot_exe}" ]
	then
		if [ ${all_cnt} -gt 3 ]
		then
			echo "	<P class=header>${TOP_URL}All runtimes: ${all_cnt} entries from ${all_start} to ${all_end}</P>"
			echo "	<IMG SRC=\"${realm_path}/scc.${host}.all_runtime.png\" ALT=\"all runtimes\">"

			if [ -f scc.${host}.recent_runtime.png ]
			then
				echo "	<P class=header>${TOP_URL}Recent runtimes: ${recent_cnt} entries from ${recent_start} to ${recent_end}</P>"
				echo "	<IMG SRC=\"${realm_path}/scc.${host}.recent_runtime.png\" ALT=\"recent runtimes\">"
			fi

			echo "	<P class=header>${TOP_URL}All change counts: ${all_cnt} entries from ${all_start} to ${all_end}</P>"
			echo "	<IMG SRC=\"${realm_path}/scc.${host}.all_changes.png\" ALT=\"all changes\">"

			if [ -f scc.${host}.recent_changes.png ]
			then
				echo "	<P class=header>${TOP_URL}Recent change counts: ${recent_cnt} entries from ${recent_start} to ${recent_end}</P>"
				echo "	<IMG SRC=\"${realm_path}/scc.${host}.recent_changes.png\" ALT=\"recent changes\">"
			fi
		else
			echo "<P>Too few runs (${all_cnt}) to plot data.</P>"
		fi
	else
		echo "	<P>When gnuplot is installed, graphs will be generated and displayed on this page.</P>"
	fi

	echo "<HR>"
	echo "<P>"
	echo "This page has been generated by scc.cgi at $(date '+%Y-%m-%d %H:%M:%S'). "
	echo "The generated file will be reused until scc-summary runs. "
	echo "Change the resolution of the graphs via file _realm_/custom/scc-realm.conf. "
	echo "</P>"

	echo "</BODY>"
	echo "</HTML>"

	return 0
}

# We are called as a CGI-script, produce the proper heading.
echo "Content-Type: text/html;charset=iso-8859-1"
echo ""

# Without using the -w option of scc-update, several actions fail with unclear errors.
# Check and report whether the -w option has been used (indicated by Ben Jannedy).
if [ ! -w "${SCC_TMP}" ]
then
	report_msg "Insufficient access to tmp-directory of scc-srv, use: scc-update -w &lt;webuser&gt;"
	exit 0
fi

# Maarten Hartsuijker pointed us at the following:
# replace '<' (%3c) and '>' (%3e) by '_' to avoid Cross Site Scripting.
QS=$(echo "${QUERY_STRING:-}"			|
	sed	-e 's/+/ /g'		\
		-e 's/%20/ /g'		\
		-e 's/%23/#/g'		\
		-e 's/%2[Aa]/*/g'	\
		-e 's/%2[Bb]/+/g'	\
		-e 's/%2[Dd]/-/g'	\
		-e 's/%2[Ee]/./g'	\
		-e 's/%2[Ff]/\//g'	\
		-e 's/%3[Aa]/:/g'	\
		-e 's/%3[Bb]/;/g'	\
		-e 's/%3[Dd]/=/g'	\
		-e 's/%5[Bb]/[/g'	\
		-e 's/%5[Cc]/\\/g'	\
		-e 's/%5[Dd]/]/g'	\
		-e 's/%5[Ee]/^/g'	\
		-e 's/%5[Ff]/_/g'	\
		-e 's/%3[Cc]/_/g'	\
		-e 's/</_/g'		\
		-e 's/%3[Ee]/_/g'	\
		-e 's/>/_/g'		\
		-e 's/%//g')

# Global order of processing logic:
# - generate statistics for a single system
# - search data in
#   - snapshot(s), logbook(s), SMT data file(s), rule data
#   - generate table with hits
#   - generate table with #hits and hosts, sorted on #hits
#   - generate table with systems without hit
# - display without searching
#   - single file or summary of snapshot, logbook, SMT data, rules
# - compare (parts of) two systems

# Generating the statistics for system:
# format for QUERY_STRING: sys=<system>&statistics=1
stat=$(echo "${QS}" | sed -n -e 's/.*statistics=//p')
if [ -n "${stat}" ]
then
	system=$(echo "${QS}" | sed -n -e 's/sys=//p' | sed -e 's/&.*//')
	if [ ! -f scc.${system}.stats.html ]
	then
		if [ -f custom/scc-realm.conf ]
		then
			. custom/scc-realm.conf
		fi
		if [ "${SCC_STATS:-yes}" = "no" ]
		then
			report_msg "No statictics configured."
			exit 0
		fi
		export SCC_STATS_X_RES="${SCC_STATS_X_RES:-1024}"
		export SCC_STATS_Y_RES="${SCC_STATS_Y_RES:-768}"

		if [ -f scc.${system}.log ]
		then
			gen_stats_page "${web_realm_dir}" "${system}" >scc.${system}.stats.html
		else
			report_msg "No data available for ${system}."
			exit 0
		fi
	fi
	if [ -s scc.${system}.stats.html ]
	then
		cat scc.${system}.stats.html
	else
		report_msg "Runtime error for statictics."
	fi
	exit 0
fi

# Using the first START-button, to retrieve data, results in the following
# format for QUERY_STRING: sys=<system>&opt=<option>&search=<search>&s_case=<case>
# Start to check whether option is non-empty. Determine other variables later.
option=$(echo "${QS}" | sed -n -e 's/.*opt=//p' | sed -e 's/&.*//')

if [ -n "${option}" ]
then
	system=$(echo "${QS}" | sed -n -e 's/sys=//p' | sed -e 's/&.*//')
	string=$(echo "${QS}" | sed -n -e 's/.*search=//p' | sed -e 's/&.*//')
	s_case=$(echo "${QS}" | sed -n -e 's/.*s_case=//p' | sed -e 's/&.*//')
	s_limit=$(echo "${QS}" | sed -n -e 's/.*s_limit=//p' | sed -e 's/&.*//')

	if [ -n "${string}" ]
	then
		# A search-string has been supplied, we are going to search.
		header
		# Do not center this page as the data to be displayed can contain very long lines.
		echo "<A id=\"TOP\" HREF=\"${scc_web_path_dir}/scc-help/scc-search-index.html\">${logo_tag}</A>"

		case_opt="-i"
		case_label="(ignore case)"
		if [ -n "${s_case}" ]
		then
			case_opt=""
			case_label="(exact match)"
		fi

		search_files_label="snapshot(s)"
		search_suffix="cur"
		show_suffix=""
		if [ ${option} = "log" ]
		then
			search_files_label="logbook(s)"
			search_suffix="log"
			show_suffix=".log"
		elif [ ${option} = "smt" ]
		then
			search_files_label="SMT-data"
			show_suffix=".smt"
		elif [ ${option} = "rules" ]
		then
			search_files_label="Rules"
			show_suffix=""
		fi

		[ "${logging}" ] && echo "${log_date}:${realm}:search for:${string}: in ${system}, ${search_files_label}" >>${SCC_LOG}

		SEARCH_LABEL="Searched for: &quot;<SPAN CLASS=\"warning\">${string}</SPAN>&quot; ${case_label} in ${search_files_label} for ${system}"

		echo "<P class=\"header\">"
		echo "${HOME_URL}"
		echo "${SEARCH_LABEL}"
		if [ "${system}" = "all_systems" ]
		then
			echo "&nbsp;&nbsp;&nbsp;&nbsp;Sorted on <A HREF=\"#cnt_hits\">#hits</A>"
		fi
		echo "</P>"

		if [ "${system}" = "all_systems" ]
		then
			search_sys=""

			# Use scc-summary.data to determine all system file names, format is:
			# "general_data":<host>:<model>:<os>:<release>:<last_day>:<last_time>:<domain>:<runtime>:<size>:<virtualization>
			# File is sorted on hostname (ignore case).
			search_files="$(sed	-e "s/^general_data:/scc./"	\
						-e "s/:.*/.${search_suffix}/" scc-summary.data)"

			count_all=$(wc -l <scc-summary.data)
		else
			search_sys="${system}"
			search_files="scc.${system}.${search_suffix}"
			count_all=1
		fi

		# Restrict the amount of data per system to the limit:
		# - 10 lines for multi-file search
		# - 1000 lines for single file search
		# We allow one extra line to signal the "overflow" in the result of the search.
		limit=1001
		all_search=0
		if [ ${count_all} -gt 1 ]
		then
			limit=11
			all_search=1
			fi
		if [ -z "${s_limit}" ]
		then
			limit=1000000
		fi

		rm -f ${TMP_FILE_1} ${TMP_FILE_2}

		if [ ${option} = "smt" ]
		then
			# Search for string in SMT file(s)
			awk -F:	'{
					# Format of the input is: "smt-data":<host>:<software>:<version>
					if ( ( s != "" ) && ( s != $2 ) )
					{
						next
					}
					$1 = ""
					if ( length( c ) > 0 )
					{
						# Ignore case, map data and RE to uppercase.
						m = match( toupper( $0 ), toupper( r ) )
					}
					else
					{
						m = match( $0, r )
					}
					if ( m > 0 )
					{
						sys = $2
						$2 = ""
						printf( "%s %s\n", sys, $0 )
					}
				}'	c="${case_opt}"		\
					s="${search_sys}"	\
					r="${string}"		\
						scc-smt.data
		elif [ ${option} = "rules" ]
		then
			# Search for string in rules file(s)
			awk	'/^#/	{ next }
					{
						# Format of the input-data is:
						# <keyword> <host> <data>
						if ( ( s != "" ) && ( s != $2 ) )
						{
							next
						}
						if ( length( c ) > 0 )
						{
							# Ignore case, map data and RE to uppercase.
							m = match( toupper( $0 ), toupper( r ) )
						}
						else
						{
							m = match( $0, r )
						}
						if ( m > 0 )
						{
							sys = $2
							$2 = ""
							printf( "%s %s\n", sys, $0 )
						}
					}'	c="${case_opt}"		\
						s="${search_sys}"	\
						r="${string}"		\
							scc-rules.data
		elif [ ${option} = "log" ]
		then
			# Search for string in log file(s)
			echo "${search_files}"				|
			xargs grep ${case_opt} "${string}" /dev/null	|
			sort -t: -k1,1f -k2,3r				|
			sed	-e 's/^scc\.//'			\
				-e 's/\.log:/ /'		\
				-e 's/:data::new::/ new /'	\
				-e 's/:data::old::/ old /'

		else
			# Search for string in configuration file(s)
			echo "${search_files}"				|
			xargs grep ${case_opt} "${string}" /dev/null	|
			sed	-e 's/^scc\.//'	\
				-e 's/\.cur:/ /'
		fi							|
		awk 	'{
				# We count the number of hits for each system, format of the data is:
				# <host> <data>
				cnt[ $1 ] += 1
				if ( cnt[ $1 ] <= l )
				{
					print
				}
			}
			END	{
					for ( s in cnt )
					{
						print "cnt", s, cnt[ s ] >>o
					}
				}'	l="${limit}"	\
					o=${TMP_FILE_2}			|
		sed	-e 's/&/\&amp;/g'	\
			-e 's/</\&lt;/g'	\
			-e 's/>/\&gt;/g'	\
			-e 's/"/\&quot;/g' >${TMP_FILE_1}

		systems_hit=$(sed -e 's/^cnt://' -e 's/:.*//' ${TMP_FILE_2} | sort -f )
		if [ -z "${systems_hit}" ]
		then
			echo "<P class=\"header\">No match found.</P>"
			trailer
			exit 0
		fi
		count_hit=$(wc -l <${TMP_FILE_2})
		absent=$(( count_all - count_hit ))

		if [ "${absent}" -eq 0 ]
		then
			echo "<P>Data found on all systems.</P>"
		else
			echo "<P>Click <A HREF=\"#absent\">here</A> for ${absent} system(s) without a match."
			echo "The following ${count_hit} system(s) matched:</P>"
		fi

		# Display the search results (from TMP_FILE_1) in a table
		echo "<TABLE CLASS=SCC>"

		echo "<THEAD>"
		echo "	<TR class=Odd style=\"text-align:left;\">"
		echo "		<TH>System</TH>"
		echo "		<TH>Hits</TH>"
		echo "		<TH style=\"text-align:left;\">Data</TH>"
		echo "	</TR>"
		echo "</THEAD>"

		echo "<TBODY>"

		# All data from one system (including a possible "overflow" message) are displayed
		# as a single cell of a table.
		echo "qs:${QS}"					|
		awk	'BEGIN	{
					c[ 0 ] = "Even"
					c[ 1 ] = "Odd"
					tr_c = 2;		# TR class 
				}
			/^qs:/	{
					sub( "^qs:", "" )
					gsub( "&", "&amp;" )
					cgi_args = $0
					next
				}
			/^cnt/	{ cnt[ $2 ] = $3; next }
				{
					# Format of the data is:
					# <host> <data>
					if ( $1 != prev )
					{
						if ( data_shown )
						{
							# terminate row of previous system
							printf( "    </TD>\n</TR>\n" )
						}

						# New window to avoid searching again when going back from the following URL.
						host_html = sprintf("<A TARGET=\"_blank\" HREF=\"%s/%s/scc.%s%s.html\"><SPAN CLASS=\"mono\">%s</SPAN></A>",
									d, r, $1, s, $1 )
						prev = $1
						cnt_per_host = 0
					}
					else
					{
						host_html = ""
					}
					data_shown = 1

					cnt_per_host++
					if ( cnt_per_host < l )
					{
						if ( length( host_html ) )
						{
							# Keep hostname and hit-count at first line of cell.
							# Do not wrap the data and fqdn-hostnames.
							printf( "<TR class=%s>\n", c[ tr_c++ % 2 ] )
							printf( "	<TD class=Even style=\"white-space: nowrap; vertical-align:top;\">%s</TD>\n", host_html )
							if ( all_search )
							{
								# Add an URL to search only this system
								# New window to avoid searching again when going back from the following URL.
								cgi_path = sprintf( "%s/%s/cgi-bin/scc-wrapper.cgi", d, r )
								sys_cgi_args = cgi_args
								sub( "all_systems", $1, sys_cgi_args )
								printf( "	<TD class=Odd style=\"vertical-align:top;\"><A TARGET=\"_blank\" HREF=\"%s?%s\">%d</A></TD>\n",
									cgi_path, sys_cgi_args, cnt[ $1 ] )
							}
							else
							{
								printf( "	<TD class=Odd style=\"vertical-align:top;\">%d</TD>\n",
									cnt[ $1 ] )
							}
							printf( "	<TD class=Even style=\"white-space: nowrap;\">    <SPAN CLASS=\"mono\">" )
						}
						else
						{
							printf( "	<BR><SPAN CLASS=\"mono\">" )
						}
						$1 = ""
						sub( "^  *", "", $0 )
						print $0 "</SPAN>"
					}
					else if ( cnt_per_host == l )
					{
						print "	<BR><SPAN CLASS=\"warning\">data limited to " l - 1 " lines per system</SPAN>"
					}
				}
				END	{
						if ( NR > 0 )
						{
							printf( "    </TD>\n</TR>\n" );	# Terminate the last cell
						}
						printf( "</TBODY>\n" )
						printf( "</TABLE>\n" );			# End the table
					}'	all_search=${all_search}	\
						l="${limit}"			\
						s="${show_suffix}"		\
						d="${scc_web_path_dir}"		\
						r="${realm}"			\
							- ${TMP_FILE_2} ${TMP_FILE_1}

		# Display #hits and hosts of the search results sorted on #hits
		if [ "${system}" = "all_systems" ]
		then
			# Generate table with cnt_hits and host, sorted on cnt_hits
			echo "<P class=\"header\" id=\"cnt_hits\">${TOP_URL}${SEARCH_LABEL}</P>"
			echo "<P>Matching systems sorted on number of hits:</P>"

			echo "<TABLE CLASS=SCC>"
			echo "<THEAD>"
			echo "	<TR class=Odd style=\"text-align:left;\">"
			echo "		<TH>Number of hits</TH>"
			echo "		<TH>System</TH>"
			echo "		<TH>Virtualization</TH>"
			echo "		<TH>Model</TH>"
			echo "		<TH>OS</TH>"
			echo "		<TH>Release</TH>"
			echo "	</TR>"
			echo "</THEAD>"
			echo "<TBODY>"

			# Ensure singe sort on decreasing #hits and alphabetic order of systems within #hist
			awk '{ printf( "%06d:%s:%d\n", ( 9999999 - $3 ), $2, $3 ) }' ${TMP_FILE_2}	|
			sort										|
			awk -F: 'BEGIN	{
						c[ 0 ] = "Even"
						c[ 1 ] = "Odd"
						tr_c = 2;		# TR class 
					}
				/^general_data/	{
						# Add some general system info to the systems without a match.
						# Format of the input is:
						# "general_data":<host>:<model>:<os>:<release>:<last_day>:<last_time>:<snap_size>:<runtime>:<snap_size>:<virtualization>
						model[ $2 ] = $3
						if ( length( $3 ) == 0 )
						{
							model[ $2 ] = "&nbsp;"
						}
						os[ $2 ] = $4
						rel[ $2 ] = $5
						virt[ $2 ] = $11
						next
					}
					{
						if ( cgi_args_done == 0 )
						{
							gsub( "&", "&amp;", q )
							cgi_args = q
							cgi_args_done = 1
						}

						printf( "<TR class=%s>\n", c[ tr_c++ % 2 ] )

						# Add an URL to search only this system
						cgi_path = sprintf( "%s/%s/cgi-bin/scc-wrapper.cgi", d, r )
						sys_cgi_args = cgi_args
						sub( "all_systems", $2, sys_cgi_args )
						# New window to avoid searching again when going back from the following URL.
						printf( "	<TD class=Odd style=\"text-align:right;\"><A TARGET=\"_blank\" HREF=\"%s?%s\">%d</A></TD>\n", cgi_path, sys_cgi_args, $3 )
						printf( "	<TD class=Even><A TARGET=\"_blank\" HREF=\"%s/%s/scc.%s.html\"><SPAN CLASS=\"mono\">%s</SPAN></A></TD>\n", d, r, $2, $2 )
						printf( "	<TD class=Odd>%s</TD>\n", virt[ $2 ] )
						printf( "	<TD class=Even>%s</TD>\n", model[ $2 ] )
						printf( "	<TD class=Odd>%s</TD>\n", os[ $2 ] )
						printf( "	<TD class=Even>%s</TD>\n", rel[ $2 ] )

						print "</TR>"
					}'	d="${scc_web_path_dir}"	\
						r="${realm}"		\
						q="${QS}"		\
							scc-summary.data - 2>/dev/null

			echo "</TBODY>"
			echo "</TABLE>"
		fi


		if [ "${absent}" -ne 0 ]
		then
			# Display the systems without a match in a separate table
			echo "<P class=\"header\" id=\"absent\">${TOP_URL}${SEARCH_LABEL}</P>"

			echo "<P>The following ${absent} system(s) did not match:</P>"

			# Indicate what systems to ignore in the following summary.
			echo "${systems_hit}"			|
			awk	'{
					# Each line contains (with #hits > 0):
					# cnt <system> <#hits>
					print "ignore:" $2
				}' >${TMP_FILE_1}

			echo "${search_files}"			|
			tr " " "\012"				|
			sed	-e 's@^scc\.@@'	\
				-e "s@\.${search_suffix}@@"	|
			awk -F: 'BEGIN	{
						c[ 0 ] = "Even"
						c[ 1 ] = "Odd"
						tr_c = 2;		# TR class 
					}
				/^general_data/	{
						# Add some general system info to the systems without a match.
						# Format of the input is:
						# "general_data":<host>:<model>:<os>:<release>:<last_day>:<last_time>:<snap_size>:<runtime>:<snap_size>:<virtualization>
						model[ $2 ] = $3
						if ( length( $3 ) == 0 )
						{
							model[ $2 ] = "&nbsp;"
						}
						os[ $2 ] = $4
						rel[ $2 ] = $5
						last_change[ $2 ] = sprintf( "%s %s", $6, $7 )
						if ( length( last_change[ $2 ] ) == 0 )
						{
							last_change[ $2 ] = "&nbsp;"
						}
						virt[ $2 ] = $11
						next
					}
				/^ignore/	{ ignore[ $2 ] = 1; next
						}
					{
						if ( ignore[ $1 ] > 0 )
						{
							next
						}

						if ( header_done == 0 )
						{
							print "<TABLE CLASS=SCC>"
							print "<THEAD>"
							print "	<TR class=Odd style=\"text-align:left;\">"
							print "		<TH>System</TH>"
							print "		<TH>Virtualization</TH>"
							print "		<TH>Model</TH>"
							print "		<TH>OS</TH>"
							print "		<TH>Release</TH>"
							print "		<TH>Last change</TH>"
							print "	</TR>"
							print "</THEAD>"
							print "<TBODY>"
							header_done=1
						}
						printf( "<TR class=%s>\n", c[ tr_c++ % 2 ] )
						printf( " <TD class=Even><A TARGET=\"_blank\" HREF=\"%s/%s/scc.%s.html\"><SPAN CLASS=\"mono\">%s</SPAN></A></TD>\n", d, r, $1, $1 )
						printf( " <TD class=Odd>%s</TD>\n", virt[ $1 ] )
						printf( " <TD class=Even>%s</TD>\n", model[ $1 ] )
						printf( " <TD class=Odd>%s</TD>\n", os[ $1 ] )
						printf( " <TD class=Even>%s</TD>\n", rel[ $1 ] )
						printf( " <TD class=Odd><A TARGET=\"_blank\" HREF=\"%s/%s/scc.%s.log.html\">%s</A></TD>\n", d, r, $1, last_change[ $1 ] )
						print "</TR>"
					}
					END	{
							print "</TBODY>"
							print "</TABLE>"
						}'	d="${scc_web_path_dir}"	\
							r="${realm}"		\
								scc-summary.data ${TMP_FILE_1} - 2>/dev/null
		fi

		trailer
		exit 0
	fi

	# No search string; display single log file or summary of log files
	if [ ${option} = "log" ]
	then
		[ "${logging}" ] && echo "${log_date}:${realm}:show logging" >>${SCC_LOG}

		if [ ${system} = "all_systems" ]
		then
			cat "./scc-log-index.html"
		elif [ -r "./scc.${system}.log.html" ]
		then
			# The log file contains an URL to Home (index.html) and an URL to the snapshot.
			# These URLs do not contain a full path. Add the full path to avoid that the files
			# are searched "under" the CGI-script.
			f1="index.html"
			f2="scc.${system}.html"
			sed	-e "s@^<LINK HREF=\"custom/style.css@<LINK HREF=\"${web_realm_dir}/custom/style.css@"	\
				-e "s@HREF=\"*${f1}\"*>Home</A>@HREF=\"${web_realm_dir}/${f1}\">Home</A>@"		\
				-e "s@HREF=\"*${f2}\"*@HREF=\"${web_realm_dir}/${f2}\"@"				\
					< "./scc.${system}.log.html"
		else
			report_msg "Cannot read file scc.${system}.log.html"
		fi
	   	exit 0
	fi

	# No search string; display single snapshot file or summary of system data
	if [ ${option} = "cnf" ]
	then
		[ "${logging}" ] && echo "${log_date}:${realm}:show snapshots" >>${SCC_LOG}

		if [ ${system} = "all_systems" ]
		then
			cat "./scc-summary-sys.html"
		elif [ -r "./scc.${system}.html" ]
		then
			# The snapshot contains an URL to Home (index.html) and an URL to the log file.
			# These URLs do not contain a full path. Add the full path to avoid that the files
			# are searched "under" the CGI-script.
			f1="index.html"
			f2="scc.${system}.log.html"
			sed	-e "s@^<LINK HREF=\"custom/style.css@<LINK HREF=\"${web_realm_dir}/custom/style.css@"	\
				-e "s@HREF=\"*${f1}\"*>Home</A>@HREF=\"${web_realm_dir}/${f1}\">Home</A>@"		\
				-e "s@HREF=\"*${f2}\"*@HREF=\"${web_realm_dir}/${f2}\"@"				\
					< "./scc.${system}.html"
		else
			report_msg "Cannot read file scc.${system}.html"
		fi
		exit 0
	fi

	# No search string; display single SMT file or summary of SMT data
	if [ ${option} = "smt" ]
	then
		[ "${logging}" ] && echo "${log_date}:${realm}:show SMT-data" >>${SCC_LOG}

		if [ ${system} = "all_systems" ]
		then
			if [ -f ./scc-smt-index.html ]
			then
				cat "./scc-smt-index.html"
			else
				report_msg "Cannot read file scc-smt-index.html"
			fi
		elif [ -r "./scc.${system}.smt.html" ]
		then
			# The file has been generated by scc-smt and only contains full paths to html-files.
			cat "./scc.${system}.smt.html"
		else
			report_msg "Cannot read file scc.${system}.smt.html"
		fi
		exit 0
	fi

	# No search string; display single or all rule data
	if [ ${option} = "rules" ]
	then
		[ "${logging}" ] && echo "${log_date}:${realm}:show Rules-data" >>${SCC_LOG}

		if [ ${system} = "all_systems" ]
		then
			if [ -f ./scc-rules-index.html ]
			then
				cat "./scc-rules-index.html"
			else
				report_msg "Cannot read file scc-rules-index.html"
			fi
		else
			# Get the data for the system, preserve the headers related to the messages.
			awk	'/^#/	{ header = $0; next }
					{
						if ( $2 == s )
						{
							if ( length( header ) )
							{
								print header
								header = ""
							}
							print
						}
					}' s="${system}" scc-rules.data 2>/dev/null		|
			${SCC_BIN}/scc-rules -d "${scc_web_path_dir}" -h ${system} "${realm}"
		fi
		exit 0
	fi

	report_msg "Unknown option: ${option}"
	exit 0
fi

# Using the second START-button, to compare snapshots of two systems, results in the following
# format for QUERY_STRING: sys1=<system1>&sys2=<system2>&class=<class>&class=<class>...
classes=$(echo "${QS}" | tr "&" "\012" | sed -n -e 's/.*class=//p')
system1=$(echo "${QS}" | sed -n -e 's/sys1=//p' | sed -e 's/&.*//')
system2=$(echo "${QS}" | sed -n -e 's/.*sys2=//p' | sed -e 's/&.*//')

if [ -z "${classes}" ]
then
	report_msg "No class(es) specified for comparing systems"
elif [ "${system1}" = "${system2}" ]
then 
	report_msg "Identical systems are not compared"
else
	[ "${logging}" ] && echo "${log_date}:${realm}:compare systems:${system1} and ${system2}" >>${SCC_LOG}

	if [ -r scc.${system1}.cur -a -r scc.${system2}.cur ]
	then
		header

		echo "<P style=\"text-align:center;\"><A HREF=\"${scc_web_path_dir}/scc-help/scc-compare-index.html\">${logo_tag}</A></P>"

		echo "${classes}" >${group}
		show_classes=$(echo "${classes}" | tr "\012" ",")
		show_classes="${show_classes%,}"

		${SCC_BIN}/scc-syscmp -l ${TMP_FILE_2} ${group} scc.${system1}.cur scc.${system2}.cur >${TMP_FILE_1} 
		cnt_1="$(head -n 1 ${TMP_FILE_2})"
		cnt_2="$(tail -n 1 ${TMP_FILE_2})"
		label_1="<SPAN CLASS=\"scc_sys_a\">${system1}</span> (${cnt_1} lines of class-data)"
		label_2="<SPAN CLASS=\"scc_sys_b\">${system2}</span> (${cnt_2} lines of class-data)"

		if [ -s ${TMP_FILE_1} ]
		then
			cnt=$(wc -l <${TMP_FILE_1})

			echo "<P class=\"header\">"
			echo "${HOME_URL}"
			echo "Configuration"
			echo "&nbsp;&nbsp;&nbsp;&nbsp;"
			echo "<A HREF=\"${web_realm_dir}/scc.${system1}.html\">${system1}</A>"
			echo "&nbsp;&nbsp;&nbsp;&nbsp;"
			echo "<A HREF=\"${web_realm_dir}/scc.${system2}.html\">${system2}</A>"
			echo "</P>"
			echo "<P>${cnt} differences between ${label_1} and ${label_2} for class: ${show_classes}</P>"

			echo "<PRE>"
			sed	-e 's/&/\&amp;/g'							\
				-e 's/</\&lt;/g'							\
				-e 's/>/\&gt;/g'							\
				-e 's/"/\&quot;/g'							\
				-e "s@^\(${system1} *:.*\)@<SPAN CLASS=\"scc_sys_a\">\1</span>@"	\
				-e "s@^\(${system2} *:.*\)@<SPAN CLASS=\"scc_sys_b\">\1</span>@" ${TMP_FILE_1}
			echo "</PRE>"
			echo "<HR>"
		else
			echo "<P class=\"header\">"
			echo "${HOME_URL}"
			echo "${label_1} and ${label_2} are identical for class: ${show_classes}"
			echo "</P>"
		fi
		rm -f ${TMP_FILE_1} ${TMP_FILE_2}

		trailer
	else
		report_msg "Cannot find snapshots for ${system1} and/or ${system2}"
	fi
fi

exit 0
