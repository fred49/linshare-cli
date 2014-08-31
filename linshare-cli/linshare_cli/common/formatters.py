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

import datetime
from hurry.filesize import size as filesize

# pylint: disable=R0921
# pylint: disable=C0111
# -----------------------------------------------------------------------------
class Formatter(object):
    def __init__(self, prop, formatt=None):
        """ prop name and value(s)"""
        self.prop = prop
        self.formatt = formatt

    def get_val(self, row):
        val = row.get(self.prop)
        if val is None:
            raise ValueError("missing key : " + self.prop)
        return val


# -----------------------------------------------------------------------------
class DateFormatter(Formatter):

    def __init__(self, prop, formatt="%Y-%m-%d %H:%M:%S"):
        super(DateFormatter, self).__init__(prop, formatt)
        self.formatt = "{da:" + formatt + "}"

    def __call__(self, row):
        ldate = row.get(self.prop)
        if ldate is not None:
            row[self.prop] = self.formatt.format(
                da=datetime.datetime.fromtimestamp(ldate / 1000))


# -----------------------------------------------------------------------------
class SizeFormatter(Formatter):

    def __init__(self, prop):
        super(SizeFormatter, self).__init__(prop)

    def __call__(self, row):
        lsize = row.get(self.prop)
        if lsize is not None:
            row[self.prop] = filesize(lsize)
