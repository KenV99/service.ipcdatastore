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

import time
from cPickle import PickleError, PicklingError, dump, load

IPCERROR_UKNOWN = 0
IPCERROR_NO_VALUE_FOUND = 1
IPCERROR_USE_CACHED_COPY = 2
IPCERROR_SERVER_TIMEOUT = 3
IPCERROR_CONNECTION_CLOSED = 4
IPCERROR_NONSERIALIZABLE = 5
# ipcerror_codestomsg = {
#     IPCERROR_UKNOWN: 'Unknown error',
#     IPCERROR_NO_VALUE_FOUND: 'No value found for index',
#     IPCERROR_USE_CACHED_COPY: 'Use cached copy',
#     IPCERROR_SERVER_TIMEOUT: 'Server not responding',
#     IPCERROR_CONNECTION_CLOSED: 'Sever connection closed',
#     IPCERROR_NONSERIALIZABLE: 'Object not serializable'
# }


class DataObjectBase(object):
    def __init__(self):
        self.ts = None
        self.value = None

class DataObject(DataObjectBase):
    def __init__(self, dox):
        super(DataObject, self).__init__()
        self.ts = dox.ts
        self.value = dox.value

class DataObjectX(DataObjectBase):
    def __init__(self, value):
        super(DataObjectX, self).__init__()
        self.ts = time.time()
        self.value = value
        self.requestors = {}

class DataObjects(object):
    def __init__(self):
        self.__odict = {}

    def set(self, author, name, value):
        dox = DataObjectX(value)
        idx = (str(author), str(name))
        self.__odict[idx] = dox

    def get(self, requestor, author, name, force=False):
        idx = (str(author), str(name))
        if idx in self.__odict:
            dox = self.__odict[idx]
            do = DataObject(dox)
            if requestor in dox.requestors and force is False:
                if dox.requestors[requestor] == dox.ts:
                    return chr(IPCERROR_USE_CACHED_COPY)
                else:
                    dox.requestors[requestor] = dox.ts
                    return do
            else:
                dox.requestors[requestor] = dox.ts
                return do
        else:
            return chr(IPCERROR_NO_VALUE_FOUND)

    def delete(self, author, name):
        idx = (str(author), str(name))
        if idx in self.__odict:
            dox = self.__odict.pop(idx)
            do = DataObject(dox)
            return do
        else:
            return chr(IPCERROR_NO_VALUE_FOUND)

    def get_data_list(self, author=None):
        dl = {}
        for key in self.__odict.keys():
            if key[0] == author or author is None:
                if key[0] in dl:
                    dl[key[0]].append(key[1])
                else:
                    dl[key[0]] = [key[1]]
        return dl

    def clearall(self):
        self.__odict = {}

    def savedata(self, author, fn):
        save = {}
        for key in self.__odict:
            if key[0] == author:
                tmp = self.__odict[key]
                tmp.requestors = {}
                save[key] = tmp
        try:
            output = open(fn, 'wb')
            dump(save, output, -1)
            output.close()
        except Exception as e:
            pass

    def restoredata(self, author, fn):
        try:
            inputf = open(fn, 'rb')
            restore = load(inputf)
            inputf.close()
        except Exception as e:
            pass
        else:
            for key in restore:
                self.__odict[key] = restore[key]

    def clearcache(self, requestor):
        for key in self.__odict:
            if requestor in self.__odict[key].requestors:
                del self.__odict[key].requestors[requestor]

