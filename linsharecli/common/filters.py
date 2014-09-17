#! /usr/bin/env python
# -*- coding: utf-8 -*-


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


from __future__ import unicode_literals
import types
import datetime
import re

# pylint: disable=R0921
# pylint: disable=C0111
# -----------------------------------------------------------------------------
class Filter(object):
    def __init__(self, prop, values=None):
        """ prop name and value(s)"""
        self.prop = prop
        self.values = values

    def is_enable(self):
        if self.values is None:
            return False
        elif isinstance(self.values, list):
            if len(self.values) == 0:
                return False
            else:
                for i in self.values:
                    if i is not None:
                        return True
        else:
            return True

    def get_val(self, row):
        if isinstance(self.prop, list):
            vals = {}
            for prop in self.prop:
                vals[prop] = self._get_val(row, prop)
            return vals
        else:
            return self._get_val(row, self.prop)

    def _get_val(self, row, prop):
        val = row.get(prop)
        if val is None:
            raise ValueError("missing key : " + self.prop)
        return val

# -----------------------------------------------------------------------------
class PartialOr(Filter):
    """Get the current property into the current row, and match the result with
     a list of values"""

    def __init__(self, prop, values, ignorecase=False):
        super(PartialOr, self).__init__(prop, values)
        if self.is_enable():
            if not isinstance(values, list):
                raise ValueError("input values should be a list")
            pattern = r"^.*(" + "|".join(self.values) + ").*$"
            if ignorecase:
                self.regex = re.compile(pattern, re.IGNORECASE)
            else:
                self.regex = re.compile(pattern)

    def __call__(self, row):
        if not self.is_enable():
            return True
        vals = self.get_val(row)
        if isinstance(vals, dict):
            for val in vals.values():
                if self.regex.match(val):
                    return True
        else:
            if isinstance(vals, types.UnicodeType):
                if self.regex.match(vals):
                    return True
            else:
                if self.regex.match(str(vals)):
                    return True
        return False


# -----------------------------------------------------------------------------
class PartialMultipleAnd(Filter):
    """Get the current property into the current row, and match the result with
     a list of values"""

    def __init__(self, propvalues, ignorecase=False):
        super(PartialMultipleAnd, self).__init__(propvalues.keys(), propvalues.values())
        self.regex = {}
        self.propvalues = propvalues
        if self.is_enable():
            for key, value in propvalues.items():
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
        for key, val in vals.items():
            if self.regex[key]:
                if not self.regex[key].match(val):
                    return False
        return True


# -----------------------------------------------------------------------------
class PartialDate(Filter):
    """Get the current property into the current row, and match the result with
     a list of values"""

    def __init__(self, prop, value):
        super(PartialDate, self).__init__(prop, value)
        if self.is_enable():
            pattern = r"" + str(value)
            self.regex = re.compile(pattern)

    def __call__(self, row):
        if not self.is_enable():
            return True
        vals = self.get_val(row)
        if isinstance(vals, dict):
            for val in vals.values():
                if self.regex.match(val):
                    return True
        else:
            formatt = "{da:%Y-%m-%d %H:%M:%S}"
            vals = formatt.format(
                da=datetime.datetime.fromtimestamp(vals / 1000))
            if self.regex.match(vals):
                return True
        return False


# -----------------------------------------------------------------------------
class Equal(Filter):
    """Get the current property into the current row, and test equality.
    Only one value is possible"""

    def __init__(self, prop, values=None):
        super(Equal, self).__init__(prop, values)

    def __call__(self, row):
        if not self.is_enable():
            return True
        val = self.get_val(row)
        if val == self.values:
            return True
        return False


# -----------------------------------------------------------------------------
class Equals(Filter):
    """Get the current property into the current row, and test equality.
    A list of values will be test"""

    def __init__(self, prop, values=None):
        super(Equals, self).__init__(prop, values)

    def __call__(self, row):
        if not self.is_enable():
            return True
        val = self.get_val(row)
        if val in self.values:
            return True
        return False
