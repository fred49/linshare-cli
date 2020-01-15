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
# Copyright 2014 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



from argtoolbox import DefaultCompleter as Completer
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.cell import CellBuilder
from linsharecli.common.tables import TableBuilder


class UsersListCommand(DefaultCommand):
    """ List all users store into LinShare."""
    IDENTIFIER = "mail"

    def __call__(self, args):
        super(UsersListCommand, self).__call__(args)
        if not  (args.firstname or args.lastname or args.mail):
            raise ValueError('You should use at leat one option among : --firstname, --lastname or --mail')
        endpoint = self.ls.users
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell("domain", CellBuilder('{value:.8}', '{value}'))
        json_obj = endpoint.search(args.firstname, args.lastname, args.mail)
        return tbu.build().load_v2(json_obj).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(UsersListCommand, self).__call__(args)
        cli = self.ls.users
        return cli.get_rbu().get_keys(True)


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
    parser_tmp2.add_argument(
        '-k', '--field', action='append', dest="fields"
    ).completer = Completer("complete_fields")
    parser_tmp2.set_defaults(__func__=UsersListCommand(config))
