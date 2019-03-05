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


from __future__ import unicode_literals

import datetime
# pylint: disable=import-error
from hurry.filesize import size as filesize
from hurry.filesize import si

# pylint: disable=too-few-public-methods
class Formatter(object):
    """TODO"""
    def __init__(self, prop, formatt=None):
        """ prop name and value(s)"""
        self.prop = prop
        self.formatt = formatt

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
            row[self.prop] = self.formatt.format(
                da=datetime.datetime.fromtimestamp(ldate / 1000))


class SizeFormatter(Formatter):
    """TODO"""

    def __init__(self, prop, empty=None):
        super(SizeFormatter, self).__init__(prop)
        self.empty = empty

    def __call__(self, row, context=None):
        lsize = row.get(self.prop)
        if lsize is not None:
            row[self.prop] = filesize(lsize, system=si)
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
        if self.prop not in row.keys():
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


class WelcomeMessageFormatter(Formatter):
    """TODO"""

    def __init__(self, prop):
        super(WelcomeMessageFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            row[self.prop] = '{name} ({uuid:.8})'.format(**parameter)


class UserProvidersFormatter(Formatter):
    """TODO"""

    def __init__(self, prop):
        super(UserProvidersFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            output = []
            for param in parameter:
                display = ("{baseDn} (ldap:{ldapConnectionUuid:.8},"
                           "pattern:{userLdapPatternUuid:.8})"
                          )
                output.append(display.format(**param))
            row[self.prop] = ",".join(output)


class LastAuthorFormatter(Formatter):
    """Convert resource owner (user) value to a readable name"""

    def __init__(self, prop):
        super(LastAuthorFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            row[self.prop] = '{name} <{mail}>'.format(
                **parameter)
