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


class CellFactory(object):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, raw=False, vertical=False, debug=0):
        self.raw = raw
        self.debug = debug
        self.vertical = vertical
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger("linsharecli.cell." + classname)
        self.date_cells = [
            "creationDate",
            "modificationDate",
            "expirationDate",
            "uploadDate"
        ]
        self.size_cells = ["size"]
        self.custom_cells = {}

    def __call__(self, name, value, row=None):
        if name in self.custom_cells.keys():
            clazz = self.custom_cells.get(name)
        elif name in self.date_cells:
            clazz = DateCell
        elif name in self.size_cells:
            clazz = SizeCell
        elif isinstance(value, int):
            clazz = ICell
        elif isinstance(value, list):
            clazz = ComplexCell
        elif isinstance(value, dict):
            clazz = ComplexCell
        else:
            clazz = SCell
        if self.debug >= 2:
            self.log.debug("building cell ...")
            self.log.debug("property: %s", name)
            self.log.debug("value type: %s", type(value))
            self.log.debug("value: %s", value)
            self.log.debug("raw: %s", self.raw)
            self.log.debug("vertical: %s", self.vertical)
        cell = clazz(value)
        cell.name = name
        cell.raw = self.raw
        cell.vertical = self.vertical
        if row is not None:
            cell.row = row
        if self.debug >= 3:
            self.log.debug("cell type: %s", type(cell))
            # str method from all cell must return encoded strings
            self.log.debug("cell rendering: %s", str(cell).decode('utf-8'))
            self.log.debug("cell built.")
        return cell


class BaseCell(object):
    pass

class SCell(BaseCell):
    """This class is used to emulate str type for veryprettytable.
    VeryPrettyTable will call the __str__ method on non-unicode objects.
    It requires that the __str__ output is utf-8 encoded."""
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, value):
        self.value = value
        self.raw = False
        self.row = {}
        self.vertical = False
        self.name = None
        self._format = None
        self._format_vertical = None
        self.none = "-"

    @property
    def formatt(self):
        """TODO"""
        return self._format

    @formatt.setter
    def formatt(self, formatt):
        """TODO"""
        self._format = formatt

    @property
    def formatv(self):
        """TODO"""
        return self._format_vertical

    @formatv.setter
    def formatv(self, formatv):
        """TODO"""
        self._format_vertical = formatv

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        """TODO"""
        if self.raw:
            if self.value is None:
                return "None"
            return unicode(self.value)
        if self.value is None:
            return self.none
        if self.vertical:
            if self._format_vertical:
                return self._format_vertical.format(value=self.value)
        if self._format:
            return self._format.format(value=self.value)
        return unicode(self.value)

    def __cmp__(self, value):
        if self.value == value:
            return 0
        if self.value > value:
            return 1
        return -1

    def __eq__(self, item):
        return self.value == item

    def __add__(self, item):
        return self.value + item

    def lower(self):
        """return a lower case version of the current value"""
        return self.value.lower()


class DateCell(BaseCell):
    """TODO"""

    # pylint: disable=too-few-public-methods
    def __init__(self, value):
        self.value = value
        self.raw = False
        self.row = {}
        self.vertical = False
        self._d_formatt = "{da:%Y-%m-%d %H:%M:%S}"
        self.name = None
        self.none = "-"

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        if self.raw:
            return unicode(self.value)
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

    def __eq__(self, item):
        return self.value == item


class ICell(int, BaseCell):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        super(ICell, self).__init__(value)
        self.value = value
        self.raw = False
        self.row = {}
        self.vertical = False
        self.name = None

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        if self.raw:
            return unicode(self.value)
        return unicode(self.value)


class SizeCell(BaseCell):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        self.value = value
        self.raw = False
        self.row = {}
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
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        if self.raw:
            return unicode(self.value)
        if self.value is None:
            return self.none
        return filesize(self.value, system=si)

    def __eq__(self, item):
        return self.value == item


class ComplexCell(BaseCell):
    """TODO"""
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, value):
        self.value = value
        self.raw = False
        self.row = {}
        self.vertical = False
        self.name = None
        self._format = None
        self._format_vertical = None
        self.none = "-"

    @property
    def formatt(self):
        """TODO"""
        return self._format

    @formatt.setter
    def formatt(self, formatt):
        """TODO"""
        self._format = formatt

    @property
    def formatv(self):
        """TODO"""
        return self._format_vertical

    @formatv.setter
    def formatv(self, formatv):
        """TODO"""
        self._format_vertical = formatv

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        if self.raw:
            return unicode(self.value)
        if self.vertical:
            if self._format_vertical:
                return self._format_vertical.format(**self.value)
        if self._format:
            return self._format.format(**self.value)
        return unicode(self.value)

    def keys(self):
        """TODO"""
        return self.value.keys()

    def __getitem__(self, key):
        return self.value[key]

    def __eq__(self, item):
        return self.value == item


class CellBuilder(object):
    """wrapper to build a Cell with extra parameters."""
    # pylint: disable=too-few-public-methods

    def __init__(self, formatt, formatv=None, cell=SCell):
        self._format = formatt
        self._formatv = formatt
        if formatv:
            self._formatv = formatv
        self.clazz = cell

    def __call__(self, value):
        cell = self.clazz(value)
        cell.formatt = self._format
        cell.formatv = self._formatv
        return cell


class ComplexCellBuilder(CellBuilder):
    """wrapper to build a ComplexCell with extra parameters."""
    # pylint: disable=too-few-public-methods

    def __init__(self, formatt, formatv=None):
        super(ComplexCellBuilder, self).__init__(formatt, formatv, ComplexCell)
