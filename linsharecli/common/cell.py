#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""TODO"""


# This file is part of Linshare cli.
#
# LinShare cli is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LinShare cli is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LinShare cli.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2019 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

from __future__ import unicode_literals

import datetime
import logging

from hurry.filesize import size as filesize
from hurry.filesize import si


class CellBuilder(object):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, name, raw=False, vertical=False, debug=0):
        self.clazz = None
        self.name = name
        self.raw = raw
        self.debug = debug
        self.vertical = vertical
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger("linsharecli.cell." + classname)

    def __call__(self, value):
        if self.clazz is None:
            if self.name in ["creationDate", "modificationDate", "expirationDate"]:
                self.clazz = DateCell
            elif self.name in ["size"]:
                self.clazz = SizeCell
            elif isinstance(value, int):
                self.clazz = ICell
            elif isinstance(value, dict):
                self.clazz = ComplexCell
            else:
                self.clazz = SCell
        if self.debug >= 2:
            self.log.debug("building cell ...")
            self.log.debug("property: %s", self.name)
            self.log.debug("value type: %s", type(value))
            self.log.debug("value: %s", value)
            self.log.debug("raw: %s", self.raw)
            self.log.debug("vertical: %s", self.vertical)
        cell = self.clazz(value)
        cell.name = self.name
        cell.raw = self.raw
        cell.vertical = self.vertical
        if self.debug >= 3:
            self.log.debug("cell type: %s", type(cell))
            # str method from all cell must return encoded strings
            self.log.debug("cell rendering: %s", str(cell).decode('utf-8'))
            self.log.debug("cell built.")
        return cell


class SCell(object):
    """This class is used to emulate str type for veryprettytable.
    VeryPrettyTable will call the __str__ method on non-unicode objects.
    It excepts that the __str__ output is utf-8 encoded."""
    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        self.value = value
        self.raw = False
        self.vertical = False
        self.name = None
        self.none = "-"

    def __str__(self):
        value = None
        if self.raw:
            if self.value is None:
                value = "None"
            else:
                value = self.value
        else:
            if self.value is None:
                value = self.none
            else:
                value = self.value
        return value.encode('utf-8')

    def __cmp__(self, value):
        if self.value == value:
            return 0
        if self.value > value:
            return 1
        return -1


class DateCell(object):
    """TODO"""

    # pylint: disable=too-few-public-methods
    def __init__(self, value):
        self.value = value
        self.raw = False
        self.vertical = False
        self._d_formatt = "{da:%Y-%m-%d %H:%M:%S}"
        self.name = None
        self.none = "-"

    def __str__(self):
        if self.raw:
            return str(self.value)
        if self.value is not None:
            # if self.vertical:
            #     self._d_formatt = "{da:%Y-%m-%d}"
            return self._d_formatt.format(
                da=datetime.datetime.fromtimestamp(self.value / 1000))
        return self.none

    def __cmp__(self, value):
        if self.value == value:
            return 0
        if self.value > value:
            return 1
        return -1

    def __div__(self, value):
        return self.value / value


class ICell(int):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        super(ICell, self).__init__(value)
        self.value = value
        self.raw = False
        self.vertical = False
        self.name = None

    def __str__(self):
        if self.raw:
            return str(self.value)
        return str(self.value)


class SizeCell(object):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        self.value = value
        self.raw = False
        self.vertical = False
        self.name = None
        self.none = "-"

    def __cmp__(self, value):
        if self.value == value:
            return 0
        if self.value > value:
            return 1
        return -1

    def __div__(self, value):
        return self.value / value

    def __str__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        return filesize(self.value, system=si)


class ComplexCell(object):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        self.value = value
        self.raw = False
        self.vertical = False
        self.name = None
        self._format = None

    @property
    def formatt(self):
        """TODO"""
        return self._format

    @formatt.setter
    def formatt(self, formatt):
        """TODO"""
        self._format = formatt

    def __str__(self):
        if self._format:
            return self._format.format(**self.value)
        return str(self.value).encode('utf-8')

    def keys(self):
        """TODO"""
        return self.value.keys()

    def __getitem__(self, key):
        return self.value[key]
