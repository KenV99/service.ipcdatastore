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
    def __init__(self):
        self.errno = -1
        pass


class VarNotFoundError(IPCClientError):
    def __init__(self):
        self.message = ''

    def updatemessage(self, varname, author):
        self.message = 'Variable not found on server for author={0}, var_name={1}'. format(author, varname)


class ServerReconnectFailedError(IPCClientError):
    def __init__(self, uri, tb):
        self.message = 'Server connection closed and could not be reopened for {0}'.format(uri)
        self.tb = tb


class ServerUnavailableError(IPCClientError):
    def __init__(self, uri, tb):
        self.message = 'Server unavailable for uri:{0}'.format(uri)
        self.tb = tb


class ObjectNotSerializableError(IPCClientError):
    def __init__(self):
        self.message = ''

    def updatemessage(self, obj):
        self.message = 'The object of type {0} provided failed serialization'.format(str(type(obj)))


class UseCachedCopyError(IPCClientError):
    def __init__(self):
        self.message = 'Using cached copy'


class SaveFailedError(IPCClientError):
    def __init__(self):
        self.message = ''

    def updatemessage(self, author, fn):
        self.message = 'Save failed for author={0}, filename={1}'.format(author, fn)


class RestoreFailedError(IPCClientError):
    def __init__(self):
        self.message = ''

    def updatemessage(self, author, fn):
        self.message = 'Restore failed for author={0}, filename={1}'.format(author, fn)


class UnknownError(IPCClientError):
    def __init__(self, msg, tb):
        self.message = msg.message
        self.tb = tb


class NoError(IPCClientError):
    def __init__(self):
        self.errno = -1