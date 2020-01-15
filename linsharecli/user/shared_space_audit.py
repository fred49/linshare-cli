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




import copy
import json

from argparse import RawTextHelpFormatter
from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand as Command
from linsharecli.common.filters import PartialOr
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.cell import CellBuilder
from linsharecli.common.cell import ComplexCell
from linsharecli.common.cell import ActorCell
from linsharecli.common.cell import AuthUserCell
from linsharecli.common.cell import ComplexCellBuilder
from linsharecli.common.tables import TableBuilder


class DefaultCommand(Command):
    """TODO"""

    IDENTIFIER = "name"

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


class ResourceCell(ComplexCell):
    """TODO"""

    _format_filter = '{uuid}'

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none

        action = self.row['action']
        resource_type = self.row['type']

        fmt = 'Missing format. {raw}'
        data = {}
        data['action'] = action
        data['raw'] = "?"
        if self.extended:
            fmt = 'Missing format.\n{raw}'
            data['raw'] = json.dumps(
                copy.deepcopy(self.value),
                sort_keys=True, indent=2
            )
        if resource_type == "WORKGROUP":
            if action == "CREATE":
                fmt = 'New workGroup : {name} ({uuid:.8})'
                data.update(self.value)
        elif resource_type == "WORKGROUP_MEMBER":
            if action == "CREATE":
                fmt = 'New member : {name} ({uuid:.8})'
                if self.vertical:
                    fmt = 'New member : {name} ({uuid})'
                data.update(self.value['user'])
        elif resource_type == "WORKGROUP_FOLDER":
            if action == "CREATE":
                fmt = 'New folder : {name} ({uuid:.8})'
                if self.vertical:
                    fmt = 'New folder : {name} ({uuid})'
                data.update(self.value)
        elif resource_type == "WORKGROUP_DOCUMENT":
            if action == "CREATE":
                fmt = 'New document : {name} ({uuid:.8})'
                if self.vertical:
                    fmt = 'New document : {name} ({uuid})'
                data.update(self.value)
        elif resource_type == "WORKGROUP_DOCUMENT_REVISION":
            if action == "CREATE":
                fmt = 'New version : {name} ({uuid:.8})'
                if self.vertical:
                    fmt = 'New version : {name} ({uuid})'
                data.update(self.value)
        return fmt.format(**data)


class ListCommand(Command):
    """ List all Jwt token."""

    IDENTIFIER = "creationDate"
    RESOURCE_IDENTIFIER = "uuid"

    @Time('linsharecli.shared_spaces.audit', label='Global time : %(time)s')
    def __call__(self, args):
        super(ListCommand, self).__call__(args)
        endpoint = self.ls.shared_spaces.audit
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
            PartialOr(self.RESOURCE_IDENTIFIER, args.uuids, True, match_raw=True),
            PartialOr("resource", [args.resource], True, match_raw=False),
        )
        tbu.add_custom_cell("actor", ActorCell)
        tbu.add_custom_cell("authUser", AuthUserCell)
        tbu.add_custom_cell("uuid", CellBuilder('{value:.8}', '{value}'))
        tbu.add_custom_cell("resource", ResourceCell)
        tbu.add_custom_cell(
            "workGroup",
            ComplexCellBuilder(
                '{name}\n({uuid:.8})',
                '{name} ({uuid:})',
                '{name}',
            )
        )
        table = tbu.build().load_v2(endpoint.list(args.ss_uuid))
        table.align['resource'] = "l"
        return table.render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(ListCommand, self).__call__(args)
        cli = self.ls.shared_spaces.audit
        return cli.get_rbu().get_keys(True)


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
        help="list shared space audit traces")
    parser.add_argument('identifiers', nargs="*", help="filter by fragments of date")
    parser.add_argument('-u', '--uuid', dest="uuids", action="append",
                        help="Filter by uuid fragments.")
    parser.add_argument('-e', '--resource', action="store",
                        help="Filter by resource uuid")
    add_list_parser_options(parser, cdate=True)
    parser.set_defaults(__func__=ListCommand(config))
