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



from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_list_parser_options
from argtoolbox import DefaultCompleter as Completer


class ThreadMembersListCommand(DefaultCommand):
    """ List all thread members store from a thread."""
    IDENTIFIER = "name"

    def __call__(self, args):
        super(ThreadMembersListCommand, self).__call__(args)
        cli = self.ls.thread_members
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        json_obj = cli.list(args.uuid)
        table.load(json_obj)
        table.render()
        return True

    def complete(self, args, prefix):
        super(ThreadMembersListCommand, self).__call__(args)
        json_obj = self.ls.threads.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(ThreadMembersListCommand, self).__call__(args)
        cli = self.ls.thread_members
        return cli.get_rbu().get_keys(True)


def add_parser(subparsers, name, desc, config):
    """Add all thread member sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()
    parser = subparsers2.add_parser(
        'list',
        help="list thread members.")
    parser.add_argument(
        '-u',
        '--uuid',
        action="store",
        dest="uuid",
        required=True).completer = Completer()
    add_list_parser_options(parser, cdate=True)
    parser.set_defaults(__func__=ThreadMembersListCommand(config))
