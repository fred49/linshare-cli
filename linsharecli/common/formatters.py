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
# Copyright 2014-2016 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#




import logging
import datetime
# pylint: disable=import-error
from humanfriendly import format_size

# pylint: disable=too-few-public-methods
class Formatter(object):
    """TODO"""
    def __init__(self, prop, formatt=None):
        """ prop name and value(s)"""
        self.prop = prop
        self.formatt = formatt
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger(classname)

    def get_val(self, row):
        """TODO"""
        val = row.get(self.prop)
        if val is None:
            raise ValueError("missing key : " + self.prop)
        return val

    def __call__(self, row, context=None):
        raise NotImplementedError()


class DateFormatter(Formatter):
    """TODO"""

    def __init__(self, prop, formatt="%Y-%m-%d %H:%M:%S"):
        super(DateFormatter, self).__init__(prop, formatt)
        self.formatt = "{da:" + formatt + "}"

    def __call__(self, row, context=None):
        ldate = row.get(self.prop)
        if ldate is not None:
            try:
                row[self.prop] = self.formatt.format(
                    da=datetime.datetime.fromtimestamp(ldate / 1000))
            except TypeError:
                pass


class SizeFormatter(Formatter):
    """TODO"""

    def __init__(self, prop, empty=None):
        super(SizeFormatter, self).__init__(prop)
        self.empty = empty

    def __call__(self, row, context=None):
        lsize = row.get(self.prop)
        if lsize is not None:
            if hasattr(lsize, "value"):
                # it is a cell. we must not transform it right now
                # bacause it will tranform it in string and break the sort
                # feature.
                return
            try:
                row[self.prop] = format_size(lsize)
            except TypeError:
                pass
        else:
            if self.empty:
                row[self.prop] = self.empty


class NoneFormatter(Formatter):
    """Convert None value to an empty string only if key exists"""

    def __init__(self, prop):
        super(NoneFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        # do not create/format a property that does not already exist.
        # Because Htable does not support it
        if self.prop not in list(row.keys()):
            return
        parameter = row.get(self.prop)
        if parameter is None:
            row[self.prop] = ""


class OwnerFormatter(Formatter):
    """Convert resource owner (user) value to a readable name"""

    def __init__(self, prop):
        super(OwnerFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            row[self.prop] = '{firstName} {lastName} <{mail}>'.format(
                **parameter)


class DomainFormatter(Formatter):
    """Convert resource domain value to a readable name"""

    def __init__(self, prop, full=False):
        super(DomainFormatter, self).__init__(prop)
        self.full = full

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            l_format = '{label}'
            if context.args.vertical:
                l_format = '{label} ({identifier})'
            if self.full:
                l_format = '{label} ({identifier})'
            row[self.prop] = l_format.format(**parameter)


class GenericFormatter(Formatter):
    """Convert resource domain value to a readable name"""

    def __init__(self, prop, full=False):
        super(GenericFormatter, self).__init__(prop)
        self.full = full

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            l_format = '{name}'
            if context.args.vertical:
                l_format = '{name} ({uuid})'
            if self.full:
                l_format = '{name} ({uuid})'
            row[self.prop] = l_format.format(**parameter)


class LastAuthorFormatter(Formatter):
    """Convert resource owner (user) value to a readable name"""

    def __init__(self, prop):
        super(LastAuthorFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            row[self.prop] = '{name} <{mail}>'.format(
                **parameter)


class ActorFormatter(Formatter):
    """Convert resource domain value to a readable name"""

    def __init__(self, prop, full=False):
        super(ActorFormatter, self).__init__(prop)
        self.full = full

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            l_format = '{name}'
            if context.args.vertical:
                l_format = '{name} <{mail}> ({uuid})'
            if self.full:
                l_format = '{name} <{mail}> ({uuid})'
            row[self.prop] = l_format.format(**parameter)


class UuidFormatter(Formatter):
    """TODO"""

    def __init__(self, prop):
        super(UuidFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        value = row.get(self.prop)
        if value:
            if not context.args.vertical:
                row[self.prop] = '{uuid:8.8}'.format(uuid=value)


class LastAuthorFormatterV2(Formatter):
    """Convert resource owner (user) value to a readable name.
    This formatter requires using row of Cells (type)"""

    def __init__(self, prop):
        super(LastAuthorFormatterV2, self).__init__(prop)

    def __call__(self, row, context=None):
        cell = row.get(self.prop)
        if cell and hasattr(cell, "formatt"):
            cell.formatt = '{name}'
            if cell.vertical:
                cell.formatt = '{name} <{mail}>'


class DebugFormatter(Formatter):
    """Just print row and cell types and content"""

    def __call__(self, row, context=None):
        print(">---")
        print(("prop:", self.prop))
        print(("row :", type(row)))
        ldate = row.get(self.prop)
        print(("type:", type(ldate)))
        print(("raw :", ldate.value))
        print(("val :", ldate))
        print("---<")
