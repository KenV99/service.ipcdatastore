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
#    along with this program. If not, see <http://www.gnu.org/license/>.



import sys
import os
import threading

import xbmc
import xbmcgui
import xbmcaddon

"""
.. note::
   IT IS EXTREMELY IMPORTANT THAT THE DIRECTORY WHERE THE FILE(S) THAT CONTAIN(S) THE CLASS DEFINITION(S) OF THE
   OBJECT(S) THAT WILL BE SHARED BY THE SEVER IS (ARE) IN A PATH LOCATION ACCESSIBLE FROM ANYWHERE ANY CLIENT MAY
   CONNECT.
   Do not use realtive path imports at the time of object instantiation before registering on the server.
   The client will not be able to retrieve the return structures and will generate an error.
   Either add the path of object direct to sys.path or use addon.xml to add a module type extension point to point
   to the path where the module containing the definition of the object to be shared resides
"""

path_to_shared_obj = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'lib')
if path_to_shared_obj not in sys.path:
    sys.path.insert(0, path_to_shared_obj)
from datastore import DataObjects
# ******************************************************************************************************************

path_to_required_modules = os.path.join(xbmcaddon.Addon('script.module.ipc').getAddonInfo('path'), 'lib')
if path_to_required_modules not in sys.path:
    sys.path.insert(0, path_to_required_modules)
from ipc.ipcserver import IPCServer

from resources.lib.ipcclientx import IPCClientX
from resources.lib.mediainfofromlog import get_log_mediainfo

myserver = None


def serverstart(data_name='kodi-IPC', host='localhost', port=9099):
    """

    This function starts the pyro4 server. It runs in a separate thread. See :class:ipc.ipcserver.IPCServer

    :param data_name: Arbitrary name for the data object being shared as a remote object
    :type data_name: str
    :param host: Specifies the resolvable hostname or IP address for the socket where the object will be shared.
    :type host: str
    :param port: The port for the socket
    :type port: int
    :return: None

    """

    #    .start() is required since the server is started in a separate thread. This done to prevent
    #    blocking and allow us to call in to stop thread during abort by holding a reference to the server daemon
    #    without doing this, an error is generated in the kodi logfile. The method of polling xbmc.abortrequested
    #    will likely be changed in the Helix final release.
    global myserver
    myserver = IPCServer(DataObjects(), name=data_name, host=host, port=port)
    xbmc.log('*&*&*&*& ipcdatastore: Attempting to start server on {0}:{1}'.format(host, port))
    myserver.start()


def testclient():
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
    client = IPCClientX(addon_id='service.ipcdatastore')
    xbmc.log('*&*&*&*& ipcdatastore: Attempting to contact server at: {0}'.format(client.uri))
    client.set('x', 20)
    y = client.get('x')
    if y != 20:
        raise ValueError('*&*&*&*& ipcdatastore: IPC Server check failed')
    else:
        xbmc.log('*&*&*&*& ipcdatastore: IPC Server passed connection test')


class PlayerServer(xbmc.Player):
    def __init__(self):
        super(PlayerServer, self).__init__()
        self.playingfile = None
        self.server_flag = False

    def onPlayBackStarted(self):
        # This actually puts the data on the server
        self.playingfile = self.getPlayingFile()
        mydict = get_log_mediainfo()
        client = IPCClientX(addon_id='service.ipcdatastore')
        client.raise_exception = True
        client.set('videodata', mydict, author='service.ipcdatastore')
        self.server_flag = True
        del client

    def onPlayBackResumed(self):
        if self.playingfile != self.getPlayingFile():
            self.onPlayBackStarted()

    def onPlayBackStopped(self):
        if self.server_flag:
            client = IPCClientX(addon_id='service.ipcdatastore')
            client.set('videodata', None)
            self.server_flag = False

    def onPlayBackEnded(self):
        self.onPlayBackStopped()


class PlayerClient(xbmc.Player):
    """
    .. class:: PlayerClient(xbmc.Player)

    Separate Player subclassed from xbmc.Player that would otherwise be instantiated from a different addon

    """

    def __init__(self):
        super(PlayerClient, self).__init__()
        self.playingfile = None

    def onPlayBackStarted(self):
        self.playingfile = self.getPlayingFile()
        client = IPCClientX(addon_id='service.ipcdatastore')
        data = None
        numchecks = 8
        while numchecks > 0:
            data = client.get('videodata', author='service.ipcdatastore')
            if data is None:
                xbmc.sleep(500)
                numchecks -= 1
            else:
                break
        dialog = xbmcgui.Dialog()
        if isinstance(data, dict):
            msg = '{0}x{1} @ {2}'.format(data['dwidth'], data['dheight'], data['fps'])
            dialog.notification('ipcdatastore', msg, None, 2000, True)
        else:
            dialog.notification('ipcdatastore', 'Time out error receiving data x {0}'.format(9 - numchecks),
                                None, 2000, True)

    def onPlayBackResumed(self):
        if self.playingfile != self.getPlayingFile():
            self.onPlayBackStarted()


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
    data_name = xbmcaddon.Addon().getSetting('data_name')
    serverstart(data_name=data_name, host=host, port=port)
    xbmc.sleep(2000)
    testclient()


def start_video_client():
    player = PlayerClient()
    while not xbmc.abortRequested:
        xbmc.sleep(250)


def main():
    monitor = MonitorSettings()
    if xbmcaddon.Addon().getSetting('startserver') == 'true':
        start()
        if xbmcaddon.Addon().getSetting('servevideo') == 'true':
            player_s = PlayerServer()
            if xbmcaddon.Addon().getSetting('showdata') == 'true':
                # Start the client that shows the video data in a separate thread to simulate it being started remotely
                # and prevent a threading conflict with the two player instances and the clients
                t = threading.Thread(target=start_video_client)
                t.start()
                pass
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