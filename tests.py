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
import time
import unittest

try:
    from ipcclientx import IPCClient
except:
    from resources.lib.ipcclientx import IPCClient
try:
    from datastore import DataObjects
except:
    from resources.lib.datastore import DataObjects
try:
    import ipcclientxerrors
except:
    import resources.lib.ipcclientxerrors as ipcclientxerrors

from ipcserver import IPCServer
import pyro4

if 'win' in sys.platform:
    isKodi = 'XBMC' in sys.executable
else:
    isKodi = True
if isKodi:
    import xbmc
    import xbmcgui
    import xbmcaddon
    import xbmcvfs
    __settings__ = xbmcaddon.Addon("service.ipcdatastore")
    __language__ = __settings__.getLocalizedString

def platform():
    if isKodi:
        if xbmc.getCondVisibility('system.platform.android'):
            return 'android'
        elif xbmc.getCondVisibility('system.platform.linux'):
            return 'linux'
        elif xbmc.getCondVisibility('system.platform.windows'):
            return 'windows'
        elif xbmc.getCondVisibility('system.platform.osx'):
            return 'osx'
        elif xbmc.getCondVisibility('system.platform.atv2'):
            return 'atv2'
        elif xbmc.getCondVisibility('system.platform.ios'):
            return 'ios'
    else:
        return sys.platform

class TestIPCClient(unittest.TestCase):

    def senddata(self, client):
        self.data = {'int': 5, 'float':1.314, 'str':'abcdef', 'tuple':(7, 'hello'), 'list':[0, 8.1, 'goodbye'],
                     'dict':{'name':'Ned Stark', 'deceased':True}}
        for key in self.data:
            client.set(key, self.data[key], author=self.name)

    def setUp(self):
        self.client = IPCClient()
        self.name = 'ipcdatastore'
        self.senddata(self.client)


    def test_get(self):
        for key in self.data:
            x = self.client.get(key, author=self.name, requestor='tests')
            self.assertEqual(x, self.data[key], msg='Failed get for: {0}'.format(key))

    def test_get_ts(self):
        for key in self.data:
            x = self.client.get(key, author=self.name, requestor='tests', return_tuple=True)
            ts = x.ts
            if hasattr(self, 'assertIsInstance'):
                self.assertIsInstance(ts, float, msg='Failed get timestamp for: {0}'.format(key))
            else:
                if isinstance(ts, float):
                    test = -1
                else:
                    test = 0
                self.assertEqual(test, -1, msg='Failed get timestamp for: {0}'.format(key))

    def test_get_data_list(self):
        dl = self.client.get_data_list()[self.name]
        if isinstance(dl, list):
            k = self.data.keys()
            self.assertEqual(dl.sort(), k.sort(), msg='Failed: data lists not equivalent')
        else:
            self.assertEqual(1, 2, 'Failed: data list returned in wrong format')

    def test_delete(self):
        x = self.client.delete('tuple')
        self.assertEqual(x, self.data['tuple'], msg='Failed to return data on delete')
        x = self.client.get('tuple')
        self.assertEqual(x, None, msg='Failed to return None after delete')

    def test_cache(self):
        x = self.client.get('str', author=self.name, requestor='tests', return_tuple=True)
        self.assertEqual(x.cached, False, msg='Failed due to value cached on first pass')
        x = self.client.get('str', author=self.name, requestor='tests', return_tuple=True)
        self.assertEqual(x.cached, True, msg='Failed to cache value')

    def test_clearcache(self):
        x = self.client.get('int', author=self.name, requestor='tests', return_tuple=True)
        self.assertEqual(x.cached, False, msg='Failed due to value cached on first pass')
        self.client.clearcache()
        x = self.client.get('int', author = self.name, requestor='tests', return_tuple=True)
        self.assertEqual(x.cached, False, msg='Failed to clear cache')

    def test_clearall(self):
        dl = self.client.get_data_list()[self.name]
        self.client.clearall()
        dl = self.client.get_data_list()
        self.assertEqual(dl, {}, msg='Failed to clear all')

    def test_save_restore(self):
        dl = self.client.get_data_list()[self.name]
        self.client.savedata(self.name)
        self.client.clearall()
        dl = self.client.get_data_list()
        self.client.restoredata(self.name)
        dl = self.client.get_data_list()[self.name]
        k = self.data.keys()
        self.assertEqual(dl.sort(), k.sort(), msg='Failed save/restore')

    def test_unserializable_error(self):
        self.client.raise_exception = True
        ee = None
        try:
            self.client.set(self.name, self.client.get)
        except Exception as e:
            ee = e
        self.assertEqual(ee.__class__.__name__, ipcclientxerrors.ObjectNotSerializableError.__name__, msg='Failed'
                                                                                            ' pickle exception testing')
        self.client.raise_exception = False

    def test_valuenotfound_error(self):
        self.client.raise_exception = True
        ee = None
        try:
            self.client.get('garbage')
        except Exception as e:
            ee = e
        self.assertEqual(ee.__class__.__name__, ipcclientxerrors.VarNotFoundError.__name__, msg='Failed to raise value'
                                                                                                ' not found error')
        self.client.raise_exception = False

    def test_serverunavailable_error(self):
        tmp = self.client.uri
        self.client.raise_exception = True
        self.client.num_of_server_retries = 1
        self.client.uri = 'PYRO:kodi-IGA@localhost:9990'
        self.assertEqual(self.client.server_available(), False, msg='Failed server_available testing for unavail server')
        ee= None
        try:
            self.client.get('x')
        except Exception as e:
            ee=e
        self.assertEqual(ee.__class__.__name__, ipcclientxerrors.ServerUnavailableError.__name__, msg='Failed to raise'
                                                                                              ' ServerUnavailableError')
        self.client.raise_exception = False
        self.client.uri = tmp

def runtests():
    pyro4.config.COMMTIMEOUT = 2
    if isKodi:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__(32011), __language__(32012), __language__(32013))
        if ret == 0:
            return
    client = IPCClient()
    if client.server_available():
        serverstartedfortest = False
    else:
        server = IPCServer(DataObjects())
        server.start()
        time.sleep(2)
        if not client.server_available():
            if isKodi:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(32011), __language__(32014))
                return
            else:
                print 'Server down and could not be started'
                return
        else:
            serverstartedfortest = True

    if isKodi:
        path = xbmc.translatePath(r'special://masterprofile/addon_data/service.ipcdatastore/')
        if xbmcvfs.exists(path) == 0:
            xbmcvfs.mkdirs(path)
        os.chmod(path, 0666)
        fn = os.path.join(path, 'test.log')
        if xbmcvfs.exists(fn) != 0:
            os.chmod(fn, 0666)
    else:
        fn = 'test.log'
    try:
        with open(fn, 'a') as logf:
            logf.write('\n\nTests Started: {0}\n'.format(time.strftime('%x %I:%M %p %Z')))
            if serverstartedfortest:
                logf.write('Server started for testing\n\n')
            else:
                logf.write('Using server previously started for tests\n')
            suite = unittest.TestLoader().loadTestsFromTestCase(TestIPCClient)
            unittest.TextTestRunner(stream = logf, verbosity=2).run(suite)
            if serverstartedfortest:
                logf.write('Stopping server\n')
                server.stop()
            else:
                client = IPCClient()
                client.set('x', 20, 'ipcdatastore')
    except Exception as e:
        if isKodi:
            dialog = xbmcgui.Dialog()
            dialog.ok('Error', e.message)
            xbmc.log('IPC Datastore Testing Error: {0}'.format(e.message))
            xbmc.log(sys.exc_info()[3].format_exc())
        return
    if isKodi:
        dialog = xbmcgui.Dialog()
        text = '{0}: {1}'.format(__language__(32015), fn)
        dialog.ok(__language__(32016), text[0:50], text[50:])
        xbmc.log('IPC Server test suite run and logged')


if __name__ == '__main__':
    runtests()


