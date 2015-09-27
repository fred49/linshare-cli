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

from linshareapi.cache import Time
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import HTable
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from argtoolbox import DefaultCompleter as Completer
import argparse


# -----------------------------------------------------------------------------
class FunctionalityListCommand(DefaultCommand):
    """ List all functionalities."""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"

    @Time('linsharecli.domains', label='Global time : %(time)s')
    def __call__(self, args):
        super(FunctionalityListCommand, self).__call__(args)
        cli = self.ls.funcs
        table = self.get_table(args, cli, self.IDENTIFIER)
        json_obj = cli.list()
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.identifiers, True)]
        return self._list(args, cli, table, json_obj, filters=filters)

    def complete(self, args, prefix):
        super(FunctionalityListCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        super(FunctionalityListCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

# -----------------------------------------------------------------------------
class FunctionalityDisplayCommand(DefaultCommand):
    """ List all functionalities."""

    def __call__(self, args):
        super(FunctionalityDisplayCommand, self).__call__(args)
        table = HTable()
        table.field_names = ["Name", "Values"]
        # styles
        table.align["Name"] = "l"
        table.align["Values"] = "l"
        table.padding_width = 1
        json_obj = self.ls.funcs.get(args.identifier, args.domain)
        if self.debug:
            self.pretty_json(json_obj)
        if not json_obj.get('displayable'):
            print "You can not modify this functionality in this domain"
            return True
        table.add_row(['Identifier', json_obj.get('identifier')])
        table.add_row(['Domain', json_obj.get('domain')])
        apo = json_obj.get('activationPolicy')
        if not apo.get('system') and apo.get('parentAllowUpdate'):
            table.add_row(['Activation Policy',
                           self.format_policy(apo)])
        cpo = json_obj.get('configurationPolicy')
        if not cpo.get('system') and cpo.get('parentAllowUpdate'):
            table.add_row(['Configuration Policy',
                           self.format_policy(cpo)])
        dpo = json_obj.get('delegationPolicy')
        if dpo is not None:
            if not dpo.get('system') and dpo.get('parentAllowUpdate'):
                table.add_row(['Delegation Policy',
                               self.format_policy(dpo)])
        param = self.format_parameters(json_obj)
        if param:
            cpt = 0
            for param in param:
                cpt += 1
                if cpt > 1:
                    name = u'Parameters' + str(cpt)
                else:
                    name = u'Parameters'
                if json_obj.get('parentAllowParametersUpdate'):
                    table.add_row([name, param])
        out = table.get_string()
        print unicode(out)
        return True

    def format_policy(self, row):
        if row is None:
            return row
        d_format = "Status : {status!s:13s} | Policy : {policy:10s}"
        return unicode(d_format).format(**row)

    def format_parameters(self, json_obj):
        ret = []
        for param in json_obj.get('parameters'):
            row = {}
            f_type = param.get('type')
            row['type'] = f_type
            if  f_type == "INTEGER":
                row['value'] = param.get('integer')
            elif  f_type == "STRING":
                row['value'] = param.get('string')
            if  f_type == "UNIT_SIZE":
                row['value'] = str(param.get('integer')) + " " + param.get('string')
            elif  f_type == "UNIT_TIME":
                row['value'] = str(param.get('integer')) + " " + param.get('string')
            elif  f_type == "BOOLEAN":
                row['value'] = param.get('bool')
            if row:
                d_format = "Type   : {type!s:13s} | Value  : {value!s}"
                ret.append(unicode(d_format).format(**row))
        return ret

    def complete(self, args, prefix):
        super(FunctionalityDisplayCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        super(FunctionalityDisplayCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class FunctionalityUpdateCommand(DefaultCommand):
    """ List all functionalities."""

    def __call__(self, args):
        super(FunctionalityUpdateCommand, self).__call__(args)
        resource = None
        for model in self.ls.funcs.list():
            if model.get('identifier') == args.identifier:
                resource = model
                break
        if resource is None:
            raise ValueError("Functionality not found")
        if self.debug:
            self.pretty_json(resource)

        if args.domain:
            resource['domain'] = args.domain

        policy = None
        if args.activation_policy:
            policy = resource.get('activationPolicy')
        elif args.configuration_policy:
            policy = resource.get('configurationPolicy')
        elif args.delegation_policy:
            policy = resource.get('delegationPolicy')
        if policy:
            if args.policy is not None:
                policy['policy'] = args.policy
            if args.status is not None:
                policy['status'] = args.status

        param = self.get_param(args, resource)
        if param:
            f_type = param.get('type')
            if args.value is not None:
                if  f_type == "INTEGER":
                    param['integer'] = args.value
                elif  f_type == "STRING":
                    param['string'] = args.value
                elif  f_type == "UNIT_SIZE":
                    param['integer'] = args.value
                elif  f_type == "UNIT_TIME":
                    param['integer'] = args.value
                elif  f_type == "BOOLEAN":
                    param['bool'] = args.status
            if args.unit is not None:
                if  f_type == "UNIT_SIZE":
                    param['string'] = args.unit
                elif  f_type == "UNIT_TIME":
                    param['string'] = args.unit

        #self.pretty_json(resource)
        #return True
        return self._run(
            self.ls.funcs.update,
            "The following functinality '%(identifier)s' was successfully updated",
            args.identifier,
            resource)
        #json_obj = self.ls.funcs.get(args.identifier, args.domain)
        #keys = self.ls.funcs.get_rbu().get_keys()


    def get_param(self, args, resource):
        args.param = 1
        pmax = len(resource.get('parameters'))
        if args.param < 1 or args.param > pmax:
            raise ValueError("invalid value for param.")
        return resource['parameters'][args.param - 1]


    def complete(self, args, prefix):
        super(FunctionalityUpdateCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        super(FunctionalityUpdateCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_unit(self, args, prefix):
        """ Complete with available units."""
        super(FunctionalityUpdateCommand, self).__call__(args)
        if args.identifier is None:
            return ["error-identier-not-set",]
        json_obj = self.ls.funcs.get(args.identifier, args.domain)
        param = self.get_param(args, json_obj)
        return param.get("select")

    def complete_policies(self, args, prefix):
        """ Complete with available policies."""
        return "MANDATORY FORBIDDEN ALLOWED".split()


# -----------------------------------------------------------------------------
class FunctionalityResetCommand(DefaultCommand):
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
        super(FunctionalityResetCommand, self).__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        super(FunctionalityResetCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    """Add all domain sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list functionalities.")
    parser.add_argument('identifiers', nargs="*")
    parser.add_argument('-d', '--domain', action="store",
                             help="").completer = Completer('complete_domain')
    add_list_parser_options(parser)
    parser.set_defaults(__func__=FunctionalityListCommand())

    # command : display
    parser_tmp2 = subparsers2.add_parser(
        'display', help="display a functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="").completer = Completer('complete_domain')
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.set_defaults(__func__=FunctionalityDisplayCommand())

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update a functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('-d', '--domain', action="store",
                             help="Completion available").completer = Completer('complete_domain')
    policy_group = parser_tmp2.add_argument_group('Choose the policy to update')
    group = policy_group.add_mutually_exclusive_group()
    group.add_argument(
        '-a',
        '--activation-policy',
        action="store_true",
        help="activation policy")

    group.add_argument(
        '-c',
        '--configuration-policy',
        action="store_true",
        help="configuration policy")

    group.add_argument(
        '-g',
        '--delegation-policy',
        action="store_true",
        help="delegation policy")
    parser_tmp2.add_argument(
        '-p',
        '--policy',
        action="store",
        help="MANDATORY, FORBIDDEN, ALLOWED"
        ).completer = Completer('complete_policies')
    status_group = parser_tmp2.add_argument_group('Status')
    group = status_group.add_mutually_exclusive_group()
    group.add_argument(
        '--disable',
        default=None,
        action="store_false",
        dest="status")
    group.add_argument(
        '--enable',
        default=None,
        action="store_true",
        dest="status")

    parser_tmp2.add_argument(
        '-v',
        '--value',
        action="store")
    parser_tmp2.add_argument(
        '--param',
        action="store",
        default=1,
        help=argparse.SUPPRESS)
    parser_tmp2.add_argument(
        '-u',
        '--unit',
        action="store").completer = Completer('complete_unit')

    parser_tmp2.set_defaults(__func__=FunctionalityUpdateCommand())

    # command : reset
    parser_tmp2 = subparsers2.add_parser(
        'reset', help="reset a functionality.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('domain', action="store",
                             help="").completer = Completer('complete_domain')
    parser_tmp2.set_defaults(__func__=FunctionalityResetCommand())
