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



import urllib.error

from argparse import ArgumentError
from argtoolbox import DefaultCompleter as Completer
from linshareapi.cache import Time
from linshareapi.core import LinShareException
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import Action
from linsharecli.common.tables import DeleteAction as DeleteActionTable
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
            else:
                dformat += " | RO"
        return dformat.format(**self.value)


class MailActivationsCommand(DefaultCommand):
    """TODO"""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"
    RESOURCE_IDENTIFIER = "identifier"

    DEFAULT_TOTAL = "MailActivation found : %(count)s"
    MSG_RS_NOT_FOUND = "No MailActivation could be found."

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


class UpdateAction(Action):
    """Update mail activation, is supposed to be used by an action table."""

    MSG_RS_UPDATED = (
        "%(position)s/%(count)s: "
        "The MailActivation '%(identifier)s' was updated. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_UPDATED = "The MailActivation '%(identifier)s' can not be updated."
    MSG_RS_CAN_NOT_BE_UPDATED_M = "%(count)s MailActivation(s) can not be updated."

    def init(self, args, cli, endpoint):
        super(UpdateAction, self).init(args, cli, endpoint)
        return self

    def __call__(self, args, cli, endpoint, data):
        """TODO"""
        self.init(args, cli, endpoint)
        count = len(data)
        position = 0
        res = 0
        for row in data:
            position += 1
            status = self.update_row(row, position, count, args.status)
            res += abs(status - 1)
        if res > 0:
            meta = {'count': res}
            self.pprint(self.MSG_RS_CAN_NOT_BE_UPDATED_M, meta)
            return False
        return True

    def update_row(self, row, position, count, status):
        """TODO"""
        self.log.debug("row : %s", row)
        meta = {}
        meta.update(row)
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        if status == 'CP_DISABLE':
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
        elif status == 'DISABLE':
            row['enable'] = False
        elif status == 'ENABLE':
            row['enable'] = True
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


class DomainTitle(Action):
    """TODO"""

    display = True

    def init(self, args, cli, endpoint):
        super(DomainTitle, self).init(args, cli, endpoint)
        self.display = not getattr(args, 'no_title', False)

    def __call__(self, args, cli, endpoint, data):
        self.init(args, cli, endpoint)
        if self.display:
            domain = "LinShareRootDomain"
            if args.domain:
                domain = args.domain
            domain = cli.domains.get(domain)
            dformat = "{label} ({identifier})"
            print()
            print("###>", dformat.format(**domain))
            print()


class MailActivationsListCommand(MailActivationsCommand):
    """ List all mail_activations."""
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
        tbu.add_action('status', UpdateAction())
        tbu.add_action('delete', DeleteAction())
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        json_obj = endpoint.list(args.domain)
        tbu.add_pre_render_class(DomainTitle())
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
    """ List all mail_activations."""

    def __call__(self, args):
        super().__call__(args)
        cli = self.ls
        endpoint = self.ls.mail_activations
        data = [endpoint.get(args.identifier),]
        action = UpdateAction()
        return action(args, cli, endpoint, data)


class DeleteAction(DeleteActionTable):
    """TODO"""

    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The mail_activation '%(name)s' (%(uuid)s) was reset. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The mail_activation '%(uuid)s' can not be reset."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s mail_activation(s) can not be reset."

    def __init__(self):
        super(DeleteAction, self).__init__(
            identifier="name",
            resource_identifier="identifier"
        )
        self.domain = None

    def init(self, args, cli, endpoint):
        super(DeleteAction, self).init(args, cli, endpoint)
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


class MailActivationsResetCommand(MailActivationsCommand):
    """ Reset a functionality."""

    def __call__(self, args):
        super().__call__(args)
        act = DeleteAction()
        act.init(args, self.ls, self.ls.mail_activations)
        return act.delete([args.identifier,])

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

    actions_group.add_argument(
        '--disable',
        default=None,
        action="store_const",
        help="Disable this mail_activations, this email will never be sent",
        const="DISABLE",
        dest="status")
    actions_group.add_argument(
        '--enable',
        default=None,
        action="store_const",
        help="Enable this mail_activations, this email will be sent",
        const="ENABLE",
        dest="status")
    add_parser_options(actions_group, "Configuration Policy", "cp-")

def add_parser(subparsers, name, desc, config):
    """Add all domain sub commands."""
    # pylint: disable=too-many-statements
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list mail_activations.")
    parser.add_argument('identifiers', nargs="*")
    parser.add_argument(
        '-d', '--domain', action="store",
        help="").completer = Completer('complete_domain')
    groups = add_list_parser_options(parser, delete=True)
    # groups : filter_group, sort_group, format_group, actions_group
    actions_group = groups[3]
    add_update_parser(actions_group, required=False)
    parser.set_defaults(__func__=MailActivationsListCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update a mail_activation.")
    parser.add_argument('identifier', action="store",
                        help="").completer = Completer()
    parser.add_argument('domain', action="store",
                        help="Completion available").completer = Completer('complete_domain')
    parser.add_argument('--dry-run', action="store_true")
    add_update_parser(parser, required=False)
    parser.set_defaults(__func__=MailActivationsUpdateCommand(config))

    # command : reset
    parser = subparsers2.add_parser(
        'reset', help="reset a mail_activation.")
    parser.add_argument('identifier', action="store",
                        help="").completer = Completer()
    parser.add_argument('domain', action="store",
                        help="").completer = Completer('complete_domain')
    parser.set_defaults(__func__=MailActivationsResetCommand(config))
