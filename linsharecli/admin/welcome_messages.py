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
# Copyright 2018 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

from __future__ import unicode_literals

from argtoolbox import DefaultCompleter as Completer
from linshareapi.cache import Time
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.actions import CreateAction
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.formatters import Formatter
from linsharecli.common.formatters import DomainFormatter
from linsharecli.common.formatters import DateFormatter


class WelcomeMessagesCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "name"
    DEFAULT_SORT = "name"
    DEFAULT_SORT_NAME = "name"
    RESOURCE_IDENTIFIER = "uuid"

    DEFAULT_TOTAL = "Welcome message found : %(count)s"
    MSG_RS_NOT_FOUND = "No welcome message could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The welcome message '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The welcome message '%(name)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s welcome message(s) can not be deleted."
    MSG_RS_UPDATED = "The welcome message '%(name)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The welcome message '%(name)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    def complete(self, args, prefix):
        super(WelcomeMessagesCommand, self).__call__(args)
        json_obj = self.ls.welcome_messages.list(args.current_domain)
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super(WelcomeMessagesCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
# pylint: disable=too-few-public-methods
class WelcomeEntriesFormatter(Formatter):
    """TODO"""

    def __init__(self, prop):
        super(WelcomeEntriesFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            keys = (v[0:2] for v in parameter.keys())
            row[self.prop] = " ".join(keys)
            row[self.prop] += ". See --detail."


# -----------------------------------------------------------------------------
class WelcomeMessagesListCommand(WelcomeMessagesCommand):
    """ List all welcome messages."""

    @Time('linsharecli.wlcmsg', label='Global time : %(time)s')
    def __call__(self, args):
        super(WelcomeMessagesListCommand, self).__call__(args)
        cli = self.ls.welcome_messages
        if args.detail:
            return self.list_detail(args, cli)
        else:
            return self.list_table(args, cli)

    def list_detail(self, args, cli):
        """TODO"""
        keys = []
        keys.append(self.IDENTIFIER)
        keys.append(self.RESOURCE_IDENTIFIER)
        keys.append('VIETNAMESE')
        keys.append('ENGLISH')
        keys.append('FRENCH')
        args.vertical = True
        table = self.get_raw_table(args, cli, self.IDENTIFIER, keys)
        # useless and required ! Design flaw ?
        table.sortby = self.IDENTIFIER
        json_obj = []
        filteror = PartialOr(self.IDENTIFIER, args.identifiers, True)
        for json_row in cli.list(args.current_domain):
            if filteror(json_row):
                data = json_row.get('welcomeMessagesEntries')
                data[self.IDENTIFIER] = json_row.get(self.IDENTIFIER)
                data[self.RESOURCE_IDENTIFIER] = json_row.get(self.RESOURCE_IDENTIFIER)
                json_obj.append(data)
        json_obj = sorted(json_obj, reverse=args.reverse, key=lambda x: x.get(table.sortby))
        return self._list(args, cli, table, json_obj)

    def list_table(self, args, cli):
        """TODO"""
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        json_obj = cli.list(args.current_domain)
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.identifiers, True)]
        formatters = [DomainFormatter("myDomain"),
                      DateFormatter('creationDate'),
                      DateFormatter('modificationDate'),
                      WelcomeEntriesFormatter('welcomeMessagesEntries')]
        return self._list(args, cli, table, json_obj, formatters=formatters,
                          filters=filters)

    # pylint: disable=unused-argument
    def complete_fields(self, args, prefix):
        """TODO"""
        super(WelcomeMessagesListCommand, self).__call__(args)
        cli = self.ls.welcome_messages
        return cli.get_rbu().get_keys(True)


# -----------------------------------------------------------------------------
class WelcomeMessagesCreateCommand(WelcomeMessagesCommand):
    """Create welcome message."""

    def __call__(self, args):
        super(WelcomeMessagesCreateCommand, self).__call__(args)
        if args.domain:
            args.domain = {'identifier': args.domain}
        act = CreateAction(self, self.ls.welcome_messages)
        return act.load(args).execute()


# -----------------------------------------------------------------------------
class WelcomeMessagesUpdateCommand(WelcomeMessagesCommand):
    """Update welcome message."""

    def __call__(self, args):
        super(WelcomeMessagesUpdateCommand, self).__call__(args)
        cli = self.ls.welcome_messages
        resource = cli.get(args.identifier)
        rbu = cli.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        resource = rbu.to_resource()
        if not getattr(args, 'name', False):
            if args.is_file:
                fde = open(args.value, 'r')
                resource.get('welcomeMessagesEntries')[args.entry] = fde.read()
            else:
                resource.get('welcomeMessagesEntries')[args.entry] = args.value
        return self._run(
            cli.update,
            self.MSG_RS_UPDATED,
            args.identifier,
            resource)


# -----------------------------------------------------------------------------
class WelcomeMessagesDeleteCommand(WelcomeMessagesCommand):
    """Delete welcome message."""

    def __call__(self, args):
        super(WelcomeMessagesDeleteCommand, self).__call__(args)
        cli = self.ls.welcome_messages
        return self._delete_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    """Add all welcome message sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list welcome message.")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser, delete=True, cdate=False)
    parser.add_argument('--detail', action="store_true",
                        help="Display the whole content of a welcome message")
    parser.add_argument('--current-domain').completer = Completer("complete_domain")
    parser.set_defaults(__func__=WelcomeMessagesListCommand(config))

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete welcome message.")
    add_delete_parser_options(parser_tmp2)
    parser_tmp2.add_argument('--current-domain').completer = Completer("complete_domain")
    parser_tmp2.set_defaults(__func__=WelcomeMessagesDeleteCommand(config))

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create welcome message.")
    parser_tmp2.add_argument('uuid').completer = Completer()
    parser_tmp2.add_argument('name')
    parser_tmp2.add_argument('--domain').completer = Completer("complete_domain")
    parser_tmp2.add_argument('--cli-mode', action="store_true", help="")
    parser_tmp2.set_defaults(__func__=WelcomeMessagesCreateCommand(config))

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update welcome message.")
    parser_tmp2.add_argument('identifier').completer = Completer()
    parser_tmp2.add_argument('name', action="store", help="")
    parser_tmp2.add_argument('--current-domain').completer = Completer("complete_domain")
    parser_tmp2.set_defaults(__func__=WelcomeMessagesUpdateCommand(config))

    # command : update-entry
    parser_tmp2 = subparsers2.add_parser(
        'update-entry', help="update welcome message entries.")
    parser_tmp2.add_argument('identifier').completer = Completer()
    parser_tmp2.add_argument('--entry', choices=['ENGLISH', 'FRENCH', 'VIETNAMESE'],
                             action="store", help="", required=True)
    parser_tmp2.add_argument('value', action="store", help="Payload for an entry.")
    parser_tmp2.add_argument(
        '--is-file', action="store_true",
        help="If True, value attribute should contains the path to a file to load.")
    parser_tmp2.set_defaults(__func__=WelcomeMessagesUpdateCommand(config))
