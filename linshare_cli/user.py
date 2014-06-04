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

import logging
import urllib2
import copy
import os
import linshare_cli.common as common
from linshare_cli.core import UserCli
from argtoolbox import DefaultCompleter
from argtoolbox import query_yes_no
import argtoolbox
from argparse import RawTextHelpFormatter
from veryprettytable import VeryPrettyTable


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
        print unicode(self.config)
        print args
        print ""


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
        if args.show_columns:
            self.print_fields(json_obj)
            return True

        keys = []
        keys.append(u'name')
        keys.append(u'size')
        keys.append(u'uuid')
        keys.append(u'creationDate')

        if args.extended:
            keys.append(u'type')
            keys.append(u'expirationDate')
            keys.append(u'modificationDate')

        self.format_date(json_obj, 'creationDate')
        self.format_filesize(json_obj, 'size')
        self.format_date(json_obj, 'modificationDate')
        self.format_date(json_obj, 'expirationDate')

        # computing data for presentation
        maxlength = self.getmaxlength(json_obj)
        datatype = self.getdatatype(json_obj)

        # computing string format
        d_format = ""
        if args.output_format:
            d_format = args.output_format
            d_format = d_format.decode('UTF-8')
        else:
            for key in keys:
                d_format += self.build_on_field(key, maxlength, datatype)

        from operator import itemgetter
        param = "creationDate"
        reverse = args.reverse
        if args.name:
            param = "name"
        if args.size:
            param = "size_raw"

        json_obj = sorted(json_obj, reverse=reverse, key=itemgetter(param))
        if args.no_title:
            self.print_list(json_obj, d_format, no_legend=args.no_legend)
        else:
            self.print_list(json_obj, d_format, "Documents",
                            no_legend=args.no_legend)


# -------------------------- Documents ----------------------------------------
# -----------------------------------------------------------------------------
class DocumentsListV2Command(DefaultCommand):
    """ List all documents store into LinShare."""

    def __call__(self, args):
        super(DocumentsListV2Command, self).__call__(args)

        json_obj = self.ls.documents.list()

        keys = []
        keys.append(u'name')
        keys.append(u'uuid')
        keys.append(u'size')
        keys.append(u'creationDate')
        if args.extended:
            keys.append(u'type')
            keys.append(u'expirationDate')
            keys.append(u'description')
            keys.append(u'modificationDate')
            keys.append(u'ciphered')

        self.format_date(json_obj, 'creationDate')
        self.format_filesize(json_obj, 'size')
        self.format_date(json_obj, 'modificationDate')
        self.format_date(json_obj, 'expirationDate')

        table = VeryPrettyTable(keys)

        # styles
        table.align[u"name"] = "l"
        table.padding_width = 1
        table.align["size"] = "l"

        if args.name:
            table.reversesort = args.reverse
            table.sortby = "name"
        elif args.size:
            from operator import itemgetter
            json_obj = sorted(json_obj, reverse=args.reverse,
                              key=itemgetter("size_raw"))
        else:
            table.reversesort = args.reverse
            table.sortby = "creationDate"

        if True:
            for row in json_obj:
                data = []
                for key in keys:
                    data.append(row[key])
                table.add_row(data)
                #table.add_row(data, fore_color="red")
        if False:
            table = VeryPrettyTable()
            for key in keys:
                table.add_column(key, [row[key] for row in json_obj])

        out = table.get_string(
            fields=keys,
            #start=10,
            #end=10,
            #sortby=param
            )
        print unicode(out)


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
    parser_tmp2.add_argument('--no-title', action="store_true",
                             help="dont show the title")
    parser_tmp2.add_argument('--no-legend', action="store_true",
                             help="dont show the legend")
    parser_tmp2.add_argument('--size', action="store_true",
                             help="sort by file size")
    parser_tmp2.add_argument('-f', '--format', dest="output_format",
                             action="store",
                             help="""Change output format, ex:
{name:60s}{size!s:^10s}{uuid:40s}""")
    parser_tmp2.add_argument('--show-columns', action="store_true",
                             help="List all available fields in received data.")
    parser_tmp2.set_defaults(__func__=DocumentsListCommand())


    parser_tmp2 = subparsers2.add_parser(
        'listv2',
        formatter_class=RawTextHelpFormatter,
        help="list documents from linshare")
    parser_tmp2.add_argument('-r', '--reverse', action="store_true",
                             help="reverse order while sorting", default=False)
    parser_tmp2.add_argument('-c', '--creation-date', action="store_true",
                             help="sort by creation date")
    parser_tmp2.add_argument('-n', '--name', action="store_true",
                             help="sort by file name")
    #parser_tmp2.add_argument('-x', action="store_true",
    #                         help="vertical display")
    parser_tmp2.add_argument('--extended', action="store_true",
                             help="extended format")
    parser_tmp2.add_argument('--size', action="store_true",
                             help="sort by file size")
    parser_tmp2.set_defaults(__func__=DocumentsListV2Command())


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
def add_test_parser(subparsers, config):
    parser_tmp = subparsers.add_parser('test', add_help=False)
    parser_tmp.add_argument('files', nargs='*')
    parser_tmp.set_defaults(__func__=TestCommand(config))
