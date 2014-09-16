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
from argtoolbox import DefaultCompleter
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import SizeFormatter
from operator import itemgetter


# -----------------------------------------------------------------------------
class ReceivedSharesListCommand(DefaultCommand):
    IDENTIFIER = "name"

    def __call__(self, args):
        super(ReceivedSharesListCommand, self).__call__(args)
        cli = self.ls.rshares
        table = self.get_table(args, cli, self.IDENTIFIER)
        # No default sort.
        table.sortby = None
        json_obj = cli.list()
        # sort by size
        if args.sort_size:
            json_obj = sorted(json_obj, reverse=args.reverse,
                              key=itemgetter("size"))
        elif args.sort_name:
            table.sortby = "name"
        else:
            table.sortby = "creationDate"
        table.show_table(
            json_obj,
            filters=[PartialOr(self.IDENTIFIER, args.names, True),
                     PartialDate("creationDate", args.cdate)],
            formatters=[DateFormatter('creationDate'),
                        DateFormatter('expirationDate'),
                        SizeFormatter('size'),
                        DateFormatter('modificationDate')]
        )
        return True


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

    parser_tmp2 = subparsers2.add_parser(
        'download',
        help="download received shares from linshare")
    parser_tmp2.set_defaults(__func__=ReceivedSharesDownloadCommand())
    parser_tmp2.add_argument(
        'uuids',
        nargs='+',
        help="share's uuids you want to download."
        ).completer = DefaultCompleter()

    parser_tmp2 = subparsers2.add_parser(
        'list',
        help="list received shares from linshare")
    parser_tmp2.add_argument('--csv', action="store_true", help="Csv output")
    parser_tmp2.add_argument('--raw', action="store_true",
                             help="Disable all formatters")
    parser_tmp2.set_defaults(__func__=ReceivedSharesListCommand())
    parser_tmp2.add_argument('names', nargs="*", help="")
    parser_tmp2.add_argument('--date', action="store", dest="cdate")
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.add_argument('--sort-name', action="store_true",
                             help="sort by file name")
    parser_tmp2.add_argument('--sort-size', action="store_true",
                             help="sort by file size")
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting")
    parser_tmp2.add_argument('-t', '--vertical', action="store_true",
                             help="use vertical output mode")
