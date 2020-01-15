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
from argtoolbox import DefaultCompleter as Completer
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.actions import CreateAction
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.tables import TableBuilder


class LdapConnectionsCommand(DefaultCommand):
    """For  api >= 1.9"""
    # pylint: disable=too-many-instance-attributes
    IDENTIFIER = "label"
    DEFAULT_SORT = "label"
    RESOURCE_IDENTIFIER = "uuid"

    DEFAULT_TOTAL = "Ldap connection found : %(count)s"
    MSG_RS_NOT_FOUND = "No Ldap connection could be found."
    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The Ldap connection '%(label)s' (%(uuid)s) was deleted. "
        "(%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The Ldap connection '%(label)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s Ldap connection(s) can not be deleted."
    MSG_RS_UPDATED = "The Ldap connection '%(label)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = (
        "The Ldap connection '%(label)s' (%(uuid)s) was "
        "successfully created. (%(_time)s s)"
    )

    # pylint: disable=invalid-name
    def init_old_language_key(self):
        """For  api >= 1.6 and api <= 1.8"""
        self.IDENTIFIER = "identifier"
        self.DEFAULT_SORT = "identifier"
        self.RESOURCE_IDENTIFIER = "identifier"

        self.DEFAULT_TOTAL = "Ldap connection found : %(count)s"
        self.MSG_RS_NOT_FOUND = "No Ldap connection could be found."
        self.MSG_RS_DELETED = "The Ldap connection '%(identifier)s' was deleted. (%(time)s s)"
        self.MSG_RS_DELETED = (
            "%(position)s/%(count)s: "
            "The Ldap connection '%(identifier)s' was deleted. (%(time)s s)"
        )
        self.MSG_RS_CAN_NOT_BE_DELETED = "The Ldap connection '%(identifier)s' can not be deleted."
        self.MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s Ldap connection(s) can not be deleted."
        self.MSG_RS_UPDATED = "The Ldap connection '%(identifier)s' was successfully updated."
        self.MSG_RS_CREATED = "The Ldap connection '%(identifier)s' was successfully created."

    def complete(self, args, prefix):
        super(LdapConnectionsCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        json_obj = self.ls.ldap_connections.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


class LdapConnectionsListCommand(LdapConnectionsCommand):
    """ List all ldap connections."""

    @Time('linsharecli.ldap', label='Global time : %(time)s')
    def __call__(self, args):
        super(LdapConnectionsListCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        endpoint = self.ls.ldap_connections
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        return tbu.build().load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(LdapConnectionsListCommand, self).__call__(args)
        cli = self.ls.ldap_connections
        return cli.get_rbu().get_keys(True)


class LdapConnectionsCreateCommand(LdapConnectionsCommand):
    """Create ldap connection."""

    def __call__(self, args):
        super(LdapConnectionsCreateCommand, self).__call__(args)
        self.log.debug("api_version : " + str(self.api_version))
        if self.api_version == 0:
            self.init_old_language_key()
        act = CreateAction(self, self.ls.ldap_connections)
        return act.load(args).execute()

class LdapConnectionsUpdateCommand(LdapConnectionsCommand):
    """Update ldap connection."""

    def __call__(self, args):
        super(LdapConnectionsUpdateCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        cli = self.ls.ldap_connections
        resource = cli.get(args.identifier)
        rbu = cli.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            cli.update,
            self.MSG_RS_UPDATED,
            args.identifier,
            rbu.to_resource())


class LdapConnectionsDeleteCommand(LdapConnectionsCommand):
    """Delete ldap connection."""

    def __call__(self, args):
        super(LdapConnectionsDeleteCommand, self).__call__(args)
        cli = self.ls.ldap_connections
        if self.api_version == 0:
            self.init_old_language_key()
            return self._delete(
                args,
                cli,
                args.identifier)
        return self._delete_all(args, cli, args.uuids)


def add_parser(subparsers, name, desc, config):
    """Add all ldap connections sub commands."""
    api_version = config.server.api_version.value
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list ldap connections.")
    parser.add_argument('identifiers', nargs="*", help="")
    if api_version == 0:
        add_list_parser_options(parser, delete=True)
    else:
        add_list_parser_options(parser, delete=True, cdate=False)
    parser.set_defaults(__func__=LdapConnectionsListCommand(config))

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete ldap connections.")
    if api_version == 0:
        parser_tmp2.add_argument(
            'identifier',
            action="store",
            help="").completer = Completer()
    else:
        add_delete_parser_options(parser_tmp2)
    parser_tmp2.set_defaults(__func__=LdapConnectionsDeleteCommand(config))

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create ldap connections.")
    parser_tmp2.add_argument('--provider-url', action="store", help="",
                             required=True)
    parser_tmp2.add_argument('--principal', action="store", help="")
    parser_tmp2.add_argument('--credential', action="store", help="")
    parser_tmp2.add_argument('--cli-mode', action="store_true", help="")
    if api_version == 0:
        parser_tmp2.add_argument('identifier', action="store", help="")
        parser_tmp2.set_defaults(__func__=LdapConnectionsCreateCommand(config))
    else:
        parser_tmp2.add_argument('label', action="store", help="")
        parser_tmp2.set_defaults(__func__=LdapConnectionsCreateCommand(config))

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update ldap connections.")
    parser_tmp2.add_argument(
        'identifier', action="store", help="").completer = Completer()
    parser_tmp2.add_argument('--provider-url', action="store", help="")
    parser_tmp2.add_argument('--principal', action="store", help="")
    parser_tmp2.add_argument('--credential', action="store", help="")
    parser_tmp2.set_defaults(__func__=LdapConnectionsUpdateCommand(config))
