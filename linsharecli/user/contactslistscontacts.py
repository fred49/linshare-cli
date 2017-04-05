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
# Copyright 2017 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

from __future__ import unicode_literals

from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand as Command
from linsharecli.common.filters import PartialOr
from linsharecli.common.formatters import OwnerFormatter
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from argtoolbox import DefaultCompleter as Completer
from argparse import RawTextHelpFormatter


# -----------------------------------------------------------------------------
class ContactListsCompleter(object):

    def __init__(self, config):
        self.config = config

    def __call__(self, prefix, **kwargs):
        from argcomplete import debug
        try:
            debug("\n------------ ContactListsCompleter -----------------")
            debug("Kwargs content :")
            for i, j in kwargs.items():
                debug("key : " + str(i))
                debug("\t - " + str(j))
            debug("\n------------ ContactListsCompleter -----------------\n")
            args = kwargs.get('parsed_args')
            thread_cmd = DefaultCommand(self.config)
            return thread_cmd.complete_lists(args, prefix)
        # pylint: disable-msg=W0703
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")

# -----------------------------------------------------------------------------
class DefaultCommand(Command):

    IDENTIFIER = "mail"
    DEFAULT_SORT = "mail"

    DEFAULT_TOTAL = "ContactsList found : %(count)s"
    MSG_RS_NOT_FOUND = "No contactslist could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The contactslist '%(mail)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The contactslist '%(mail)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s contactslist(s) can not be deleted."
    MSG_RS_UPDATED = "The contactslist '%(mail)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The contactslist '%(mail)s' (%(uuid)s) was successfully created."

    CFG_DELETE_MODE = 1
    CFG_DELETE_ARG_ATTR = "mailing_list_uuid"

    ACTIONS = {
        'delete': '_delete_all',
        'count_only': '_count_only',
    }

    def complete(self, args, prefix):
        super(DefaultCommand, self).__call__(args)
        json_obj = self.ls.contactslistscontacts.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    def complete_lists(self, args, prefix):
        super(DefaultCommand, self).__call__(args)
        json_obj = self.ls.contactslists.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))



# -----------------------------------------------------------------------------
class ListCommand(DefaultCommand):
    """ List all contactslists store into LinShare."""

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(ListCommand, self).__call__(args)
        cli = self.ls.contactslistscontacts
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        json_obj = cli.list(args.mailing_list_uuid)
        # Filters
        filters = [
            PartialOr(self.IDENTIFIER, args.pattern, True)
        ]
        formatters = [
            OwnerFormatter('owner'),
        ]
        return self._list(args, cli, table, json_obj, filters=filters,
                          formatters=formatters)

    def complete_fields(self, args, prefix):
        super(ListCommand, self).__call__(args)
        cli = self.ls.contactslistscontacts
        return cli.get_rbu().get_keys(True)


# -----------------------------------------------------------------------------
class CreateCommand(DefaultCommand):

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(CreateCommand, self).__call__(args)
        rbu = self.ls.contactslistscontacts.get_rbu()
        rbu.load_from_args(args)
        identifier = getattr(args, self.IDENTIFIER)
        return self._run(
            self.ls.contactslistscontacts.create,
            self.MSG_RS_CREATED,
            identifier,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class DeleteCommand(DefaultCommand):
    """Delete contactslist."""

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(DeleteCommand, self).__call__(args)
        cli = self.ls.contactslistscontacts
        return self._delete_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
class UpdateCommand(DefaultCommand):

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(UpdateCommand, self).__call__(args)
        cli = self.ls.contactslistscontacts
        identifier = getattr(args, self.RESOURCE_IDENTIFIER)
        resource = cli.get(args.mailing_list_uuid, identifier)
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
    parser_tmp.add_argument(
        '-u',
        '--uuid',
        action="store",
        dest="mailing_list_uuid",
        help="list uuid",
        required=True).completer = ContactListsCompleter(config)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list contactslist from linshare")
    parser.add_argument(
        'pattern', nargs="*",
        help="Filter documents by their names")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser, delete=True, cdate=True)
    parser.set_defaults(__func__=ListCommand(config))


    # command : create
    parser = subparsers2.add_parser(
        'create', help="create contactslist.")
    parser.add_argument(DefaultCommand.IDENTIFIER, action="store", help="")
    parser.add_argument('--public', dest="public", action="store_true", help="")
    parser.add_argument('--first-name', action="store", help="")
    parser.add_argument('--last-name', action="store", help="")
    parser.set_defaults(__func__=CreateCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete contactslist")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=DeleteCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update contactslist.")
    parser.add_argument(
        'uuid', action="store", help="").completer = Completer()
    #parser.add_argument('--identifier', action="store", help="")
    parser.add_argument("--" + DefaultCommand.IDENTIFIER, action="store", help="")
    parser.add_argument('--public', dest="public", action="store_true", help="")
    parser.add_argument('--first-name', action="store", help="")
    parser.add_argument('--last-name', action="store", help="")
    parser.set_defaults(__func__=UpdateCommand(config))
