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



from argparse import RawTextHelpFormatter
from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.tables import TableBuilder
from vhatable.filters import PartialMultipleAnd
from vhatable.filters import PartialOr


class UsersListCommand(DefaultCommand):
    """ List all users store into LinShare."""
    IDENTIFIER = "mail"
    DEFAULT_SORT = "mail"

    @Time('linsharecli.users', label='Global time : %(time)s')
    def __call__(self, args):
        super(UsersListCommand, self).__call__(args)
        endpoint = self.ls.users
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialMultipleAnd(
                {
                    "mail": args.mail,
                    "firstName": args.firstname,
                    "lastName": args.lastname
                },
                True),
            PartialOr("uuid", args.uuid),
            PartialOr(self.IDENTIFIER, args.pattern, True)
        )
        return tbu.build().load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        super(UsersListCommand, self).__call__(args)
        cli = self.ls.users
        return cli.get_rbu().get_keys(True)


def add_parser(subparsers, name, desc, config):
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list users from linshare")
    parser.add_argument(
        'pattern', nargs="*",
        help="Filter documents by their names")
    parser.add_argument('-f', '--firstname', action="store")
    parser.add_argument('-l', '--lastname', action="store")
    parser.add_argument('-m', '--mail', action="store")
    parser.add_argument('-u', '--uuid', action="append")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=UsersListCommand(config))
