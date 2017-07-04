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
from linsharecli.user.core import DefaultCommand
from linsharecli.common.filters import PartialOr
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import CreateAction
from argtoolbox import DefaultCompleter as Completer


# -----------------------------------------------------------------------------
class ThreadsCommand(DefaultCommand):

    DEFAULT_TOTAL = "Workgroups found : %(count)s"
    MSG_RS_NOT_FOUND = "No workgroups could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The workgroup '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The workgroup '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s workgroup(s) can not be deleted."
    MSG_RS_CREATED = "The workgroup '%(name)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    ACTIONS = {
        'delete' : '_delete_all',
        'count_only' : '_count_only',
    }

    def init_old_language_key(self):
        """For api <= 2"""
        self.DEFAULT_TOTAL = "Threads found : %(count)s"
        self.MSG_RS_NOT_FOUND = "No threads could be found."
        self.MSG_RS_DELETED = "%(position)s/%(count)s: The thread '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
        self.MSG_RS_CAN_NOT_BE_DELETED = "The thread '%(uuid)s' can not be deleted."
        self.MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s thread(s) can not be deleted."
        self.MSG_RS_CREATED = "The thread '%(name)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    def complete(self, args, prefix):
        super(ThreadsCommand, self).__call__(args)
        if self.api_version < 2:
            self.init_old_language_key()
        json_obj = self.ls.threads.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


# -----------------------------------------------------------------------------
class ThreadsListCommand(ThreadsCommand):
    """ List all threads store."""
    IDENTIFIER = "name"
    DEFAULT_SORT = "name"

    @Time('linsharecli.threads', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadsListCommand, self).__call__(args)
        if self.api_version < 2:
            self.init_old_language_key()
        cli = self.ls.threads
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        json_obj = cli.list()
        # Filters
        filters = PartialOr(self.IDENTIFIER, args.identifiers, True)
        # Formatters
        formatters = [DateFormatter('creationDate'),
                      DateFormatter('modificationDate')]
        return self._list(args, cli, table, json_obj, formatters, filters)

    def complete_fields(self, args, prefix):
        super(ThreadsListCommand, self).__call__(args)
        cli = self.ls.threads
        return cli.get_rbu().get_keys(True)


# -----------------------------------------------------------------------------
class ThreadsCreateCommand(ThreadsCommand):

    @Time('linsharecli.threads', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadsCreateCommand, self).__call__(args)
        if self.api_version < 2:
            self.init_old_language_key()
        act = CreateAction(self, args, self.ls.threads)
        return act.execute()


# -----------------------------------------------------------------------------
class ThreadsUpdateCommand(ThreadsCommand):

    @Time('linsharecli.threads', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadsUpdateCommand, self).__call__(args)
        if self.api_version < 2:
            self.init_old_language_key()
        rbu = self.ls.threads.get_rbu()
        rbu.load_from_args(args)
        return self._run(
            self.ls.threads.update,
            "The following threads '%(name)s' was successfully \
updated",
            args.uuid,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class ThreadsDeleteCommand(ThreadsCommand):

    @Time('linsharecli.thread', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadsDeleteCommand, self).__call__(args)
        if self.api_version < 2:
            self.init_old_language_key()
        cli = self.ls.threads
        return self._delete_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list threads")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser, delete=True, cdate=True)
    parser.set_defaults(__func__=ThreadsListCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete threads")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=ThreadsDeleteCommand(config))

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create thread.")
    parser.add_argument('name', action="store", help="")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=ThreadsCreateCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update thread.")
    parser.add_argument(
        'uuid', action="store", help="").completer = Completer()
    parser.add_argument('name', action="store", help="")
    parser.set_defaults(__func__=ThreadsUpdateCommand(config))
