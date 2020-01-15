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
# Copyright 2018 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



from linshareapi.cache import Time
from argtoolbox import DefaultCompleter as Completer
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import hook_file_content
from linsharecli.common.actions import CreateAction
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.tables import TableBuilder


class PublicKeysCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "issuer"
    DEFAULT_SORT = "issuer"
    RESOURCE_IDENTIFIER = "uuid"

    # pylint: disable=line-too-long
    DEFAULT_TOTAL = "Public keys found : %(count)s"
    MSG_RS_NOT_FOUND = "No public keys could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The public key '%(issuer)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The public key '%(issuer)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s public key(s) can not be deleted."
    MSG_RS_UPDATED = "The public key '%(issuer)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The public key '%(issuer)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    def complete(self, args, prefix):
        super(PublicKeysCommand, self).__call__(args)
        json_obj = self.ls.public_keys.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    # pylint: disable=unused-argument
    def complete_fields(self, args, prefix):
        """TODO"""
        super(PublicKeysCommand, self).__call__(args)
        cli = self.ls.public_keys
        return cli.get_rbu().get_keys(True)

    def complete_domain(self, args, prefix):
        """TODO"""
        super(PublicKeysCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


class PublicKeysListCommand(PublicKeysCommand):
    """ List all public keys."""

    @Time('linsharecli.publickeys', label='Global time : %(time)s')
    def __call__(self, args):
        super(PublicKeysListCommand, self).__call__(args)
        endpoint = self.ls.public_keys
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        return tbu.build().load_v2(endpoint.list()).render()


class PublicKeysCreateCommand(PublicKeysCommand):
    """Create public key."""

    def __call__(self, args):
        super(PublicKeysCreateCommand, self).__call__(args)
        act = CreateAction(self, self.ls.public_keys)
        act.add_hook("publicKey", hook_file_content)
        return act.load(args).execute()


class PublicKeyDeleteCommand(PublicKeysCommand):
    """Delete public key."""

    def __call__(self, args):
        super(PublicKeyDeleteCommand, self).__call__(args)
        cli = self.ls.public_keys
        return self._delete_all(args, cli, args.uuids)


def add_parser(subparsers, name, desc, config):
    """Add all public key sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list public key.")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser, delete=True, cdate=False)
    parser.add_argument('--domain',
                       ).completer = Completer("complete_domain")
    parser.set_defaults(__func__=PublicKeysListCommand(config))

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete public key.")
    add_delete_parser_options(parser_tmp2)
    parser_tmp2.set_defaults(__func__=PublicKeyDeleteCommand(config))

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create public key.")
    parser_tmp2.add_argument('issuer')
    parser_tmp2.add_argument('-f', '--format', choices=['PEM', 'RSA'],
                             default="PEM", dest="format")
    parser_tmp2.add_argument('--key', action="store",
                             required=True)
    parser_tmp2.add_argument('--cli-mode', action="store_true", help="")
    parser_tmp2.add_argument('--domain', default="LinShareRootDomain"
                            ).completer = Completer("complete_domain")
    parser_tmp2.set_defaults(__func__=PublicKeysCreateCommand(config))
