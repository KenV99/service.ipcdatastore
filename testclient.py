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

import xbmc
import xbmcgui
import xbmcaddon

from resources.lib.ipcclientx import IPCClient

__settings__ = xbmcaddon.Addon("service.ipcdatastore")
__language__ = __settings__.getLocalizedString

client = IPCClient()
xbmc.log('*&*&*&*& ipcdatastore: Attempting to contact server at: {0}'.format(client.uri))
dialog = xbmcgui.Dialog()
if client.server_available():
    dl = client.get_data_list()
    x = client.get('x', author='service.ipcdatastore', requestor='testclient')
    if x == 20:
        dialog.ok(__language__(32007),__language__(32008))
    else:
        dialog.ok(__language__(32007), __language__(32009))
else:
    dialog.ok(__language__(32007), __language__(32010))