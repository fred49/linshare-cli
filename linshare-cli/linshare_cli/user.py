#! /usr/bin/env python
# -*- coding: utf-8 -*-


# This file is part of Linshare user cli.
#
# LinShare user cli is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LinShare user cli is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LinShare user cli.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2013 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

from __future__ import unicode_literals

import urllib2
import linshare_cli.common as common
from linshare_api.core import UserCli
from linshare_cli.common import VTable
from linshare_cli.common import HTable
from argtoolbox import DefaultCompleter
import argtoolbox
from argparse import RawTextHelpFormatter
from operator import itemgetter


# -----------------------------------------------------------------------------
class DefaultCommand(common.DefaultCommand):
    """ Default command object use by the ser API. If you want to add a new
    command to the command line interface, your class should extend this one.
    """

    def __get_cli_object(self, args):
        cli = UserCli(args.host, args.user, args.password, args.verbose,
                        args.debug)
        if args.base_url:
            cli.base_url = args.base_url
        return cli


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


# -------------------------- Documents ----------------------------------------
# -----------------------------------------------------------------------------
class DocumentsListCommand(DefaultCommand):
    """ List all documents store into LinShare."""

    def __call__(self, args):
        super(DocumentsListCommand, self).__call__(args)

        json_obj = self.ls.documents.list()

        keys = []
        keys.append('name')
        keys.append('size')
        keys.append('uuid')
        keys.append('creationDate')

        if args.extended:
            keys.append('type')
            keys.append('expirationDate')
            keys.append('modificationDate')
            keys.append('description')
            keys.append('ciphered')

        self.format_date(json_obj, 'creationDate')
        self.format_filesize(json_obj, 'size')
        self.format_date(json_obj, 'modificationDate')
        self.format_date(json_obj, 'expirationDate')

        table = None
        if args.vertical:
            table = VTable(keys)
        else:
            table = HTable(keys)
            # styles
            table.align["identifier"] = "l"
            table.padding_width = 1

        if args.size:
            json_obj = sorted(json_obj, reverse=args.reverse,
                              key=itemgetter("size_raw"))
        else:
            table.sortby = "creationDate"
        table.reversesort = args.reverse
        if args.name:
            table.sortby = "name"

        table.print_table(json_obj, keys)


# -----------------------------------------------------------------------------
class DocumentsUploadCommand(DefaultCommand):
    """ Upload a file to LinShare using its rest api. return the uploaded
    document uuid  """

    def __call__(self, args):
        super(DocumentsUploadCommand, self).__call__(args)

        for file_path in args.files:
            json_obj = self.ls.documents.upload(file_path, args.description)
            if json_obj:
                json_obj['time'] = self.ls.last_req_time
                self.log.info(
                    "The file '%(name)s' (%(uuid)s) was uploaded. (%(time)ss)",
                    json_obj)


# -----------------------------------------------------------------------------
class DocumentsDownloadCommand(DefaultCommand):

    def __call__(self, args):
        super(DocumentsDownloadCommand, self).__call__(args)

        for uuid in args.uuids:
            try:
                file_name, req_time = self.ls.documents.download(uuid)
                self.log.info(
                    "The file '" + file_name +
                    "' was downloaded. (" + req_time + "s)")
            except urllib2.HTTPError as ex:
                print "Error : "
                print ex
                return

    def complete(self, args, prefix):
        super(DocumentsDownloadCommand, self).__call__(args)

        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


# -----------------------------------------------------------------------------
class DocumentsDeleteCommand(DefaultCommand):

    def __call__(self, args):
        super(DocumentsDeleteCommand, self).__call__(args)

        for uuid in args.uuids:
            try:
                json_obj = self.ls.documents.delete(uuid)
                file_name = json_obj.get('name')
                self.log.info(
                    "The file '" + file_name +
                    "' (" + uuid + ")" +
                    " was deleted. (" + self.ls.last_req_time + "s)")
            except urllib2.HTTPError as ex:
                print "Error : "
                print ex
                return

    def complete(self, args, prefix):
        super(DocumentsDeleteCommand, self).__call__(args)

        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


# -----------------------------------------------------------------------------
class DocumentsUploadAndSharingCommand(DefaultCommand):

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
            import re
            json_obj = self.ls.users.list()
            guesses = []
            mails = []
            cpt = 0
            for v in json_obj:
                mail = v.get('mail')
                if re.match(".*" + prefix + ".*", mail):
                    guesses.append(mail)
                if mail.startswith(prefix):
                    cpt += 1
                    mails.append(mail)
                if cpt >=5:
                    break
            if mails:
                return mails
            else:
                cpt = 0
                warning = ["Some results :"]
                for i in guesses:
                    cpt += 1
                    warning.append(" * " + i + "\n")
                    if cpt >=4:
                        break
                warn("".join(warning))
                return guesses
        else:
            warn("Completion need at least 3 characters.")


# ----------------- Received Shares -------------------------------------------
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


# -------------------------- Shares -------------------------------------------
# -----------------------------------------------------------------------------
class SharesCommand(DefaultCommand):

    def __call__(self, args):
        super(SharesCommand, self).__call__(args)

        for uuid in args.uuids:
            for mail in args.mails:
                code, msg, req_time = self.ls.shares.share(uuid, mail)

                if code == 204:
                    self.log.info(
                        "The document '" + uuid +
                        "' was successfully shared with " + mail +
                        " ( " + req_time + "s)")
                else:
                    self.log.warn("Trying to share document '" + uuid +
                                  "' with " + mail)
                    self.log.error("Unexpected return code : " + str(code) +
                                   " : " + msg)

    def complete(self, args, prefix):
        super(SharesCommand, self).__call__(args)

        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))

    def complete_mail(self, args, prefix):
        super(SharesCommand, self).__call__(args)

        if len(prefix) >= 3:
            json_obj = self.ls.users.list()
            return (v.get('mail')
                    for v in json_obj if v.get('mail').startswith(prefix))


# -------------------------- Threads ------------------------------------------
# -----------------------------------------------------------------------------
class ThreadsListCommand(DefaultCommand):
    """ List all threads store into LinShare."""

    def __call__(self, args):
        super(ThreadsListCommand, self).__call__(args)

        json_obj = self.ls.threads.list()
        d_format = "{name:60s}{creationDate:30s}{uuid:30s}"
        #self.pretty_json(json_obj)
        self.format_date(json_obj, 'creationDate')
        self.print_list(json_obj, d_format, "Threads")


# -----------------------------------------------------------------------------
class ThreadMembersListCommand(DefaultCommand):
    """ List all thread members store from a thread."""

    def __call__(self, args):
        super(ThreadMembersListCommand, self).__call__(args)

        json_obj = self.ls.thread_members.list(args.uuid)

        d_format = "{firstName:11s}{lastName:10s}{admin:<7}{readonly:<9}{id}"
        #self.pretty_json(json_obj)
        self.print_list(json_obj, d_format, "Thread members")

    def complete(self, args, prefix):
        super(ThreadMembersListCommand, self).__call__(args)

        json_obj = self.ls.threads.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))


# -------------------------- Users --------------------------------------------
# -----------------------------------------------------------------------------
class UsersListCommand(DefaultCommand):
    """ List all users store into LinShare."""

    def __call__(self, args):
        super(UsersListCommand, self).__call__(args)

        json_obj = self.ls.users.list()
        d_format = "{firstName:11s}{lastName:10s}{domain:<20}{mail}"
        #print "%(firstName)-10s %(lastName)-10s\t %(domain)s %(mail)s" % f
        #self.pretty_json(json_obj)
        self.print_list(json_obj, d_format, "Users")


###############################################################################
### documents
###############################################################################
def add_document_parser(subparsers, name, desc):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()

    parser_tmp2 = subparsers2.add_parser('upload',
                                         help="upload documents to linshare")
    parser_tmp2.set_defaults(__func__=DocumentsUploadCommand())
    parser_tmp2.add_argument('--desc', action="store", dest="description",
                             required=False, help="Optional description.")
    parser_tmp2.add_argument('files', nargs='+')

    parser_tmp2 = subparsers2.add_parser('upshare',
                                         help="upload and share documents")
    parser_tmp2.set_defaults(__func__=DocumentsUploadAndSharingCommand())
    parser_tmp2.add_argument('files', nargs='+')
    parser_tmp2.add_argument('-m',
                             '--mail',
                             action="append",
                             dest="mails",
                             required=True,
                             help="Recipient mails."
                             ).completer = DefaultCompleter()


    parser_tmp2 = subparsers2.add_parser(
        'download',
        help="download documents from linshare")
    parser_tmp2.set_defaults(__func__=DocumentsDownloadCommand())
    parser_tmp2.add_argument('uuids', nargs='+').completer = DefaultCompleter()

    parser_tmp2 = subparsers2.add_parser(
        'delete',
        help="delete documents from linshare")
    parser_tmp2.set_defaults(__func__=DocumentsDeleteCommand())
    parser_tmp2.add_argument('uuids', nargs='+').completer = DefaultCompleter()

    parser_tmp2 = subparsers2.add_parser(
        'list',
        formatter_class=RawTextHelpFormatter,
        help="list documents from linshare")
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting")
    parser_tmp2.add_argument('-c', '--creation-date', action="store_true",
                             help="sort by creation date")
    parser_tmp2.add_argument('-n', '--name', action="store_true",
                             help="sort by file name")
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.add_argument('--size', action="store_true",
                             help="sort by file size")
    #parser_tmp2.add_argument('--show-columns', action="store_true",
    #                         help="List all available fields in received data.")
    parser_tmp2.add_argument('-t', '--vertical', action="store_true",
                             help="use vertical output mode")
    parser_tmp2.set_defaults(__func__=DocumentsListCommand())


###############################################################################
### shares
###############################################################################
def add_share_parser(subparsers, name, desc):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()

    parser_tmp2 = subparsers2.add_parser('create',
                                         help="share files into linshare")
    parser_tmp2.set_defaults(__func__=SharesCommand())
    parser_tmp2.add_argument(
        'uuids',
        nargs='+',
        help="document's uuids you want to share."
        ).completer = DefaultCompleter()
    parser_tmp2.add_argument(
        '-m', '--mail', action="append", dest="mails", required=True,
        help="Recipient mails.").completer = DefaultCompleter("complete_mail")


###############################################################################
### received shares
###############################################################################
def add_received_share_parser(subparsers, name, desc):
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


###############################################################################
###  threads
###############################################################################
def add_threads_parser(subparsers, name, desc):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()
    parser_tmp2 = subparsers2.add_parser(
        'list',
        help="list threads from linshare")
    parser_tmp2.set_defaults(__func__=ThreadsListCommand())

    parser_tmp2 = subparsers2.add_parser(
        'listmembers',
        help="list thread members.")
    parser_tmp2.add_argument(
        '-u',
        '--uuid',
        action="store",
        dest="uuid",
        required=True).completer = DefaultCompleter()
    parser_tmp2.set_defaults(__func__=ThreadMembersListCommand())


###############################################################################
###  users
###############################################################################
def add_users_parser(subparsers, name, desc):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()
    parser_tmp2 = subparsers2.add_parser('list',
                                         help="list users from linshare")
    parser_tmp2.set_defaults(__func__=UsersListCommand())


###############################################################################
### test
###############################################################################
def add_test_parser(subparsers, config):
    parser_tmp = subparsers.add_parser('test', add_help=False)
    parser_tmp.add_argument('files', nargs='*')
    parser_tmp.set_defaults(__func__=TestCommand(config))
