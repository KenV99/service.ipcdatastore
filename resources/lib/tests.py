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

from resources.lib.ipcclientx import IPCClient
import unittest

class TestIPCClient(unittest.TestCase):

    def senddata(self, client):
        self.data = {'int': 5, 'float':1.314, 'str':'abcdef', 'tuple':(7, 'hello'), 'list':[0, 8.1, 'goodbye'],
                     'dict':{'name':'Ned Stark', 'deceased':True}}
        for key in self.data:
            client.set(key, self.data[key])

    def setUp(self):
        self.client = IPCClient()
        self.name = 'ipcdatastore'
        self.senddata(self.client)

    def test_get(self):
        for key in self.data:
            x = self.client.get(self.name, key)
            self.assertEqual(x, self.data[key], msg='Failed get for: {0}'.format(key))

    def test_get_ts(self):
        for key in self.data:
            x = self.client.get(self.name, key, ts=True)
            ts = x[1]
            self.assertIsInstance(ts, float, msg='Failed get timestamp for: {0}'.format(key))

    def test_get_data_list(self):
        dl = self.client.get_data_list()[self.name]
        self.assertIsInstance(dl, list, msg='Failed to get list for get_data_list')
        if isinstance(dl, list):
            k = self.data.keys()
            self.assertEqual(dl.sort(), k.sort())

    def test_delete(self):
        x = self.client.delete(self.name, 'tuple')
        self.assertEqual(x, self.data['tuple'], msg='Failed to return data on delete')
        x = self.client.get(self.name, 'tuple')
        self.assertIs(x, None, msg='Failed to return None after delete')

    def test_cache(self):
        x = self.client.get(self.name,'str',retiscached=True)
        self.assertIs(x[1],False, msg='Failed due to value cached on first pass')
        x = self.client.get(self.name,'str',retiscached=True)
        self.assertIs(x[1], True, msg='Failed to cache value')

    def test_clearcache(self):
        x = self.client.get(self.name,'int',retiscached=True)
        self.assertIs(x[1],False, msg='Failed due to value cached on first pass')
        self.client.clearcache()
        x = self.client.get(self.name,'int',retiscached=True)
        self.assertIs(x[1], False, msg='Failed to clear cache')

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
        self.assertEqual(dl.sort(), k.sort())


if __name__ == '__main__':
    unittest.main()



