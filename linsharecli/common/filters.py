#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""This module contains only filters, they are design to be apply to a row
of a Vertical or Horizotal table."""


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
# Copyright 2014 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



import types
import datetime
import re
import logging
from linsharecli.common.cell import BaseCell


class Filter(object):
    """TODO"""

    def __init__(self, prop, values=None):
        """ prop name and value(s)"""
        self.prop = prop
        self.values = values
        classname = self.__class__.__name__.lower()
        self.log = logging.getLogger("linsharecli.filters." + classname)

    def is_enable(self):
        """Return true is the current filter is enabled and should be applied."""
        if self.values is None:
            return False
        if isinstance(self.values, list):
            # pylint: disable=len-as-condition
            if len(self.values) == 0:
                return False
            for i in self.values:
                if i is not None:
                    return True
            return False
        return True

    def get_val(self, row):
        """return values from the current row that need to be tested again the
        current filter."""
        if isinstance(self.prop, list):
            vals = {}
            for prop in self.prop:
                vals[prop] = self._get_val(row, prop)
            return vals
        return self._get_val(row, self.prop)

    def _get_val(self, row, prop):
        val = row.get(prop)
        if val is None:
            raise ValueError("missing key : " + self.prop)
        self.log.debug("type: %s", type(val))
        self.log.debug("value: '%s'", val)
        return val


class PartialOr(Filter):
    """Get the current property into the current row, and match the result with
     a list of values"""

    def __init__(self, prop, values, ignorecase=False, match_raw=False):
        super(PartialOr, self).__init__(prop, values)
        self.match_raw = match_raw
        if self.is_enable():
            if not isinstance(values, list):
                raise ValueError("input values should be a list")
            self.log.debug("values: %s", self.values)
            pattern = r"^.*(" + "|".join(self.values) + ").*$"
            self.log.debug("raw pattern: %s", pattern)
            if ignorecase:
                self.regex = re.compile(pattern, re.IGNORECASE)
            else:
                self.regex = re.compile(pattern)
    def __str__(self):
        return "PartialOr: " + str(self.values)

    def __call__(self, row):
        # pylint: disable=too-many-return-statements
        if not self.is_enable():
            return True
        vals = self.get_val(row)
        if isinstance(vals, dict):
            for val in list(vals.values()):
                return self.__match(val)
        else:
            return self.__match(vals)

    def __match(self, val):
        if isinstance(val, str):
            if self.regex.match(val):
                return True
        elif isinstance(val, BaseCell):
            self.log.debug("cell type: %s", type(val))
            if self.match_raw:
                if self.regex.match(val.value):
                    return True
            else:
                if val.match(self.regex):
                    return True
        else:
            if self.regex.match(val):
                return True
        return False


class PartialMultipleAnd(Filter):
    """Get the current property into the current row, and match the result with
     a list of values"""

    def __init__(self, propvalues, ignorecase=False):
        super(PartialMultipleAnd, self).__init__(list(propvalues.keys()), list(propvalues.values()))
        self.regex = {}
        self.propvalues = propvalues
        if self.is_enable():
            for key, value in list(propvalues.items()):
                self.regex[key] = None
                if value is not None:
                    pattern = r"^.*" + value + ".*$"
                    if ignorecase:
                        self.regex[key] = re.compile(pattern, re.IGNORECASE)
                    else:
                        self.regex[key] = re.compile(pattern)

    def __call__(self, row):
        if not self.is_enable():
            return True
        vals = self.get_val(row)
        for key, val in list(vals.items()):
            if self.regex[key]:
                if not self.regex[key].match(val):
                    return False
        return True


class PartialDate(Filter):
    """Get the current property into the current row, and match the result with
     a list of values"""

    def __init__(self, prop, value):
        super(PartialDate, self).__init__(prop, value)
        if self.is_enable():
            pattern = r"^.*" + value + ".*$"
            self.regex = re.compile(pattern)

    def __call__(self, row):
        if not self.is_enable():
            return True
        vals = self.get_val(row)
        if isinstance(vals, dict):
            for val in list(vals.values()):
                if self.regex.match(val):
                    return True
        else:
            formatt = "{da:%Y-%m-%d %H:%M:%S}"
            vals = formatt.format(
                da=datetime.datetime.fromtimestamp(vals / 1000))
            self.log.debug("type of values: %s", vals)
            if self.regex.match(vals):
                return True
        return False


class Equal(Filter):
    """Get the current property into the current row, and test equality.
    Only one value is possible"""

    def __call__(self, row):
        if not self.is_enable():
            return True
        val = self.get_val(row)
        if val == self.values:
            return True
        return False


class Equals(Filter):
    """Get the current property into the current row, and test equality.
    A list of values will be test"""

    def __call__(self, row):
        if not self.is_enable():
            return True
        val = self.get_val(row)
        if val in self.values:
            return True
        return False
