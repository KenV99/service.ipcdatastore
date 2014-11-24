#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 KenV99
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#


def start_debugger(port=51234, suspend=False):
    import sys
    if 'win' in sys.platform:
        isKodi = 'XBMC' in sys.executable
    else:
        isKodi = True
    if isKodi:
        import xbmcvfs
        chkfileexists = xbmcvfs.exists
    else:
        import os
        chkfileexists = os.path.isfile
    if chkfileexists(r'C:\Program Files (x86)\JetBrains\PyCharm 4.0\pycharm-debug-py3k.egg'):
        sys.path.append(r'C:\Program Files (x86)\JetBrains\PyCharm 4.0\pycharm-debug-py3k.egg')
        import pydevd
        pydevd.settrace('localhost', port=port, stdoutToServer=True, stderrToServer=True, suspend=suspend)