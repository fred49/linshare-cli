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



import re

from argparse import ArgumentError
from argparse import RawTextHelpFormatter
from linshareapi.cache import Time
from linshareapi.core import LinShareException
from linsharecli.user.core import DefaultCommand
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import add_download_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import Action
from linsharecli.common.tables import DeleteAction
from linsharecli.common.tables import DownloadAction
from argtoolbox import DefaultCompleter as Completer


class DocumentsCommand(DefaultCommand):
    """ List all documents store into LinShare."""

    def complete(self, args, prefix):
        super(DocumentsCommand, self).__call__(args)
        json_obj = self.ls.documents.list()
        return (
            v.get('uuid') for v in json_obj if v.get('uuid').startswith(prefix))


class ShareAction(Action):
    """TODO"""

    def __init__(self,
                 api_version,
                 identifier="name",
                 resource_identifier="uuid"
                ):
        super(ShareAction, self).__init__()
        self.api_version = api_version
        self.identifier = identifier
        self.resource_identifier = resource_identifier
        self.mails = None
        self.rbu = None

    def init(self, args, cli, endpoint):
        super(ShareAction, self).init(args, cli, endpoint)
        self.mails = getattr(args, "mails", None)
        if not self.mails:
            self.mails = []
        self.rbu = cli.shares.get_rbu()
        self.rbu.load_from_args(args)
        self.log.debug("rbu share: %s", self.rbu)
        return self

    def __call__(self, args, cli, endpoint, data):
        # pylint: disable=too-many-locals
        """TODO"""
        self.init(args, cli, endpoint)
        uuids = [row.get(self.resource_identifier) for row in data]
        return self.share_all(uuids)

    def share_all(self, uuids):
        """TODO"""
        if self.api_version == 0:
            raise ValueError("Not supported for the current api version : " + str(self.api_version))
        # copy of very very old lines of code.
        self.rbu.set_value('documents', uuids)
        recipients = []
        for mail in self.mails:
            recipients.append({'mail': mail})
        self.rbu.set_value('recipients', recipients)
        self.log.debug("rbu share: " + str(self.rbu))
        json_obj = self.cli.shares.create(self.rbu.to_resource())
        if self.debug >= 2:
            self.pretty_json(json_obj)
        documents = []
        recipients = []
        for i in json_obj:
            doc = i.get('document')
            if doc is None:
                # Somewhere between 1.8.4 and 1.8.7,
                # the attribute was properly renamed.
                # This line of code is just for compatibility
                doc = i.get('documentDto')
            document = doc['name'] + " (" + doc['uuid'] +")"
            if document not in documents:
                documents.append(document)
            # recipients
            reci = i['recipient']
            if reci['firstName']:
                recipient = "%(firstName)s %(lastName)s (%(mail)s)" % reci
            else:
                recipient = "%(mail)s" % reci
            if recipient not in recipients:
                recipients.append(recipient)
        self.pprint("The following documents :\n")
        for doc in sorted(documents):
            self.pprint(" - " + doc)
        self.pprint("\n were shared with :\n")
        for doc in sorted(recipients):
            self.pprint(" - " + doc)
        self.pprint("")
        return True


class DocumentsListCommand(DocumentsCommand):
    """ List all documents store into LinShare."""

    def __init__(self, config, gparser):
        super(DocumentsListCommand, self).__init__(config)
        self.gparser = gparser

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsListCommand, self).__call__(args)
        if args.share:
            self.check_required_options_v2(args, self.gparser)
        endpoint = self.ls.documents
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_action('share', ShareAction(self.api_version))
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.names, True),
            PartialDate("creationDate", args.cdate)
        )
        return tbu.build().load_v2(endpoint.list()).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        super(DocumentsListCommand, self).__call__(args)
        cli = self.ls.documents
        return cli.get_rbu().get_keys(True)

    def complete_mail(self, args, prefix):
        super(DocumentsListCommand, self).__call__(args)
        from argcomplete import warn
        if len(prefix) >= 3:
            json_obj = self.ls.autocomplete.list(prefix)
            return (v.get('display') for v in json_obj)
        else:
            warn("---------------------------------------")
            warn("Completion need at least 3 characters.")
            warn("---------------------------------------")
        return []


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


class DocumentsDownloadCommand(DocumentsCommand):
    """TODO"""

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsDownloadCommand, self).__call__(args)
        act = DownloadAction()
        act.init(args, self.ls, self.ls.documents)
        return act.download(args.uuids)


class DocumentsDeleteCommand(DocumentsCommand):
    """TODO"""

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsDeleteCommand, self).__call__(args)
        act = DeleteAction()
        act.init(args, self.ls, self.ls.documents)
        return act.delete(args.uuids)


class DocumentsUpdateCommand(DocumentsCommand):

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsUpdateCommand, self).__call__(args)
        a = ['description', 'meta_data', 'name', 'new_file']
        one_set = False
        for i in a:
            if getattr(args, i, None) is not None:
                one_set = True
                break
        if not one_set:
            raise ArgumentError(
                None,
                "You need to choose --file or at least one of the three options : --name or --meta-data or --description")
        cli = self.ls.documents
        try:
            document = cli.get(args.uuid)
            if args.new_file:
                json_obj = cli.update_file(args.uuid, args.new_file)
                if json_obj:
                    json_obj['time'] = self.ls.last_req_time
                    json_obj['new'] = args.new_file
                    self.log.info(
                        "The file '%(name)s' (%(uuid)s) was updated with %(new)s. (%(time)ss)",
                        json_obj)
                else:
                    return False
            else:
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


class DocumentsUploadAndSharingCommand(DefaultCommand):
    """TODO"""

    def __init__(self, config, gparser):
        super(DocumentsUploadAndSharingCommand, self).__init__(config)
        self.gparser = gparser

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(DocumentsUploadAndSharingCommand, self).__call__(args)
        self.check_required_options_v2(args, self.gparser)
        uuids = []
        for file_path in args.files:
            json_obj = self.ls.documents.upload(file_path)
            uuids.append(json_obj.get('uuid'))
            json_obj['time'] = self.ls.last_req_time
            self.log.info(
                "The file '%(name)s' (%(uuid)s) was uploaded. (%(time)ss)",
                json_obj)
        act = ShareAction(self.api_version)
        act.init(args, self.ls, self.ls.documents)
        return act.share_all(uuids)

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


def add_sharing_parser(parser, config):
    """TODO"""
    gparser = parser.add_argument_group(
        "Recipients",
        "You must at least use one of these options")
    gparser.add_argument(
        '-m', '--mail', action="append", dest="mails",
        help="Recipient mails.").completer = Completer("complete_mail")
    gparser.add_argument(
        '--contact-list', action="append", dest="contact_list",
        help="list of contact list uuids")
    share_group = parser.add_argument_group('Sharing options')
    share_group.add_argument('--expiration-date', action="store")
    share_group.add_argument('--secured', action="store_true", default=None)
    share_group.add_argument('--no-secured', action="store_false", default=None,
                             dest="secured")
    share_group.add_argument(
        '--USDA', action="store_true",
        help=(
            "USDA aka Undownloaded Shared Document Alert.\n"
            "If enable, you will receive a email containing a report about "
            "the sharing after N days.\n"
            "This report will list document by document the recipients and if "
            "they had downloaded the document."
        ),
        default=None, dest="enable_USDA")
    share_group.add_argument(
        '--no-USDA', action="store_false",
        help="Disable USDA report",
        default=None, dest="enable_USDA")
    if config.server.api_version.value >= 2:
        share_group.add_argument(
            '--force-anonymous-sharing', action="store_true",
            help=(
                "If enable, you will receive a email containing a resume of the "
                "sharing, with the lists of all recipients and documents."
            ),
            default=None)
        share_group.add_argument(
            '--no-force-anonymous-sharing', action="store_false", default=None,
            help="Disable forced usage of anonymous sharing if it is enabled on the server.",
            dest="force_anonymous_sharing")
    share_group.add_argument(
        '--sharing-acknowledgement', action="store_true", default=None,
        help=(
            "If enable, you will receive a email containing a resume of the "
            "sharing, with the lists of all recipients and documents."
        ),
        dest="sharing_acknowledgement")
    share_group.add_argument(
        '--no-sharing-acknowledgement', action="store_false", default=None,
        help="Disable sharing acknowledgement if it is enabled on the server.",
        dest="sharing_acknowledgement")
    share_group.add_argument('--message', action="store")
    share_group.add_argument('--subject', action="store")
    return gparser

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
    parser.set_defaults(__func__=DocumentsUploadCommand(config))

    # command : upshare
    parser = subparsers2.add_parser(
        'upshare',
        help="upload and share documents")
    parser.add_argument('files', nargs='+')
    gparser = add_sharing_parser(parser, config)
    parser.set_defaults(__func__=DocumentsUploadAndSharingCommand(config, gparser))

    # command : download
    parser = subparsers2.add_parser(
        'download',
        help="download documents from linshare")
    add_download_parser_options(parser)
    parser.set_defaults(__func__=DocumentsDownloadCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete documents from linshare")
    add_delete_parser_options(parser)
    parser.set_defaults(__func__=DocumentsDeleteCommand(config))

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
    gparser = add_sharing_parser(parser, config)
    parser.set_defaults(__func__=DocumentsListCommand(config, gparser))
    # command : list : share options

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
    parser.add_argument('--file', dest='new_file')
    parser.set_defaults(__func__=DocumentsUpdateCommand(config))
