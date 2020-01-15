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
# Copyright 2017 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



from argparse import RawTextHelpFormatter
from argtoolbox import DefaultCompleter as Completer
from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand as Command
from linsharecli.common.filters import PartialOr
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import DeleteAction


class ContactListsCompleter(object):
    """TODO"""

    def __init__(self, config):
        self.config = config

    def __call__(self, prefix, **kwargs):
        from argcomplete import debug
        try:
            debug("\n------------ ContactListsCompleter -----------------")
            debug("Kwargs content :")
            for i, j in list(kwargs.items()):
                debug("key : " + str(i))
                debug("\t - " + str(j))
            debug("\n------------ ContactListsCompleter -----------------\n")
            args = kwargs.get('parsed_args')
            thread_cmd = DefaultCommand(self.config)
            return thread_cmd.complete_lists(args, prefix)
        # pylint: disable=broad-except
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")


class DefaultCommand(Command):
    """TODO"""

    IDENTIFIER = "mail"
    DEFAULT_SORT = "mail"

    DEFAULT_TOTAL = "ContactsList found : %(count)s"
    MSG_RS_NOT_FOUND = "No contactslist could be found."
    MSG_RS_UPDATED = "The contactslist '%(mail)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The contactslist '%(mail)s' (%(uuid)s) was successfully created."

    CFG_DELETE_MODE = 1
    CFG_DELETE_ARG_ATTR = "mailing_list_uuid"

    def complete(self, args, prefix):
        super(DefaultCommand, self).__call__(args)
        json_obj = self.ls.contactslistscontacts.list(args.mailing_list_uuid)
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    def complete_lists(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(DefaultCommand, self).__call__(args)
        json_obj = self.ls.contactslists.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))


class ListCommand(DefaultCommand):
    """ List all contactslists store into LinShare."""

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(ListCommand, self).__call__(args)
        endpoint = self.ls.contactslistscontacts
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_action('delete', DeleteAction(
            mode=self.CFG_DELETE_MODE,
            parent_identifier=self.CFG_DELETE_ARG_ATTR
        ))
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.pattern, True)
        )
        json_obj = endpoint.list(args.mailing_list_uuid)
        return tbu.build().load_v2(json_obj).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(ListCommand, self).__call__(args)
        cli = self.ls.contactslistscontacts
        return cli.get_rbu().get_keys(True)


class CreateCommand(DefaultCommand):
    """TODO"""

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(CreateCommand, self).__call__(args)
        rbu = self.ls.contactslistscontacts.get_rbu()
        rbu.load_from_args(args)
        identifier = getattr(args, self.IDENTIFIER)
        # FIXME : CREATE
        return self._run(
            self.ls.contactslistscontacts.create,
            self.MSG_RS_CREATED,
            identifier,
            rbu.to_resource())


class DeleteCommand(DefaultCommand):
    """Delete contactslist."""

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(DeleteCommand, self).__call__(args)
        act = DeleteAction(
            mode=self.CFG_DELETE_MODE,
            parent_identifier=self.CFG_DELETE_ARG_ATTR
        )
        act.init(args, self.ls, self.ls.contactslistscontacts)
        return act.delete(args.uuids)


class UpdateCommand(DefaultCommand):
    """TODO"""

    @Time('linsharecli.contactslistscontacts', label='Global time : %(time)s')
    def __call__(self, args):
        super(UpdateCommand, self).__call__(args)
        cli = self.ls.contactslistscontacts
        identifier = getattr(args, self.RESOURCE_IDENTIFIER)
        resource = cli.get(args.mailing_list_uuid, identifier)
        rbu = cli.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        # FIXME: CREATE
        return self._run(
            cli.update,
            self.MSG_RS_UPDATED,
            identifier,
            rbu.to_resource())


def add_parser(subparsers, name, desc, config):
    """TODO"""
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
