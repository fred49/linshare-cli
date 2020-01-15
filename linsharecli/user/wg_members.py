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
from linshareapi.core import LinShareException
from argtoolbox import DefaultCompleter as Completer
from linsharecli.user.core import DefaultCommand
from linsharecli.common.filters import PartialOr
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.actions import CreateAction
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import DeleteAction



class ThreadCompleter(object):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, config):
        self.config = config

    def __call__(self, prefix, **kwargs):
        from argcomplete import debug
        try:
            debug("\n------------ ThreadCompleter -----------------")
            debug("Kwargs content :")
            for i, j in list(kwargs.items()):
                debug("key : " + str(i))
                debug("\t - " + str(j))
            debug("\n------------ ThreadCompleter -----------------\n")
            args = kwargs.get('parsed_args')
            thread_cmd = ThreadMembersListCommand(self.config)
            return thread_cmd.complete_threads(args, prefix)
        # pylint: disable=broad-except
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")


class ThreadMembersCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "userMail"
    RESOURCE_IDENTIFIER = "userUuid"
    DEFAULT_SORT = "userMail"

    MSG_RS_CREATED = (
        "The thread member '%(firstName)s %(lastName)s' "
        "(%(userUuid)s) was successfully created. (%(_time)s s)")

    CFG_DELETE_MODE = 1
    CFG_DELETE_ARG_ATTR = "thread_uuid"

    def init_old_language_key(self):
        """For api <= 2"""
        pass

    def _delete(self, args, cli, uuid, position=None, count=None):
        # pylint: disable=too-many-arguments
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
                return False
            meta['name'] = json_obj.get('name')
            self.pprint(self.MSG_RS_DELETED, meta)
            return True
        except urllib.error.HTTPError as ex:
            self.log.error("Delete error : %s", ex)
            return False

    def complete(self, args, prefix):
        super(ThreadMembersCommand, self).__call__(args)
        # from argcomplete import debug
        # debug("\n------------ test -----------------")
        json_obj = self.ls.thread_members.list(args.thread_uuid)
        return (
            v.get('userUuid') for v in json_obj if v.get(
                'userUuid'
            ).startswith(prefix))

    def complete_threads(self, args, prefix):
        """TODO"""
        super(ThreadMembersCommand, self).__call__(args)
        json_obj = self.ls.threads.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))

    def complete_mail(self, args, prefix):
        """TODO"""
         # pylint: disable=unused-argument
        super(ThreadMembersCommand, self).__call__(args)
        from argcomplete import warn
        if len(prefix) >= 3:
            json_obj = self.ls.users.list()
            return (v.get('mail')
                    for v in json_obj if v.get('mail').startswith(prefix))
        warn("---------------------------------------")
        warn("Completion need at least 3 characters.")
        warn("---------------------------------------")
        return None

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


class ThreadMembersListCommand(ThreadMembersCommand):
    """ List all thread members."""

    @Time('linsharecli.tmembers', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadMembersListCommand, self).__call__(args)
        endpoint = self.ls.thread_members
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True)
        )
        return tbu.build().load_v2(endpoint.list(args.thread_uuid)).render()

    def complete_fields(self, args, prefix):
        """TODO"""
         # pylint: disable=unused-argument
        super(ThreadMembersListCommand, self).__call__(args)
        cli = self.ls.thread_members
        return cli.get_rbu().get_keys(True)


class ThreadMembersCreateCommand(ThreadMembersCommand):
    """Add a new member to a thread/workgroup"""

    @Time('linsharecli.tmembers', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadMembersCreateCommand, self).__call__(args)
        if self.api_version < 2:
            self.init_old_language_key()
        act = CreateAction(self, self.ls.thread_members)
        act.add_hook("userMail", self.hook_user_mail)
        return act.load(args).execute()

    def hook_user_mail(self, user_mail, context):
        """Looking for user's domain with input email"""
        user = self.ls.users.get(user_mail)
        if not user:
            self.log.error("Can not find an user using this email: %s",
                           user_mail)
            raise ValueError("User does not exists : " + str(user_mail))
        if self.debug:
            self.pretty_json(user)
        context.set_value('userDomainId', user.get('domain'))
        return user_mail


class ThreadMembersUpdateCommand(ThreadMembersCommand):
    """TODO"""

    def __call__(self, args):
        super(ThreadMembersUpdateCommand, self).__call__(args)
        rbu = self.ls.thread_members.get_rbu()
        rbu.load_from_args(args)
        return self._run(
            self.ls.thread_members.update,
            "The following thread members '%(name)s' was successfully updated",
            args.uuid,
            rbu.to_resource())


class ThreadMembersDeleteCommand(ThreadMembersCommand):
    """TODO"""

    @Time('linsharecli.thread', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadMembersDeleteCommand, self).__call__(args)
        act = DeleteAction(
            mode=self.CFG_DELETE_MODE,
            parent_identifier=self.CFG_DELETE_ARG_ATTR
        )
        act.init(args, self.ls, self.ls.thread_members)
        return act.delete(args.uuids)


def add_parser(subparsers, name, desc, config):
    """TODO"""
    # api_version = config.server.api_version.value
    parser_tmp = subparsers.add_parser(name, help=desc)
    parser_tmp.add_argument(
        '-u',
        '--uuid',
        action="store",
        dest="thread_uuid",
        help="thread uuid",
        required=True).completer = ThreadCompleter(config)

    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list thread members")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(
        parser,
        delete=False,
        cdate=True
    )
    parser.set_defaults(__func__=ThreadMembersListCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete thread members")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=ThreadMembersDeleteCommand(config))

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create thread member.")
    parser.add_argument(
        '--mail',
        dest="user_mail",
        required=True,
        help="").completer = Completer('complete_mail')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--admin', action="store_true", help="")
    group.add_argument('--readonly', action="store_true", help="")
    parser.add_argument('--cli-mode', action="store_true", help="")
    parser.set_defaults(__func__=ThreadMembersCreateCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update thread.")
    parser.add_argument(
        'userUuid', action="store", help="").completer = Completer()
    parser.add_argument('role', choices=["admin", "normal", "restricted"],
                        help="")
    parser.set_defaults(__func__=ThreadMembersUpdateCommand(config))
