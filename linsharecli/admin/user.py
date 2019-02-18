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

from argtoolbox import DefaultCompleter as Completer
from linshareapi.cache import Time
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import DomainFormatterResolver
from linsharecli.common.actions import UpdateAction
from linsharecli.common.actions import CreateAction
from linsharecli.common.core import add_list_parser_options


class UsersCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "mail"
    DEFAULT_SORT = "mail"
    DEFAULT_SORT_NAME = "lastName"
    RESOURCE_IDENTIFIER = "uuid"

    # pylint: disable=line-too-long
    DEFAULT_TOTAL = "Users : %(count)s"
    MSG_RS_NOT_FOUND = "No user be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The user '%(mail)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The user '%(mail)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s user(s) can not be deleted."
    MSG_RS_UPDATED = "The user '%(mail)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The user '%(mail)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    def complete_domain(self, args, prefix):
        """TODO"""
        super(UsersCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


class UsersListCommand(UsersCommand):
    """ List all users store into LinShare."""

    @Time('linsharecli.users', label='Global time : %(time)s')
    def __call__(self, args):
        super(UsersListCommand, self).__call__(args)
        cli = self.ls.users
        if not  (args.firstname or args.lastname or args.mail):
            raise ValueError(('You should use at leat one option among :'
                              '--firstname, --lastname or --mail'))
        json_obj = cli.search(args.firstname, args.lastname, args.mail)
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        formatters = [
            DateFormatter('creationDate'),
            DomainFormatterResolver(self.ls.domains, 'domain'),
            DateFormatter('modificationDate')
        ]
        # Filters
        # filters = [PartialOr(self.IDENTIFIER, args.identifiers, True)]
        # print cli.get('4900ea27-db08-439d-b14b-166407e7540a')
        return self._list(args, cli, table, json_obj, formatters=formatters)

    def complete_fields(self, args, prefix):
        """TODO"""
        super(UsersListCommand, self).__call__(args)
        cli = self.ls.users
        return cli.get_rbu().get_keys(True)


class UsersCreateCommand(UsersCommand):
    """Create the user's profile."""

    @Time('linsharecli.users', label='Global time : %(time)s')
    def __call__(self, args):
        super(UsersCreateCommand, self).__call__(args)
        cli = self.ls.users
        act = CreateAction(self, cli)
        return act.load(args).execute()

class UsersUpdateCommand(UsersCommand):
    """ List all users store into LinShare."""

    @Time('linsharecli.users', label='Global time : %(time)s')
    def __call__(self, args):
        super(UsersUpdateCommand, self).__call__(args)
        cli = self.ls.users
        resource = cli.get(args.identifier)
        act = UpdateAction(self, cli)
        act.rbu = cli.get_rbu()
        act.rbu.copy(resource)
        return act.load(args).execute()
        # return act.load(args).execute(rbu.to_resource())


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    """Add all user sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()
    api_version = config.server.api_version.value

    # command : list
    parser = subparsers2.add_parser('list', help="list some users")
    # parser.add_argument( 'pattern', nargs="*", help="Filter documents by their names")
    parser.add_argument('-f', '--firstname', action="store")
    parser.add_argument('-l', '--lastname', action="store")
    parser.add_argument('-m', '--mail', action="store")
    if api_version < 2:
        parser.add_argument('--extended', action="store_true",
                            help="extended format")
        parser.add_argument('-r', '--reverse', action="store_true",
                            help="reverse order while sorting")
        parser.add_argument('-t', '--vertical', action="store_true",
                            help="use vertical output mode")
        parser.add_argument('--csv', action="store_true", help="Csv output")
        parser.add_argument('--raw', action="store_true",
                            help="Disable all formatters")
        parser.add_argument(
            '-k', '--field', action='append', dest="fields"
            ).completer = Completer("complete_fields")
    else:
        add_list_parser_options(parser, delete=False, cdate=True)
    parser.set_defaults(__func__=UsersListCommand(config))

    if api_version >= 2:
        parser = subparsers2.add_parser('update', help="update a user")
        parser.add_argument('identifier', action="store")
        parser.add_argument('-f', '--first-name', action="store")
        parser.add_argument('-l', '--last-name', action="store")
        parser.add_argument('-m', '--mail', action="store")
        parser.add_argument('--cli-mode', action="store_true",
                            help="""Cli mode will format output to be used in
                            a script, by returning only identifiers or numbers
                            without any information messages.""")

        parser.add_argument('--role')
        parser.add_argument('--accountType')
        parser.add_argument('--locale')
        parser.add_argument('--can-upload')
        parser.add_argument('--can-create-guest')
        parser.add_argument('--external-mail-locale')
        parser.set_defaults(__func__=UsersUpdateCommand(config))

        parser = subparsers2.add_parser('create', help="create user's profile")
        parser.add_argument('domain', action="store").completer = Completer("complete_domain")
        parser.add_argument('mail', action="store")
        parser.add_argument('--cli-mode', action="store_true",
                            help="""Cli mode will format output to be used in
                            a script, by returning only identifiers or numbers
                            without any information messages.""")

        parser.set_defaults(__func__=UsersCreateCommand(config))
