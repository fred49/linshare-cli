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



from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import add_download_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.tables import DownloadAction
from linsharecli.common.tables import DeleteAction
from linsharecli.common.tables import TableBuilder

class ReceivedSharesCommand(DefaultCommand):
    """ List all received shares"""

    def complete(self, args, prefix):
        super(ReceivedSharesCommand, self).__call__(args)
        json_obj = self.ls.rshares.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


class ReceivedSharesListCommand(ReceivedSharesCommand):
    """TODO"""

    @Time('linsharecli.rshares', label='Global time : %(time)s')
    def __call__(self, args):
        super(ReceivedSharesListCommand, self).__call__(args)
        endpoint = self.ls.rshares
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.names, True),
            PartialDate("creationDate", args.cdate)
        )
        return tbu.build().load_v2(endpoint.list()).render()


    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(ReceivedSharesListCommand, self).__call__(args)
        cli = self.ls.rshares
        return cli.get_rbu().get_keys(True)


class ReceivedSharesDownloadCommand(ReceivedSharesCommand):
    """TODO"""

    @Time('linsharecli.rshares', label='Global time : %(time)s')
    def __call__(self, args):
        super(ReceivedSharesDownloadCommand, self).__call__(args)
        act = DownloadAction()
        act.init(args, self.ls, self.ls.rshares)
        return act.download(args.uuids)


class ReceivedSharesDeleteCommand(ReceivedSharesCommand):
    """TODO"""

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(ReceivedSharesDeleteCommand, self).__call__(args)
        act = DeleteAction()
        act.init(args, self.ls, self.ls.rshares)
        return act.delete(args.uuids)


def add_parser(subparsers, name, desc, config):
    """TODO"""
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()

    # command : download
    parser = subparsers2.add_parser(
        'download',
        help="download received shares")
    add_download_parser_options(parser)
    parser.set_defaults(__func__=ReceivedSharesDownloadCommand(config))

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list received shares")
    parser.add_argument('names', nargs="*", help="")
    add_list_parser_options(parser, download=True, delete=True, cdate=True)
    parser.set_defaults(__func__=ReceivedSharesListCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete received shares")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=ReceivedSharesDeleteCommand(config))
