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

from linshare_cli.common.core import VTable
from linshare_cli.common.core import HTable
from linshare_cli.admin.core import DefaultCommand
from argtoolbox import DefaultCompleter as Completer
import re


# -----------------------------------------------------------------------------
class UsersListCommand(DefaultCommand):
    """ List all users store into LinShare."""

    def __call__(self, args):
        super(UsersListCommand, self).__call__(args)
        json_obj = self.ls.users.search(args.firstname, args.lastname,
                                        args.mail)
        self.format_date(json_obj, 'creationDate')
        self.format_date(json_obj, 'modificationDate')
        self.format_date(json_obj, 'expirationDate')
        keys = self.ls.users.get_rbu().get_keys(args.extended)
        table = None
        if args.vertical:
            table = VTable(keys, debug=self.debug)
        else:
            table = HTable(keys)
            # styles
            table.align["mail"] = "l"
            table.padding_width = 1
        table.sortby = "mail"
        table.reversesort = args.reverse

        def filters(row):
            if not args.identifiers:
                return True
            if re.search(r"^.*(" + "|".join(args.identifiers) + ").*$",
                         row.get('uuid')):
                return True
            return False
        table.print_table(json_obj, keys, filters)
        return True


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc):
    """Add all user sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()
    parser_tmp2 = subparsers2.add_parser('list',
                                         help="list users from linshare")
    parser_tmp2.add_argument('identifiers', nargs="*",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-f', '--firstname', action="store")
    parser_tmp2.add_argument('-l', '--lastname', action="store")
    parser_tmp2.add_argument('-m', '--mail', action="store")
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting")
    parser_tmp2.add_argument('-t', '--vertical', action="store_true",
                             help="use vertical output mode")
    parser_tmp2.set_defaults(__func__=UsersListCommand())
