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

from linshare_cli.user.core import DefaultCommand


# -----------------------------------------------------------------------------
class UsersListCommand(DefaultCommand):
    """ List all users store into LinShare."""

    def __call__(self, args):
        super(UsersListCommand, self).__call__(args)

        json_obj = self.ls.users.list()
        d_format = "{firstName:11s}{lastName:10s}{domain:<20}{mail}"
        #print "%(firstName)-10s %(lastName)-10s\t %(domain)s %(mail)s" % f
        #self.pretty_json(json_obj)
        self.print_list(json_obj, d_format, "Users")


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()
    parser_tmp2 = subparsers2.add_parser('list',
                                         help="list users from linshare")
    parser_tmp2.set_defaults(__func__=UsersListCommand())
