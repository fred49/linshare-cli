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



from argparse import ArgumentError
from argtoolbox import DefaultCompleter as Completer
from linshareapi.cache import Time
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.tables import TableBuilder
from linsharecli.common.cell import ComplexCell


class PolicyCell(ComplexCell):
    """TODO"""

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        dformat = "{status!s:<5} | {policy:.1}"
        if self.vertical:
            dformat = "Enable={status!s:<5} | {policy:<10}"
        if not self.value.get('parentAllowUpdate'):
            if self.vertical:
                dformat += " | READONLY"
        return dformat.format(**self.value)


class MailActivationsCommand(DefaultCommand):
    """TODO"""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"
    RESOURCE_IDENTIFIER = "identifier"

    DEFAULT_TOTAL = "MailActivation found : %(count)s"
    MSG_RS_NOT_FOUND = "No MailActivation could be found."
    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The MailActivation '%(identifier)s' was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The MailActivation '%(identifier)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s MailActivation(s) can not be reset."

    MSG_RS_UPDATED = (
        "%(position)s/%(count)s: "
        "The MailActivation '%(identifier)s' was updated. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_UPDATED = "The MailActivation '%(identifier)s' can not be updated."
    MSG_RS_CAN_NOT_BE_UPDATED_M = "%(count)s MailActivation(s) can not be updated."

    ACTIONS = {
        'status' : '_update_all',
        'count_only' : '_count_only',
    }


    def complete(self, args, prefix):
        super().__call__(args)
        json_obj = self.ls.mail_activations.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def _update_all(self, args, cli, uuids):
        """TODO"""
        return self._apply_to_all(
            args, cli, uuids,
            self.MSG_RS_CAN_NOT_BE_UPDATED_M,
            self._update_func_policies)

    def _update_func_policies(self, args, cli, uuid, position=None, count=None):
        """TODO"""
        # pylint: disable=too-many-arguments
        # pylint: disable=unused-argument
        resource = cli.get(uuid, args.domain)
        policy = resource.get('configurationPolicy')
        if args.policy_type is not None:
            policy = resource.get(args.policy_type)
        if policy is None:
            raise ArgumentError(None, "No delegation policy for this functionality")
        policy['policy'] = args.status
        if args.status == "ENABLE" or args.status == "DISABLE":
            if args.status == "ENABLE":
                policy['status'] = True
            else:
                policy['status'] = False
            policy['policy'] = "ALLOWED"
        return self._update(args, cli, resource)


class MailActivationsListCommand(MailActivationsCommand):
    """ List all functionalities."""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"

    @Time('linsharecli.mail_activations', label='Global time : %(time)s')
    def __call__(self, args):
        super().__call__(args)
        endpoint = self.ls.mail_activations
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell("activationPolicy", PolicyCell)
        tbu.add_custom_cell("delegationPolicy", PolicyCell)
        tbu.add_custom_cell("configurationPolicy", PolicyCell)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        json_obj = endpoint.list(args.domain)
        table = tbu.build()
        return table.load_v2(json_obj).render()

    def complete(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.mail_activations.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super().__call__(args)
        cli = self.ls.mail_activations
        return cli.get_rbu().get_keys(True)


class MailActivationsUpdateCommand(MailActivationsCommand):
    """ List all functionalities."""

    def __call__(self, args):
        super().__call__(args)
        cli = self.ls.mail_activations
        return self._update_func_policies(args, cli, args.identifier)


class MailActivationsUpdateBooleanCommand(MailActivationsCommand):
    """ Update BOOLEAN functionalities."""

    def __call__(self, args):
        super().__call__(args)
        cli = self.ls.mail_activations
        resource = cli.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(resource)
        if resource.get('type') not in ('BOOLEAN', 'UNIT_BOOLEAN_TIME'):
            raise ArgumentError(None, "Invalid functionality type")
        parameters = resource.get('parameters')
        param_type1 = parameters[0].get('type')
        param_type2 = None
        if len(parameters) == 2:
            param_type2 = parameters[1].get('type')
        param = parameters[0]
        if param_type1 != 'BOOLEAN':
            if param_type2 != 'BOOLEAN':
                raise ArgumentError(None, "Invalid functionality type")
            else:
                param = parameters[1]
        param['bool'] = args.boolean
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.mail_activations.list(args.domain)
        res = []
        for val in json_obj:
            if val.get('identifier').startswith(prefix):
                if val.get('type') in ('BOOLEAN', 'UNIT_BOOLEAN_TIME'):
                    for param in val.get('parameters'):
                        if param.get('type') == 'BOOLEAN':
                            res.append(val.get('identifier'))
        return res


class MailActivationsResetCommand(MailActivationsCommand):
    """ Reset a functionality."""

    def __call__(self, args):
        super().__call__(args)
        json_obj = self.ls.mail_activations.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(json_obj)
        name = json_obj.get('identifier')
        name += " (domain : " + json_obj.get('domain') + ")"
        return self._delete(
            self.ls.mail_activations.reset,
            "The funtionality " + name + " was successfully reseted.",
            name,
            json_obj)

    def complete(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.mail_activations.list(args.domain)
        return (val.get('identifier')
                for val in json_obj if val.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.domains.list()
        return (val.get('identifier')
                for val in json_obj if val.get('identifier').startswith(prefix))


def add_update_parser(parser, required=True):
    """TODO"""
    policy_group = parser.add_argument_group(
        'Choose the policy to update, default is activation policy ')
    group = policy_group.add_mutually_exclusive_group()
    group.add_argument(
        '--cp',
        '--configuration-policy',
        action="store_const",
        const="configurationPolicy",
        dest="policy_type",
        help="configuration policy")

    status_group = parser.add_argument_group('Status')
    group = status_group.add_mutually_exclusive_group(required=required)
    group.add_argument(
        '--disable',
        default=None,
        action="store_const",
        help="Set policy to ALLOWED and status to disable",
        const="DISABLE",
        dest="status")
    group.add_argument(
        '--enable',
        default=None,
        action="store_const",
        help="Set policy to ALLOWED and status to enable",
        const="ENABLE",
        dest="status")
    group.add_argument(
        '--mandatory',
        action="store_const",
        help="Set policy to MANDATORY and status to enable",
        const="MANDATORY",
        dest="status")
    group.add_argument(
        '--forbidden',
        action="store_const",
        help="Set policy to FORBIDDEN and status to disable",
        const="FORBIDDEN",
        dest="status")

def add_parser(subparsers, name, desc, config):
    """Add all domain sub commands."""
    # pylint: disable=too-many-statements
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list functionalities.")
    parser.add_argument('identifiers', nargs="*")
    parser.add_argument(
        '-d', '--domain', action="store",
        help="").completer = Completer('complete_domain')
    groups = add_list_parser_options(parser)
    # groups : filter_group, sort_group, format_group, actions_group
    actions_group = groups[3]
    actions_group.add_argument('--dry-run', action="store_true")
    add_update_parser(parser, required=False)
    parser.set_defaults(__func__=MailActivationsListCommand(config))

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update a functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    parser_tmp2.add_argument('--dry-run', action="store_true")
    add_update_parser(parser_tmp2)
    parser_tmp2.set_defaults(__func__=MailActivationsUpdateCommand(config))

    # command : reset
    parser_tmp2 = subparsers2.add_parser(
        'reset', help="reset a functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('domain', action="store",
                             help="").completer = Completer('complete_domain')
    parser_tmp2.set_defaults(__func__=MailActivationsResetCommand(config))
