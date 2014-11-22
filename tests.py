#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 KenV99
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import shutil
import stat
import time
import unittest

if 'win' in sys.platform:
    isKodi = 'xbmc' in sys.executable.lower() or 'kodi' in sys.executable.lower()
else:
    isKodi = True
if isKodi:
    import xbmc
    import xbmcgui
    import xbmcaddon
    import xbmcvfs
    __language__ = xbmcaddon.Addon("service.ipcdatastore").getLocalizedString

    # ensure aceess to required script.module. Currently an issue in Helix Betas
    path_to_required_modules = os.path.join(xbmcaddon.Addon('script.module.ipc').getAddonInfo('path'), 'lib')
    if path_to_required_modules not in sys.path:
        sys.path.insert(0, path_to_required_modules)

# required modules outside local path
from ipc.ipcserver import IPCServer
import pyro4

# required modules that should be in local path
from resources.lib.ipcclientx import IPCClientX
from resources.lib.datastore import DataObjects
import resources.lib.ipcclientxerrors as ipcclientxerrors

# Globals
server = None
persist_dir = None
port = None


class TestIPCClient(unittest.TestCase):
    def senddata(self, client):
        self.data = {'int': 5, 'float': 1.314, 'str': 'abcdef', 'tuple': (7, 'hello'), 'list': [0, 8.1, 'goodbye'],
                     'dict': {'name': 'Ned Stark', 'deceased': True}}
        for key in self.data:
            client.set(key, self.data[key], author=self.name)

    def setUp(self):
        self.client = IPCClientX()
        self.name = 'tests.ipcdatastore'
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
        x = self.client.delete('tuple', author=self.name)
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
        x = self.client.get('int', author=self.name, requestor='tests', return_tuple=True)
        self.assertEqual(x.cached, False, msg='Failed to clear cache')

    def test_clearall(self):
        self.client.clearall()
        dl = self.client.get_data_list()
        self.assertEqual(dl, {}, msg='Failed to clear all')

    def test_save_restore(self):
        self.client.savedata(self.name)
        self.client.clearall()
        self.client.restoredata(self.name)
        dl = self.client.get_data_list()[self.name]
        k = self.data.keys()
        self.assertEqual(dl.sort(), k.sort(), msg='Failed save/restore')
        self.client.delete_data(self.name)

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
        self.assertEqual(self.client.server_available(), False, msg='Failed server_available testing for'
                                                                    ' unavail server')
        ee = None
        try:
            self.client.get('int', author=self.name)
        except Exception as e:
            ee = e
        self.assertEqual(ee.__class__.__name__, ipcclientxerrors.ServerUnavailableError.__name__, msg='Failed to raise'
                         ' ServerUnavailableError')
        self.client.raise_exception = False
        self.client.uri = tmp

    def test_persistence(self):
        global server
        self.client.set('persist', 3.14159, author=self.name, persist=True)
        server.stop()
        server = None
        server = IPCServer(DataObjects(persist_dir=persist_dir), port=port)
        server.start()
        x = self.client.get('persist', author=self.name, requestor='tests')
        self.client.remove_persistence('persist', author=self.name)
        self.assertEqual(x, 3.14159, msg='Failed persistence bulk test')

    def test_persistence_bu(self):
        global server
        self.client.set('persist', 3.14159, author=self.name, persist=True)
        self.client.get_exposed_object().setautosave(False)
        server.stop()
        server = None
        server = IPCServer(DataObjects(persist_dir=persist_dir), port=port)
        server.start()
        x = self.client.get('persist', author=self.name, requestor='tests')
        self.client.remove_persistence('persist', author=self.name)
        self.assertEqual(x, 3.14159, msg='Failed persistence backup test')


def runtests():
    global server, persist_dir, port
    default_dir_mod = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    default_file_mod = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH
    pyro4.config.COMMTIMEOUT = 2
    if isKodi:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__(32011), __language__(32012), __language__(32013))
        if ret == 0:
            return
        port = int(xbmcaddon.Addon("service.ipcdatastore").getSetting('port')) + 20
        persist_dir = xbmc.translatePath('special://masterprofile/addon_data/service.ipcdatastore/tests')
    else:
        port = 9099
        persist_dir = r"C:\Users\Ken User\AppData\Roaming\XBMC\userdata\addon_data\service.ipcdatastore\tests"
    if os.path.exists(persist_dir) is False:
        os.mkdir(persist_dir, default_dir_mod)
    else:
        os.chmod(persist_dir, default_dir_mod)
    server = IPCServer(DataObjects(persist_dir=persist_dir), port=port)
    server.start()
    time.sleep(2)
    client = IPCClientX(port=port)
    if isKodi:
        xbmc.log('*&*&*&*& ipcdatastore: Attempting to contact server at: {0}'.format(client.uri))
    else:
        print '*&*&*&*& ipcdatastore: Attempting to contact server at: {0}'.format(client.uri)
    if not client.server_available():
        if isKodi:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(32011), __language__(32014))
            return
        else:
            print 'Server down and could not be started'
            return
    if isKodi:
        path = xbmc.translatePath(r'special://masterprofile/addon_data/service.ipcdatastore')
        if xbmcvfs.exists(path) == 0:
            xbmcvfs.mkdirs(path)
        os.chmod(path, default_dir_mod)
        fn = os.path.join(path, 'test.log')
        if xbmcvfs.exists(fn) != 0:
            os.chmod(fn, default_file_mod)
    else:
        fn = 'test.log'
    try:
        with open(fn, 'a') as logf:
            logf.write('\n\nTests Started: {0}\n'.format(time.strftime('%x %I:%M %p %Z')))
            suite = unittest.TestLoader().loadTestsFromTestCase(TestIPCClient)
            unittest.TextTestRunner(stream=logf, verbosity=2).run(suite)
        server.stop()
    except Exception as e:
        if isKodi:
            dialog = xbmcgui.Dialog()
            if hasattr(e, 'message'):
                if e.message != '':
                    msg = e.message
                else:
                    msg = str(sys.exc_info()[1])
            else:
                msg = str(sys.exc_info()[1])
            dialog.ok('Error', msg)
            xbmc.log('*&*&*&*& ipcdatastore: Testing Error: {0}'.format(msg))
            if hasattr(sys.exc_info()[2], 'format_exc'):
                xbmc.log(sys.exc_info()[2].format_exc())
        return
    shutil.rmtree(persist_dir)
    if isKodi:
        os.chmod(path, default_dir_mod)
        os.chmod(fn, default_file_mod)
        dialog = xbmcgui.Dialog()
        text = '{0}: {1}'.format(__language__(32015), fn)
        dialog.ok(__language__(32016), text[0:50], text[50:])
        xbmc.log('*&*&*&*& ipcdatastore: Test suite run and logged')


if __name__ == '__main__':
    runtests()
