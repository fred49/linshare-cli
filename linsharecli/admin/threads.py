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



from linshareapi.cache import Time
from vhatable.filters import PartialOr
from linsharecli.common.core import add_list_parser_options
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.tables import TableBuilder


class ThreadsListCommand(DefaultCommand):
    """ List all threads store into LinShare."""
    IDENTIFIER = "name"

    @Time('linsharecli.threads', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadsListCommand, self).__call__(args)
        endpoint = self.ls.threads
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        return tbu.build().load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(ThreadsListCommand, self).__call__(args)
        cli = self.ls.threads
        return cli.get_rbu().get_keys(True)


def add_parser(subparsers, name, desc, config):
    """Add all thread sub commands."""
    if config.server.api_version.value >= 5:
        return
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list threads from linshare")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=ThreadsListCommand(config))
