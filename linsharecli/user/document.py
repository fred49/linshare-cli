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
from linsharecli.user.share import ShareAction
from linshareapi.core import LinShareException
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import add_download_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import SizeFormatter
from argparse import RawTextHelpFormatter
from argparse import ArgumentError
from argtoolbox import DefaultCompleter as Completer


# -----------------------------------------------------------------------------
class DocumentsCommand(DefaultCommand):
    """ List all documents store into LinShare."""

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
        'share' : '_share_all',
        'count_only' : '_count_only',
    }

    def complete(self, args, prefix):
        super(DocumentsCommand, self).__call__(args)
        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


# -----------------------------------------------------------------------------
class DocumentsListCommand(DocumentsCommand):
    """ List all documents store into LinShare."""

    @Time('linsharecli.document', label='Global time : %(time)s')
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

    def _share_all(self, args, cli, uuids):
        if args.api_version == 1:
            if not args.mails:
                raise ValueError("To share files, you need to use -m/--mail option.")
            command = ShareAction(self)
            return command(args, cli, uuids)
        else:
            raise ValueError("Not supported for the current api version : " + str(args.api_version))

    def complete_mail(self, args, prefix):
        super(DocumentsListCommand, self).__call__(args)
        from argcomplete import warn
        if len(prefix) >= 3:
            json_obj = self.ls.users.list()
            return (v.get('mail')
                    for v in json_obj if v.get('mail').startswith(prefix))
        else:
            warn("---------------------------------------")
            warn("Completion need at least 3 characters.")
            warn("---------------------------------------")


# -----------------------------------------------------------------------------
class DocumentsUploadCommand(DefaultCommand):
    """ Upload a file to LinShare using its rest api. return the uploaded
    document uuid  """

    @Time('linsharecli.document', label='Global time : %(time)s')
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
        return True


# -----------------------------------------------------------------------------
class DocumentsDownloadCommand(DocumentsCommand):

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsDownloadCommand, self).__call__(args)
        cli = self.ls.documents
        return self._download_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
class DocumentsDeleteCommand(DocumentsCommand):

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsDeleteCommand, self).__call__(args)
        cli = self.ls.documents
        return self._delete_all(args, cli, args.uuids)


# -----------------------------------------------------------------------------
class DocumentsUpdateCommand(DocumentsCommand):

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsUpdateCommand, self).__call__(args)
        a = ['description', 'meta_data', 'name']
        one_set = False
        for i in a:
            if getattr(args, i, None) is not None:
                one_set = True
                break
        if not one_set:
            raise ArgumentError(None, "You need to choose at least one of the three options : --name or --meta-data or --description")
        cli = self.ls.documents
        try:
            document = cli.get(args.uuid)
            original_name = document.get('name')
            rbu = cli.get_rbu()
            rbu.copy(document)
            rbu.load_from_args(args)
            json_obj = cli.update(rbu.to_resource())
            if json_obj.get('name') == original_name:
                message_ok = "The following document '%(name)s' was successfully updated"
                self.pprint(message_ok, json_obj)
            else:
                json_obj['original_name'] = original_name
                message_ok = "The former document '%(original_name)s' (renamed to '%(name)s') was successfully updated"
                self.pprint(message_ok, json_obj)
            if self.verbose or self.debug:
                self.pretty_json(json_obj)
            return True
        except LinShareException as ex:
            self.pprint_error(ex.args[1] + " : " + args.uuid)
        return False


# -----------------------------------------------------------------------------
class DocumentsUploadAndSharingCommand(DefaultCommand):

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsUploadAndSharingCommand, self).__call__(args)
        if args.api_version == 0:
            return self._upshare_1_7(args)
        elif args.api_version == 1:
            return self._upshare_1_8(args)

    def _upshare_1_8(self, args):
        """Method to share documents. compatible >= 1.8 """
        uuids = []
        for file_path in args.files:
            json_obj = self.ls.documents.upload(file_path)
            uuids.append(json_obj.get('uuid'))
            json_obj['time'] = self.ls.last_req_time
            self.log.info(
                "The file '%(name)s' (%(uuid)s) was uploaded. (%(time)ss)",
                json_obj)
        command = ShareAction(self)
        cli = self.ls.shares
        return command(args, cli, uuids)

    def _upshare_1_7(self, args):
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
        return True

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
def add_parser(subparsers, name, desc, config):
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
    # command : list : share action
    action_parser = add_list_parser_options(
        parser, download=True, delete=True, cdate=True)[3]
    action_parser.add_argument(
        '--share',
        action="store_true",
        dest="share",
        help="You can share all displayed files by the list command.")
    parser.set_defaults(__func__=DocumentsListCommand())
    # command : list : share options
    share_group = parser.add_argument_group('Sharing options')
    share_group.add_argument('--expiration-date', action="store")
    share_group.add_argument('--secured', action="store_true", default=None)
    share_group.add_argument('--no-secured', action="store_false", default=None, dest="secured")
    share_group.add_argument('--message', action="store")
    share_group.add_argument('--subject', action="store")
    share_group.add_argument(
        '-m',
        '--mail',
        action="append",
        dest="mails",
        # required=True,
        help="Recipient (email)."
        ).completer = Completer("complete_mail")

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update document meta data.")
    parser.add_argument('uuid').completer = Completer()
    parser.add_argument('--name', action="store",
                        help="document new name")
    parser.add_argument('--meta-data', action="store",
                        help="document meta data")
    parser.add_argument('--description', action="store",
                        help="document description")
    parser.set_defaults(__func__=DocumentsUpdateCommand())
