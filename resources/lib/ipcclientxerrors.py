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

IPCERROR_UKNOWN = 0
IPCERROR_NO_VALUE_FOUND = 1
IPCERROR_USE_CACHED_COPY = 2
IPCERROR_SERVER_TIMEOUT = 3
IPCERROR_CONNECTION_CLOSED = 4
IPCERROR_NONSERIALIZABLE = 5
IPCERROR_SAVEFAILED = 6
IPCERROR_RESTOREFAILED = 7


class IPCClientError(Exception):
    """
    Base class for other exception classes
    """
    def __init__(self):
        self.errno = -1
        pass


class VarNotFoundError(IPCClientError):
    """
    Raised when the author/variable name combination is not found on the server

    :var message: Error message containing the author and variable name, if set
    """
    def __init__(self):
        self.message = ''

    def updatemessage(self, varname, author):
        """
        Allows updating .message if at the time the exception is instantiated, the variable name and author are
        not available (typical case).
        """
        self.message = 'Variable not found on server for author={0}, var_name={1}'. format(author, varname)


class ServerReconnectFailedError(IPCClientError):
    """
    Raised when a previous connection could not be reopened
    """
    def __init__(self, uri, tb):
        """
        :param uri: The uri to display in the message
        :param tb:  The string traceback
        """
        self.message = 'Server connection closed and could not be reopened for {0}'.format(uri)
        self.tb = tb


class ServerUnavailableError(IPCClientError):
    """

    """
    def __init__(self, uri, tb):
        """
        :param uri: The uri to display in the message
        :param tb:  The string traceback
        """
        self.message = 'Server unavailable for uri:{0}'.format(uri)
        self.tb = tb


class ObjectNotSerializableError(IPCClientError):
    """
    Raised when an object to be used is not seriablizable with the current serializer
    """
    def __init__(self):
        self.message = ''

    def updatemessage(self, obj):
        """
        Allows for message updating when the object is unavailable at the time of instantiation
        :param obj:  the object that failed serialization
        """
        self.message = 'The object of type {0} provided failed serialization'.format(str(type(obj)))


class UseCachedCopyError(IPCClientError):
    """
    Raised when the server instructs the client to use data from the cache
    """
    def __init__(self):
        self.message = 'Using cached copy'


class SaveFailedError(IPCClientError):
    """
    Raised when a pickle save fails on the server
    """
    def __init__(self):
        self.message = ''

    def updatemessage(self, author, fn):
        self.message = 'Save failed for author={0}, filename={1}'.format(author, fn)


class RestoreFailedError(IPCClientError):
    """
    Raised when a pickle restore fails on the server
    """
    def __init__(self):
        self.message = ''

    def updatemessage(self, author, fn):
        self.message = 'Restore failed for author={0}, filename={1}'.format(author, fn)


class UnknownError(IPCClientError):
    """
    Error otherwise not defined
    """
    def __init__(self, msg, tb):
        self.message = msg.message
        self.tb = tb


class NoError(IPCClientError):
    """
    Default case when no errors have occurred. Used to keep interface with IPCClientX.__getwrapper consistent.
    """
    def __init__(self):
        self.errno = -1