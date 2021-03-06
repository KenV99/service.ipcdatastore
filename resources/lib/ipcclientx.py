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
from collections import namedtuple
from cPickle import PickleError, PicklingError

if 'win' in sys.platform:
    isKodi = 'xbmc' in sys.executable.lower() or 'kodi' in sys.executable.lower()
else:
    isKodi = True

if isKodi:
    import xbmc
    import xbmcaddon
    import xbmcvfs
    # ensure access to shared object definition
    path_to_shared_obj = os.path.join(xbmcaddon.Addon('service.ipcdatastore').getAddonInfo('path'), 'resources', 'lib')
    if path_to_shared_obj not in sys.path:
        sys.path.insert(0, path_to_shared_obj)

    # ensure aceess to required script.module. Currently an issue in Helix Beta 2
    path_to_required_modules = os.path.join(xbmcaddon.Addon('script.module.ipc').getAddonInfo('path'), 'lib')
    if path_to_required_modules not in sys.path:
        sys.path.insert(0, path_to_required_modules)
else:
    try:
        from xbmcdummy import xbmc, xbmcaddon, xbmcvfs
    except:
        from resources.lib.xbmcdummy import xbmc, xbmcaddon, xbmcvfs

# required modules outside local path
import pyro4
import pyro4.errors
import pyro4.util
from ipc.ipcclient import IPCClient as IPCClient

# required modules that should be in local path
import resources.lib.ipcclientxerrors as ipcclientxerrors
from resources.lib.caller_name import caller_name

__callingmodule__ = caller_name()

DEBUG = False
if DEBUG:
    from datastore import DataObjects

class IPCClientX(IPCClient):
    """
    Subclasses IPCClient from script.module.ipc and extends functionality for a datastore object

    """

    def __init__(self, addon_id='', name='kodi-IPC', host='localhost', port=9099, datatype='pickle'):
        """
        :param addon_id: *Optional keyword*. If specified, this supersedes the name/port/host. IPCClient checks
                            settings.xml for the info.
        :type addon_id: str
        :param name: *Optional keyword*. Arbitrary name for the object being used, must match the name used by server
        :type name: str
        :param port: *Optional keyword*. Port matching server port
        :type port: int
        :param datatype: *Optional keyword*. Type of data transport being used options: pickle, serpent, json,
                          marshall. Must match server.
        :type datatype: str

        There are two useful *public* attributes than can be changed after instantiation:

        ==========================  =============================================================================
        ``raise_exception``:        | When set to True, will raise exceptions that can be caught rather than
                                    | failing silently, which is the default behavior.
        ``num_of_server_retries``:  | If the client fails to connect to the server, the number of retries before
                                    | failing finally.
        ==========================  =============================================================================

        """
        super(IPCClientX, self).__init__(addon_id, name, host, port, datatype)
        self.cache = {}
        if __callingmodule__ == 'default.py':
            self.addonname = xbmcaddon.Addon().getAddonInfo('id')
        else:
            self.addonname = 'service.ipcdatastore'
        self.raise_exception = False
        self.num_of_server_retries = 5
        self.ReturnData = namedtuple('Data', ['value', 'ts', 'cached'])
        if DEBUG:
            self.dos = DataObjects()
            self.dos.set('x', 20, 'ipcdatastore')

    @staticmethod
    def logexception(exc):
        xbmc.log(exc.message)
        if hasattr(exc, 'tb'):
            xbmc.log(exc.tb)

    def __callwrapper(self, calltype, *args):
        retries = self.num_of_server_retries
        err = -1
        do = None
        exc = None
        while retries > 0:
            try:
                if DEBUG:
                    dos = self.dos
                else:
                    dos = pyro4.Proxy(self.uri)
                do = getattr(dos, calltype)(*args)
            except pyro4.errors.ConnectionClosedError:
                retries -= 1
                if not DEBUG and dos:
                    dos._pyroReconnect()
                err = ipcclientxerrors.IPCERROR_CONNECTION_CLOSED
                exc = ipcclientxerrors.ServerReconnectFailedError
            except pyro4.errors.CommunicationError:
                retries -= 1
                err = ipcclientxerrors.IPCERROR_SERVER_TIMEOUT
            except (PickleError, PicklingError, TypeError):
                # TypeError is what you get when using cPickle and the object is not serializable for some reason
                err = ipcclientxerrors.IPCERROR_NONSERIALIZABLE
                break
            except Exception:
                err = ipcclientxerrors.IPCERROR_UKNOWN
                break
            else:
                err = -1
                if not DEBUG and dos:
                    dos._pyroRelease()
                break
        #  Client side errors
        if err == ipcclientxerrors.IPCERROR_SERVER_TIMEOUT:
            exc = ipcclientxerrors.ServerUnavailableError(self.uri, self.get_traceback())
        elif err == ipcclientxerrors.IPCERROR_CONNECTION_CLOSED:
            exc = ipcclientxerrors.ServerReconnectFailedError(self.uri, self.get_traceback())
        elif err == ipcclientxerrors.IPCERROR_NONSERIALIZABLE:
            exc = ipcclientxerrors.ObjectNotSerializableError()
        elif err == ipcclientxerrors.IPCERROR_UKNOWN:
            exc = ipcclientxerrors.UnknownError(sys.exc_info()[1], self.get_traceback())
        # Server side errors
        elif do is not None:
            if isinstance(do, str):
                # To minimize the amount of data sent back during an error, the error is sent as a one byte string
                err = ord(do)
                if err == ipcclientxerrors.IPCERROR_NO_VALUE_FOUND:
                    exc = ipcclientxerrors.VarNotFoundError()
                elif err == ipcclientxerrors.IPCERROR_USE_CACHED_COPY:
                    exc = ipcclientxerrors.UseCachedCopyError()
                elif err == ipcclientxerrors.IPCERROR_SAVEFAILED:
                    exc = ipcclientxerrors.SaveFailedError()
                elif err == ipcclientxerrors.IPCERROR_RESTOREFAILED:
                    exc = ipcclientxerrors.RestoreFailedError()
                elif err != -1:
                    exc = ipcclientxerrors.UnknownError(sys.exc_info()[1], self.get_traceback())
        if exc is not None:
            exc.errno = err
        else:
            exc = ipcclientxerrors.NoError()
        return do, exc

    def set(self, name, value, author=None, persist=False):
        """
        Sets a value on the server. Automatically adds the addon name as the author. The value is any valid object
        that can be accepted by the chosen datatype (see :class:`above <IPCClientX>`). If the class attribute
        raise_exception is True, will raise an exception with failure.

        :param name: *Required*. The variable name
        :type name: str
        :param value: *Required*. The value of the variable
        :type name: Any object type compatible with the datatype transport
        :param author: *Optional keyword*. The originator of the data which along with the variable name is used
                        as the primary key for the backend dictionary for storing the item.
        :type author: str
        :param persist: Flag data to be saved between Kodi sessions
        :type persist: bool
        :returns: True for success, False for failure
        :rtype: bool

        """
        if author is None:
            author = self.addonname
        do, exc = self.__callwrapper('set', name, value, author, persist)
        if exc.errno == ipcclientxerrors.IPCERROR_NONSERIALIZABLE:
            exc.updatemessage(value)
        if exc.errno != -1:
            self.logexception(exc)
            if self.raise_exception:
                raise exc
            else:
                return False
        else:
            return True

    def __setreturn(self, do, cached=False, return_tuple=False):
        """
        Assembles the return to be either a single object or a list of objects depending on the options during the
        call.
        :type do: DataObject(), None
        :type cached: bool
        :type return_tuple: bool
        :return: Either the stored item or a :py:class:`collections.namedtuple` containing the stored item followed by
                 the timestamp(float) and whether or not the item was returned from the cache
        :rtype: object or namedtuple('Data', ['value', 'ts', 'cached'])
        """
        if do is not None:
            value = do.value
            ts = do.ts
        else:
            value = None
            ts = None
        if return_tuple:
            ret = self.ReturnData(value, ts, cached)
        else:
            ret = value
        return ret

    def __get(self, name, author, requestor, force=False):
        do, exc = self.__callwrapper('get', requestor, name, author, force)
        return do, exc

    def get(self, name, author=None, requestor=None, return_tuple=False):
        """
        Retrieves data from the server based on author and variable name, optionally returns a
        :py:func:`namedtuple <collections.namedtuple>` which also includes time stamp (float) and a bool representing
        whether or not the item came from the local cache.
        There is a caching function implemented such that the server tracks addon requests for data - if the most recent
        version has already been received by the client, a message is sent to the client to look in it's cache for the
        data. There is a fallback such that if the data is NOT in the cache, the server then provides the data. Each
        piece of data that is received is locally cached for this purpose.

        If returning a :py:func:`namedtuple <collections.namedtuple>`, the parameters can be accessed as follows::

           nt = client.get('x', author='me', requestor='me', return_tuple=True)
           x = nt.value
           x_timestamp = nt.ts
           x_was_cached = nt.cached

        :param name: *Required*. The variable name
        :type name: str
        :param author: *Optional keyword*. The author of the data. All of the data is indexed by author and variable
                        name in order to reduce variable name overlap. If not supplied, the addon name is used.
        :type author: str
        :param requestor: *Optional keyword*. The name of the requestor of the data. Defaults to the addon name if
                            found. Used for caching.
        :type requestor: str
        :param return_tuple: *Optional keyword*. Whether to return the stored object or a named tuple containing the
                              object, the timestamp and a bool indicating that the object came from the local cache.
                              The named tuple returns the value, ts and cached.
        :type return_tuple: bool
        :return: Either the value(object) assigned to 'name' or a :py:func:`namedtuple <collections.namedtuple>`
                 containing the value, ts and/or if the item came from the local cache.
        :rtype: object or :py:func:`namedtuple <collections.namedtuple>` defined as:
                ``('Data', ['value', 'ts', 'cached'])``

        """
        if author is None:
            author = self.addonname
        if requestor is None:
            requestor = self.addonname
        idx = (author, name)
        do, exc = self.__get(name, author, requestor)
        if exc.errno == ipcclientxerrors.IPCERROR_USE_CACHED_COPY:
            if idx in self.cache:
                do = self.cache[idx]
                return self.__setreturn(do, cached=True, return_tuple=return_tuple)
            else:  # SHOULD BE IN CACHE, SO FORCE SERVER TO PROVIDE
                do, exc = self.__get(name, author, requestor, force=True)
                if exc.errno == ipcclientxerrors.IPCERROR_NO_VALUE_FOUND:
                    exc.varname = name
                    exc.author = author
                if exc.errno != -1:
                    self.logexception(exc)
                    if self.raise_exception:
                        raise exc
                    else:
                        return self.__setreturn(None, return_tuple=return_tuple)
                else:
                    self.cache[idx] = do
                    return self.__setreturn(do, return_tuple=return_tuple)
        elif exc.errno == ipcclientxerrors.IPCERROR_NO_VALUE_FOUND:
            exc.updatemessage(name, author)
        if exc.errno != -1:
            self.logexception(exc)
            if self.raise_exception:
                raise exc
            else:
                return self.__setreturn(None, return_tuple=return_tuple)
        else:
            self.cache[idx] = do
            return self.__setreturn(do, return_tuple=return_tuple)

    def delete(self, name, author=None, return_tuple=False):
        """
        Deletes an item from the datastore and returns the deleted item's value. Returns None if not found or raises
        an exception if the IPCClientX.raise_exceptions attribute is set to True. The return item is optionally returned
        as a namedtuple (see :func:`get() <IPCClientX.get>`).

        :param name: *Required*. The name of the variable to be deleted.
        :type name: str
        :param author: *Optional keyword*. The author of the data. Defaults to the addon id.
        :type author:
        :param return_tuple: *Optional keyword*. Flag to return data as namedtuple as in :func:`ipcclientx.IPCClientX.get`
        :type return_tuple: bool
        :return:
        :rtype: object or :py:func:`namedtuple <collections.namedtuple>`, None on failure

        """
        if author is None:
            author = self.addonname
        do, exc = self.__callwrapper('delete', name, author)
        if exc.errno == ipcclientxerrors.IPCERROR_NO_VALUE_FOUND:
            exc.updatemessage(name, author)
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return self.__setreturn(None, return_tuple=return_tuple)
        else:
            idx = (author, name)
            if idx in self.cache:
                del self.cache[idx]
            return self.__setreturn(do, return_tuple=return_tuple)

    def get_data_list(self, author=None):
        """
        Retrieves either a dict or list containing the variables names stored on the server.

        :param author: *Optional keyword*. The author of the data or object
        :type author: str or None
        :return: A dictionary containing the authors as key and their variable names as a list. If author specified,
                 returns a list with the variable names. Returns None on failure or raises an exception.
        :rtype: dict or list

        """
        dl, exc = self.__callwrapper('get_data_list', author)
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return None
        else:
            return dl

    def clearall(self):
        """
        Clears all of the data on the server. Use with caution if multiple users are storing data.

        :return: True on success, False on failure
        :rtype: bool

        """
        do, exc = self.__callwrapper('clearall')
        self.cache = {}
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return False
        else:
            return True

    def clearcache(self):
        """
        Clears both the local cache and the server cache for the given addon calling using the addon name.

        :return: True on success, False on failure.
        :rtype: bool

        """
        do, exc = self.__callwrapper('clearcache', self.addonname)
        self.cache = {}
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return False
        else:
            return True

    def savedata(self, author=None):
        """
        Saves all of the data for a given author as a pickle object in the addon_data directory for
        service.ipcdatastore. Plan is to implement a way to do this automatically on server shutdown.

        :param author: *Optional keyword*. Defaults to addon id.
        :type author: str or None
        :return: True on success, False on failure
        :rtype: bool

        """
        if author is None:
            author = self.addonname
        path = xbmc.translatePath('special://masterprofile/addon_data/service.ipcdatastore')
        fn = '{0}-{1}.p'.format(self.addonname, author)
        fn = os.path.join(path, fn)
        do, exc = self.__callwrapper('savedata', author, fn)
        if exc.errno == ipcclientxerrors.IPCERROR_SAVEFAILED:
            exc.updatemessage(author, fn)
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return False
        else:
            return True

    def restoredata(self, author=None):
        """
        Restores data on the server from a previously saved pickle (see :func:`savedata() <IPCClientX.savedata>`)

        :param author: *Optional keyword*. The author whose data is to be restored. Defaults to addon id.
        :type author: str
        :return: True on success, False on failure
        :rtype: bool

        """
        if author is None:
            author = self.addonname
        path = xbmc.translatePath('special://masterprofile/addon_data/service.ipcdatastore/')
        fn = os.path.join(path, '{0}-{1}.p'.format(self.addonname, author))
        if xbmcvfs.exists('{0}.gz'.format(fn)) == 1:
            do, exc = self.__callwrapper('restoredata', author, fn)
            if exc.errno == ipcclientxerrors.IPCERROR_RESTOREFAILED:
                exc.updatemessage(author, fn)
            if exc.errno != -1:
                if self.raise_exception:
                    self.logexception(exc)
                    raise exc
                else:
                    return False
            else:
                self.clearcache()
                return True
        else:
            if self.raise_exception:
                exc = ipcclientxerrors.RestoreFailedError
                exc.updatemessage(author, fn)
                exc.message += " File Not Found"
                raise exc
            else:
                return False

    def delete_data(self, author=None):
        """
        Delete data on the server in the form of a previously saved pickle (see :func:`savedata() <IPCClientX.savedata>`)

        :param author: *Optional keyword*. The author whose data is to be restored. Defaults to addon id.
        :type author: str
        :return: True on success, False on failure
        :rtype: bool

        """
        if author is None:
            author = self.addonname
        path = xbmc.translatePath('special://masterprofile/addon_data/service.ipcdatastore/')
        fn = os.path.join(path, '{0}-{1}.p.gz'.format(self.addonname, author))
        if xbmcvfs.exists(fn) == 1:
            try:
                os.remove(fn)
            except Exception as e:
                if self.raise_exception:
                    exc = ipcclientxerrors.UnknownError
                    exc.message += " File Not Found"
                    raise exc
                else:
                    return False
            else:
                return True
        else:
            if self.raise_exception:
                exc = ipcclientxerrors.UnknownError
                exc.message += " File Not Found"
                raise exc
            else:
                return False

    def add_persistence(self, varname, author=None):
        """
        Adds a persistence tag to a pre-existing stored object and saves data to backup.

        :param varname:
        :type varname: str
        :param author:
        :type author: str
        :return: True on success, False on failure
        :rtype: bool
        """
        if author is None:
            author = self.addonname
        do, exc = self.__callwrapper('add_persistence', varname, author)
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return False
        else:
            return True

    def remove_persistence(self, varname, author=None):
        """
        Removes the persistence tag from a stored object and deletes it from backup.

        :param varname:
        :type varname: str
        :param author:
        :type author: str
        :return: True on success, False on failure
        :rtype: bool
        """
        if author is None:
            author = self.addonname
        do, exc = self.__callwrapper('remove_persistence', varname, author)
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return False
        else:
            return True

