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



import urllib.request, urllib.error, urllib.parse

from linshareapi.cache import Time
from linsharecli.common.filters import PartialOr
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import add_list_parser_options
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.tables import TableBuilder
from argtoolbox import DefaultCompleter as Completer

# from argcomplete import warn
from argcomplete import debug

class InconsistentUsersCommand(DefaultCommand):
    """For  api >= 1.9"""
    IDENTIFIER = "mail"
    DEFAULT_SORT = "mail"
    RESOURCE_IDENTIFIER = "uuid"

    DEFAULT_TOTAL = "Inconsistent user found : %(count)s"
    MSG_RS_NOT_FOUND = "No inconsistent user could be found."
    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The inconsistent user '%(mail)s' (%(uuid)s) was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The inconsistent user '%(mail)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s inconsistent user (s) can not be deleted."
    MSG_RS_CAN_NOT_BE_UPDATED_M = "%(count)s inconsistent user (s) can not be updated."
    MSG_RS_CAN_NOT_BE_UPDATED = "The inconsistent user '%(mail)s'  '%(uuid)s' can not be deleted."
    MSG_RS_UPDATED = "The inconsistent user '%(mail)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The inconsistent user '%(mail)s' (%(uuid)s) was successfully created."

    def complete(self, args, prefix):
        super(InconsistentUsersCommand, self).__call__(args)
        json_obj = self.ls.iusers.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    def complete_domain(self, args, prefix):
        """TODO"""
        super(InconsistentUsersCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        debug(str(json_obj))
        resource_identifier = "identifier"
        return (v.get(resource_identifier)
                for v in json_obj if v.get(resource_identifier).startswith(prefix))


class InconsistentUsersListCommand(InconsistentUsersCommand):
    """ List all users store into LinShare."""

    # FIXME: handle custom action : set domain
    # how to trigger email check.
    # FIXME: ACTIONS is not supported anymore
    ACTIONS = {
        'set_domain' : '_set_domains',
    }

    @Time('linsharecli.iusers', label='Global time : %(time)s')
    def __call__(self, args):
        super(InconsistentUsersListCommand, self).__call__(args)
        endpoint = self.ls.iusers
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        return tbu.build().load_v2(endpoint.list()).render()

    def _set_domains(self, args, cli, uuids):
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            res += self._set_domain(args, cli, uuid, position, count)
        if res > 0:
            meta = {'count': res}
            self.pprint(self.MSG_RS_CAN_NOT_BE_UPDATED_M, meta)
            return False
        return True

    def _set_domain(self, args, cli, uuid, position=None, count=None):
        # pylint: disable=too-many-arguments
        try:
            if not position:
                position = 1
                count = 1
            meta = {}
            meta['uuid'] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            json_obj = cli.get(uuid)
            if not json_obj:
                meta = {'uuid': uuid}
                self.pprint(self.MSG_RS_CAN_NOT_BE_UPDATED, meta)
                return 1
            if not getattr(args, "dry_run", False):
                json_obj['domain'] = args.set_domain
                json_obj = cli.update(json_obj)
                meta['time'] = self.ls.last_req_time
            meta[self.IDENTIFIER] = json_obj.get(self.IDENTIFIER)
            self.pprint(self.MSG_RS_UPDATED, meta)
            return 0
        except urllib.error.HTTPError as ex:
            self.log.error("Delete error : %s", ex)
            return 1

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(InconsistentUsersListCommand, self).__call__(args)
        cli = self.ls.iusers
        return cli.get_rbu().get_keys(True)


class InconsistentUsersDeleteCommand(InconsistentUsersCommand):
    """ Delete inconsistent users."""

    @Time('linsharecli.iusers', label='Global time : %(time)s')
    def __call__(self, args):
        super(InconsistentUsersDeleteCommand, self).__call__(args)
        cli = self.ls.iusers
        return self._delete_all(args, cli, args.uuids)


class InconsistentUsersUpdateCommand(InconsistentUsersCommand):
    """ List all users store into LinShare."""

    @Time('linsharecli.iusers', label='Global time : %(time)s')
    def __call__(self, args):
        super(InconsistentUsersUpdateCommand, self).__call__(args)
        cli = self.ls.iusers
        resource = cli.get(args.identifier)
        rbu = cli.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            cli.update,
            self.MSG_RS_UPDATED,
            args.identifier,
            rbu.to_resource())


def add_parser(subparsers, name, desc, config):
    """Add all user sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()
    # api_version = config.server.api_version.value

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list domains")
    parser.add_argument(
        'identifiers', nargs="*",
        help="Filter domains by their identifiers")
    parser.add_argument('-n', '--label', action="store_true",
                        help="sort by domain label")
    parsers = add_list_parser_options(parser, delete=True, cdate=False)
    actions = parsers[3]
    actions.add_argument(
        "--set-domain",
        help="update all inconsistent users with selected domain"
        ).completer = Completer("complete_domain")
    parser.set_defaults(__func__=InconsistentUsersListCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update inconsistent users.")
    parser.add_argument(
        'identifier', action="store", help="").completer = Completer()
    parser.add_argument(
        '--domain', action="store",
        help="").completer = Completer("complete_domain")
    parser.set_defaults(__func__=InconsistentUsersUpdateCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete', help="delete inconsistent users.")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=InconsistentUsersDeleteCommand(config))
