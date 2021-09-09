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



import datetime
import logging

from vhatable.cell import ComplexCell

class ActorCell(ComplexCell):
    """TODO"""

    def __init__(self, value):
        super(ActorCell, self).__init__(value)
        self._format = '{name} \n({uuid:.8})'
        self._format_vertical = '{name} ({uuid})'

    def __unicode__(self):
        """TODO"""
        # pylint: disable=too-many-return-statements
        if self.raw:
            if self.value is None:
                return "None"
            return str(self.value)
        if self.value is None:
            return self.none
        auth_user = self.row['authUser']
        _format = self._format
        _format_vertical = self._format_vertical
        if auth_user.hidden:
            if self.value['uuid'] != auth_user['uuid']:
                _format = '{name} \033[91m*\033[0m\n({uuid:.8})'
                _format_vertical = '{name} \033[91m*\033[0m ({uuid})'
        if self.vertical:
            return _format_vertical.format(**self.value)
        return _format.format(**self.value)


class AuthUserCell(ComplexCell):
    """TODO"""

    def __init__(self, value):
        super(AuthUserCell, self).__init__(value)
        self._format = '{name}\n({uuid:.8})'
        self._format_vertical = '{name} ({uuid})'

    def __unicode__(self):
        """TODO"""
        # pylint: disable=too-many-return-statements
        if self.raw:
            if self.value is None:
                return "None"
            return str(self.value)
        if self.value is None:
            return self.none
        if self.vertical:
            if self._format_vertical:
                return self._format_vertical.format(**self.value)
        if self._format:
            actor = self.row['actor']
            if self.value['uuid'] == actor['uuid'] and not actor.hidden:
                return "- idem -"
            return self._format.format(**self.value)
        return str(self.value)
