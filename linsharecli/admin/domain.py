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
class DomainsListCommand(DefaultCommand):
    """ List all domains."""
    IDENTIFIER = "identifier"

    def __call__(self, args):
        super(DomainsListCommand, self).__call__(args)
        cli = self.ls.domains
        table = self.get_table(args, cli, self.IDENTIFIER)
        if args.label:
            table.sortby = "label"
        table.show_table(
            cli.list(),
            PartialOr(self.IDENTIFIER, args.identifiers, True)
        )
        return True

    def complete(self, args, prefix):
        super(DomainsListCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
# Ignore unused variable prefix
# pylint: disable-msg=W0613
class DomainsCreateCommand(DefaultCommand):
    """ List all domains."""

    def __call__(self, args):
        super(DomainsCreateCommand, self).__call__(args)
        rbu = self.ls.domains.get_rbu()
        rbu.load_from_args(args)
        return self._run(
            self.ls.domains.create,
            "The following domain '%(identifier)s' was successfully created",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainsCreateCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_type(self, args, prefix):
        """ Complete with available domain type."""
        super(DomainsCreateCommand, self).__call__(args)
        return self.ls.domains.options_type()

    def complete_role(self, args, prefix):
        """ Complete with available role."""
        super(DomainsCreateCommand, self).__call__(args)
        return self.ls.domains.options_role()

    def complete_language(self, args, prefix):
        """ Complete with available language."""
        super(DomainsCreateCommand, self).__call__(args)
        return self.ls.domains.options_language()


# -----------------------------------------------------------------------------
class DomainsUpdateCommand(DefaultCommand):
    """ Update a domain."""

    def __call__(self, args):
        super(DomainsUpdateCommand, self).__call__(args)
        resource = None
        for model in self.ls.domains.list():
            if model.get('identifier') == args.identifier:
                resource = model
                break
        if resource is None:
            raise ValueError("Domain idenfier not found")
        rbu = self.ls.domains.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            self.ls.domains.update,
            "The following domain '%(identifier)s' was successfully updated",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainsUpdateCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_role(self, args, prefix):
        """ Complete with available role."""
        super(DomainsUpdateCommand, self).__call__(args)
        return self.ls.domains.options_role()

    def complete_language(self, args, prefix):
        """ Complete with available language."""
        super(DomainsUpdateCommand, self).__call__(args)
        return self.ls.domains.options_language()


# -----------------------------------------------------------------------------
class DomainsDeleteCommand(DefaultCommand):
    """ List all domains."""

    def __call__(self, args):
        super(DomainsDeleteCommand, self).__call__(args)
        return self._delete(
            self.ls.domains.delete,
            "The following domain '" + args.identifier + "' was \
successfully deleted",
            args.identifier,
            args.identifier)

    def complete(self, args, prefix):
        super(DomainsDeleteCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class DomainProvidersCreateCommand(DefaultCommand):
    """ Update a domain."""

    def __call__(self, args):
        super(DomainProvidersCreateCommand, self).__call__(args)
        resource = None
        for model in self.ls.domains.list():
            if model.get('identifier') == args.identifier:
                resource = model
                break
        if resource is None:
            raise ValueError("Domain idenfier not found")
        rbu = self.ls.domains.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        providers = [{
            "baseDn": args.basedn,
            "domainPatternId": args.dpattern,
            "ldapConnectionId": args.ldap
        }]
        rbu.set_value("providers", providers)
        return self._run(
            self.ls.domains.update,
            "The following user provider for domain '%(identifier)s' was \
successfully created",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainProvidersCreateCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_ldap(self, args, prefix):
        super(DomainProvidersCreateCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_dpattern(self, args, prefix):
        super(DomainProvidersCreateCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class DomainProvidersDeleteCommand(DefaultCommand):
    """ List all domains."""

    def __call__(self, args):
        super(DomainProvidersDeleteCommand, self).__call__(args)
        resource = None
        for model in self.ls.domains.list():
            if model.get('identifier') == args.identifier:
                resource = model
                break
        if resource is None:
            raise ValueError("Domain idenfier not found")
        rbu = self.ls.domains.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        providers = []
        rbu.set_value("providers", providers)
        return self._run(
            self.ls.domains.update,
            "The following user provider '%(identifier)s' was successfully \
deleted",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainProvidersDeleteCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class DomainProvidersUpdateCommand(DefaultCommand):
    """ Update a user provider."""

    def __call__(self, args):
        super(DomainProvidersUpdateCommand, self).__call__(args)
        resource = None
        for model in self.ls.domains.list():
            if model.get('identifier') == args.identifier:
                resource = model
                break
        if resource is None:
            raise ValueError("Domain idenfier not found")
        rbu = self.ls.domains.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        resource = rbu.to_resource()
        for i in resource['providers']:
            if args.ldap is not None:
                i['ldapConnectionId'] = args.ldap
            if args.dpattern is not None:
                i['domainPatternId'] = args.dpattern
            if args.basedn is not None:
                i['baseDn'] = args.basedn
        return self._run(
            self.ls.domains.update,
            "The following user provider '%(identifier)s' was successfully \
updated",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainProvidersUpdateCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_ldap(self, args, prefix):
        super(DomainProvidersUpdateCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_dpattern(self, args, prefix):
        super(DomainProvidersUpdateCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc):
    """Add all domain sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser_tmp2 = subparsers2.add_parser(
        'list', help="list domains.")
    parser_tmp2.add_argument('identifiers', nargs="*",
                             help="").completer = Completer()
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting")
    parser_tmp2.add_argument('-n', '--label', action="store_true",
                             help="sort by domain label")
    parser_tmp2.add_argument('-t', '--vertical', action="store_true",
                             help="use vertical output mode")
    parser_tmp2.add_argument('--csv', action="store_true", help="Csv output")
    parser_tmp2.add_argument('--raw', action="store_true",
                             help="Disable all formatters")
    parser_tmp2.set_defaults(__func__=DomainsListCommand())

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create domain.")
    parser_tmp2.add_argument('--label', action="store", help="")
    parser_tmp2.add_argument('identifier', action="store", help="")
    parser_tmp2.add_argument(
        '--type', dest="domain_type", action="store", help="",
        required=True).completer = Completer("complete_type")
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.add_argument(
        '--role', dest="role", action="store",
        help="").completer = Completer("complete_role")
    parser_tmp2.add_argument(
        '--language', dest="language", action="store",
        help="").completer = Completer("complete_language")
    parser_tmp2.add_argument(
        '--parent', dest="parent_id", action="store",
        help="TODO").completer = Completer()
    parser_tmp2.add_argument(
        '--mime-policy', dest="mime_policy", action="store",
        help="TODO").completer = Completer("complete_mime")
    parser_tmp2.add_argument(
        '--domain-policy', dest="domain_policy", action="store",
        help="TODO").completer = Completer("complete_policy")
    parser_tmp2.add_argument(
        '--mail-config', dest="mail_config", action="store",
        help="TODO").completer = Completer("complete_mail")
    parser_tmp2.set_defaults(__func__=DomainsCreateCommand())

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update domain.")
    parser_tmp2.add_argument(
        'identifier', action="store", help="").completer = Completer()
    parser_tmp2.add_argument('--label', action="store", help="")
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.add_argument(
        '--role', dest="role", action="store",
        help="").completer = Completer("complete_role")
    parser_tmp2.add_argument(
        '--language', dest="language", action="store",
        help="").completer = Completer("complete_language")
    parser_tmp2.set_defaults(__func__=DomainsUpdateCommand())

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete domain.")
    parser_tmp2.add_argument(
        'identifier', action="store",
        help="").completer = Completer()
    parser_tmp2.set_defaults(__func__=DomainsDeleteCommand())

    # command : set provider
    parser_tmp2 = subparsers2.add_parser(
        'setup', help="add user provider.")
    parser_tmp2.add_argument(
        'identifier', action="store",
        help="domain identifier").completer = Completer()
    parser_tmp2.add_argument('--basedn', action="store", help="",
                             required=True)
    parser_tmp2.add_argument(
        '--ldap', dest="ldap", action="store", help="ldap identifier",
        required=True).completer = Completer("complete_ldap")
    parser_tmp2.add_argument(
        '--dpattern', dest="dpattern", action="store",
        help="domain pattern identifier",
        required=True).completer = Completer("complete_dpattern")
    parser_tmp2.set_defaults(__func__=DomainProvidersCreateCommand())

    # command : update provider
    parser_tmp2 = subparsers2.add_parser(
        'updateup', help="update user provider.")
    parser_tmp2.add_argument(
        'identifier', action="store",
        help="domain identifier").completer = Completer()
    parser_tmp2.add_argument('--basedn', action="store", help="")
    parser_tmp2.add_argument(
        '--ldap', dest="ldap", action="store",
        help="ldap identifier").completer = Completer("complete_ldap")
    parser_tmp2.add_argument(
        '--dpattern', dest="dpattern", action="store",
        help="domain pattern identifier").completer = Completer(
            "complete_dpattern")
    parser_tmp2.set_defaults(__func__=DomainProvidersUpdateCommand())

    # command : del provider
    parser_tmp2 = subparsers2.add_parser(
        'delup', help="add user provider.")
    parser_tmp2.add_argument(
        'identifier', action="store",
        help="domain identifier").completer = Completer()
    parser_tmp2.set_defaults(__func__=DomainProvidersDeleteCommand())
