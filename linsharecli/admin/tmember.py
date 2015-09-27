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

from linsharecli.common.filters import PartialOr
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.core import VTable
from linsharecli.common.core import HTable
from linsharecli.admin.core import DefaultCommand
from argtoolbox import DefaultCompleter as Completer


# -----------------------------------------------------------------------------
class ThreadMembersListCommand(DefaultCommand):
    """ List all thread members store from a thread."""
    IDENTIFIER = "name"

    def __call__(self, args):
        super(ThreadMembersListCommand, self).__call__(args)
        cli = self.ls.thread_members
        table = self.get_table(args, cli, self.IDENTIFIER)
        table.show_table(
            cli.list(args.uuid)
        )
        return True

    def complete(self, args, prefix):
        super(ThreadMembersListCommand, self).__call__(args)
        json_obj = self.ls.threads.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    """Add all thread member sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()
    parser_tmp2 = subparsers2.add_parser(
        'list',
        help="list thread members.")
    parser_tmp2.add_argument(
        '-u',
        '--uuid',
        action="store",
        dest="uuid",
        required=True).completer = Completer()
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting")
    parser_tmp2.add_argument('-t', '--vertical', action="store_true",
                             help="use vertical output mode")
    parser_tmp2.add_argument('--csv', action="store_true", help="Csv output")
    parser_tmp2.add_argument('--raw', action="store_true",
                             help="Disable all formatters")
    parser_tmp2.set_defaults(__func__=ThreadMembersListCommand())
