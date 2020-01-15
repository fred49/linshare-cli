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



import json

from linshareapi.cache import Time
from argtoolbox import DefaultCompleter as Completer
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.actions import CreateAction
from linsharecli.common.tables import DeleteAction
from linsharecli.common.tables import TableBuilder
from linsharecli.common.cell import ComplexCell
from linsharecli.common.cell import ComplexCellBuilder


class DomainsCommand(DefaultCommand):
    """For  api >= 1.9"""
    # pylint: disable=too-many-instance-attributes
    IDENTIFIER = "label"
    DEFAULT_SORT = "label"
    RESOURCE_IDENTIFIER = "identifier"

    DEFAULT_TOTAL = "Domain found : %(count)s"
    MSG_RS_NOT_FOUND = "No domain could be found."
    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The domain '%(label)s' (%(identifier)s) was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The domain '%(label)s'  '%(identifier)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s domain (s) can not be deleted."
    MSG_RS_UPDATED = "The domain '%(label)s' (%(identifier)s) was successfully updated."
    MSG_RS_CREATED = (
        "The domain '%(label)s' (%(identifier)s) "
        "was successfully created. (%(_time)s s)"
    )

    # pylint: disable=no-self-use
    def init_old_language_key(self):
        """For  api >= 1.6 and api <= 1.8"""
        DomainsCommand.IDENTIFIER = "identifier"
        DomainsCommand.DEFAULT_SORT = "identifier"
        DomainsCommand.RESOURCE_IDENTIFIER = "identifier"

        DomainsCommand.DEFAULT_TOTAL = "Domain found : %(count)s"
        DomainsCommand.MSG_RS_NOT_FOUND = "No domain could be found."
        DomainsCommand.MSG_RS_DELETED = "The domain '%(identifier)s' was deleted. (%(time)s s)"
        DomainsCommand.MSG_RS_DELETED = (
            "%(position)s/%(count)s: "
            "The domain '%(identifier)s' was deleted. (%(time)s s)"
        )
        DomainsCommand.MSG_RS_CAN_NOT_BE_DELETED = "The domain '%(identifier)s' can not be deleted."
        DomainsCommand.MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s domain (s) can not be deleted."
        DomainsCommand.MSG_RS_UPDATED = "The domain '%(identifier)s' was successfully updated."
        DomainsCommand.MSG_RS_CREATED = "The domain '%(identifier)s' was successfully created."

    def complete(self, args, prefix):
        super(DomainsCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        json_obj = self.ls.domains.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    def complete_welcome(self, args, prefix):
        """TODO"""
        super(DomainsCommand, self).__call__(args)
        json_obj = self.ls.welcome_messages.list(args.identifier)
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))


class ProviderCell(ComplexCell):
    """TODO"""

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        output = []
        for param in self.value:
            display = (
                "{baseDn} (ldap:{ldapConnectionUuid:.8}, "
                "pattern:{userLdapPatternUuid:.8})"
            )
            output.append(display.format(**param))
        return ",".join(output)


class DDeleteAction(DeleteAction):
    """TODO"""

    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The domain '%(label)s' (%(identifier)s) was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The domain '%(identifier)s' can not be deleted."

    def __init__(self):
        super(DDeleteAction, self).__init__(
            mode=0,
            identifier="label",
            resource_identifier="identifier",
        )


class DomainsListCommand(DomainsCommand):
    """ List all domains."""

    @Time('linsharecli.domains', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainsListCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        endpoint = self.ls.domains
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.add_action('delete', DDeleteAction())
        tbu.load_args(args)
        tbu.add_custom_cell("currentWelcomeMessage", ComplexCellBuilder('{name} ({uuid:.8})'))
        tbu.add_custom_cell("providers", ProviderCell)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        return tbu.build().load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(DomainsListCommand, self).__call__(args)
        cli = self.ls.domains
        return cli.get_rbu().get_keys(True)


class DomainsCreateCommand(DomainsCommand):
    """ List all domains."""
    # pylint: disable=unused-argument

    def __call__(self, args):
        super(DomainsCreateCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        if not args.description:
            args.description = args.identifier

        act = CreateAction(self, self.ls.domains)
        if act.load(args).execute():
            if not args.domain_policy_auto:
                return True
            else:
                domain_uuid = act.result.get('identifier')
                policy = {
                    "accessPolicy": {
                        "rules": [
                            {
                                "domain": {
                                    "identifier": domain_uuid,
                                },
                                "type": "ALLOW"
                            },
                            {
                                "type": "DENY_ALL"
                            }
                        ]
                    },
                    "label": args.identifier,
                }
                self.log.debug(json.dumps(policy, sort_keys=True, indent=2))
                policy = self.ls.domain_policies.create(policy)
                self.log.debug(json.dumps(policy, sort_keys=True, indent=2))
                domain = self.ls.domains.get(domain_uuid)
                domain['policy'] = policy
                self.ls.domains.update(domain)
            return True
        else:
            return False

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

    def complete_mail_language(self, args, prefix):
        """ Complete with available external mail language."""
        super(DomainsCreateCommand, self).__call__(args)
        return self.ls.domains.options_mail_language()


class DomainsUpdateCommand(DomainsCommand):
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
        resource = rbu.to_resource()
        if hasattr(args, 'current_welcome_message'):
            if args.current_welcome_message:
                resource['currentWelcomeMessage'] = {
                    'uuid': args.current_welcome_message
                }
        return self._run(
            self.ls.domains.update,
            "The following domain '%(identifier)s' was successfully updated",
            args.identifier,
            resource)

    def complete(self, args, prefix):
        super(DomainsUpdateCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_role(self, args, prefix):
        """ Complete with available role."""
        # pylint: disable=unused-argument
        super(DomainsUpdateCommand, self).__call__(args)
        return self.ls.domains.options_role()

    def complete_language(self, args, prefix):
        """ Complete with available language."""
        # pylint: disable=unused-argument
        super(DomainsUpdateCommand, self).__call__(args)
        return self.ls.domains.options_language()


class DomainsDeleteCommand(DomainsCommand):
    """ List all domains."""

    def __call__(self, args):
        super(DomainsDeleteCommand, self).__call__(args)
        cli = self.ls.domains
        if self.api_version == 0:
            self.init_old_language_key()
            return self._delete(
                args,
                cli,
                args.identifier)
        return self._delete_all(args, cli, args.uuids)


class DomainProvidersCreateCommand(DomainsCommand):
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
            "userLdapPatternUuid": args.dpattern,
            "ldapConnectionUuid": args.ldap
        }]
        if self.api_version < 2:
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
        """TODO"""
        super(DomainProvidersCreateCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_dpattern(self, args, prefix):
        """TODO"""
        super(DomainProvidersCreateCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


class DomainProvidersDeleteCommand(DomainsCommand):
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


class DomainProvidersUpdateCommand(DomainsCommand):
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
        ldap_uuid = "ldapConnectionUuid"
        ldap_pattern_uuid = "userLdapPatternUuid"
        if self.api_version < 2:
            ldap_uuid = "ldapConnectionId"
            ldap_pattern_uuid = "domainPatternId"
        for i in resource['providers']:
            if args.ldap is not None:
                i[ldap_uuid] = args.ldap
            if args.dpattern is not None:
                i[ldap_pattern_uuid] = args.dpattern
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
        """TODO"""
        super(DomainProvidersUpdateCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_dpattern(self, args, prefix):
        """TODO"""
        super(DomainProvidersUpdateCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


def add_parser(subparsers, name, desc, config):
    """Add all domain sub commands."""
    # pylint: disable=too-many-statements
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()
    api_version = config.server.api_version.value

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list domains")
    parser.add_argument(
        'identifiers', nargs="*",
        help="Filter domains by their identifiers")
    parser.add_argument('-n', '--label', action="store_true",
                        help="sort by domain label")
    if api_version == 0:
        add_list_parser_options(parser, delete=True, cdate=False)
    else:
        add_list_parser_options(parser, delete=True, cdate=False)
    parser.set_defaults(__func__=DomainsListCommand(config))

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
        '--domain-policy-auto', dest="domain_policy_auto", action="store_true",
        help="TODO")
    parser_tmp2.add_argument(
        '--mail-config', dest="mail_config", action="store",
        help="TODO").completer = Completer("complete_mail")
    parser_tmp2.add_argument('--cli-mode', action="store_true", help="")
    parser_tmp2.set_defaults(__func__=DomainsCreateCommand(config))

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
    if api_version >= 1:
        parser_tmp2.add_argument(
            '--mail-language', dest="external_mail_locale", action="store",
            help="").completer = Completer("complete_mail_language")
    parser_tmp2.add_argument(
        '--welcome', dest="current_welcome_message", action="store",
        help="welcome message identifier").completer = Completer(
            "complete_welcome")
    parser_tmp2.set_defaults(__func__=DomainsUpdateCommand(config))

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete domain.")
    if api_version == 0:
        parser_tmp2.add_argument(
            'identifier',
            action="store",
            help="").completer = Completer()
    else:
        add_delete_parser_options(parser_tmp2)
    parser_tmp2.set_defaults(__func__=DomainsDeleteCommand(config))

    # command : set provider
    parser_tmp2 = subparsers2.add_parser(
        'setup', help="configure user provider.")
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
    parser_tmp2.set_defaults(__func__=DomainProvidersCreateCommand(config))

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
    parser_tmp2.set_defaults(__func__=DomainProvidersUpdateCommand(config))

    # command : del provider
    parser_tmp2 = subparsers2.add_parser(
        'cleanup', help="clean user provider.")
    parser_tmp2.add_argument(
        'identifier', action="store",
        help="domain identifier").completer = Completer()
    parser_tmp2.set_defaults(__func__=DomainProvidersDeleteCommand(config))
