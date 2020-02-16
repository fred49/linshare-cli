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
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.actions import CreateAction
from linsharecli.common.actions import UpdateAction
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.tables import DeleteAction
from linsharecli.common.tables import TableBuilder
from linsharecli.common.cell import ComplexCell


class DomainPoliciesCommand(DefaultCommand):
    """ List all domain policies store into LinShare."""

    IDENTIFIER = "label"
    DEFAULT_SORT = "identifier"
    RESOURCE_IDENTIFIER = "identifier"
    DEFAULT_TOTAL = "Domain policies found : %(count)s"
    MSG_RS_NOT_FOUND = "No domain policies could be found."
    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The domain policy '%(identifier)s' was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The domain policy '%(identifier)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%s domain policy(s) can not be deleted."
    MSG_RS_DOWNLOADED = (
        "%(position)s/%(count)s: "
        "The domain policy '%(label)s' (%(identifier)s) was downloaded. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One domain policy can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%s domain policies can not be downloaded."
    MSG_RS_CREATED = (
        "The domain policy '%(label)s' (%(identifier)s) was "
        "successfully created. (%(_time)s s)"
    )
    MSG_RS_UPDATED = "The resource '%(label)s' (%(identifier)s) was successfully updated."

    def complete(self, args, prefix):
        super(DomainPoliciesCommand, self).__call__(args)
        json_obj = self.ls.domain_policies.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


class AccessPolicyCell(ComplexCell):
    """TODO"""

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        output = []
        if self.vertical:
            output.append("\n\t>---")
        for rule in self.value['rules']:
            display = " - {type}"
            if self.vertical:
                display = "\t - {type}"
            rule_dct = {}
            rule_dct['type'] = rule['type']
            rule_dct['domain'] = ""
            rule_dct['domain_uuid'] = ""
            if rule.get('domain'):
                display = " - {type:<7} : {domain} ({domain_uuid:.8})"
                if self.vertical:
                    display = "\t - {type:<7} : {domain} ({domain_uuid})"
                rule_dct['domain'] = rule['domain']['label']
                rule_dct['domain_uuid'] = rule['domain']['identifier']
            output.append(display.format(**rule_dct))
        if self.vertical:
            output.append("\t ---<")
        else:
            output.append("      -----------")
        return "\n".join(output)


class DPDeleteAction(DeleteAction):
    """TODO"""

    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The domain policy '%(label)s' (%(identifier)s) was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The domain policy '%(identifier)s' can not be deleted."

    def __init__(self):
        super(DPDeleteAction, self).__init__(
            mode=0,
            identifier="label",
            resource_identifier="identifier",
        )


class DomainPoliciesListCommand(DomainPoliciesCommand):
    """ List all domain policies."""

    @Time('linshareadmcli.domainpolicies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesListCommand, self).__call__(args)
        endpoint = self.ls.domain_policies
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell("accessPolicy", AccessPolicyCell)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        tbu.add_action('delete', DPDeleteAction())
        table = tbu.build()
        table.align['accessPolicy'] = "l"
        return table.load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(DomainPoliciesListCommand, self).__call__(args)
        cli = self.ls.domain_policies
        return cli.get_rbu().get_keys(True)


class DomainPoliciesCreateCommand(DomainPoliciesCommand):
    """Create domain policy."""

    @Time('linshareadmcli.domain_policies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesCreateCommand, self).__call__(args)
        act = CreateAction(self, self.ls.domain_policies)
        return act.load(args).execute()


class DomainPoliciesUpdateCommand(DomainPoliciesCommand):
    """Update domain policy."""

    @Time('linshareadmcli.domain_policies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesUpdateCommand, self).__call__(args)
        self.check_required_options(
            args,
            ['description', 'label'],
            ["--description", "--label"])
        endpoint = self.ls.domain_policies
        resource = endpoint.get(args.identifier)
        if resource is None:
            raise ValueError("Domain policy idenfier not found")
        act = UpdateAction(self, endpoint)
        rbu = endpoint.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return act.load(args).execute(rbu.to_resource())


class DomainPoliciesDeleteCommand(DomainPoliciesCommand):
    """Delete domain policy."""

    @Time('linshareadmcli.domain_policies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesDeleteCommand, self).__call__(args)
        act = DPDeleteAction()
        act.init(args, self.ls, self.ls.domain_policies)
        return act.delete(args.identifiers)


def add_parser(subparsers, name, desc, config):
    """Add all domain policies sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list domain policies")
    parser.add_argument(
        'identifiers', nargs="*",
        help="Filter domain policies by their identifiers")
    add_list_parser_options(parser, delete=True, cdate=False)
    parser.set_defaults(__func__=DomainPoliciesListCommand(config))

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete domain policies.")
    parser_tmp2.add_argument('identifiers',
                             nargs="*",
                             action="store",
                             help="").completer = Completer()
    parser_tmp2.set_defaults(__func__=DomainPoliciesDeleteCommand(config))

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create domain policies.")
    parser_tmp2.add_argument('label', action="store", help="")
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.add_argument('--cli-mode', action="store_true", help="")
    parser_tmp2.set_defaults(__func__=DomainPoliciesCreateCommand(config))

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update domain policies.")
    parser_tmp2.add_argument(
        'identifier', action="store", help="").completer = Completer()
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.add_argument('--label', action="store", help="")
    parser_tmp2.add_argument('--cli-mode', action="store_true", help="")
    parser_tmp2.set_defaults(__func__=DomainPoliciesUpdateCommand(config))
