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

import sys
import os

import xbmc
import xbmcaddon

#from resources.lib.debugger import start_debugger
#start_debugger()

# *****************************************************************************************************************
#  IT IS EXTREMELY IMPORTANT THAT THE DIRECTORY WHERE THE FILE(S) THAT CONTAIN(S) THE CLASS DEFINITION(S) OF THE
#  OBJECT(S) THAT WILL BE SHARED BY THE SEVER IS (ARE) IN A PATH LOCATION ACCESSIBLE FROM ANYWHERE ANY CLIENT MAY
#  CONNECT.
#  Do not use realtive path imports at the time of object instantiation before registering on the server.
#  The client will not be able to retrieve the return structures and will generate an error.
sys.path.append(os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'lib'))
from datastore import DataObjects
# ******************************************************************************************************************

from ipc.ipcserver import IPCServer
from resources.lib.ipcclientx import IPCClient

myserver = None

def serverstart(host='localhost', port=9099):
    global myserver
    #  Following 2 lines start the IPC Server based on Pyro4 (see IPCServer definition for details)
    #
    #  .start() is required since the server is started in a separate thread. This done to prevent
    #    blocking and allow us to call in to stop thread during abort by holding a reference to the server daemon
    #    without this, an error is generated in the kodi logfile
    myserver = IPCServer(DataObjects(), host=host, port=port)
    xbmc.log('*&*&*&*& ipcdatastore: Attempting to start server on {0}:{1}'.format(host, port))
    myserver.start()

def testclient(host='localhost', port=9099):
    #  Now that the server is started, lets open a client connection and put some data in the store
    #    Obviously the server could be started by one addon and used by two other clients to communicate,
    #    but for demonstration purposes, lets store some data and then retrieve it in the example
    #    'script.ipcclient'
    #
    #  IPCClient() takes the same optional keyword args as listed above for IPCServer()
    #  Obviously you need to configure the client identically to the server for them to talk to one another
    #  In the example IPCServer, the object that is shared is a simple datastore
    #  It is designed with the following functions:
    #     For all calls, a pseudo namespace with the addon name is established to help prevent conflict with
    #     variable names potentially coming from different addons
    #  put(addon_name as string, variable_name as string, data)
    #    This is the simple form of put. data can be any type that can be accepted by the above datatype
    #  get(addon_name as string, variable_name as string) - returns data and timestamp
    #  delete(addon_name as string, variable_name as string)
    #     deletes the individual variable and it's value from the datastore
    #     returns the last data value and timestamp
    #  clear_all(addon_name) - deletes all of the data associated with the addon_name
    #     returns all of the data in a keyword dict
    client = IPCClient(host=host, port=port)
    xbmc.log('*&*&*&*& ipcdatastore: Attempting to contact server at: {0}'.format(client.uri))
    client.set('x', 20)
    y = client.get('x')
    if y != 20:
        raise ValueError('*&*&*&*& ipcdatastore: IPC Server check failed')
    else:
        xbmc.log('*&*&*&*& ipcdatastore: IPC Server passed connection test')

class MonitorSettings(xbmc.Monitor):
    def __init__(self):
        super(MonitorSettings, self).__init__()

    def onSettingsChanged(self):
        """
        Allows the server to start if not already started when the user changes the setting 'Start server' on the
        settings page to true. Currently will NOT restart server with a change in host or port.
        """
        if xbmcaddon.Addon().getSetting('startserver') == 'true' and myserver is None:
            start()

def start():
    host = xbmcaddon.Addon().getSetting('host')
    port = int(xbmcaddon.Addon().getSetting('port'))
    serverstart(host=host, port=port)
    xbmc.sleep(2000)
    testclient(host=host, port=port)

def main():
    monitor = MonitorSettings()
    if xbmcaddon.Addon().getSetting('startserver') == 'true':
        start()
    while not xbmc.abortRequested:
        xbmc.sleep(1000)
    #  If you don't call .stop() an error will turn up in the log when kodi terminates
    #  The above 'keep alive' loop is not truly necessary, as the server runs as a daemon, however under certain
    #  circumstances, if kodi exits erroneously, the thread may be left in memory and keep the process alive.
    #  If this occurs, you may not be able to restart kodi without manually terminating the orphaned process.
    if myserver is not None:
        myserver.stop()
    if myserver.running is False:
        xbmc.log('*&*&*&*& ipcdatastore: IPC Server Stopped')

if __name__ == '__main__':
    main()