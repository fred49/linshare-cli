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



from argparse import RawTextHelpFormatter
from argtoolbox import DefaultCompleter as Completer
from linshareapi.cache import Time
from linsharecli.admin.core import DefaultCommand as Command
from linsharecli.common.filters import PartialOr
from linsharecli.common.actions import UpdateAction
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import DeleteAction


class DefaultCommand(Command):
    """TODO"""

    IDENTIFIER = "name"
    DEFAULT_SORT = "name"

    MSG_RS_UPDATED = "The shared space '%(name)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The shared space '%(name)s' (%(uuid)s) was successfully created."

    def complete(self, args, prefix):
        super(DefaultCommand, self).__call__(args)
        json_obj = self.ls.shared_spaces.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


class ListCommand(DefaultCommand):
    """ List all shared_spaces store into LinShare."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(ListCommand, self).__call__(args)
        endpoint = self.ls.shared_spaces
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.names, True),
            PartialOr(self.RESOURCE_IDENTIFIER, args.uuids, True)
        )
        return tbu.build().load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(ListCommand, self).__call__(args)
        cli = self.ls.shared_spaces
        return cli.get_rbu().get_keys(True)


class DetailCommand(DefaultCommand):
    """ List all shared_spaces store into LinShare."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(DetailCommand, self).__call__(args)
        endpoint = self.ls.shared_spaces
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        json_obj = []
        for uuid in args.uuids:
            json_obj.append(endpoint.get(uuid))
        return tbu.build().load_v2(json_obj).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(DetailCommand, self).__call__(args)
        cli = self.ls.shared_spaces
        return cli.get_rbu().get_keys(True)


class DeleteCommand(DefaultCommand):
    """Delete shared space."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(DeleteCommand, self).__call__(args)
        act = DeleteAction()
        act.init(args, self.ls, self.ls.shared_spaces)
        return act.delete(args.uuids)


class UpdateCommand(DefaultCommand):
    """TODO"""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(UpdateCommand, self).__call__(args)
        self.check_required_options(
            args,
            ['name'],
            ["--name"])
        endpoint = self.ls.shared_spaces
        node = endpoint.get(args.uuid)
        act = UpdateAction(self, endpoint)
        rbu = endpoint.get_rbu()
        rbu.copy(node)
        rbu.load_from_args(args)
        return act.load(args).execute(rbu.to_resource())


def add_parser(subparsers, name, desc, config):
    """TODO"""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list shared space from linshare")
    parser.add_argument('names', nargs="*", help="")
    parser.add_argument('-u', '--uuids', nargs="*", help="")
    add_list_parser_options(parser, delete=True, cdate=True)
    parser.set_defaults(__func__=ListCommand(config))

    # command : detail
    parser = subparsers2.add_parser(
        'detail',
        formatter_class=RawTextHelpFormatter,
        help="detail shared space from linshare")
    parser.add_argument('uuids', nargs="+", help="")
    add_list_parser_options(parser, delete=True, cdate=True)
    parser.set_defaults(__func__=DetailCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete shared space")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=DeleteCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update shared space.")
    parser.add_argument(
        'uuid', action="store", help="").completer = Completer()
    parser.add_argument('--name', action="store", help="Filter by name (partial)")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=UpdateCommand(config))
