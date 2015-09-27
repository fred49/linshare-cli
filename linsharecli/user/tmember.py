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

import urllib2
from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand
from linsharecli.common.filters import PartialOr
#from linsharecli.common.formatters import DateFormatter
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linshareapi.core import LinShareException
from argtoolbox import DefaultCompleter as Completer



# -----------------------------------------------------------------------------
class ThreadCompleter(object):

    def __call__(self, prefix, **kwargs):
        from argcomplete import debug
        try:
            debug("\n------------ ThreadCompleter -----------------")
            debug("Kwargs content :")
            for i, j in kwargs.items():
                debug("key : " + str(i))
                debug("\t - " + str(j))
            debug("\n------------ ThreadCompleter -----------------\n")
            args = kwargs.get('parsed_args')
            thread_cmd = ThreadMembersListCommand()
            return thread_cmd.complete_threads(args, prefix)
        # pylint: disable-msg=W0703
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")


# -----------------------------------------------------------------------------
class ThreadMembersCommand(DefaultCommand):

    IDENTIFIER = "userMail"
    RESOURCE_IDENTIFIER = "userUuid"
    DEFAULT_SORT = "userMail"
    DEFAULT_SORT_NAME = "userMail"

    DEFAULT_TOTAL = "Thread members found : %(count)s"
    MSG_RS_NOT_FOUND = "No thread members could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The thread '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The thread '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s thread(s) can not be deleted."

    ACTIONS = {
        'delete' : '_delete_all',
        'count_only' : '_count_only',
    }

    def _delete(self, args, cli, uuid, position=None, count=None):
        try:
            meta = {}
            meta['uuid'] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            if getattr(args, "dry_run", False):
                json_obj = cli.get(args.thread_uuid, uuid)
            else:
                json_obj = cli.delete(args.thread_uuid, uuid)
                meta['time'] = self.ls.last_req_time
            if not json_obj:
                meta = {'uuid': uuid}
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED, meta)
                return 1
            meta['name'] = json_obj.get('name')
            self.pprint(self.MSG_RS_DELETED, meta)
            return 0
        except urllib2.HTTPError as ex:
            self.log.error("Delete error : %s", ex)
            return 1


    def complete(self, args, prefix):
        super(ThreadMembersCommand, self).__call__(args)
        #from argcomplete import debug
        #debug("\n------------ test -----------------")
        json_obj = self.ls.thread_members.list(args.thread_uuid)
        return (
            v.get('userUuid') for v in json_obj if v.get('userUuid').startswith(prefix))

    def complete_threads(self, args, prefix):
        super(ThreadMembersCommand, self).__call__(args)
        json_obj = self.ls.threads.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))

    def complete_mail(self, args, prefix):
        super(ThreadMembersCommand, self).__call__(args)
        from argcomplete import warn
        if len(prefix) >= 3:
            json_obj = self.ls.users.list()
            return (v.get('mail')
                    for v in json_obj if v.get('mail').startswith(prefix))
        else:
            warn("---------------------------------------")
            warn("Completion need at least 3 characters.")
            warn("---------------------------------------")


    def _run(self, method, message_ok, err_suffix, *args):
        try:
            json_obj = method(*args)
            self.log.info(message_ok, json_obj)
            if self.debug:
                self.pretty_json(json_obj)
            return True
        except LinShareException as ex:
            self.log.debug("LinShareException : " + str(ex.args))
            self.log.error(ex.args[1] + " : " + err_suffix)
        return False



# -----------------------------------------------------------------------------
class ThreadMembersListCommand(ThreadMembersCommand):
    """ List all thread members."""

    @Time('linsharecli.tmembers', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadMembersListCommand, self).__call__(args)
        cli = self.ls.thread_members
        table = self.get_table(args, cli, self.IDENTIFIER)
        json_obj = cli.list(args.thread_uuid)
        # Filters
        filters = PartialOr(self.IDENTIFIER, args.identifiers, True)
        # Formatters
        #formatters = [DateFormatter('creationDate'),
        #            DateFormatter('modificationDate')]
        return self._list(args, cli, table, json_obj, filters=filters)


# -----------------------------------------------------------------------------
class ThreadMembersCreateCommand(ThreadMembersCommand):

    @Time('linsharecli.tmembers', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadMembersCreateCommand, self).__call__(args)
        rbu = self.ls.thread_members.get_rbu()
        rbu.load_from_args(args)
        data = rbu.to_resource()
        print data
        user = self.ls.users.get(data.get('userMail'))
        data['userDomainId'] = user.get('domain')
        return self.ls.thread_members.create(data)
        return self._run(
            self.ls.thread_members.create,
            "The following thread members '%(name)s' was successfully \
created",
            args.user_mail,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class ThreadMembersUpdateCommand(ThreadMembersCommand):

    def __call__(self, args):
        super(ThreadMembersUpdateCommand, self).__call__(args)
        rbu = self.ls.thread_members.get_rbu()
        rbu.load_from_args(args)
        return self._run(
            self.ls.thread_members.update,
            "The following thread members '%(name)s' was successfully \
updated",
            args.uuid,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class ThreadMembersDeleteCommand(ThreadMembersCommand):

    @Time('linsharecli.thread', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadMembersDeleteCommand, self).__call__(args)
        cli = self.ls.thread_members
        return self._delete_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    parser_tmp = subparsers.add_parser(name, help=desc)
    parser_tmp.add_argument(
        '-u',
        '--uuid',
        action="store",
        dest="thread_uuid",
        help="thread uuid",
        required=True).completer = ThreadCompleter()

    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list thread members")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser, delete=True, cdate=True)
    parser.set_defaults(__func__=ThreadMembersListCommand())

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete thread members")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=ThreadMembersDeleteCommand())

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create thread member.")
    parser.add_argument(
        '--mail',
        dest="user_mail",
        help="").completer = Completer('complete_mail')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--admin', action="store_true", help="")
    group.add_argument('--readonly', action="store_true", help="")
    parser.set_defaults(__func__=ThreadMembersCreateCommand())

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update thread.")
    parser.add_argument(
        'userUuid', action="store", help="").completer = Completer()
    parser.add_argument('role', choices=["admin", "normal","restricted"], help="")
    parser.set_defaults(__func__=ThreadMembersUpdateCommand())
