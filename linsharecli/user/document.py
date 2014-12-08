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

import re

from linshareapi.cache import Time
from linsharecli.user.core import DefaultCommand
from linsharecli.user.core import add_list_parser_options
from linsharecli.user.core import add_delete_parser_options
from linsharecli.user.core import add_download_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import SizeFormatter
from argparse import RawTextHelpFormatter
from argtoolbox import DefaultCompleter as Completer


# -----------------------------------------------------------------------------
class DocumentsCommand(DefaultCommand):
    """ List all documents store into LinShare."""

    DEFAULT_TOTAL = "Documents found : %s"
    MSG_RS_NOT_FOUND = "No documents could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The document '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The document '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%s document(s) can not be deleted."
    MSG_RS_DOWNLOADED = "%(position)s/%(count)s: The document '%(name)s' (%(uuid)s) was downloaded. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One document can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%s documents can not be downloaded."

    def complete(self, args, prefix):
        super(DocumentsCommand, self).__call__(args)
        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


# -----------------------------------------------------------------------------
class DocumentsListCommand(DocumentsCommand):
    """ List all documents store into LinShare."""

    @Time('linsharecli.document', label='Global time : %s')
    def __call__(self, args):
        super(DocumentsListCommand, self).__call__(args)
        cli = self.ls.documents
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

    def _create_all(self, args, cli, uuids):
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            res += self._create(args, cli, uuid, position, count)
        if res > 0:
            self.log.warn("some file (%s) have not been shared.", res)

    def _create(self, args, cli, uuid, position=None, count=None):
        if args.mails is not None:
            for mail in args.mails:
                code, msg, req_time = self.ls.shares.share(uuid, mail)
                if code == 204:
                    self.log.info(
                        "The document '" + uuid +
                        "' was successfully shared with " + mail +
                        " ( " + req_time + "s)")
                else:
                    self.log.warn("Trying to share document '" +
                                  uuid + "' with " + mail)
                    self.log.error("Unexpected return code : " +
                                   str(code) + " : " + msg)
        return 0

    def complete_mail(self, args, prefix):
        super(DocumentsListCommand, self).__call__(args)
        from argcomplete import warn
        if len(prefix) >= 3:
            json_obj = self.ls.users.list()
            return (v.get('mail')
                    for v in json_obj if v.get('mail').startswith(prefix))
        else:
            warn("Completion need at least 3 characters.")


# -----------------------------------------------------------------------------
class DocumentsUploadCommand(DefaultCommand):
    """ Upload a file to LinShare using its rest api. return the uploaded
    document uuid  """

    @Time('linsharecli.document', label='Global time : %s')
    def __call__(self, args):
        super(DocumentsUploadCommand, self).__call__(args)
        count = len(args.files)
        position = 0
        for file_path in args.files:
            position += 1
            json_obj = self.ls.documents.upload(file_path, args.description)
            if json_obj:
                json_obj['time'] = self.ls.last_req_time
                json_obj['position'] = position
                json_obj['count'] = count
                self.log.info(
                    "%(position)s/%(count)s: The file '%(name)s' (%(uuid)s) was uploaded. (%(time)ss)",
                    json_obj)


# -----------------------------------------------------------------------------
class DocumentsDownloadCommand(DocumentsCommand):

    @Time('linsharecli.document', label='Global time : %s')
    def __call__(self, args):
        super(DocumentsDownloadCommand, self).__call__(args)
        cli = self.ls.documents
        self._download_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
class DocumentsDeleteCommand(DocumentsCommand):

    @Time('linsharecli.document', label='Global time : %s')
    def __call__(self, args):
        super(DocumentsDeleteCommand, self).__call__(args)
        cli = self.ls.documents
        self._delete_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
class DocumentsUploadAndSharingCommand(DefaultCommand):

    @Time('linsharecli.document', label='Global time : %s')
    def __call__(self, args):
        super(DocumentsUploadAndSharingCommand, self).__call__(args)
        for file_path in args.files:
            json_obj = self.ls.documents.upload(file_path)
            uuid = json_obj.get('uuid')
            json_obj['time'] = self.ls.last_req_time
            self.log.info(
                "The file '%(name)s' (%(uuid)s) was uploaded. (%(time)ss)",
                json_obj)
            for mail in args.mails:
                code, msg, req_time = self.ls.shares.share(uuid, mail)
                if code == 204:
                    self.log.info(
                        "The document '" + uuid +
                        "' was successfully shared with " + mail +
                        " ( " + req_time + "s)")
                else:
                    self.log.warn("Trying to share document '" +
                                  uuid + "' with " + mail)
                    self.log.error("Unexpected return code : " +
                                   str(code) + " : " + msg)

    def complete(self, args, prefix):
        super(DocumentsUploadAndSharingCommand, self).__call__(args)
        from argcomplete import warn
        if len(prefix) >= 3:
            json_obj = self.ls.users.list()
            return (v.get('mail')
                    for v in json_obj if v.get('mail').startswith(prefix))
        else:
            warn("Completion need at least 3 characters.")

    def complete2(self, args, prefix):
        super(DocumentsUploadAndSharingCommand, self).__call__(args)
        from argcomplete import warn
        if len(prefix) >= 3:
            json_obj = self.ls.users.list()
            guesses = []
            mails = []
            cpt = 0
            for user in json_obj:
                mail = user.get('mail')
                if re.match(".*" + prefix + ".*", mail):
                    guesses.append(mail)
                if mail.startswith(prefix):
                    cpt += 1
                    mails.append(mail)
                if cpt >= 5:
                    break
            if mails:
                return mails
            else:
                cpt = 0
                warning = ["Some results :"]
                for i in guesses:
                    cpt += 1
                    warning.append(" * " + i + "\n")
                    if cpt >= 4:
                        break
                warn("".join(warning))
                return guesses
        else:
            warn("Completion need at least 3 characters.")


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc):
    """This method adds to the input subparser, all parsers for document
    methods"""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : upload
    parser = subparsers2.add_parser(
        'upload',
        help="upload documents to linshare")
    parser.add_argument('--desc', action="store", dest="description",
                        required=False, help="Optional description.")
    parser.add_argument('files', nargs='+')
    parser.set_defaults(__func__=DocumentsUploadCommand())

    # command : upshare
    parser = subparsers2.add_parser(
        'upshare',
         help="upload and share documents")
    parser.add_argument('files', nargs='+')
    parser.add_argument(
        '-m',
        '--mail',
        action="append",
        dest="mails",
        required=True,
        help="Recipient mails."
        ).completer = Completer()
    parser.set_defaults(__func__=DocumentsUploadAndSharingCommand())

    # command : download
    parser = subparsers2.add_parser(
        'download',
        help="download documents from linshare")
    add_download_parser_options(parser)
    parser.set_defaults(__func__=DocumentsDownloadCommand())

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete documents from linshare")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=DocumentsDeleteCommand())

    # command : list
    parser = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list documents from linshare")
    parser.add_argument(
        'names', nargs="*",
        help="Filter documents by their names")
    parser.add_argument(
        '-m',
        '--mail',
        action="append",
        dest="mails",
        # required=True,
        help="Recipient mails."
        ).completer = Completer("complete_mail")
    parser.add_argument('--share', action="store_true", dest="create")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=DocumentsListCommand())
