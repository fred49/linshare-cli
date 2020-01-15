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
# Copyright 2019 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



import getpass
import time
import urllib.request, urllib.error, urllib.parse
import os

from argparse import ArgumentError
from linshareapi.cache import Time
from linshareapi.core import LinShareException
from argtoolbox import DefaultCompleter as Completer
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_list_parser_options_format
from linsharecli.common.tables import TableBuilder


class AuthenticationCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "mail"
    DEFAULT_SORT = "mail"
    RESOURCE_IDENTIFIER = "uuid"

    # pylint: disable=unused-argument
    def complete_fields(self, args, prefix):
        """TODO"""
        super(AuthenticationCommand, self).__call__(args)
        cli = self.ls.authentication
        return cli.get_rbu().get_keys(True)


class AuthenticationListCommand(AuthenticationCommand):
    """ List all Jwt token."""

    @Time('linsharecli.jwt', label='Global time : %(time)s')
    def __call__(self, args):
        super(AuthenticationListCommand, self).__call__(args)
        endpoint = self.ls.authentication
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        return tbu.build().load_v2(endpoint.list()).render()


class ChangePasswordCommand(AuthenticationCommand):
    """Update password for local users only."""

    def __init__(self, config):
        super(ChangePasswordCommand, self).__init__(config)
        self.enable_auth = False
        self.protected_args.append("new_password")

    @Time('linsharecli.jwt', label='Global time : %(time)s')
    def __call__(self, args):
        # pylint: disable=too-many-return-statements
        super(ChangePasswordCommand, self).__call__(args)
        if args.ask_new_password:
            try:
                args.new_password = getpass.getpass("Please enter your password:")
                new_password = getpass.getpass("Please confirm your password:")
                if args.new_password != new_password:
                    self.log.error("The provided passwords do not match!")
                    return False
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt exception was caught.")
                print("Program terminated.")
                return False
        if args.new_password_from_env:
            args.new_password = os.getenv(args.new_password_from_env.upper())
        if not args.new_password:
            msg = "You must provide a new password, see -h for help."
            raise ArgumentError(None, msg)
        # creating a new cli instance with new password.
        if not self.ls.auth(quiet=True):
            self.log.warn("Current password is not valid.")
            self.log.info("Trying to authenticate with the new provided password")
            auth_handler = urllib.request.HTTPBasicAuthHandler()
            try:
                auth_handler.add_password(
                    realm="Name Of Your LinShare Realm",
                    uri=self.ls.host.encode('utf8'),
                    user=self.ls.user.encode('utf8'),
                    passwd=args.new_password.encode('utf8'))
            except UnicodeEncodeError:
                self.log.error(
                    "the program was not able to compute "
                    + "the basic authentication token.")
                return False
            urllib.request.install_opener(urllib.request.build_opener(auth_handler))
            if self.ls.auth(quiet=True):
                self.log.info("New password is already defined.")
                return True
            self.log.error("Can't update the current password.")
            return False
        else:
            self.log.info("Current password is valid.")
            if args.password == args.new_password:
                self.log.info("Current password and new password are the same.")
                return True
            self.log.info("Updating password...")
            cli = self.ls.authentication
            rbu = cli.get_rbu_update()
            rbu.set_value('oldPwd', args.password)
            rbu.set_value('newPwd', args.new_password)
            rbu.check_required_fields()
            data = rbu.to_resource()
            return self.update_password(cli, data)

    def update_password(self, cli, data):
        """TODO"""
        try:
            start = time.time()
            if self.debug >= 2:
                self.pretty_json(data)
            res = cli.update(data)
            end = time.time()
            json_obj = {}
            json_obj['_time'] = end - start
            if res:
                msg = "The password was successfully updated."
                self.pprint(msg, json_obj)
                return True
            msg = "The password was not updated."
            self.pprint(msg, json_obj)
            return False
        except LinShareException as ex:
            self.log.debug("LinShareException : " + str(ex.args))
            self.log.error(ex.args[1])
        return False


def add_parser(subparsers, name, desc, config):
    """TODO"""
    parser = subparsers.add_parser(name, help=desc)
    subparsers2 = parser.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'me', help="Display my account")
    filter_group = parser.add_argument_group('Filters')
    filter_group.add_argument(
        '-k', '--field', action='append', dest="fields"
        ).completer = Completer("complete_fields")
    add_list_parser_options_format(parser)
    parser.set_defaults(__func__=AuthenticationListCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update my password (local users only).")
    password_group = parser.add_argument_group('Password')
    group = password_group.add_mutually_exclusive_group(required=True)
    group.add_argument('-n', '--new-password')
    group.add_argument('-a', '--ask-new-password', action="store_true")
    group.add_argument(
        '-e',
        '--new-password-from-env',
        action="store",
        help="If set, the program will load your password from this environement variable.")
    parser.set_defaults(__func__=ChangePasswordCommand(config))
