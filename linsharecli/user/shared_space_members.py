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
from linshareapi.cache import Time
from argtoolbox import DefaultCompleter as Completer
from linsharecli.user.core import DefaultCommand as Command
from linsharecli.common.filters import PartialOr
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.cell import ComplexCellBuilder
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import DeleteAction
from linsharecli.common.actions import CreateAction
from linsharecli.common.actions import UpdateAction


class DefaultCommand(Command):
    """TODO"""

    IDENTIFIER = "creationDate"

    MSG_RS_UPDATED = "The shared space member '%(account)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The shared space member '%(account)s' (%(uuid)s) was successfully created."

    CFG_DELETE_MODE = 1
    CFG_DELETE_ARG_ATTR = "ss_uuid"


    def complete(self, args, prefix):
        super(DefaultCommand, self).__call__(args)
        json_obj = self.ls.shared_spaces.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    def complete_shared_spaces(self, args, prefix):
        """TODO"""
        super(DefaultCommand, self).__call__(args)
        json_obj = self.ls.shared_spaces.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


class SharedSpaceCompleter(object):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, config):
        self.config = config

    def __call__(self, prefix, **kwargs):
        from argcomplete import debug
        try:
            debug("\n------------ SharedSpaceCompleter -----------------")
            debug("Kwargs content :")
            for i, j in list(kwargs.items()):
                debug("key : " + str(i))
                debug("\t - " + str(j))
            debug("\n------------ SharedSpaceCompleter -----------------\n")
            args = kwargs.get('parsed_args')
            cmd = DefaultCommand(self.config)
            return cmd.complete_shared_spaces(args, prefix)
        # pylint: disable=broad-except
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")
            import traceback
            traceback.print_exc()
            debug("\n------\n")
            return ["comlete-error"]


class ListCommand(DefaultCommand):
    """ List all shared_spaces store into LinShare."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(ListCommand, self).__call__(args)
        endpoint = self.ls.shared_spaces.members
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell(
            "role",
            ComplexCellBuilder(
                '{name}\n({uuid:.8})',
                '{name} ({uuid:})',
                '{name}',
            )
        )
        tbu.add_custom_cell(
            "account",
            ComplexCellBuilder(
                '{name}\n({uuid:.8})',
                '{name} <{mail}> ({uuid})',
                '{name}',
            )
        )
        tbu.add_custom_cell("node", ComplexCellBuilder('{nodeType}: {name} ({uuid:.8})'))
        tbu.add_action('delete', DeleteAction(
            mode=self.CFG_DELETE_MODE,
            parent_identifier=self.CFG_DELETE_ARG_ATTR
        ))
        tbu.add_filters(
            PartialOr("account", args.accounts, True),
            PartialOr(self.RESOURCE_IDENTIFIER, args.uuids, True),
            PartialOr("role", args.roles, True)
        )
        return tbu.build().load_v2(endpoint.list(args.ss_uuid)).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(ListCommand, self).__call__(args)
        cli = self.ls.shared_spaces
        return cli.get_rbu().get_keys(True)


class CreateCommand(DefaultCommand):
    """TODO"""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(CreateCommand, self).__call__(args)
        act = CreateAction(self, self.ls.shared_spaces.members)
        act.load(args)
        act.rbu.set_value('node', {'uuid': args.ss_uuid})
        return act.execute()


class DeleteCommand(DefaultCommand):
    """Delete shared space."""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(DeleteCommand, self).__call__(args)
        act = DeleteAction(
            mode=self.CFG_DELETE_MODE,
            parent_identifier=self.CFG_DELETE_ARG_ATTR
        )
        act.init(args, self.ls, self.ls.shared_spaces.members)
        return act.delete(args.uuids)


class UpdateCommand(DefaultCommand):
    """TODO"""

    @Time('linsharecli.shared_spaces', label='Global time : %(time)s')
    def __call__(self, args):
        super(UpdateCommand, self).__call__(args)
        self.check_required_options(
            args,
            ['role'],
            ["--role"])
        endpoint = self.ls.shared_spaces.members
        node = endpoint.get(args.ss_uuid, args.uuid)
        act = UpdateAction(self, endpoint)
        rbu = endpoint.get_rbu()
        rbu.copy(node)
        rbu.load_from_args(args)
        return act.load(args).execute(rbu.to_resource())


def add_parser(subparsers, name, desc, config):
    """TODO"""
    parser_tmp = subparsers.add_parser(name, help=desc)
    parser_tmp.add_argument(
        'ss_uuid',
        help="shared_space uuid"
        ).completer = SharedSpaceCompleter(config)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list shared space from linshare")
    parser.add_argument(
        'accounts', nargs="*",
        help="Filter documents by their account names")
    parser.add_argument('-u', '--uuid', dest="uuids", action="append", help="")
    parser.add_argument('-o', '--role', dest="roles", action="append",
                        choices=['ADMIN', 'WRITER', 'CONTRIBUTOR', 'READER'],
                        help="")
    add_list_parser_options(parser, delete=True, cdate=True)
    parser.set_defaults(__func__=ListCommand(config))

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create shared space.")
    parser.add_argument('account', action="store", help="Account uuid")
    parser.add_argument('--role', action="store",
                        choices=['ADMIN', 'WRITER', 'CONTRIBUTOR', 'READER'],
                        help="")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=CreateCommand(config))

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
    parser.add_argument('--role', action="store",
                        choices=['ADMIN', 'WRITER', 'CONTRIBUTOR', 'READER'],
                        help="")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=UpdateCommand(config))
