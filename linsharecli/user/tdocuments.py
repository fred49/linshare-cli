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
from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import SizeFormatter
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import add_download_parser_options
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
            thread_cmd = ThreadDocumentsListCommand()
            return thread_cmd.complete_threads(args, prefix)
        # pylint: disable-msg=W0703
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")


# -----------------------------------------------------------------------------
class ThreadMembersCommand(DefaultCommand):

    DEFAULT_TOTAL = "Documents found : %(count)s"
    MSG_RS_NOT_FOUND = "No documents could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The document '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The document '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s document(s) can not be deleted."
    MSG_RS_DOWNLOADED = "%(position)s/%(count)s: The document '%(name)s' (%(uuid)s) was downloaded. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One document can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%(count)s documents can not be downloaded."

    ACTIONS = {
        'delete' : '_delete_all',
        'download' : '_download_all',
        'count_only' : '_count_only',
    }

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

    def _download(self, args, cli, uuid, position=None, count=None):
        directory = getattr(args, "directory", None)
        if directory:
            if not os.path.isdir(directory):
                os.makedirs(directory)
        meta = {}
        meta['uuid'] = uuid
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        try:
            if getattr(args, "dry_run", False):
                json_obj = cli.get(uuid)
                meta['name'] = json_obj.get('name')
            else:
                file_name, req_time = cli.download(args.thread_uuid, uuid, directory)
                meta['name'] = file_name
                meta['time'] = req_time
            self.pprint(self.MSG_RS_DOWNLOADED, meta)
            return 0
        except urllib2.HTTPError as ex:
            meta['code'] = ex.code
            meta['ex'] = str(ex)
            if ex.code == 404:
                self.pprint_error("http error : %(ex)s", meta)
                self.pprint_error("Can not download the missing document : %(uuid)s", meta)
            return 1

    def _delete(self, args, cli, uuid, position=None, count=None):
        try:
            meta = {}
            meta['uuid'] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            if getattr(args, "dry_run", False):
                json_obj = cli.get(uuid)
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


# -----------------------------------------------------------------------------
class ThreadDocumentsUploadCommand(ThreadMembersCommand):
    """ Upload a file to LinShare using its rest api. return the uploaded
    document uuid  """

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadDocumentsUploadCommand, self).__call__(args)
        count = len(args.files)
        position = 0
        for file_path in args.files:
            position += 1
            json_obj = self.ls.thread_entries.upload(args.thread_uuid, file_path, args.description)
            if json_obj:
                json_obj['time'] = self.ls.last_req_time
                json_obj['position'] = position
                json_obj['count'] = count
                self.log.info(
                    "%(position)s/%(count)s: The file '%(name)s' (%(uuid)s) was uploaded. (%(time)ss)",
                    json_obj)
        return True


# -----------------------------------------------------------------------------
class ThreadDocumentsListCommand(ThreadMembersCommand):
    """ List all thread members."""

    @Time('linsharecli.tdocument', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadDocumentsListCommand, self).__call__(args)
        cli = self.ls.thread_entries
        table = self.get_table(args, cli, self.IDENTIFIER)
        json_obj = cli.list(args.thread_uuid)
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.names, True),
                 PartialDate("creationDate", args.cdate)]
        # Formatters
        formatters = [DateFormatter('creationDate'),
                    SizeFormatter('size'),
                    DateFormatter('modificationDate')]
        return self._list(args, cli, table, json_obj, formatters, filters)


# -----------------------------------------------------------------------------
class ThreadDocumentsDownloadCommand(ThreadDocumentsListCommand):

    @Time('linsharecli.tdocument', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadDocumentsDownloadCommand, self).__call__(args)
        cli = self.ls.thread_entries
        return self._download_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
class ThreadDocumentsDeleteCommand(ThreadDocumentsListCommand):

    @Time('linsharecli.tdocument', label='Global time : %(time)s')
    def __call__(self, args):
        super(ThreadDocumentsDeleteCommand, self).__call__(args)
        cli = self.ls.thread_entries
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
        help="list documents from linshare")
    parser.add_argument(
        'names', nargs="*",
        help="Filter documents by their names")
    add_list_parser_options(
        parser, download=True, delete=True, cdate=True)[3]
    parser.set_defaults(__func__=ThreadDocumentsListCommand())

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete thread members")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=ThreadDocumentsListCommand())

    # command : download
    parser = subparsers2.add_parser(
        'download',
        help="download documents from linshare")
    add_download_parser_options(parser)
    parser.set_defaults(__func__=ThreadDocumentsDownloadCommand())

    # command : upload
    parser = subparsers2.add_parser(
        'upload',
        help="upload documents to linshare")
    parser.add_argument('--desc', action="store", dest="description",
                        required=False, help="Optional description.")
    parser.add_argument('files', nargs='+')
    parser.set_defaults(__func__=ThreadDocumentsUploadCommand())

