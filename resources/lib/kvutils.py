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
import shutil
import time


def isKodi():
    if sys.platform.startswith('win'):
        ret = 'xbmc' in sys.executable.lower() or 'kodi' in sys.executable.lower()
    else:
        ret = True
    return ret

if isKodi():
    import xbmc

PLATFORM_UNKNOWN = 00
PLATFORM_LINUX = 01
PLATFORM_RASPBERRYPI = 02
PLATFORM_WINDOWS = 03
PLATFORM_OSX = 04
PLATFORM_IOS = 05
PLATFORM_ATV2 = 06
PLATFORM_ANDROID = 07


class KVxbmc(object):
    @staticmethod
    def log(msg, loglevel=None):
        print msg

    @staticmethod
    def sleep(msec):
        time.sleep(msec/1000.0)

    @staticmethod
    def translatePath(path):
        assert isinstance(path, str)
        if path.startswith('special://masterprofile/'):
            newpath = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'XBMC', 'userdata')
            path = path.replace('special://masterprofile/', '')
            mlist = path.split('/')
            retpath = os.path.join(newpath, *mlist)

        elif path.startswith('special://home/'):
            newpath = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'XBMC')
            path = path.replace('special://home/', '')
            mlist = path.split('/')
            retpath = os.path.join(newpath, *mlist)
        else:
            retpath = path
        return retpath


def platform():
    if isKodi():
        if xbmc.getCondVisibility('System.Platform.Linux.RaspberryPi'):
            ret = PLATFORM_RASPBERRYPI
        elif xbmc.getCondVisibility('System.Platform.Linux'):
            ret = PLATFORM_LINUX
        elif xbmc.getCondVisibility('System.Platform.Windows'):
            ret = PLATFORM_WINDOWS
        elif xbmc.getCondVisibility('System.Platform.OSX'):
            ret = PLATFORM_OSX
        elif xbmc.getCondVisibility('System.Platform.IOS'):
            ret = PLATFORM_IOS
        elif xbmc.getCondVisibility('System.Platform.ATV2'):
            ret = PLATFORM_ATV2
        elif xbmc.getCondVisibility('System.Platform.Android'):
            ret = PLATFORM_ANDROID
        else:
            ret = PLATFORM_UNKNOWN
    else:
        sp = sys.platform
        if sp.startswith('win'):
            ret = PLATFORM_WINDOWS
        elif os.uname()[4] is 'arm':
            ret = PLATFORM_ANDROID
        elif sp.startswith('linux'):
            ret = PLATFORM_LINUX
        elif sp.startswith('darwin'):
            ret = PLATFORM_OSX
        else:
            ret = PLATFORM_UNKNOWN
    return ret

g_platform = platform()


class KVxbmcvfX(object):
    def __init__(self):
        super(xbmcvfs, self).__init__(None)

    @staticmethod
    def chmod(path, mode):
        if platform() != PLATFORM_WINDOWS:
            return os.chmod(path, mode)

    @staticmethod
    def access(path, strmode=''):
        mode = os.F_OK
        if len(strmode) == 2:
            if strmode[0:0].lower() == 'r':
                mode = mode | os.R_OK
            if strmode[1:1].lower() == 'w':
                mode = mode | os.W_OK
            if strmode[2:2].lower == 'x':
                mode = mode | os.X_OK
        return os.access(path, mode)

    @staticmethod
    def rmtree(path):
        shutil.rmtree(path)


class KVxbmcvfs(object):

    @staticmethod
    def chmod(path, mode):
        return os.chmod(path, mode)

    @staticmethod
    def access(path, strmode=''):
        mode = os.F_OK
        if len(strmode) == 2:
            if strmode[0:0].lower() == 'r':
                mode = mode | os.R_OK
            if strmode[1:1].lower() == 'w':
                mode = mode | os.W_OK
            if strmode[2:2].lower == 'x':
                mode = mode | os.X_OK
        return os.access(path, mode)

    @staticmethod
    def copy(source, destination):
        return shutil.copy2(source, destination)

    @staticmethod
    def delete(file):
        return os.remove(file)

    @staticmethod
    def exists(path):
        return os.path.exists(path)

    @staticmethod
    def listdir(path):
        return os.listdir(path)

    @staticmethod
    def mkdir(path):
        return os.mkdir(path)

    @staticmethod
    def mkdirs(path, mode=None):
        if mode is None:
            return os.makedirs(path)
        else:
            return os.makedirs(path, mode=mode)

    @staticmethod
    def rename(file, newFileName):
        return os.rename(file, newFileName)

    @staticmethod
    def rmdir(path):
        return os.rmdir(path)

    class File(object):
        def __new__(cls, filename, ftype=None):
            cls.filename = filename
            cls.type = ftype
            if cls.type is None:
                mode = 'r'
            else:
                mode = ftype[0]
            cls.file = open(filename, mode)
            return cls.file

        @classmethod
        def close(cls):
            return cls.file.close()

        @classmethod
        def read(cls, bytes=None):
            if bytes is None:
                return cls.file.read()
            else:
                return cls.file.read(bytes)

        def readBytes(cls, numbytes):
            return cls.file.read(bytes)

        def seek(cls, offset, from_what):
            return cls.file.seek(offset, from_what)

        def size(cls):
            return cls.file.__sizeof__()

        def write(cls, buffer):
            return cls.file.write(buffer)

    @staticmethod
    class Stat(object):
        def __new__(cls, path):
            cls.path = path

        @classmethod
        def st_mode(cls):
            pass

    @staticmethod
    def rmtree(path):
        shutil.rmtree(path)


class KVxbmcaddon(object):
    g_default_addon_id = None

    def __new__(cls):
        pass

    @staticmethod
    def set_default_addon_id(addon_id):
        KVxbmcaddon.g_default_addon_id = addon_id

    @staticmethod
    class Addon(object):
        def __init__(self, id=None):
            if id is None:
                self.id = KVxbmcaddon.g_default_addon_id
            else:
                self.id = id

        def getLocalizedString(self, id):
            pass

        def getAddonInfo(self, id):
            if id == 'id':
                return self.id
            if id == 'path':
                return KVxbmc.translatePath('special://home/addons/{0}'.format(self.id))

        @staticmethod
        def getSetting(self, id):
            pass

        @staticmethod
        def openSettings(self):
            pass

        @staticmethod
        def setSetting(self, id, value):
            pass



