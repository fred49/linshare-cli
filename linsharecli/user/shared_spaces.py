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
# pylint: disable=import-error
from vhatable.filters import PartialOr
from linsharecli.user.core import DefaultCommand as Command
from linsharecli.common.actions import CreateOneAction
from linsharecli.common.actions import UpdateOneAction
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.tables import Action
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import DeleteAction


class DefaultCommand(Command):
    """TODO"""

    IDENTIFIER = "name"

    MSG_RS_UPDATED = (
        "The shared space '%(name)s' (%(uuid)s) was successfully updated."
    )
    MSG_RS_CREATED = (
        "The shared space '%(name)s' (%(uuid)s) was successfully created."
    )

    def complete(self, args, prefix):
        super().__call__(args)
        json_obj = self.ls.shared_spaces.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(
                    self.RESOURCE_IDENTIFIER).startswith(prefix))

    def complete_drive(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.shared_spaces.list()

        def cond(node):
            start_with = node.get(self.RESOURCE_IDENTIFIER).startswith(prefix)
            return start_with and node['nodeType'] == "DRIVE"
        return (v.get(self.RESOURCE_IDENTIFIER) for v in json_obj if cond(v))

    def complete_workspace(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.shared_spaces.list()

        def cond(node):
            start_with = node.get(self.RESOURCE_IDENTIFIER).startswith(prefix)
            return start_with and node['nodeType'] == "WORK_SPACE"
        return (v.get(self.RESOURCE_IDENTIFIER) for v in json_obj if cond(v))


class Breadcrumb(Action):
    """TODO"""

    display = True

    def init(self, args, cli, endpoint):
        """TODO"""
        super().init(args, cli, endpoint)
        self.display = not getattr(args, 'no_breadcrumb', False)

    def __call__(self, args, cli, endpoint, data):
        self.init(args, cli, endpoint)
        if self.display:
            drive_uuid = getattr(args, 'drive', None)
            if drive_uuid:
                node = endpoint.get(drive_uuid)
                print()
                print("###>", node['name'])
                print()


class ListCommand(DefaultCommand):
    """ List all shared_spaces store into LinShare."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super().__call__(args)
        endpoint = self.ls.shared_spaces
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.names, True),
            PartialOr(self.RESOURCE_IDENTIFIER, args.uuids, True)
        )
        tbu.add_pre_render_class(Breadcrumb())
        if self.config.server.api_version.value == 4.2:
            # pylint: disable=unexpected-keyword-arg
            return tbu.build().load_v2(
                    endpoint.list(drive=args.drive)).render()
        if self.config.server.api_version.value >= 5:
            # pylint: disable=unexpected-keyword-arg
            return tbu.build().load_v2(
                    endpoint.list(workspace=args.workspace)).render()
        return tbu.build().load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super().__call__(args)
        cli = self.ls.shared_spaces
        return cli.get_rbu().get_keys(True)


class DetailCommand(DefaultCommand):
    """ List all shared_spaces store into LinShare."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super().__call__(args)
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
        super().__call__(args)
        cli = self.ls.shared_spaces
        return cli.get_rbu().get_keys(True)


class DeleteCommand(DefaultCommand):
    """Delete shared space."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super().__call__(args)
        act = DeleteAction()
        act.init(args, self.ls, self.ls.shared_spaces)
        return act.delete(args.uuids)


class UpdateCommand(DefaultCommand):
    """TODO"""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super().__call__(args)
        self.check_required_options(
            args,
            ['name'],
            ["--name"])
        endpoint = self.ls.shared_spaces
        node = endpoint.get(args.uuid)
        act = UpdateOneAction(self, endpoint)
        rbu = endpoint.get_rbu()
        rbu.copy(node)
        rbu.load_from_args(args)
        return act.load(args).execute(rbu.to_resource())


class CreateCommand(DefaultCommand):
    """TODO"""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super().__call__(args)
        act = CreateOneAction(self, self.ls.shared_spaces)
        act.load(args)
        return act.execute()


def add_parser(subparsers, name, desc, config):
    """TODO"""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()
    api_version = config.server.api_version.value

    # command : list
    parser = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list shared space from linshare")
    parser.add_argument('names', nargs="*",
                        help="Filter shared spaces by uuid")
    if api_version == 4.2:
        parser.add_argument(
            '-d', '--drive', help="See the content of a drive.",
        ).completer = Completer('complete_drive')
    if api_version >= 5:
        parser.add_argument(
            '-w', '--workspace', help="See the content of a workspace.",
        ).completer = Completer('complete_workspace')
    parser.add_argument(
        '-u', '--uuids', nargs="*", help="Filter shared spaces by uuid")
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

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create shared space.")
    parser.add_argument('name', action="store", help="shared space name")
    if api_version == 4.2:
        parser.add_argument('--type', dest="node_type", action="store",
                            choices=['WORK_GROUP', 'DRIVE'],
                            help="")
    if api_version >= 5:
        parser.add_argument('--type', dest="node_type", action="store",
                            choices=['WORK_GROUP', 'WORK_SPACE'],
                            help="")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=CreateCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update shared space.")
    parser.add_argument(
        'uuid', action="store", help="").completer = Completer()
    parser.add_argument(
            '--name', action="store",
            help="Filter by name (partial)")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=UpdateCommand(config))
