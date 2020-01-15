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


class ParameterCell(ComplexCell):
    """TODO"""

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        res = []
        # every func has only one parameter except SHARE_EXPIRATION.
        # before 1.9, there is two parameters,
        # since 1.9 there is two functionality
        for parameter in self.value:
            dformat = "Unknown parameter type : {type}"
            p_type = parameter['type']
            if p_type in ["STRING", "INTEGER"]:
                dformat = "{" + p_type.lower() + "}"
            elif p_type == "BOOLEAN":
                dformat = "{bool}"
            elif p_type in ["UNIT_SIZE", "UNIT_TIME"]:
                dformat = "{integer} {string}"
            elif p_type == "ENUM_LANG":
                dformat = "{string}"
            res.append(dformat.format(**parameter))
        return " | ".join(res)


class FunctionalityCommand(DefaultCommand):
    """TODO"""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"
    RESOURCE_IDENTIFIER = "identifier"

    DEFAULT_TOTAL = "Functionality found : %(count)s"
    MSG_RS_NOT_FOUND = "No Functionality could be found."
    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The Functionality '%(identifier)s' was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The Functionality '%(identifier)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s Functionality(s) can not be reset."

    MSG_RS_UPDATED = (
        "%(position)s/%(count)s: "
        "The Functionality '%(identifier)s' was updated. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_UPDATED = "The Functionality '%(identifier)s' can not be updated."
    MSG_RS_CAN_NOT_BE_UPDATED_M = "%(count)s Functionality(s) can not be updated."

    ACTIONS = {
        'status' : '_update_all',
        'count_only' : '_count_only',
    }


    def complete(self, args, prefix):
        super(FunctionalityCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super(FunctionalityCommand, self).__call__(args)
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
        policy = resource.get('activationPolicy')
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


class FunctionalityListCommand(FunctionalityCommand):
    """ List all functionalities."""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"

    @Time('linsharecli.funcs', label='Global time : %(time)s')
    def __call__(self, args):
        super(FunctionalityListCommand, self).__call__(args)
        endpoint = self.ls.funcs
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell("parameters", ParameterCell)
        tbu.add_custom_cell("activationPolicy", PolicyCell)
        tbu.add_custom_cell("configurationPolicy", PolicyCell)
        tbu.add_custom_cell("delegationPolicy", PolicyCell)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
            PartialOr("type", args.funct_type, True)
        )
        json_obj = endpoint.list(args.domain, args.sub_funcs)
        table = tbu.build()
        table.align['parameters'] = "l"
        return table.load_v2(json_obj).render()

    def complete(self, args, prefix):
        """TODO"""
        super(FunctionalityListCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super(FunctionalityListCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(FunctionalityListCommand, self).__call__(args)
        cli = self.ls.funcs
        return cli.get_rbu().get_keys(True)


class FunctionalityUpdateCommand(FunctionalityCommand):
    """ List all functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateCommand, self).__call__(args)
        cli = self.ls.funcs
        return self._update_func_policies(args, cli, args.identifier)


class FunctionalityUpdateStringCommand(FunctionalityCommand):
    """ Update STRING functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateStringCommand, self).__call__(args)
        cli = self.ls.funcs
        resource = cli.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(resource)
        if resource.get('type') != 'STRING':
            raise ArgumentError(None, "Invalid functionality type")
        param = resource['parameters'][0]
        param['string'] = args.string
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super(FunctionalityUpdateStringCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier')
                .startswith(prefix) and v.get('type') == 'STRING')


class FunctionalityUpdateTimeCommand(FunctionalityCommand):
    """ Update TIME functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateTimeCommand, self).__call__(args)
        cli = self.ls.funcs
        resource = cli.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(resource)
        if resource.get('type') not in ('UNIT', 'UNIT_BOOLEAN_TIME'):
            raise ArgumentError(None, "Invalid functionality type")
        parameters = resource.get('parameters')
        param_type1 = parameters[0].get('type')
        param_type2 = None
        if len(parameters) == 2:
            param_type2 = parameters[1].get('type')
        param = parameters[0]
        if param_type1 != 'UNIT_TIME':
            if param_type2 != 'UNIT_TIME':
                raise ArgumentError(None, "Invalid functionality type")
            else:
                param = parameters[1]
        param['integer'] = args.value
        if args.unit:
            param['string'] = args.unit
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super(FunctionalityUpdateTimeCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        res = []
        for val in json_obj:
            if val.get('identifier').startswith(prefix):
                if val.get('type') in ('UNIT', 'UNIT_BOOLEAN_TIME'):
                    for param in val.get('parameters'):
                        if param.get('type') == 'UNIT_TIME':
                            res.append(val.get('identifier'))
        return res


class FunctionalityUpdateLangCommand(FunctionalityCommand):
    """ Update TIME functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateLangCommand, self).__call__(args)
        cli = self.ls.funcs
        resource = cli.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(resource)
        if resource.get('type') != 'ENUM_LANG':
            raise ArgumentError(None, "Invalid functionality type")
        parameters = resource.get('parameters')
        param = parameters[0]
        param['string'] = args.lang
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super(FunctionalityUpdateLangCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (val.get('identifier')
                for val in json_obj if val.get('identifier')
                .startswith(prefix) and val.get('type') == 'ENUM_LANG')


class FunctionalityUpdateSizeCommand(FunctionalityCommand):
    """ Update TIME functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateSizeCommand, self).__call__(args)
        cli = self.ls.funcs
        resource = cli.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(resource)
        if resource.get('type') != 'UNIT':
            raise ArgumentError(None, "Invalid functionality type")
        if resource.get('parameters')[0].get('type') != 'UNIT_SIZE':
            raise ArgumentError(None, "Invalid functionality type")
        param = resource['parameters'][0]
        param['integer'] = args.value
        if args.unit:
            param['string'] = args.unit
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super(FunctionalityUpdateSizeCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        res = []
        for val in json_obj:
            if val.get('identifier').startswith(prefix):
                if val.get('type') == 'UNIT':
                    if val.get('parameters')[0].get('type') == 'UNIT_SIZE':
                        res.append(val.get('identifier'))
        return res


class FunctionalityUpdateIntegerCommand(FunctionalityCommand):
    """ Update INTEGER functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateIntegerCommand, self).__call__(args)
        cli = self.ls.funcs
        resource = cli.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(resource)
        if resource.get('type') != 'INTEGER':
            raise ArgumentError(None, "Invalid functionality type")
        param = resource['parameters'][0]
        param['integer'] = args.integer
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super(FunctionalityUpdateIntegerCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (val.get('identifier')
                for val in json_obj if val.get('identifier')
                .startswith(prefix) and val.get('type') == 'INTEGER')


class FunctionalityUpdateBooleanCommand(FunctionalityCommand):
    """ Update BOOLEAN functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateBooleanCommand, self).__call__(args)
        cli = self.ls.funcs
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
        super(FunctionalityUpdateBooleanCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        res = []
        for val in json_obj:
            if val.get('identifier').startswith(prefix):
                if val.get('type') in ('BOOLEAN', 'UNIT_BOOLEAN_TIME'):
                    for param in val.get('parameters'):
                        if param.get('type') == 'BOOLEAN':
                            res.append(val.get('identifier'))
        return res


class FunctionalityResetCommand(FunctionalityCommand):
    """ Reset a functionality."""

    def __call__(self, args):
        super(FunctionalityResetCommand, self).__call__(args)
        json_obj = self.ls.funcs.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(json_obj)
        name = json_obj.get('identifier')
        name += " (domain : " + json_obj.get('domain') + ")"
        return self._delete(
            self.ls.funcs.reset,
            "The funtionality " + name + " was successfully reseted.",
            name,
            json_obj)

    def complete(self, args, prefix):
        """TODO"""
        super(FunctionalityResetCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (val.get('identifier')
                for val in json_obj if val.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super(FunctionalityResetCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (val.get('identifier')
                for val in json_obj if val.get('identifier').startswith(prefix))


def add_update_parser(parser, required=True):
    """TODO"""
    policy_group = parser.add_argument_group(
        'Choose the policy to update, default is activation policy ')
    group = policy_group.add_mutually_exclusive_group()
    group.add_argument(
        '--ap',
        '--activation-policy',
        action="store_const",
        const="activationPolicy",
        dest="policy_type",
        help="activation policy")
    group.add_argument(
        '--cp',
        '--configuration-policy',
        action="store_const",
        const="configurationPolicy",
        dest="policy_type",
        help="configuration policy")
    group.add_argument(
        '--dp',
        '--delegation-policy',
        action="store_const",
        const="delegationPolicy",
        dest="policy_type",
        help="delegation policy")

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
    filter_group = groups[0]
    filter_group.add_argument(
        '--type', action="append",
        dest="funct_type",
        help="Filter on functionality type")
    filter_group.add_argument(
        '--sub-funcs', action="store_true",
        help="Sub functionalities will not be displayed, since core 1.7")
    sort_group = groups[1]
    sort_group.add_argument(
        '--sort-type', action="store_true",
        help="Sort functionalities by type")
    add_update_parser(parser, required=False)
    parser.set_defaults(__func__=FunctionalityListCommand(config))

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update a functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    parser_tmp2.add_argument('--dry-run', action="store_true")
    add_update_parser(parser_tmp2)
    parser_tmp2.set_defaults(__func__=FunctionalityUpdateCommand(config))

    # command : update-str
    parser_tmp2 = subparsers2.add_parser(
        'update-str', help="update STRING functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    parser_tmp2.add_argument(
        'string',
        help="string value",
        action="store")
    parser_tmp2.add_argument('--dry-run', action="store_true")
    parser_tmp2.set_defaults(__func__=FunctionalityUpdateStringCommand(config))

    # command : update-int
    parser_tmp2 = subparsers2.add_parser(
        'update-int', help="update INTEGER functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    parser_tmp2.add_argument(
        'integer',
        type=int,
        help="integer value",
        action="store")
    parser_tmp2.add_argument('--dry-run', action="store_true")
    parser_tmp2.set_defaults(__func__=FunctionalityUpdateIntegerCommand(config))

    # command : update-bool
    parser_tmp2 = subparsers2.add_parser(
        'update-bool', help="update BOOLEAN functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    status_group = parser_tmp2.add_argument_group('Boolean value')
    group = status_group.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--disable',
        action="store_false",
        dest="boolean")
    group.add_argument(
        '--enable',
        action="store_true",
        dest="boolean")
    parser_tmp2.add_argument('--dry-run', action="store_true")
    parser_tmp2.set_defaults(__func__=FunctionalityUpdateBooleanCommand(config))

    # command : update-lang
    parser_tmp2 = subparsers2.add_parser(
        'update-lang', help="update language functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    parser_tmp2.add_argument(
        '-l',
        '--lang',
        action="store",
        choices=('EN', 'FR'))
    parser_tmp2.add_argument('--dry-run', action="store_true")
    parser_tmp2.set_defaults(__func__=FunctionalityUpdateLangCommand(config))

    # command : update-time
    parser_tmp2 = subparsers2.add_parser(
        'update-time', help="update UNIT functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    parser_tmp2.add_argument(
        'value',
        type=int,
        help="time value",
        action="store")
    parser_tmp2.add_argument(
        '-u',
        '--unit',
        action="store",
        choices=('DAY', 'WEEK', 'MONTH'))
    parser_tmp2.add_argument('--dry-run', action="store_true")
    parser_tmp2.set_defaults(__func__=FunctionalityUpdateTimeCommand(config))

    # command : update-size
    parser_tmp2 = subparsers2.add_parser(
        'update-size', help="update UNIT functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    parser_tmp2.add_argument(
        'value',
        type=int,
        help="size value",
        action="store")
    parser_tmp2.add_argument(
        '-u',
        '--unit',
        action="store",
        choices=('KILO', 'MEGA', 'GIGA'))
    parser_tmp2.add_argument('--dry-run', action="store_true")
    parser_tmp2.set_defaults(__func__=FunctionalityUpdateSizeCommand(config))

    # command : reset
    parser_tmp2 = subparsers2.add_parser(
        'reset', help="reset a functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('domain', action="store",
                             help="").completer = Completer('complete_domain')
    parser_tmp2.set_defaults(__func__=FunctionalityResetCommand(config))
