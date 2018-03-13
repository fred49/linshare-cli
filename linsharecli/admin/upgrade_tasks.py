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
# Copyright 2018 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

from __future__ import unicode_literals

from linshareapi.cache import Time
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import CreateAction
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import SizeFormatter
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_delete_parser_options
from argtoolbox import DefaultCompleter as Completer


class UpgradeTasksCommand(DefaultCommand):

    IDENTIFIER = "identifier"
    DEFAULT_SORT = "taskOrder"
    DEFAULT_SORT_NAME = "taskOrder"
    RESOURCE_IDENTIFIER = "identifier"

    # DEFAULT_TOTAL = "Ldap connection found : %(count)s"
    # MSG_RS_NOT_FOUND = "No Ldap connection could be found."
    # MSG_RS_DELETED = "%(position)s/%(count)s: The Ldap connection '%(label)s' (%(uuid)s) was deleted. (%(time)s s)"
    # MSG_RS_CAN_NOT_BE_DELETED = "The Ldap connection '%(label)s'  '%(uuid)s' can not be deleted."
    # MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s Ldap connection(s) can not be deleted."
    # MSG_RS_UPDATED = "The Ldap connection '%(label)s' (%(uuid)s) was successfully updated."
    # MSG_RS_CREATED = "The Ldap connection '%(label)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    def complete(self, args, prefix):
        super(UpgradeTasksCommand, self).__call__(args)
        json_obj = self.ls.ldap_connections.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


# -----------------------------------------------------------------------------
class UpgradeTasksListCommand(UpgradeTasksCommand):
    """ List all upgrade_tasks."""

    @Time('linsharecli.upgrade_tasks', label='Global time : %(time)s')
    def __call__(self, args):
        super(UpgradeTasksListCommand, self).__call__(args)
        cli = self.ls.upgrade_tasks
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        json_obj = cli.list()
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.identifiers, True),
                   PartialDate("creationDate", args.cdate)]
        # Formatters
        formatters = [DateFormatter('creationDate'),
                      DateFormatter('modificationDate')]
        return self._list(args, cli, table, json_obj, formatters, filters)

    def complete_fields(self, args, prefix):
        super(UpgradeTasksListCommand, self).__call__(args)
        cli = self.ls.ldap_connections
        return cli.get_rbu().get_keys(True)


# # -----------------------------------------------------------------------------
# class LdapConnectionsUpdateCommand(UpgradeTasksCommand):
#     """Update ldap connection."""
#
#     def __call__(self, args):
#         super(LdapConnectionsUpdateCommand, self).__call__(args)
#         if self.api_version == 0:
#             self.init_old_language_key()
#         cli = self.ls.ldap_connections
#         resource = cli.get(args.identifier)
#         rbu = cli.get_rbu()
#         rbu.copy(resource)
#         rbu.load_from_args(args)
#         return self._run(
#             cli.update,
#             self.MSG_RS_UPDATED,
#             args.identifier,
#             rbu.to_resource())


def add_parser(subparsers, name, desc, config):
    """Add all upgrade tasks sub commands."""
    # api_version = config.server.api_version.value
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list ldap connections.")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser, cdate=True)
    parser.set_defaults(__func__=UpgradeTasksListCommand(config))
