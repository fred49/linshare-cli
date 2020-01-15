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
# Copyright 2018 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



import os
import copy
import time

from linshareapi.cache import Time
from linshareapi.core import LinShareException
from linsharecli.user.core import DefaultCommand
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.actions import CreateAction
from linsharecli.common.actions import UpdateAction
from linsharecli.common.filters import PartialOr
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.cell import CellBuilder
from linsharecli.common.cell import ComplexCell
from linsharecli.common.cell import ActorCell
from linsharecli.common.cell import AuthUserCell
from linsharecli.common.cell import ComplexCellBuilder
from linsharecli.common.tables import DeleteAction
from linsharecli.common.tables import TableBuilder


class JwtCreateAction(CreateAction):
    """TODO"""

    MESSAGE_CONFIRM_KEY = 'MSG_RS_CREATED'

    def __init__(self, command, cli):
        super(JwtCreateAction, self).__init__(command, cli)
        self.output = None
        self.force = None
        self.export_var = None

    def load(self, args):
        super(JwtCreateAction, self).load(args)
        self.err_suffix = "actor"
        self.output = args.output
        self.force = args.force
        self.export_var = args.export_var
        return self

    def execute(self, data=None):
        """TODO"""
        if self.output:
            if os.path.isfile(self.output):
                if not self.force:
                    self.log.error("Output token file already exists")
                    return False
                else:
                    if not self.cli_mode:
                        self.log.warn("Existing jwt token file will be overriden.")
        try:
            start = time.time()
            json_obj = self._execute(data)
            end = time.time()
            json_obj['_time'] = end - start
            if json_obj is None:
                self.log.error("Missing return statement for _execute method")
                return False
            if self.debug:
                self.pretty_json(json_obj, "Json object returned by the server")
            if self.output:
                with open(self.output, 'w') as fde:
                    fde.write("export ")
                    fde.write(self.export_var.upper())
                    fde.write("=")
                    fde.write(json_obj['token'])
                    fde.write("\n")
            if self.cli_mode:
                print((json_obj.get(self.command.RESOURCE_IDENTIFIER)))
                return True
            msg = getattr(self.command, self.MESSAGE_CONFIRM_KEY)
            self.pprint(msg, json_obj)
            return True
        except LinShareException as ex:
            self.log.debug("LinShareException : " + str(ex.args))
            self.log.error(ex.args[1] + " : " + str(self.err_suffix))
        return False


class ResourceCell(ComplexCell):
    """TODO"""

    _format_filter = '{uuid}'

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        data = copy.deepcopy(self.value)
        data['action'] = self.row['action'].lower() + "d"
        l_format = 'Jwt token {action}: {label} ({uuid:.8})'
        if self.vertical:
            l_format = 'A jwt token named {label} was created for {subject} ({uuid})'
        return l_format.format(**data)


class JwtCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "label"
    RESOURCE_IDENTIFIER = "uuid"

    MSG_RS_UPDATED = "The Jwt '%(label)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = (
        "The Jwt '%(label)s' (%(uuid)s) was successfully created. (%(_time)s s)\n"
        "Token created: \n\n%(token)s\n"
    )

    def complete(self, args, prefix):
        super(JwtCommand, self).__call__(args)
        json_obj = self.ls.jwt.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    # pylint: disable=unused-argument
    def complete_fields(self, args, prefix):
        """TODO"""
        super(JwtCommand, self).__call__(args)
        cli = self.ls.jwt
        return cli.get_rbu().get_keys(True)

    def complete_domain(self, args, prefix):
        """TODO"""
        super(JwtCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


class JwtListCommand(JwtCommand):
    """ List all Jwt token."""

    @Time('linsharecli.jwt', label='Global time : %(time)s')
    def __call__(self, args):
        super(JwtListCommand, self).__call__(args)
        endpoint = self.ls.jwt
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
            PartialOr(self.RESOURCE_IDENTIFIER, args.uuids, True),
        )
        tbu.add_custom_cell("actor", ComplexCellBuilder('{name} ({uuid})'))
        tbu.add_custom_cell("domain", ComplexCellBuilder('{name} ({uuid})'))
        return tbu.build().load_v2(endpoint.list()).render()


class JwtListAuditCommand(JwtCommand):
    """ List all Jwt token."""

    IDENTIFIER = "creationDate"
    RESOURCE_IDENTIFIER = "uuid"

    @Time('linsharecli.jwt', label='Global time : %(time)s')
    def __call__(self, args):
        super(JwtListAuditCommand, self).__call__(args)
        endpoint = self.ls.jwt.audit
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
        return tbu.build().load_v2(endpoint.list()).render()


class JwtCreateCommand(JwtCommand):
    """Create Jwt token."""

    @Time('linsharecli.jwt', label='Global time : %(time)s')
    def __call__(self, args):
        super(JwtCreateCommand, self).__call__(args)
        act = JwtCreateAction(self, self.ls.jwt)
        return act.load(args).execute()


class JwtUpdateCommand(JwtCommand):
    """Update Jwt token."""

    @Time('linsharecli.jwt', label='Global time : %(time)s')
    def __call__(self, args):
        super(JwtUpdateCommand, self).__call__(args)
        self.check_required_options(
            args,
            ['description', 'label'],
            ["--description", "--label"])
        cli = self.ls.jwt
        node = cli.get(args.uuid)
        act = UpdateAction(self, cli)
        rbu = cli.get_rbu()
        rbu.copy(node)
        rbu.load_from_args(args)
        return act.load(args).execute(rbu.to_resource())


class JwtDeleteCommand(JwtCommand):
    """Delete Jwt token."""

    @Time('linsharecli.jwt', label='Global time : %(time)s')
    def __call__(self, args):
        super(JwtDeleteCommand, self).__call__(args)
        act = DeleteAction()
        act.init(args, self.ls, self.ls.jwt)
        return act.delete(args.uuids)


def add_parser(subparsers, name, desc, config):
    """Add all Jwt token sub commands."""
    parser = subparsers.add_parser(name, help=desc)
    subparsers2 = parser.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list Jwt token.")
    parser.add_argument('identifiers', nargs="*", help="")
    parser.add_argument('-u', '--uuid', dest="uuids", action="append",
                        help="Filter by uuid fragments.")
    add_list_parser_options(parser, delete=True, cdate=False)
    parser.set_defaults(__func__=JwtListCommand(config))

    # command : audit
    parser = subparsers2.add_parser(
        'audit', help="audit Jwt token.")
    parser.add_argument('identifiers', nargs="*", help="")
    parser.add_argument('-u', '--uuid', dest="uuids", action="append",
                        help="Filter by uuid fragments.")
    parser.add_argument('-e', '--resource', action="store",
                        help="Filter by resource uuid")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=JwtListAuditCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete', help="delete Jwt token.")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=JwtDeleteCommand(config))

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create Jwt token.")
    parser.add_argument('label')
    parser.add_argument('--description', action="store")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.add_argument('-o', '--output-token-file',
                        action="store",
                        dest="output",
                        help=("Storing the JWT token in an outputfile"
                              " instead of stdout."))
    parser.add_argument('-f', '--force', action="store_true",
                        help="Override output file even if it already exists.")
    parser.add_argument('--export-var', action="store", default="TOKEN", help="")
    parser.set_defaults(__func__=JwtCreateCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update Jwt token.")
    parser.add_argument('uuid')
    parser.add_argument('--label')
    parser.add_argument('--description', action="store")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=JwtUpdateCommand(config))
