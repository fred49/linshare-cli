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

from linsharecli.common.formatters import DateFormatter
from linsharecli.admin.core import DefaultCommand
#from argtoolbox import DefaultCompleter as Completer


# -----------------------------------------------------------------------------
class UsersListCommand(DefaultCommand):
    """ List all users store into LinShare."""
    IDENTIFIER = "mail"

    def __call__(self, args):
        super(UsersListCommand, self).__call__(args)
        cli = self.ls.users
        if not  (args.firstname or args.lastname or args.mail):
            raise ValueError('You should use at leat one option among : --firstname, --lastname or --mail')
        table = self.get_table(args, cli, self.IDENTIFIER)
        table.show_table(
            cli.search(args.firstname, args.lastname, args.mail),
            formatters=[DateFormatter('creationDate'),
             DateFormatter('expirationDate'),
             DateFormatter('modificationDate')]
        )
        return True


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    """Add all user sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()
    parser_tmp2 = subparsers2.add_parser('list',
                                         help="list users from linshare")
    parser_tmp2.add_argument('-f', '--firstname', action="store")
    parser_tmp2.add_argument('-l', '--lastname', action="store")
    parser_tmp2.add_argument('-m', '--mail', action="store")
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting")
    parser_tmp2.add_argument('-t', '--vertical', action="store_true",
                             help="use vertical output mode")
    parser_tmp2.add_argument('--csv', action="store_true", help="Csv output")
    parser_tmp2.add_argument('--raw', action="store_true",
                             help="Disable all formatters")
    parser_tmp2.set_defaults(__func__=UsersListCommand())
