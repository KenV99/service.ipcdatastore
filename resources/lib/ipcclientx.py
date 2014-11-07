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
from cPickle import PickleError, PicklingError
from ipcclient import IPCClient as IPCClientBase
import pyro4
import pyro4.errors
import pyro4.util
try:
    import ipcclientxerrors
except:
    import resources.lib.ipcclientxerrors as ipcclientxerrors
isKodi = 'XBMC' in sys.executable
if isKodi:
    import xbmc
    import xbmcaddon
    import xbmcvfs
else:
    from xbmcdummy import xbmc
    from xbmcdummy import xbmcaddon
    from xbmcdummy import xbmcvfs


IPCERROR_UKNOWN = 0
IPCERROR_NO_VALUE_FOUND = 1
IPCERROR_USE_CACHED_COPY = 2
IPCERROR_SERVER_TIMEOUT = 3
IPCERROR_CONNECTION_CLOSED = 4
IPCERROR_NONSERIALIZABLE = 5
IPCERROR_SAVEFAILED = 6
IPCERROR_RESTOREFAILED = 7

class IPCClient(IPCClientBase):
    CALL_GET = 1
    CALL_SET = 2
    CALL_DEL = 3
    CALL_LST = 4
    CALL_CLR = 5
    CALL_SAV = 6
    CALL_RST = 7
    CALL_CLC = 8

    def __init__(self, name='kodi-IPC', host='localhost', port=9091, datatype='pickle'):
        """
        :param name: Arbitrary name for the object being used, must match the name used by server
        :type name: str
        :param port: Port matching server port
        :type port: int
        :param datatype: Type of data transport being used options: pickle, serpent, json, marshall. Must match server
        :type datatype: str
        """
        super(IPCClient, self).__init__(name, host, port, datatype)
        self.cache = {}
        try:
            addonname = xbmcaddon.Addon().getAddonInfo('name')
        except:
            addonname = 'ipcdatastore'
        self.addonname = addonname.replace('.', '-')
        self.raise_exception = False
        self.num_of_server_retries = 5

    def getexposedobj(self):
        return pyro4.Proxy(self.uri)

    def logexception(self, exc):
        xbmc.log(exc.message)
        if hasattr(exc, 'tb'):
            xbmc.log(exc.tb)

    def __callwrapper(self, calltype, *args):
        # Why was this implemented this way? Why didn't I use a factory with 'getattr'?
        # Because the dataobject 'dos' is a remote object, using 'getattr' causes another cycle of requesting the
        # attributes from the serverside and then receiving them. This condenses the interaction down to one
        # call, sometimes being a one-way call. I know. It's ugly.
        retries = self.num_of_server_retries
        err = -1
        do = None
        exc = None
        while retries > 0:
            try:
                dos = pyro4.Proxy(self.uri)
                if calltype == IPCClient.CALL_SET:
                    dos.set(*args)
                elif calltype == IPCClient.CALL_GET:
                    do = dos.get(*args)
                elif calltype == IPCClient.CALL_DEL:
                    do = dos.delete(*args)
                elif calltype == IPCClient.CALL_LST:
                    do = dos.get_data_list(*args)
                elif calltype == IPCClient.CALL_CLR:
                    dos.clearall()
                elif calltype == IPCClient.CALL_SAV:
                    do = dos.savedata(*args)
                elif calltype == IPCClient.CALL_RST:
                    do = dos.restoredata(*args)
                elif calltype == IPCClient.CALL_CLC:
                    dos.clearcache(*args)
            except pyro4.errors.ConnectionClosedError as e:
                retries -=1
                dos._pyroReconnect()
                err = IPCERROR_CONNECTION_CLOSED
                exc = ipcclientxerrors.ServerReconnectFailedError
            except pyro4.errors.CommunicationError as e:
                retries -= 1
                err = IPCERROR_SERVER_TIMEOUT
            except (PickleError, PicklingError, TypeError) as e:
                # TypeError is what you get when using cPickle and the object is not serializable for some reason
                err = IPCERROR_NONSERIALIZABLE
                break
            except Exception as e:
                err = IPCERROR_UKNOWN
                break
            else:
                err = -1
                dos._pyroRelease()
                break
        #  Client side errors
        if err == IPCERROR_SERVER_TIMEOUT:
            exc = ipcclientxerrors.ServerUnavailableError(self.uri, self.get_traceback())
        elif err == IPCERROR_CONNECTION_CLOSED:
            exc = ipcclientxerrors.ServerReconnectFailedError(self.uri, self.get_traceback())
        elif err == IPCERROR_NONSERIALIZABLE:
            exc = ipcclientxerrors.ObjectNotSerializableError()
        elif err == IPCERROR_UKNOWN:
            exc = ipcclientxerrors.UnknownError(sys.exc_info()[1], self.get_traceback())
        # Server side errors
        elif do is not None:
            if isinstance(do, str):
                err = ord(do)
                if err == IPCERROR_NO_VALUE_FOUND:
                    exc = ipcclientxerrors.VarNotFoundError()
                elif err == IPCERROR_USE_CACHED_COPY:
                    exc = ipcclientxerrors.UseCachedCopyError()
                elif err == IPCERROR_SAVEFAILED:
                    exc = ipcclientxerrors.SaveFailedError()
                elif err == IPCERROR_RESTOREFAILED:
                    exc = ipcclientxerrors.RestoreFailedError()
                elif err != -1:
                    exc = ipcclientxerrors.UnknownError(sys.exc_info()[1], self.get_traceback())
        if exc is not None:
            exc.errno = err
        else:
            exc = ipcclientxerrors.NoError()
        return do, exc

    def set(self, name, value, author=None):
        """
        Sets a value on the server. Automatically adds the addon name as the author. The value is any valid object
        that can be accepted by the chosen datatype (see above). If the class attribute raise_exception is True,
        will raise an exception with failure.
        :param name: The variable name
        :type name: str
        :param value: The value of the variable
        :type name: Any object type compatible with the datatype transport
        :returns True for success, False for failure
        :rtype: bool
        """
        if author is None:
            author = self.addonname
        do, exc = self.__callwrapper(IPCClient.CALL_SET, name, value, author)
        if exc.errno == IPCERROR_NONSERIALIZABLE:
            exc.updatemessage(value)
        if exc.errno != -1:
            self.logexception(exc)
            if self.raise_exception:
                raise exc
            else:
                return False
        else:
            return True

    def __setreturn(self, do, ts, iscached=False, retiscached=False):
        if do is not None:
            ret = [do.value]
        else:
            ret = [None]
        if ts:
            ret.append(do.ts)
        if retiscached:
            ret.append(iscached)
        if len(ret) == 1:
            ret = ret[0]
        return ret

    def __get(self, name, author, force=False):
        requestor = self.addonname
        do,exc = self.__callwrapper(IPCClient.CALL_GET, requestor, name, author, force)
        return do, exc

    def get(self, name, author=None, ts=False, retiscached=False):
        """
        Retrieves data from the server based on author and variable name, optionally includes time stamp.
        There is a caching function implemented such that the server tracks addon requests for data - if the most recent
        version has already been received by the client, a message is sent to the client to look in it's cache for the
        data. There is a fallback such that if the data is NOT in the cache, the server then provides the data. Each
        piece of data that is received is also cached.
        :param author: The author of the data. All of the data is indexed by author and variable name in order to reduce
                        variable name overlap
        :type author: str
        :param name: The variable name
        :type name: str
        :param ts: Whether or not to include a timestamp in the return. If desired then recipient should then code:
                        x, ts = client.get(author, name, ts=True)
        :type ts: bool
        :return: Either the value(object) assigned to 'name' or a value, timestamp pair if ts=True
        :rtype: object
        """
        if author is None:
            author = self.addonname
        idx = (author, name)
        do, exc = self.__get(name, author)
        if exc.errno == IPCERROR_USE_CACHED_COPY:
            if idx in self.cache:
                do = self.cache[idx]
                return self.__setreturn(do, ts, True, retiscached)
            else:  #SHOULD BE IN CACHE, SO FORCE SERVER TO PROVIDE
                do, exc = self.__get(name, author, force=True)
                if exc.errno == IPCERROR_NO_VALUE_FOUND:
                    exc.varname = name
                    exc.author = author
                if exc.errno != -1:
                    self.logexception(exc)
                    if self.raise_exception:
                        raise exc
                    else:
                        return self.__setreturn(None, None, retiscached=retiscached)
                else:
                    self.cache[idx] = do
                    return self.__setreturn(do, ts, retiscached=retiscached)
        elif exc.errno == IPCERROR_NO_VALUE_FOUND:
            exc.updatemessage(name, author)
        if exc.errno != -1:
            self.logexception(exc)
            if self.raise_exception:
                raise exc
            else:
                return self.__setreturn(None, None, retiscached=retiscached)
        else:
            self.cache[idx] = do
            return self.__setreturn(do, ts, retiscached=retiscached)

    def delete(self, name, author=None, ts=False):
        if author is None:
            author = self.addonname
        do, exc = self.__callwrapper(IPCClient.CALL_DEL, name, author)
        if exc.errno == IPCERROR_NO_VALUE_FOUND:
            exc.updatemessage(name, author)
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return self.__setreturn(None, None)
        else:
            idx = (author, name)
            if idx in self.cache:
                del self.cache[idx]
            return self.__setreturn(do, ts)

    def get_data_list(self, author=None):
        dl, exc = self.__callwrapper(IPCClient.CALL_LST, author)
        if exc.errno != -1:
            if self.raise_exception:
                self.logexception(exc)
                raise exc
            else:
                return None
        else:
            return dl

    def clearall(self):
        do, exc = self.__callwrapper(IPCClient.CALL_CLR)
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
        do, exc = self.__callwrapper(IPCClient.CALL_CLC, self.addonname)
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
        if author is None:
            author = self.addonname
        path = xbmc.translatePath('special://masterprofile') + 'addon_data\\service.ipcdatastore\\'
        if xbmcvfs.exists(path) == 0:
            xbmcvfs.mkdirs(path)
        fn = '{0}{1}-{2}.p'.format(path, self.addonname, author)
        do, exc = self.__callwrapper(IPCClient.CALL_SAV, author, fn)
        if exc.errno == IPCERROR_SAVEFAILED:
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
        if author is None:
            author = self.addonname
        path = xbmc.translatePath('special://masterprofile') + 'addon_data\\service.ipcdatastore\\'
        fn = '{0}{1}-{2}.p'.format(path, self.addonname, author)
        if xbmcvfs.exists(fn) == 1:
            do, exc = self.__callwrapper(IPCClient.CALL_RST, author, fn)
            if exc.errno == IPCERROR_RESTOREFAILED:
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
