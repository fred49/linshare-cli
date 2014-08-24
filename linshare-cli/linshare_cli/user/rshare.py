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
from linshare_cli.user.core import DefaultCommand
from argtoolbox import DefaultCompleter


# -----------------------------------------------------------------------------
class ReceivedSharesListCommand(DefaultCommand):

    def __call__(self, args):
        super(ReceivedSharesListCommand, self).__call__(args)

        json_obj = self.ls.rshares.list()
        d_format = "{name:60s}{creationDate:30s}{uuid:30s}"
        self.format_date(json_obj, 'creationDate')
        self.print_list(json_obj, d_format, "Received Shares")


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
    parser_tmp2.set_defaults(__func__=ReceivedSharesListCommand())
