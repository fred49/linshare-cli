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
from linsharecli.user.core import DefaultCommand
from linsharecli.user.core import add_list_parser_options
from linsharecli.user.core import add_delete_parser_options
from linsharecli.user.core import add_download_parser_options
from argtoolbox import DefaultCompleter
from linshareapi.cache import Time
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import SizeFormatter
from operator import itemgetter


# -----------------------------------------------------------------------------
class ReceivedSharesListCommand(DefaultCommand):

    DEFAULT_TOTAL = "Received shares found : %s"
    MSG_RS_NOT_FOUND = "No received shares could be found."
    MSG_RS_DELETED = "The received share '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The received share '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%s received share(s) can not be deleted."
    MSG_RS_DOWNLOADED = "%(position)s/%(count)s: The received share '%(name)s' (%(uuid)s) was downloaded. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One received share can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%s received shares can not be downloaded."

    @Time('linsharecli.rshares', label='Global time : %s')
    def __call__(self, args):
        super(ReceivedSharesListCommand, self).__call__(args)
        cli = self.ls.rshares
        table = self.get_table(args, cli, self.IDENTIFIER)
        json_obj = cli.list()
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.names, True),
                 PartialDate("creationDate", args.cdate)]
        # Formatters
        formatters = [DateFormatter('creationDate'),
                    DateFormatter('expirationDate'),
                    SizeFormatter('size'),
                    DateFormatter('modificationDate')]
        return self._list(args, cli, table, json_obj, formatters, filters)


# -----------------------------------------------------------------------------
class ReceivedSharesDownloadCommand(DefaultCommand):

    def __call__(self, args):
        super(ReceivedSharesDownloadCommand, self).__call__(args)

        for uuid in args.uuids:
            try:
                file_name, req_time = self.ls.rshares.download(uuid)
                self.log.info(
                    "The share '" + file_name +
                    "' was downloaded. (" + req_time + "s)")
            except urllib2.HTTPError as ex:
                print "Error : "
                print ex
                return

    def complete(self, args, prefix):
        super(ReceivedSharesDownloadCommand, self).__call__(args)

        json_obj = self.ls.rshares.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()

    # command : download
    parser = subparsers2.add_parser(
        'download',
        help="download received shares from linshare")
    add_download_parser_options(parser)
    parser.set_defaults(__func__=ReceivedSharesDownloadCommand())

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list received shares from linshare")
    parser.add_argument('names', nargs="*", help="")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=ReceivedSharesListCommand())
