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
# Copyright 2016 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

from __future__ import unicode_literals

from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand
from linsharecli.common.filters import PartialMultipleAnd
from linsharecli.common.filters import PartialOr
from linsharecli.common.formatters import OwnerFormatter
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from argtoolbox import DefaultCompleter as Completer
from argparse import RawTextHelpFormatter


# -----------------------------------------------------------------------------
class GuestsCommand(DefaultCommand):

    IDENTIFIER = "mail"
    DEFAULT_SORT = "mail"

    DEFAULT_TOTAL = "Guests found : %(count)s"
    MSG_RS_NOT_FOUND = "No guests could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The guest '%(mail)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The guest '%(mail)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s guest(s) can not be deleted."
    MSG_RS_UPDATED = "The guest '%(mail)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The guest '%(firstName)s %(lastName)s <%(mail)s>' (%(uuid)s) was successfully created."

    ACTIONS = {
        'delete': '_delete_all',
        'count_only': '_count_only',
    }

    def complete(self, args, prefix):
        super(GuestsCommand, self).__call__(args)
        json_obj = self.ls.guests.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


# -----------------------------------------------------------------------------
class GuestsListCommand(GuestsCommand):
    """ List all guests store into LinShare."""

    @Time('linsharecli.guests', label='Global time : %(time)s')
    def __call__(self, args):
        super(GuestsListCommand, self).__call__(args)
        cli = self.ls.guests
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        json_obj = cli.list()
        # Filters
        filters = [
            PartialMultipleAnd(
                {
                    "mail": args.mail,
                    "firstName": args.firstname,
                    "lastName": args.lastname
                },
                True),
            PartialOr("uuid", args.uuid),
            PartialOr(self.IDENTIFIER, args.pattern, True)
        ]
        formatters = [
            OwnerFormatter('owner'),
            DateFormatter('creationDate'),
            DateFormatter('modificationDate'),
            DateFormatter('expirationDate')
        ]
        return self._list(args, cli, table, json_obj, filters=filters,
                          formatters=formatters)

    def complete_fields(self, args, prefix):
        super(GuestsListCommand, self).__call__(args)
        cli = self.ls.guests
        return cli.get_rbu().get_keys(True)


# -----------------------------------------------------------------------------
class GuestsInfoCommand(GuestsCommand):
    """ List all guests store into LinShare."""

    @Time('linsharecli.guests', label='Global time : %(time)s')
    def __call__(self, args):
        super(GuestsInfoCommand, self).__call__(args)
        cli = self.ls.guests
        # args.extended = True
        # args.vertical = True
        table = self.get_table(args, cli, self.IDENTIFIER)
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        json_obj = []
        for uuid in args.uuids:
            json_obj.append(cli.get(uuid))
        formatters = [
            OwnerFormatter('owner'),
            DateFormatter('creationDate'),
            DateFormatter('modificationDate'),
            DateFormatter('expirationDate')
        ]
        return self._list(args, cli, table, json_obj,
                          formatters=formatters)

    def complete_fields(self, args, prefix):
        super(GuestsInfoCommand, self).__call__(args)
        cli = self.ls.guests
        return cli.get_rbu().get_keys(True)


# -----------------------------------------------------------------------------
class GuestsCreateCommand(GuestsCommand):

    @Time('linsharecli.guests', label='Global time : %(time)s')
    def __call__(self, args):
        super(GuestsCreateCommand, self).__call__(args)
        rbu = self.ls.guests.get_rbu()
        rbu.load_from_args(args)
        identifier = getattr(args, self.IDENTIFIER)
        return self._run(
            self.ls.guests.create,
            self.MSG_RS_CREATED,
            identifier,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class GuestsDeleteCommand(GuestsCommand):
    """Delete guest."""

    @Time('linsharecli.guests', label='Global time : %(time)s')
    def __call__(self, args):
        super(GuestsDeleteCommand, self).__call__(args)
        cli = self.ls.guests
        return self._delete_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
class GuestsUpdateCommand(GuestsCommand):

    @Time('linsharecli.guests', label='Global time : %(time)s')
    def __call__(self, args):
        super(GuestsUpdateCommand, self).__call__(args)
        cli = self.ls.guests
        identifier = getattr(args, self.RESOURCE_IDENTIFIER)
        resource = cli.get(identifier)
        rbu = cli.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            cli.update,
            self.MSG_RS_UPDATED,
            identifier,
            rbu.to_resource())


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list guests from linshare")
    parser.add_argument(
        'pattern', nargs="*",
        help="Filter documents by their names")
    parser.add_argument('-f', '--firstname', action="store")
    parser.add_argument('-l', '--lastname', action="store")
    parser.add_argument('-m', '--mail', action="store")
    parser.add_argument('-u', '--uuid', action="append")
    add_list_parser_options(parser, delete=True, cdate=True)
    parser.set_defaults(__func__=GuestsListCommand(config))

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create guest.")
    parser.add_argument( '--mail', dest="mail", required=True, help="")
    parser.add_argument( '--firstname', dest="first_name", required=True, help="")
    parser.add_argument( '--lastname', dest="last_name", required=True, help="")
    parser.add_argument( '--can-upload', dest="can_upload", action="store_true", help="")
    parser.set_defaults(__func__=GuestsCreateCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete guests")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=GuestsDeleteCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update guest.")
    parser.add_argument(
        'uuid', action="store", help="").completer = Completer()
    parser.add_argument('--first-name', action="store", help="")
    parser.add_argument('--last-name', action="store", help="")
    parser.add_argument('--mail', action="store", help="")
    parser.add_argument('--can-upload', action="store", help="true or false")
    parser.add_argument('--restricted', action="store_false")
    parser.set_defaults(__func__=GuestsUpdateCommand(config))

    # command : info
    parser = subparsers2.add_parser(
        'info',
        help="info guests")
    parser.add_argument('uuids', nargs='+').completer = Completer()
    add_list_parser_options(parser, cdate=True)
    parser.set_defaults(__func__=GuestsInfoCommand(config))
