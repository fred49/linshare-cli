#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""TODO"""
# pylint: disable=too-many-lines
# pylint: disable=import-error


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


import urllib.error
import logging
from argparse import ArgumentError
from argtoolbox import DefaultCompleter as Completer
from vhatable.core import Action
from vhatable.cell import ComplexCell
from vhatable.cell import ComplexCellBuilder
from vhatable.filters import PartialOr
from linshareapi.cache import Time
from linshareapi.core import LinShareException
from linsharecli.common.core import add_list_parser_options
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import DeleteAction as DeleteActionTable


class PolicyCell(ComplexCell):
    # pylint: disable=too-few-public-methods
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
            else:
                dformat += " | RO"
        return dformat.format(**self.value)


class PolicyCell5(ComplexCell):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        if self.value['hidden']:
            return self.none
        dformat = (
                "Enable:         {enable}\n"
                "Allow Override: {override}\n"
                "Read Only:      {readonly}\n"
                "   ---------------   "
        )
        if self.vertical:
            dformat = (
                    "Enable: {enable} | "
                    "Allow Override: {override} | "
                    "Read Only: {readonly}"
            )
        return dformat.format(
            enable=self.value['enable']['value'],
            override=self.value['allowOverride']['value'],
            readonly=self.value['readonly'],
        )


class ParameterCell(ComplexCell):
    """TODO"""
    # pylint: disable=too-few-public-methods

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


class ParameterCell5(ComplexCell):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __unicode__(self):
        # pylint: disable=too-many-statements
        classname = str(self.__class__.__name__.lower())
        log = logging.getLogger("linsharecli.cell." + classname)
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        if self.value['hidden']:
            return self.none

        def to_string(param):
            dformat = (
                    "*Type:          {type}\n"
                    "Hidden:         {hidden}\n"
                    "Read Only:      {readonly}\n"
                    "   ---------------   "
            )
            if self.vertical:
                dformat = (
                        "Type: {type} | "
                        "Hidden: {hidden} | "
                        "Read Only: {readonly}"
                )
            return dformat.format(
                hidden=param['hidden'],
                type=param['type'],
                readonly=param['readonly'],
            )

        def default_param_rendering(param):
            # pylint: disable=too-many-statements
            # pylint: disable=too-many-branches
            p_type = param['type']
            dformat = ["Type:           {type}"]
            if self.vertical:
                dformat = ["Type: {type}"]
            values = {
                'hidden': param['hidden'],
                'type': p_type,
                'readonly': param['readonly'],
            }
            if p_type in ('BOOLEAN', 'LANGUAGE', 'STRING', 'UNIT_SIZE_DEFAULT',
                          'INTEGER_ALL', 'INTEGER_DEFAULT'):
                if self.vertical:
                    dformat.append("Default: {default}")
                else:
                    dformat.append("Default:        {default}")
                values['default'] = param['defaut']['value']
            if p_type in ('UNIT_TIME_ALL', 'UNIT_TIME_DEFAULT',
                          'UNIT_SIZE_ALL', 'UNIT_SIZE_DEFAULT'):
                if self.vertical:
                    dformat.append("Default: {default} {d_unit}")
                else:
                    dformat.append("Default:        {default} {d_unit}")
                values['default'] = param['defaut']['value']
                values['d_unit'] = param['defaut']['unit']
            if p_type in ('INTEGER_ALL', 'INTEGER_MAX'):
                if self.vertical:
                    dformat.append("Maximum: {maximum}")
                    if param['unlimited']['supported']:
                        dformat.append("Unlimited: {unlimited}")
                else:
                    dformat.append("Maximum:        {maximum}")
                    if param['unlimited']['supported']:
                        dformat.append("Unlimited:      {unlimited}")
                if param['unlimited']['supported']:
                    values['unlimited'] = param['unlimited']['value']
                values['maximum'] = param['maximum']['value']
            if p_type in ('UNIT_TIME_ALL', 'UNIT_TIME_MAX',
                          'UNIT_SIZE_ALL', 'UNIT_SIZE_MAX'):
                if self.vertical:
                    dformat.append("Maximum: {maximum} {m_unit}")
                    if param['unlimited']['supported']:
                        dformat.append("Unlimited: {unlimited}")
                else:
                    dformat.append("Maximum:        {maximum} {m_unit}")
                    if param['unlimited']['supported']:
                        dformat.append("Unlimited:      {unlimited}")
                if param['unlimited']['supported']:
                    values['unlimited'] = param['unlimited']['value']
                values['maximum'] = param['maximum']['value']
                values['m_unit'] = param['maximum']['unit']
            if self.vertical:
                dformat.append("Hidden: {hidden}")
                dformat.append("Read Only: {readonly}")
            else:
                dformat.append("Hidden:         {hidden}")
                dformat.append("Read Only:      {readonly}")
                dformat.append("   ---------------   ")
            if self.vertical:
                dformat = " | ".join(dformat)
            else:
                dformat = "\n".join(dformat)
            return dformat.format(**values)

        maptypes = {
            'BOOLEAN': default_param_rendering,
            'INTEGER_ALL': default_param_rendering,
            'INTEGER_DEFAULT': default_param_rendering,
            'INTEGER_MAX': default_param_rendering,
            'LANGUAGE': default_param_rendering,
            'STRING': default_param_rendering,
            'UNIT_SIZE_ALL': default_param_rendering,
            'UNIT_SIZE_MAX': default_param_rendering,
            'UNIT_SIZE_DEFAULT': default_param_rendering,
            'UNIT_TIME_ALL': default_param_rendering,
            'UNIT_TIME_MAX': default_param_rendering,
            'UNIT_TIME_DEFAULT': default_param_rendering,
        }
        log.debug(self.value['type'])
        return maptypes.get(self.value['type'], to_string)(self.value)


class FunctionalityCommand(DefaultCommand):
    """TODO"""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"
    RESOURCE_IDENTIFIER = "identifier"

    DEFAULT_TOTAL = "Functionality found : %(count)s"
    MSG_RS_NOT_FOUND = "No Functionality could be found."
    MSG_RS_UPDATED = (
        "%(position)s/%(count)s: "
        "The Functionality '%(identifier)s' was updated. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_UPDATED = (
            "The Functionality '%(identifier)s' can not be updated."
    )
    MSG_RS_CAN_NOT_BE_UPDATED_M = (
            "%(count)s Functionality(s) can not be updated."
    )

    def complete(self, args, prefix):
        super().__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


class UpdateAction(Action):
    """Update funtionality, is supposed to be used by an action table."""

    IDENTIFIER = "identifier"
    RESOURCE_IDENTIFIER = "identifier"

    MSG_RS_UPDATED = (
        "%(position)s/%(count)s: "
        "The Functionality '%(identifier)s' was updated. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_UPDATED = (
        "The Functionality '%(identifier)s' can not be updated."
    )
    MSG_RS_CAN_NOT_BE_UPDATED_M = (
        "%(count)s Functionality(s) can not be updated."
    )

    def __call__(self, args, cli, endpoint, data):
        """TODO"""
        self.init(args, cli, endpoint)
        count = len(data)
        position = 0
        res = 0
        for row in data:
            position += 1
            status = self.update_row(row, position, count, args)
            res += abs(status - 1)
        if res > 0:
            meta = {'count': res}
            self.pprint(self.MSG_RS_CAN_NOT_BE_UPDATED_M, meta)
            return False
        return True

    def update_row(self, row, position, count, args):
        """TODO"""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        status = args.status
        self.log.debug("row : %s", row)
        meta = {}
        meta.update(row)
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        if status == 'DISABLE':
            row['enable'] = False
        elif status == 'ENABLE':
            row['enable'] = True
        elif status == 'AP_DISABLE':
            row['activationPolicy']['policy'] = 'ALLOWED'
            row['activationPolicy']['status'] = False
        elif status == 'AP_ENABLE':
            row['activationPolicy']['policy'] = 'ALLOWED'
            row['activationPolicy']['status'] = True
        elif status == 'AP_MANDATORY':
            row['activationPolicy']['policy'] = 'MANDATORY'
            row['activationPolicy']['status'] = True
        elif status == 'AP_FORBIDDEN':
            row['activationPolicy']['policy'] = 'FORBIDDEN'
            row['activationPolicy']['status'] = False
        elif status == 'CP_DISABLE':
            row['configurationPolicy']['policy'] = 'ALLOWED'
            row['configurationPolicy']['status'] = False
        elif status == 'CP_ENABLE':
            row['configurationPolicy']['policy'] = 'ALLOWED'
            row['configurationPolicy']['status'] = True
        elif status == 'CP_MANDATORY':
            row['configurationPolicy']['policy'] = 'MANDATORY'
            row['configurationPolicy']['status'] = True
        elif status == 'CP_FORBIDDEN':
            row['configurationPolicy']['policy'] = 'FORBIDDEN'
            row['configurationPolicy']['status'] = False
        elif status == 'DP_DISABLE':
            row['delegationPolicy']['policy'] = 'ALLOWED'
            row['delegationPolicy']['status'] = False
        elif status == 'DP_ENABLE':
            row['delegationPolicy']['policy'] = 'ALLOWED'
            row['delegationPolicy']['status'] = True
        elif status == 'DP_MANDATORY':
            row['delegationPolicy']['policy'] = 'MANDATORY'
            row['delegationPolicy']['status'] = True
        elif status == 'DP_FORBIDDEN':
            row['delegationPolicy']['policy'] = 'FORBIDDEN'
            row['delegationPolicy']['status'] = False
        else:
            raise ArgumentError(None, "Unsupported update value: "
                                + str(status) + " Did you forget to provide"
                                + " the value/flag to update ?"
                                )
        self.endpoint.update(row)
        meta['time'] = self.endpoint.core.last_req_time
        if self.cli_mode:
            print(row['identifier'])
        else:
            self.pprint(self.MSG_RS_UPDATED, meta)
        return True


class UpdateActionV5(UpdateAction):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def update_row(self, row, position, count, args):
        """TODO"""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        self.log.debug("row : %s", row)
        # self.pretty_json(row)

        def getvalue(arg_value, default):
            if arg_value is None:
                return default
            return arg_value

        row['activationPolicy']['enable']['value'] = getvalue(
                args.AP_enable,
                row['activationPolicy']['enable']['value'])
        row['activationPolicy']['allowOverride']['value'] = getvalue(
                args.AP_allow_override,
                row['activationPolicy']['allowOverride']['value'])
        row['configurationPolicy']['enable']['value'] = getvalue(
                args.CP_enable,
                row['configurationPolicy']['enable']['value'])
        row['configurationPolicy']['allowOverride']['value'] = getvalue(
                args.CP_allow_override,
                row['configurationPolicy']['allowOverride']['value'])
        if 'delegationPolicy' in row:
            row['delegationPolicy']['enable']['value'] = getvalue(
                    args.DP_enable,
                    row['delegationPolicy']['enable']['value'])
            row['delegationPolicy']['allowOverride']['value'] = getvalue(
                    args.DP_allow_override,
                    row['delegationPolicy']['allowOverride']['value'])

        f_type = row['type']
        f_identifier = row['identifier']
        param = row['parameter']
        p_type = None
        # DEFAULT does not support any parameter.
        f_type_set = ('BOOLEAN', 'ENUM_LANG', 'INTEGER', 'STRING', 'UNIT')
        if param and f_type in f_type_set:
            p_type = param['type']

        if args.parameter_unlimited is not None:
            self.log.info("args.parameter_unlimited : %s",
                          args.parameter_unlimited)
            unlimiteds = (
                'INTEGER_MAX', 'INTEGER_ALL', 'UNIT_TIME_MAX', 'UNIT_TIME_ALL',
                'UNIT_SIZE_MAX', 'UNIT_SIZE_ALL'
            )
            if p_type not in unlimiteds or not param['unlimited']['supported']:
                msg = f"Unsupported unlimited flag for {f_identifier}"
                raise ArgumentError(None, msg)
            param['unlimited']['value'] = args.parameter_unlimited

        if args.parameter_default is not None:
            value = args.parameter_default
            self.log.debug("args.parameter_default : %s", value)
            defaults = (
                'BOOLEAN', 'LANGUAGE', 'STRING',
                'INTEGER_DEFAULT', 'INTEGER_ALL',
                'UNIT_TIME_DEFAULT', 'UNIT_TIME_ALL',
                'UNIT_SIZE_DEFAULT', 'UNIT_SIZE_ALL'
            )
            if p_type not in defaults:
                msg = f"Unsupported default value for {f_identifier}"
                raise ArgumentError(None, msg)
            if p_type == 'BOOLEAN':
                defaults = ('true', 'True', 'false', 'False')
                if value not in defaults:
                    msg = f"Supported value are: {defaults}"
                    raise ArgumentError(None, msg)
                # pylint: disable=simplifiable-if-statement
                if value in ('true', 'True'):
                    value = True
                else:
                    value = False
            defaults = (
                'INTEGER_DEFAULT', 'INTEGER_ALL',
                'UNIT_TIME_DEFAULT', 'UNIT_TIME_ALL',
                'UNIT_SIZE_DEFAULT', 'UNIT_SIZE_ALL'
            )
            if p_type in defaults:
                value = int(value)
            if p_type == 'LANGUAGE':
                defaults = param['defaut']['languages']
                if value not in defaults:
                    msg = f"Supported value are: {defaults}"
                    raise ArgumentError(None, msg)
            self.log.info("args.parameter_default : %s", value)
            param['defaut']['value'] = value

        if args.parameter_maximum is not None:
            value = args.parameter_maximum
            self.log.debug("args.parameter_maximum : %s", value)
            maximums = (
                'INTEGER_MAX', 'INTEGER_ALL',
                'UNIT_TIME_MAX', 'UNIT_TIME_ALL',
                'UNIT_SIZE_MAX', 'UNIT_SIZE_ALL'
            )
            if p_type not in maximums:
                msg = f"Unsupported maximum value for {f_identifier}"
                raise ArgumentError(None, msg)
            value = int(value)
            self.log.info("args.parameter_maximum : %s", value)
            param['maximum']['value'] = value

        if args.parameter_default_unit is not None:
            value = args.parameter_default_unit
            self.log.debug("args.parameter_default_unit : %s", value)
            defaults = (
                'UNIT_TIME_DEFAULT', 'UNIT_TIME_ALL',
                'UNIT_SIZE_DEFAULT', 'UNIT_SIZE_ALL'
            )
            if p_type not in defaults:
                msg = f"Unsupported default unit value for {f_identifier}"
                raise ArgumentError(None, msg)
            defaults = param['defaut']['units']
            if value not in defaults:
                msg = f"Supported value are: {defaults}"
                raise ArgumentError(None, msg)
            self.log.info("args.parameter_default_unit : %s", value)
            param['defaut']['unit'] = value

        if args.parameter_maximum_unit is not None:
            value = args.parameter_maximum_unit
            self.log.debug("args.parameter_maximum_unit : %s", value)
            maximums = (
                'UNIT_TIME_MAX', 'UNIT_TIME_ALL',
                'UNIT_SIZE_MAX', 'UNIT_SIZE_ALL'
            )
            if p_type not in maximums:
                msg = f"Unsupported maximum unit value for {f_identifier}"
                raise ArgumentError(None, msg)
            defaults = param['maximum']['units']
            if value not in defaults:
                msg = f"Supported value are: {defaults}"
                raise ArgumentError(None, msg)
            self.log.info("args.parameter_maximum_unit : %s", value)
            param['maximum']['unit'] = value
        meta = {}
        meta.update(row)
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        self.endpoint.update(row)
        meta['time'] = self.endpoint.core.last_req_time
        if self.cli_mode:
            print(row['identifier'])
        else:
            self.pprint(self.MSG_RS_UPDATED, meta)
        return True


class DeleteAction(DeleteActionTable):
    """TODO"""

    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The functionality '%(name)s' (%(uuid)s) was reset. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = (
        "The functionality '%(uuid)s' can not be reset."
    )
    MSG_RS_CAN_NOT_BE_DELETED_M = (
        "%(count)s functionality(s) can not be reset."
    )

    def __init__(self):
        super().__init__(
            identifier="name",
            resource_identifier="identifier"
        )
        self.domain = None

    def init(self, args, cli, endpoint):
        super().init(args, cli, endpoint)
        self.domain = args.domain
        return self

    def _delete(self, uuid, position=None, count=None):
        try:
            if not position:
                position = 1
                count = 1
            meta = {}
            meta['uuid'] = uuid
            meta[self.resource_identifier] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            if self.dry_run:
                json_obj = self.endpoint.get(uuid)
            else:
                json_obj = self.endpoint.reset(uuid, self.domain)
                meta['time'] = self.cli.last_req_time
            if not json_obj:
                meta = {'uuid': uuid}
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED, meta)
                return False
            if self.cli_mode:
                print((json_obj.get(self.resource_identifier)))
            else:
                meta[self.identifier] = json_obj.get(self.identifier)
                self.pprint(self.MSG_RS_DELETED, meta)
            return True
        except (urllib.error.HTTPError, LinShareException) as ex:
            self.log.error("Delete error : %s", ex)
            return False


class FunctionalityListCommand(FunctionalityCommand):
    """ List all functionalities."""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"

    @Time('linsharecli.funcs', label='Global time : %(time)s')
    def __call__(self, args):
        super().__call__(args)
        endpoint = self.ls.funcs
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        if self.api_version < 5:
            tbu.add_custom_cell("activationPolicy", PolicyCell)
            tbu.add_custom_cell("configurationPolicy", PolicyCell)
            tbu.add_custom_cell("delegationPolicy", PolicyCell)
            tbu.add_action('status', UpdateAction())
            # tbu.add_action('delete', DeleteAction())
            tbu.add_custom_cell("parameters", ParameterCell)
        else:
            tbu.add_custom_cell("activationPolicy", PolicyCell5)
            tbu.add_custom_cell("configurationPolicy", PolicyCell5)
            tbu.add_custom_cell("delegationPolicy", PolicyCell5)
            tbu.add_custom_cell("parameter", ParameterCell5)
            tbu.add_custom_cell(
                "domain",
                ComplexCellBuilder('{name} ({uuid:.8})', '{name} ({uuid})'))
            tbu.add_action("update", UpdateActionV5())
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
        super().__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
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
        cli = self.ls.funcs
        return cli.get_rbu().get_keys(True)


class FunctionalityUpdateCommand(FunctionalityCommand):
    """ List all functionalities."""

    def __init__(self, config, gparser):
        super().__init__(config)
        self.gparser = gparser

    def __call__(self, args):
        super().__call__(args)
        if self.api_version < 5:
            return self.__call_v4(args)
        return self.__call_v5(args)

    def __call_v5(self, args):
        self.check_required_options_v2(args, self.gparser)
        cli = self.ls
        endpoint = self.ls.funcs
        data = [endpoint.get(args.identifier), ]
        action = UpdateActionV5()
        return action(args, cli, endpoint, data)

    def __call_v4(self, args):
        error = False
        if args.status_deprecated or args.policy_type:
            if args.status_deprecated and not args.policy_type:
                args.policy_type = "AP_"
            if args.status_deprecated and args.policy_type:
                args.status = args.policy_type + args.status_deprecated
            else:
                error = True
        if error:
            raise ArgumentError(
                None,
                (
                    "If your using deprecated arguments --ap, --cp or --dp, "
                    "you must also provide the following flags: "
                    "--disable --enable --mandatory --forbidden.\n"
                    "Please use news flags. "
                    "Deprecated flags will removed soon."
                )
            )
        cli = self.ls
        endpoint = self.ls.funcs
        data = [endpoint.get(args.identifier), ]
        action = UpdateAction()
        return action(args, cli, endpoint, data)


class FunctionalityUpdateStringCommand(FunctionalityCommand):
    """ Update STRING functionalities."""

    def __call__(self, args):
        super().__call__(args)
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
        super().__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier')
                .startswith(prefix) and v.get('type') == 'STRING')


class FunctionalityUpdateTimeCommand(FunctionalityCommand):
    """ Update TIME functionalities."""

    def __call__(self, args):
        super().__call__(args)
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
            param = parameters[1]
        param['integer'] = args.value
        if args.unit:
            param['string'] = args.unit
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super().__call__(args)
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
        super().__call__(args)
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
        super().__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (val.get('identifier')
                for val in json_obj if val.get('identifier')
                .startswith(prefix) and val.get('type') == 'ENUM_LANG')


class FunctionalityUpdateSizeCommand(FunctionalityCommand):
    """ Update TIME functionalities."""

    def __call__(self, args):
        super().__call__(args)
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
        super().__call__(args)
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
        super().__call__(args)
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
        super().__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (val.get('identifier')
                for val in json_obj if val.get('identifier')
                .startswith(prefix) and val.get('type') == 'INTEGER')


class FunctionalityUpdateBooleanCommand(FunctionalityCommand):
    """ Update BOOLEAN functionalities."""

    def __call__(self, args):
        super().__call__(args)
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
            param = parameters[1]
        param['bool'] = args.boolean
        return self._update(args, cli, resource)

    def complete(self, args, prefix):
        """TODO"""
        super().__call__(args)
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
        super().__call__(args)
        act = DeleteAction()
        act.init(args, self.ls, self.ls.funcs)
        return act.delete([args.identifier, ])

    def complete(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.funcs.list(args.domain)
        return (val.get('identifier')
                for val in json_obj if val.get(
                    'identifier').startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super().__call__(args)
        json_obj = self.ls.domains.list()
        return (val.get('identifier')
                for val in json_obj if val.get(
                    'identifier').startswith(prefix))


def add_update_parser(actions_group, required=True):
    """TODO"""

    def add_parser_options(status_group, name, prefix):
        cst_prefix = prefix.upper().replace('-', '_')
        group = status_group.add_mutually_exclusive_group(required=required)
        group.add_argument(
            '--' + prefix + 'disable',
            default=None,
            action="store_const",
            help="Set " + name + " to ALLOWED and status to disable",
            const=cst_prefix + "DISABLE",
            dest="status")
        group.add_argument(
            '--' + prefix + 'enable',
            default=None,
            action="store_const",
            help="Set " + name + " to ALLOWED and status to enable",
            const=cst_prefix + "ENABLE",
            dest="status")
        group.add_argument(
            '--' + prefix + 'mandatory',
            action="store_const",
            help="Set " + name + " to MANDATORY and status to enable",
            const=cst_prefix + "MANDATORY",
            dest="status")
        group.add_argument(
            '--' + prefix + 'forbidden',
            action="store_const",
            help="Set " + name + " to FORBIDDEN and status to disable",
            const=cst_prefix + "FORBIDDEN",
            dest="status")

    add_parser_options(actions_group, "Activation Policy", "ap-")
    add_parser_options(actions_group, "Configuration Policy", "cp-")
    add_parser_options(actions_group, "Delegation Policy", "dp-")


def add_update_parser_v5(actions_group):
    """TODO"""

    def add_parser_options(status_group, name, prefix):
        cst_prefix = prefix.upper().replace('-', '_')
        group = status_group.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--' + prefix + 'disable',
            default=None,
            action="store_false",
            help=f"Disable {name} policy.",
            dest=cst_prefix + "enable")
        group.add_argument(
            '--' + prefix + 'enable',
            default=None,
            action="store_true",
            help=f"Enable {name} policy.",
            dest=cst_prefix + "enable")

        group = status_group.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--' + prefix + 'disallow-override',
            default=None,
            action="store_false",
            help=f"Disable {name} policy.",
            dest=cst_prefix + "allow_override")
        group.add_argument(
            '--' + prefix + 'allow-override',
            default=None,
            action="store_true",
            help=f"Enable {name} policy.",
            dest=cst_prefix + "allow_override")

    add_parser_options(actions_group, "Activation Policy", "ap-")
    add_parser_options(actions_group, "Configuration Policy", "cp-")
    add_parser_options(actions_group, "Delegation Policy", "dp-")

    choices = ('DAY', 'WEEK', 'MONTH', 'KILO', 'MEGA', 'GIGA')
    actions_group.add_argument(
            '--set-parameter-default',
            dest='parameter_default',
            help="TODO")
    actions_group.add_argument(
            '--set-parameter-default-unit',
            dest='parameter_default_unit',
            choices=choices,
            help="TODO")
    actions_group.add_argument(
            '--set-parameter-maximum',
            dest='parameter_maximum',
            help="TODO")
    actions_group.add_argument(
            '--set-parameter-maximum-unit',
            dest='parameter_maximum_unit',
            choices=choices,
            help="TODO")
    actions_group.add_argument(
            '--set-parameter-unlimited-on', action='store_true',
            dest='parameter_unlimited', default=None,
            help="TODO")
    actions_group.add_argument(
            '--set-parameter-unlimited-off', action='store_false',
            dest='parameter_unlimited', default=None,
            help="TODO")


def add_update_parser_old(parser, required=True):
    """TODO"""
    policy_group = parser.add_argument_group(
        'Deprecated. Choose the policy to update, default is activation')
    group = policy_group.add_mutually_exclusive_group()
    group.add_argument(
        '--ap',
        '--activation-policy',
        action="store_const",
        const="AP_",
        dest="policy_type",
        help="activation policy, deprecated see --ap-* options")
    group.add_argument(
        '--cp',
        '--configuration-policy',
        action="store_const",
        const="CP_",
        dest="policy_type",
        help="configuration policy, deprecated see --cp-* options")
    group.add_argument(
        '--dp',
        '--delegation-policy',
        action="store_const",
        const="DP_",
        dest="policy_type",
        help="delegation policy, deprecated see --dp-* options")

    status_group = parser.add_argument_group('Deprecated. Status')
    group = status_group.add_mutually_exclusive_group(required=required)
    group.add_argument(
        '--disable',
        default=None,
        action="store_const",
        help="Set policy to ALLOWED and status to disable",
        const="DISABLE",
        dest="status_deprecated")
    group.add_argument(
        '--enable',
        default=None,
        action="store_const",
        help="Set policy to ALLOWED and status to enable",
        const="ENABLE",
        dest="status_deprecated")
    group.add_argument(
        '--mandatory',
        action="store_const",
        help="Set policy to MANDATORY and status to enable",
        const="MANDATORY",
        dest="status_deprecated")
    group.add_argument(
        '--forbidden',
        action="store_const",
        help="Set policy to FORBIDDEN and status to disable",
        const="FORBIDDEN",
        dest="status_deprecated")


def add_parser(subparsers, name, desc, config):
    """Add all domain sub commands."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    api_version = config.server.api_version.value
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', aliases=['l'], help="list functionalities.")
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
    if api_version < 5:
        add_update_parser(actions_group, required=False)
    else:
        actions_group.add_argument('--update', action="store_true")
        update_group = parser.add_argument_group(
            "Update",
            "You must use --update flag to enable these option.")
        add_update_parser_v5(update_group)
    parser.set_defaults(__func__=FunctionalityListCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update a functionality.")
    parser.add_argument('identifier', action="store",
                        help="").completer = Completer()
    parser.add_argument(
        '-d', '--domain', action="store",
        help="Completion available").completer = Completer('complete_domain')
    parser.add_argument('--dry-run', action="store_true")
    parser.add_argument('--cli-mode', action="store_true", help="")
    if api_version < 5:
        add_update_parser(parser, required=False)
        add_update_parser_old(parser, required=False)
        parser.set_defaults(__func__=FunctionalityUpdateCommand(config, None))
    else:
        gparser = parser.add_argument_group(
            "Properties",
            "You must at least use one of these options")
        add_update_parser_v5(gparser)
        parser.set_defaults(__func__=FunctionalityUpdateCommand(
            config, gparser))

    if api_version < 5:
        # command : update-str
        parser = subparsers2.add_parser(
            'update-str', help="update STRING functionality.")
        parser.add_argument('identifier', action="store",
                            help="").completer = Completer()
        parser.add_argument(
            '-d', '--domain', action="store",
            help="Completion available"
        ).completer = Completer('complete_domain')
        parser.add_argument(
            'string',
            help="string value",
            action="store")
        parser.add_argument('--dry-run', action="store_true")
        parser.set_defaults(__func__=FunctionalityUpdateStringCommand(config))

        # command : update-int
        parser = subparsers2.add_parser(
            'update-int', help="update INTEGER functionality.")
        parser.add_argument('identifier', action="store",
                            help="").completer = Completer()
        parser.add_argument(
            '-d', '--domain', action="store",
            help="Completion available"
        ).completer = Completer('complete_domain')
        parser.add_argument(
            'integer',
            type=int,
            help="integer value",
            action="store")
        parser.add_argument('--dry-run', action="store_true")
        parser.set_defaults(__func__=FunctionalityUpdateIntegerCommand(config))

        # command : update-bool
        parser = subparsers2.add_parser(
            'update-bool', help="update BOOLEAN functionality.")
        parser.add_argument('identifier', action="store",
                            help="").completer = Completer()
        parser.add_argument(
            '-d', '--domain', action="store",
            help="Completion available"
        ).completer = Completer('complete_domain')
        status_group = parser.add_argument_group('Boolean value')
        group = status_group.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--disable',
            action="store_false",
            dest="boolean")
        group.add_argument(
            '--enable',
            action="store_true",
            dest="boolean")
        parser.add_argument('--dry-run', action="store_true")
        parser.set_defaults(__func__=FunctionalityUpdateBooleanCommand(config))

        # command : update-lang
        parser = subparsers2.add_parser(
            'update-lang', help="update language functionality.")
        parser.add_argument('identifier', action="store",
                            help="").completer = Completer()
        parser.add_argument(
            '-d', '--domain', action="store",
            help="Completion available"
        ).completer = Completer('complete_domain')
        parser.add_argument(
            '-l',
            '--lang',
            action="store",
            choices=('EN', 'FR'))
        parser.add_argument('--dry-run', action="store_true")
        parser.set_defaults(__func__=FunctionalityUpdateLangCommand(config))

        # command : update-time
        parser = subparsers2.add_parser(
            'update-time', help="update UNIT functionality.")
        parser.add_argument('identifier', action="store",
                            help="").completer = Completer()
        parser.add_argument(
            '-d', '--domain', action="store",
            help="Completion available"
        ).completer = Completer('complete_domain')
        parser.add_argument(
            'value',
            type=int,
            help="time value",
            action="store")
        parser.add_argument(
            '-u',
            '--unit',
            action="store",
            choices=('DAY', 'WEEK', 'MONTH'))
        parser.add_argument('--dry-run', action="store_true")
        parser.set_defaults(__func__=FunctionalityUpdateTimeCommand(config))

        # command : update-size
        parser = subparsers2.add_parser(
            'update-size', help="update UNIT functionality.")
        parser.add_argument('identifier', action="store",
                            help="").completer = Completer()
        parser.add_argument(
            '-d', '--domain', action="store",
            help="Completion available"
        ).completer = Completer('complete_domain')
        parser.add_argument(
            'value',
            type=int,
            help="size value",
            action="store")
        parser.add_argument(
            '-u',
            '--unit',
            action="store",
            choices=('KILO', 'MEGA', 'GIGA'))
        parser.add_argument('--dry-run', action="store_true")
        parser.set_defaults(__func__=FunctionalityUpdateSizeCommand(config))

    # command : reset
    parser = subparsers2.add_parser(
        'reset', help="reset a functionality.")
    parser.add_argument('identifier', action="store",
                        help="").completer = Completer()
    parser.add_argument('domain', action="store",
                        help="").completer = Completer('complete_domain')
    parser.set_defaults(__func__=FunctionalityResetCommand(config))
