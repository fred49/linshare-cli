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
from linsharecli.admin.core import DefaultCommand
from argtoolbox import DefaultCompleter as Completer


# -----------------------------------------------------------------------------
class LdapConnectionsListCommand(DefaultCommand):
    """ List all ldap connections."""
    IDENTIFIER = "identifier"

    def __call__(self, args):
        super(LdapConnectionsListCommand, self).__call__(args)
        cli = self.ls.ldap_connections
        table = self.get_table(args, cli, self.IDENTIFIER)
        table.show_table(
            cli.list(),
            PartialOr(self.IDENTIFIER, args.identifiers, True)
        )
        return True

    def complete(self, args, prefix):
        super(LdapConnectionsListCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class LdapConnectionsCreateCommand(DefaultCommand):
    """Create ldap connection."""

    def __call__(self, args):
        super(LdapConnectionsCreateCommand, self).__call__(args)
        rbu = self.ls.ldap_connections.get_rbu()
        rbu.load_from_args(args)
        return self._run(
            self.ls.ldap_connections.create,
            "The following ldap connection '%(identifier)s' was successfully \
created",
            args.identifier,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class LdapConnectionsUpdateCommand(DefaultCommand):
    """Update ldap connection."""

    def __call__(self, args):
        super(LdapConnectionsUpdateCommand, self).__call__(args)
        resource = None
        for model in self.ls.ldap_connections.list():
            if model.get('identifier') == args.identifier:
                resource = model
                break
        if resource is None:
            raise ValueError("Ldap idenfier not found")
        rbu = self.ls.ldap_connections.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            self.ls.ldap_connections.update,
            "The following ldap connection '%(identifier)s' was successfully \
updated",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(LdapConnectionsUpdateCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class LdapConnectionsDeleteCommand(DefaultCommand):
    """Delete ldap connection."""

    def __call__(self, args):
        super(LdapConnectionsDeleteCommand, self).__call__(args)
        return self._delete(
            self.ls.ldap_connections.delete,
            "The following ldap '" + args.identifier + "' was successfully deleted",
            args.identifier,
            args.identifier)

    def complete(self, args, prefix):
        super(LdapConnectionsDeleteCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc):
    """Add all ldap connections sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser_tmp2 = subparsers2.add_parser(
        'list', help="list ldap connections.")
    parser_tmp2.add_argument('identifiers', nargs="*",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting")
    parser_tmp2.add_argument('-t', '--vertical', action="store_true",
                             help="use vertical output mode")
    parser_tmp2.add_argument('--csv', action="store_true", help="Csv output")
    parser_tmp2.add_argument('--raw', action="store_true",
                             help="Disable all formatters")
    parser_tmp2.set_defaults(__func__=LdapConnectionsListCommand())

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete ldap connections.")
    parser_tmp2.add_argument('--identifier',
                             action="store",
                             help="",
                             required=True).completer = Completer()
    parser_tmp2.set_defaults(__func__=LdapConnectionsDeleteCommand())

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create ldap connections.")
    parser_tmp2.add_argument('identifier', action="store", help="")
    parser_tmp2.add_argument('--provider-url', action="store", help="",
                             required=True)
    parser_tmp2.add_argument('--principal', action="store", help="")
    parser_tmp2.add_argument('--credential', action="store", help="")
    parser_tmp2.set_defaults(__func__=LdapConnectionsCreateCommand())

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update ldap connections.")
    parser_tmp2.add_argument(
        'identifier', action="store", help="").completer = Completer()
    parser_tmp2.add_argument('--provider-url', action="store", help="")
    parser_tmp2.add_argument('--principal', action="store", help="")
    parser_tmp2.add_argument('--credential', action="store", help="")
    parser_tmp2.set_defaults(__func__=LdapConnectionsUpdateCommand())
