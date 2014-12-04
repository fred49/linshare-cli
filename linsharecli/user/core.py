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

import os
import urllib2
import linsharecli.common.core as common
from linshareapi.user import UserCli
import argtoolbox
from operator import itemgetter


# pylint: disable=C0111
# Missing docstring
# -----------------------------------------------------------------------------
class DefaultCommand(common.DefaultCommand):
    """ Default command object use by the ser API. If you want to add a new
    command to the command line interface, your class should extend this one.
    """

    DEFAULT_SORT = "creationDate"
    DEFAULT_SORT_SIZE = "size"
    DEFAULT_TOTAL = "Ressources found : %s"
    DEFAULT_SORT_NAME = "name"
    RESOURCE_IDENTIFIER = "uuid"
    MSG_RS_NOT_FOUND = "No resources could be found."
    MSG_RS_DELETED = "The resource '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The resource '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%s resource(s) can not be deleted."
    MSG_RS_DOWNLOADED = "The resource '%(name)s' (%(uuid)s) was downloaded. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One resource can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%s resources can not be downloaded."

    def __get_cli_object(self, args):
        cli = UserCli(args.host, args.user, args.password, args.verbose,
                        args.debug)
        if args.base_url:
            cli.base_url = args.base_url
        return cli

    def _list(self, args, cli, table, json_obj, formatters=None, filters=None):
        # No default sort.
        table.sortby = None
        # sort by size
        if getattr(args, 'sort_size', False):
            json_obj = sorted(json_obj, reverse=args.reverse,
                              key=itemgetter(self.DEFAULT_SORT_SIZE))
        if getattr(args, 'sort_name', False):
            table.sortby = self.DEFAULT_SORT_NAME
        else:
            table.sortby = self.DEFAULT_SORT
        _delete = getattr(args, 'delete', False)
        _download = getattr(args, 'download', False)
        _count_only = getattr(args, 'count_only', False)
        if _delete or _download or _count_only:
            table.load(json_obj, filters, formatters)
            rows = table.get_raw()
            if _count_only:
                self.log.info(self.DEFAULT_TOTAL, len(rows))
                return True
            if len(rows) == 0:
                self.log.warn(self.MSG_RS_NOT_FOUND)
                return True
            uuids = [row.get(self.RESOURCE_IDENTIFIER) for row in rows]
            if _download:
                self._download_all(args, cli, uuids)
            else:
                self._delete_all(args, cli, uuids)
            self.log.info(self.DEFAULT_TOTAL, len(rows))
        else:
            table.show_table(json_obj, filters, formatters)
            self.log.info(self.DEFAULT_TOTAL, len(table.get_raw()))
        return True

    def _download_all(self, args, cli, uuids):
        res = 0
        for uuid in uuids:
            res += self._download(args, cli, uuid)
        if res > 0:
            self.log.warn(self.MSG_RS_CAN_NOT_BE_DOWNLOADED_M, res)

    def _download(self, args, cli, uuid):
        directory = getattr(args, "directory", None)
        if directory:
            if not os.path.isdir(directory):
                os.makedirs(directory)
        try:
            meta = {}
            meta['uuid'] = uuid
            meta['time'] = " -"
            if getattr(args, "dry_run", False):
                json_obj = cli.get(uuid)
                meta['name'] = json_obj.get('name')
            else:
                file_name, req_time = cli.download(uuid, directory)
                meta['name'] = file_name
                meta['time'] = req_time
            self.log.info(self.MSG_RS_DOWNLOADED, meta)
            return 0
        except urllib2.HTTPError as ex:
            self.log.error("Download error : %s", ex)
            return 1

    def _delete_all(self, args, cli, uuids):
        res = 0
        for uuid in uuids:
            res += self._delete(args, cli, uuid)
        if res > 0:
            self.log.warn(self.MSG_RS_CAN_NOT_BE_DELETED_M, res)

    def _delete(self, args, cli, uuid):
        try:
            meta = {}
            meta['uuid'] = uuid
            meta['time'] = " -"
            if getattr(args, "dry_run", False):
                json_obj = cli.get(uuid)
            else:
                json_obj = cli.delete(uuid)
                meta['time'] = self.ls.last_req_time
            if not json_obj:
                self.log.warn(self.MSG_RS_CAN_NOT_BE_DELETED, {'uuid': uuid})
                return 1
            meta['name'] = json_obj.get('name')
            self.log.info(self.MSG_RS_DELETED, meta)
            return 0
        except urllib2.HTTPError as ex:
            self.log.error("Delete error : %s", ex)
            return 1


# -----------------------------------------------------------------------------
class TestCommand(argtoolbox.DefaultCommand):
    """Just for test. Print test to stdout"""

    def __init__(self, config=None):
        super(TestCommand, self).__init__(config)
        self.verbose = False
        self.debug = False

    def __call__(self, args):
        self.verbose = args.verbose
        self.debug = args.debug
        print "Test"
        print unicode(self.config)
        print args
        print ""


# -----------------------------------------------------------------------------
class ListConfigCommand(DefaultCommand):
    """"""

    def __init__(self, config=None):
        super(ListConfigCommand, self).__init__(config)
        self.verbose = False
        self.debug = False

    def __call__(self, args):
        self.verbose = args.verbose
        self.debug = args.debug
        seclist = self.config.file_parser.sections()
        print
        print "Available sections:"
        print "==================="
        print
        for i in seclist:
            if i.startswith("server-"):
                print " - " + "-".join(i.split('-')[1:])
        print ""


# -----------------------------------------------------------------------------
def add_parser(subparsers, config):
    parser_tmp = subparsers.add_parser('test', add_help=False)
    parser_tmp.add_argument('files', nargs='*')
    parser_tmp.set_defaults(__func__=TestCommand(config))
    parser_tmp = subparsers.add_parser('list')
    parser_tmp.set_defaults(__func__=ListConfigCommand(config))
