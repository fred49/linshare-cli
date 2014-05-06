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

import logging
import urllib2
import copy
import os
import linshare_cli.common as common
from linshare_cli.core import UserCli
from argtoolbox import DefaultCompleter
from argtoolbox import query_yes_no
import argtoolbox


# -----------------------------------------------------------------------------
class DefaultCommand(common.DefaultCommand):
    """ Default command object use by the ser API. If you want to add a new
    command to the command line interface, your class should extend this one.
    """

    def __get_cli_object(self, args):
        return UserCli(args.host, args.user, args.password, args.verbose,
                       args.debug, args.realm, args.application_name)


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


# -----------------------------------------------------------------------------
class ConfigGenerationCommand(object):
    def __init__(self, config):
        self.config = config
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linshare-cli.' + classname)

    def __call__(self, args):
        dict_tmp = copy.copy(args)
        delattr(dict_tmp, "__func__")
        delattr(dict_tmp, "password")
        self.log.debug("Namespace : begin :")
        for i in dict_tmp.__dict__:
            self.log.debug(i + " : " + str(getattr(args, i)))
        self.log.debug("Namespace : end.")

        configfile = os.path.expanduser('~/.' + self.config.prog_name + '.cfg')
        if args.output:
            configfile = args.output

        if not args.force_yes:
            if os.path.exists(configfile):
                self.log.warn(
                    "current file already exists : " + str(configfile))
                if not query_yes_no("overwrite ?", "no"):
                    self.log.error("aborted.")
                    return False
        self.config.write_default_config_file(configfile, args.nocomments)
        print "config file generation complete : " + str(configfile)


# -----------------------------------------------------------------------------
class ConfigAutoCompteCommand(object):
    def __call__(self, args):
        print """
This program is comptible with the python autocomplete program called
argcomplete.\n
This program should already be installed, but in some case, you have to
configure  it :

1. Global configuration
    All programs compliant with argcomplete will be detected automatically
    with bash >= 4.2.
    - sudo activate-global-python-argcomplete

2. Specific configuration
    Manually include the following command ind your ~/.bashrc:
    - eval "$(register-python-argcomplete linsharecli.py)"


"""


# -------------------------- Documents ----------------------------------------
# -----------------------------------------------------------------------------
class DocumentsListCommand(DefaultCommand):
    """ List all documents store into LinShare."""

    def __call__(self, args):
        super(DocumentsListCommand, self).__call__(args)

        json_obj = self.ls.documents.list()
        d_format = u"{name:60s}{creationDate:30s}{uuid:40s}{description}"
        self.format_date(json_obj, 'creationDate')
        from operator import itemgetter
        json_obj = sorted(json_obj, reverse = True, key=itemgetter("creationDate"))
        self.print_list(json_obj, d_format, "Documents")


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

    def complete(self, args,  prefix):
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

    def complete(self, args,  prefix):
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

    def complete(self, args,  prefix):
        super(DocumentsUploadAndSharingCommand, self).__call__(args)

        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


# ----------------- Received Shares -------------------------------------------
# -----------------------------------------------------------------------------
class ReceivedSharesListCommand(DefaultCommand):

    def __call__(self, args):
        super(ReceivedSharesListCommand, self).__call__(args)

        json_obj = self.ls.rshares.list()
        d_format = u"{name:60s}{creationDate:30s}{uuid:30s}"
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

    def complete(self, args,  prefix):
        super(SharesCommand, self).__call__(args)

        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))

    def complete_mail(self, args,  prefix):
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
        d_format = u"{name:60s}{creationDate:30s}{uuid:30s}"
        #self.pretty_json(json_obj)
        self.format_date(json_obj, 'creationDate')
        self.print_list(json_obj, d_format, "Threads")

        #self.print_test(json_obj)


# -----------------------------------------------------------------------------
class ThreadMembersListCommand(DefaultCommand):
    """ List all thread members store from a thread."""

    def __call__(self, args):
        super(ThreadMembersListCommand, self).__call__(args)

        json_obj = self.ls.thread_members.list(args.uuid)

        d_format = u"{firstName:11s}{lastName:10s}{admin:<7}{readonly:<9}{id}"
        #self.pretty_json(json_obj)
        self.print_list(json_obj, d_format, "Thread members")

    def complete(self, args,  prefix):
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
        d_format = u"{firstName:11s}{lastName:10s}{domain:<20}{mail}"
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
    parser_tmp2.add_argument('files', nargs='+').completer = DefaultCompleter()
    parser_tmp2.add_argument('-m', '--mail', action="append", dest="mails",
                             required=True, help="Recipient mails.")


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
        help="list documents from linshare")
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
### config
###############################################################################
def add_config_parser(subparsers, name, desc, config):
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()

    parser_tmp2 = subparsers2.add_parser(
        'generate',
        help="generate the default pref file")
    parser_tmp2.set_defaults(__func__=ConfigGenerationCommand(config))
    parser_tmp2.add_argument('--output', action="store")
    parser_tmp2.add_argument(
        '-n',
        dest="nocomments",
        action="store_false",
        help="config file generation without commments.")
    parser_tmp2.add_argument(
        '-f',
        dest="force_yes",
        action="store_true",
        help="overwrite the current output file even it still exists.")

    parser_tmp2 = subparsers2.add_parser(
        'autocomplete',
        help="Print help to install and configure autocompletion module")
    parser_tmp2.set_defaults(__func__=ConfigAutoCompteCommand())


###############################################################################
### test
###############################################################################
def add_test_parser(subparsers):
    parser_tmp = subparsers.add_parser('test', add_help=False)
    parser_tmp.set_defaults(__func__=TestCommand())
