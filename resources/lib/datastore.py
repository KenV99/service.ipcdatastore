#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 KenV99
#
# This program is free software: you can redistribute it and/or modify
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

import os
import sys
import stat
import time
import gzip
import threading
import re
from cPickle import dump, load

if 'win' in sys.platform:
    isKodi = 'xbmc' in sys.executable.lower() or 'kodi' in sys.executable.lower()
else:
    isKodi = True
if isKodi:
    import xbmcaddon

    path_to_required_modules = os.path.join(xbmcaddon.Addon('script.module.ipc').getAddonInfo('path'), 'lib')
    if path_to_required_modules not in sys.path:
        sys.path.insert(0, path_to_required_modules)

import pyro4

IPCERROR_UKNOWN = 0
IPCERROR_NO_VALUE_FOUND = 1
IPCERROR_USE_CACHED_COPY = 2
IPCERROR_SERVER_TIMEOUT = 3
IPCERROR_CONNECTION_CLOSED = 4
IPCERROR_NONSERIALIZABLE = 5


class DataObjectBase(object):
    """
    Base class for DataObject and DataObjectX

    """
    def __init__(self):
        self.ts = None
        self.value = None


class DataObject(DataObjectBase):
    """
    Class of all objects returned by server. Includes object and timestamp.

    """
    def __init__(self, dox):
        """
        Requires instance of :class:`datastore.DataObjectX` during instantiation: that is the class actually stored
        in the datastore dict.

        :param dox: *Required*. See above.
        :type dox: DataObjectX()

        """

        super(DataObject, self).__init__()
        self.ts = dox.ts
        self.value = dox.value


class DataObjectX(DataObjectBase):
    """
    Class used to store objects in the datastore. Extends :class:`datastore.DataOnject` with a dict of requestors
    """
    def __init__(self, value, persist=False):
        """
        :param value: The object to be stored
        :type value: pickleable obj
        """
        super(DataObjectX, self).__init__()
        self.ts = time.time()
        self.value = value
        self.requestors = {}
        self.persist = persist


class DataIO(object):
    DEFAULT_DIR_MOD = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    DEFAULT_FILE_MOD = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH

    def __init__(self):
        pass

    @staticmethod
    def loadpersist(data_dir, datadict=None):
        pass
        return datadict

    @staticmethod
    def savepersist(data_dir, datadict):
        pass

    @staticmethod
    def savepicklethread(fn, obj):
        t = threading.Thread(target=DataIO.savepickle, args=(fn,obj))
        t.start()

    @staticmethod
    def savepickle(fn, obj):
        try:
            fn = '{0}.gz'.format(fn)
            path = os.path.dirname(fn)
            os.chmod(path, DataIO.DEFAULT_DIR_MOD)
            output = gzip.open(fn, 'wb')
            dump(obj, output, -1)
            output.close()
            os.chmod(fn, DataIO.DEFAULT_FILE_MOD)
            return True
        except:
            return False

    @staticmethod
    def restorepickle(fn):
        """

        :param fn: Filename.
        :type fn: str
        :return:
        :rtype: list or dict or DataObject or None
        """
        fn = '{0}.gz'.format(fn)
        if os.path.exists(fn) is False:
            return False
        try:
            path = os.path.dirname(fn)
            os.chmod(path, DataIO.DEFAULT_DIR_MOD)
            os.chmod(fn, DataIO.DEFAULT_FILE_MOD)
            inputf = gzip.open(fn, 'rb')
            restore = load(inputf)
            inputf.close()
        except:
            return None
        else:
            return restore

    @staticmethod
    def cleanbus(path, fn=None):
        if fn is None:
            for fn in os.listdir(path):
                if fn[0] == '@':
                    i = 5
                    while i > 0:
                        try:
                            os.remove(os.path.join(path, fn))
                        except:
                            time.sleep(0.1)
                            i -= 1
                        else:
                            break
        else:
            fn = os.path.join(path, fn)
            if os.path.exists(fn):
                os.remove(fn)

    @staticmethod
    def idxfromfn(fn):
        pattern = r"@(?P<author>.+)~(?P<varname>.+)\.p\.gz"
        match = re.search(pattern, fn)
        return match.group('author'), match.group('varname')


class DataObjects(object):
    """
    The actual datastore object whose methods are exposed via pyro4.proxy
    """
    STATE_OPENED = 'open'
    STATE_CLOSED = 'closed'

    def __init__(self, persist_dir=None):
        """
        If you desire to allow data to persist between Kodi sessions, the directory to store persistent data
        is needed at the time of instantiation in order to restore any saved data, if any exists.

        :param persist_dir: the directory where the persistent data is stored
        :type persist_dir: str
        """
        self.persist_dir = persist_dir
        self.__odict = {}
        if persist_dir is not None:
            self._restorepersist()
            self._savepersist(DataObjects.STATE_OPENED)
        self.__state = DataObjects.STATE_OPENED
        self.autosave = True

    @pyro4.oneway
    def setautosave(self, val):
        """
        If True will save data when object deleted or .close() called

        :param val: True or False
        :type val: bool
        """
        self.autosave = val

    @pyro4.oneway
    def set(self, name, value, author, persist=False):
        """
        :param name:
        :type name: str
        :param value:
        :type value: object
        :param author:
        :type author: str
        :param persist:
        :type persist: bool
        :returns: Nothing
        """
        dox = DataObjectX(value, persist)
        idx = (str(author), str(name))
        self.__odict[idx] = dox
        if persist is True and self.persist_dir is not None:
            self._savepersist_bu(name, author)

    def get(self, requestor, name, author, force=False):
        """

        :param requestor:
        :type requestor: str
        :param name:
        :type name: str
        :param author:
        :type author: str
        :param force:
        :type force: bool
        :return: Either a dataoject or a one byte message code
        :rtype: :class:`datastore.DataObject` or one character str
        """
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

    def delete(self, name, author):
        """

        :param name:
        :type name: str
        :param author:
        :type author: str
        :return: Either a dataoject or a one byte message code
        :rtype: :class:`datastore.DataObject` or one character str
        """
        idx = (str(author), str(name))
        if idx in self.__odict:
            if self.__odict[idx].persist is True:
                self.remove_persistence(name, author)
            dox = self.__odict.pop(idx)
            do = DataObject(dox)
            return do
        else:
            return chr(IPCERROR_NO_VALUE_FOUND)

    def get_data_list(self, author=None):
        """

        :param author:
        :type author: str
        :return:
        :rtype: dict with author(s) as key(s)
        """
        dl = {}
        for key in self.__odict.keys():
            if key[0] == author or author is None:
                if key[0] in dl:
                    dl[key[0]].append(key[1])
                else:
                    dl[key[0]] = [key[1]]
        return dl

    @pyro4.oneway
    def clearall(self):
        """

        :return: Nothing
        """
        self.__odict = {}

    def savedata(self, author, fn):
        """

        :param author:
        :type author: str
        :param fn:
        :type fn: str
        :return: True on success, False on failure
        :rtype: bool
        """
        save = {}
        for key in self.__odict:
            if key[0] == author:
                tmp = self.__odict[key]
                tmp.requestors = {}
                save[key] = tmp
        ret = DataIO.savepickle(fn, save)
        return ret

    def restoredata(self, author, fn):
        """

        :param author:
        :type author: str
        :param fn:
        :type fn: str
        :return: True on success, False on failure
        :rtype: bool
        """
        restore = DataIO.restorepickle(fn)
        if restore is not False:
            for key in restore:
                if key[0] == author:
                    self.__odict[key] = restore[key]
            return True
        return False

    @pyro4.oneway
    def clearcache(self, requestor):
        """

        :param requestor:
        :type requestor: str
        :return: Nothing
        """
        for key in self.__odict:
            if requestor in self.__odict[key].requestors:
                del self.__odict[key].requestors[requestor]

    @pyro4.oneway
    def close(self):
        """
        Explicitly write persistent data to a file in anticipation of shutting down.

        """
        if self.persist_dir is not None and self.autosave is True:
            self._savepersist(DataObjects.STATE_CLOSED)
        self.__state = DataObjects.STATE_CLOSED

    def __del__(self):
        if self.__state == DataObjects.STATE_OPENED and self.autosave is True:
            self.close()

    def _savepersist_bu(self, varname, author):
        do = DataObject(self.__odict[(author, varname)])
        sfn = '@{0}~{1}.p'.format(author, varname)
        fn = os.path.join(self.persist_dir, sfn)
        DataIO.savepicklethread(fn, do)

    def _restorepersist_bu(self, varname, author):
        sfn = '@{0}~{1}.p'.format(author, varname)
        fn = os.path.join(self.persist_dir, sfn)
        do = DataIO.restorepickle(fn)
        dox = DataObjectX(do.value, persist=True)
        dox.ts = do.ts
        idx = (str(author), str(varname))
        self.__odict[idx] = dox

    def _savepersist(self, dos_state):
        persist = [dos_state]
        pdict = {}
        for key in self.__odict:
            wt = self.__odict[key]
            if wt.persist is True:
                do = DataObject(wt)
                pdict[key] = do
        persist.append(pdict)
        fn = os.path.join(self.persist_dir, 'persist.p')
        DataIO.savepickle(fn, persist)
        if dos_state == DataObjects.STATE_CLOSED:
            DataIO.cleanbus(self.persist_dir)

    def _restorefrombu(self):
        for fn in os.listdir(self.persist_dir):
            if fn[0] == '@':
                idx = DataIO.idxfromfn(fn)
                fullfn = os.path.join(self.persist_dir, fn)
                fullfn = fullfn[0: len(fullfn)-3]
                do = DataIO.restorepickle(fullfn)
                if do is not None:
                    dox = DataObjectX(do.value, persist=True)
                    dox.ts = do.ts
                    self.__odict[idx] = dox
        DataIO.cleanbus(self.persist_dir)

    def _restorepersist(self):
        fn = os.path.join(self.persist_dir, 'persist.p')
        persist = DataIO.restorepickle(fn)
        if persist:
            last_saved_state = persist[0]
            pdict = persist[1]
            if last_saved_state == DataObjects.STATE_OPENED:
                self._restorefrombu()
            else:
                for key in pdict:
                    wt = pdict[key]
                    dox = DataObjectX(wt.value, True)
                    dox.ts = wt.ts
                    self.__odict[key] = dox

    def add_persistence(self, varname, author):
        """
        Adds a persistence tag to a pre-existing stored object and saves data to backup.

        :param varname:
        :type varname: str
        :param author:
        :type author: str
        :return: True on success, False on failure
        :rtype: bool
        """
        if self.persist_dir is not None:
            idx = (author, varname)
            self.__odict[idx].persist = True
            self._savepersist_bu(varname, author)
            return True
        else:
            return False

    def remove_persistence(self, varname, author):
        """
        Removes the persistence tag from a stored object and deletes it from backup.

        :param varname:
        :type varname: str
        :param author:
        :type author: str
        :return: True on success, False on failure
        :rtype: bool
        """
        if self.persist_dir is not None:
            sfn = '@{0}~{1}.p.gz'.format(author, varname)
            DataIO.cleanbus(self.persist_dir, sfn)
            idx = (author, varname)
            self.__odict[idx].persist = False
            return True
        else:
            return False