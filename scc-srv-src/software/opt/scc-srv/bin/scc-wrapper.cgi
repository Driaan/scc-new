#!/bin/sh

# Wrapper for shell script to handle SCC web server actions.
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
# ID:          $Id: scc-wrapper.cgi 6217 2019-03-22 18:46:12Z siemkorteweg $


ProgName=${0##*/};			export ProgName

set -u

export SCC_BIN=/opt/scc-srv/bin

PATH=/sbin:/usr/sbin:/usr/bin:/bin:${SCC_BIN};		export PATH

# The wrapper started in the cgi-bin directory, the CGI starts in the realm.
cd ..
realm_abs_path="$(pwd)"
exec ${SCC_BIN}/scc.cgi "${realm_abs_path##*/}" 2>/dev/null

exit 1
