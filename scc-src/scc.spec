# Spec file to package SCC for RHEL, Fedora, CentOS, Mageia, ScientificLinux, OpenSuse
# Copyright (C) 2011-2018 QNH.
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
#
Summary: System Configuration Collector
# The Summary: line should be expanded to about here -----^
Name: scc
Version: 1.26.73

%if  0%{?mgaversion}
Release: %mkrel 1
%else
Release: 1%{?dist}
%endif

%if 0%{?suse_version}
License: GPL-2.0+
%else
License: GPLv2+
%endif

%if 0%{?suse_version}
Group: System/Management
%else
%if  0%{?mgaversion}
Group: System/Configuration
%else
Group: Applications/System
%endif
%endif

BuildRoot: %{_builddir}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
URL: https://sourceforge.net/projects/sysconfcollect/
Source: https://sourceforge.net/projects/sysconfcollect/files/%{name}/%{name}-%{version}/%{name}-%{version}.src.tar.gz
BuildArchitectures: noarch

%description
System Configuration Collector collects and classifies most of your 
UNIX/Linux/BSD configuration data in flat files called snapshots. This 
unique concept allows changes in snapshots of consecutive runs to be 
detected. These changes are added to a logbook that is helpful for 
administrators during troubleshooting and for auditors during audits. 
Snapshot and logbook are also available in HTML format. 

All data can be send to an SCC server where a web interface provides 
access to summaries and supports comparing snapshots of different 
servers and searching of all data.

%prep
rm -rf %{_builddir}/*
%setup -q -n %{name}-%{version}

%build
# The source contains scripts only.
# Rebase the software from /opt, /var/opt and /etc/opt:
./relocate	--no_conf_sub_dir				\
		--conf		%{_sysconfdir}/%{name}		\
		--data		%{_localstatedir}/lib/%{name}	\
		--no_mod_dir					\
		--sw_bin	%{_sbindir}			\
		--sw_doc	%{_docdir}/%{name}		\
		--sw_man	%{_mandir}

for man in software/%{_mandir}/man*/*
do
	gzip ${man}
done

%install
# Contents of the new rpm have been build under software/.
mkdir -p %{buildroot}
mv software/* %{buildroot}

%clean
rm -rf %{buildroot}

%pre
# Check and run SCC to detect changes made after the last run of SCC
[ -x %{_sbindir}/scc-log ] && %{_sbindir}/scc-log --preinstall
exit 0

%post
# Run SCC to collect the configuration in the new (actual) format
[ -x %{_sbindir}/scc-log ] && %{_sbindir}/scc-log --postinstall
exit 0

%preun
[ "${1}" = "0" ] && [ -x %{_sbindir}/scc-log ] && %{_sbindir}/scc-log --preremove
exit 0

%files
%defattr(755,root,root)
%dir %{_sysconfdir}/%{name}/
%defattr(444,root,root)
%config(noreplace) %{_sysconfdir}/%{name}/*
%defattr(755,root,root)
%dir %{_localstatedir}/lib/%{name}
%dir %{_localstatedir}/lib/%{name}/plugin_data
%dir %{_localstatedir}/lib/%{name}/transfer
%defattr(755,root,root)
%{_sbindir}/*
%defattr(444,root,root)
%{_mandir}/man1/*
%{_mandir}/man4/*
%{_mandir}/man5/*
%defattr(755,root,root)
%dir %{_docdir}/%{name}
%defattr(444,root,root)
%doc %{_docdir}/%{name}/*
%if 0%{?license}
%doc %exclude %{_docdir}/%{name}/COPYING
%license %{_docdir}/%{name}/COPYING
%endif

%changelog
* Mon Dec 23 2019 - siemkorteweg (at) users.sourceforge.net - 1.26.35-1
- Add README to install and refer to this file after install
- Several additions of collected data
* Tue May 14 2019 - siemkorteweg (at) users.sourceforge.net - 1.25.35-1
- Add bats tests
- Change copyright and support email address
- Extend collected data and reduce unwanted changes in logbook
* Thu May 10 2018 - siemkorteweg (at) users.sourceforge.net - 1.24.240-1
- Use new packaging method to transfer data to scc-srv. This requires at least release 1.18 of scc-srv.
- Busybox diff is fully supported.
- Many (vSphere) enhancements have been added.
* Sun Jun 25 2017 - siemkorteweg (at) users.sourceforge.net - 1.23.185-1
- Option handling has changed for scc, scc-log and scc-collect (-e and -S options).
- Many extensions of collected data have been implemented.
- Code has been cleaned to avoid messages and warnings of shellcheck.
* Tue Dec 1 2015 - siemkorteweg (at) users.sourceforge.net - 1.21.110-1
- In the general scripts, the option handling has been refactored and several processing enhancements have been implemented.
- The collection of data has been extended and changed to avoid unimportant changes in the logbook.
* Thu Jun 18 2015 - siemkorteweg (at) users.sourceforge.net - 1.20.125-1
- Bugfix to correctly eliminatie non-printable characters from snapshot.
* Wed Jun 10 2015 - siemkorteweg (at) users.sourceforge.net - 1.20.122-1
- The collected configuration data has been extended with many items and environments, for example docker, LXD/LXC and OpenStack.
- The generic spec file supports an install hierarchy adhering to FHS. 
* Thu Oct 30 2014 - siemkorteweg (at) users.sourceforge.net - 1.19.84-1
- The production of the SCC software packages has been changed to facilitate customization.
- SCC now runs correctly in a docker container.
* Wed Nov 23 2011 - siemkorteweg (at) users.sourceforge.net -
- Changes to satisfy rpmlint for Fedora and OpenSuSe.
