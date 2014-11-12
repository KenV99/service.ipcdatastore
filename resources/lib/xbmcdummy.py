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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os


class xbmc(object):
    LOGERROR = 2

    @staticmethod
    def log(msg, level=None):
        print msg

    @staticmethod
    def translatePath(path):
        ret = path.replace(r'special://masterprofile', r'C:\Users\Ken User\AppData\Roaming\XBMC\userdata')
        ret = ret.replace('/', '\\')
        return ret


class AddOn(object):
    def __init__(self, name=''):
        if name == '':
            name = 'ipcdatastore'
        self.name = name

    def getAddonInfo(self, myid):
        if myid == 'name':
            return self.name


class xbmcaddon(object):
    @staticmethod
    def Addon(name=''):
        return AddOn(name)


class xbmcvfs(object):
    @staticmethod
    def exists(path):
        if os.path.exists(path):
            return 1
        else:
            return 0

    @staticmethod
    def mkdirs(path):
        os.makedirs(path)