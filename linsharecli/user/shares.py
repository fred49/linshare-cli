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



from linsharecli.user.core import DefaultCommand
from argtoolbox import DefaultCompleter


class ShareAction(object):
    """"""
    def __init__(self, command):
        # all needed method are copied in order to this object looks like a Command
        self.command = command
        self.debug = self.command.debug
        self.ls = self.command.ls
        self.log = self.command.log
        self.pretty_json = self.command.pretty_json
        self.pprint = self.command.pprint
        self.pprint_warn = self.command.pprint_warn
        self.pprint_error = self.command.pprint_error
        self.api_version = self.command.api_version

    def __call__(self, args, cli, uuids):
        if self.api_version == 0:
            return self._share_all_1_7(args, cli, uuids)
        return self._share_all_1_8(args, cli, uuids)

    def _share_all_1_8(self, args, cli, uuids):
        rbu = self.ls.shares.get_rbu()
        rbu.load_from_args(args)
        rbu.set_value('documents', uuids)
        self.log.debug("rbu document: " + str(rbu))
        recipients = []
        cpt = 0
        if not args.mails:
            args.mails = []
        size = len(args.mails)
        for mail in args.mails:
            cpt += 1
            prefix = "%(cpt)s/%(size)s : " % {'cpt': cpt, 'size': size}
            rbu_user = self.ls.shares.get_rbu_user()
            rbu_user.load_from_args(args)
            rbu_user.set_value('mail', mail)
            recipients.append(rbu_user.to_resource())
            self.log.debug(prefix + "recipient: rbu user: " + str(rbu_user))
        rbu.set_value('recipients', recipients)
        json_obj = self.ls.shares.create(rbu.to_resource())
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

    def _share_all_1_7(self, args, cli, uuids):
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            res += self._share_1_7(args, cli, uuid, position, count)
        if res > 0:
            self.pprint(
                "Some file (%(count)s) have not been shared.",
                {'count': res})
            return False
        return True

    def _share_1_7(self, args, cli, uuid, position=None, count=None):
        if args.mails is None:
            self.pprint("No recipient was found !")
            return 0
        err_count = 0
        for mail in args.mails:
            if getattr(args, "dry_run", False):
                code = 204
                req_time = "- "
            else:
                code, err_msg, req_time = self.ls.shares.share(uuid, mail)
            if code == 204:
                self.pprint(
                    "The document (%(uuid)s) was successfully shared with %(mail)s (%(time)s s)",
                    {'uuid': uuid, 'mail': mail, 'time': req_time})
            else:
                err_count += 1
                meta = {
                    'mail': mail, 'uuid': uuid,
                    'code': code, 'err_msg': err_msg}
                self.pprint_warn(
                    "Trying to share document '%(uuid)s' with mail %(mail)s",
                    meta)
                self.pprint_error(
                    "Unexpected return code : %(code)s : %(err_msg)s",
                    meta)
        return err_count


class SharesCommand(DefaultCommand):
    """TODO"""

    def __init__(self, config, gparser):
        super(SharesCommand, self).__init__(config)
        self.gparser = gparser

    def __call__(self, args):
        super(SharesCommand, self).__call__(args)
        cli = self.ls.shares
        return self._share_all(args, cli, args.uuids)

    def _share_all_1_8(self, args, cli, uuids):
        """Method to share documents. compatible >= 1.8 """
        command = ShareAction(self)
        return command(args, cli, uuids)

    def _share_all(self, args, cli, uuids):
        if self.api_version == 0:
            return self._share_all_1_7(args, cli, uuids)
        self.check_required_options_v2(args, self.gparser)
        return self._share_all_1_8(args, cli, uuids)

    def _share_all_1_7(self, args, cli, uuids):
        """Deprecated method to share documents. 1.0 < compatible < 1.9 """
        # pylint: disable=unused-argument
        for uuid in args.uuids:
            for mail in args.mails:
                code, msg, req_time = self.ls.shares.share(uuid, mail)
                if code == 204:
                    self.log.info(
                        "The document '%s' was successfully shared with %s (%s)",
                        uuid,
                        mail,
                        req_time)
                else:
                    self.log.warning(
                        "Trying to share document '%s' with %s",
                        uuid, mail)
                    self.log.error("Unexpected return code: %s : %s", code, msg)
        return True

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


def add_parser(subparsers, name, desc, config):
    """TODO"""
    parser_tmp = subparsers.add_parser(name, help=desc)

    subparsers2 = parser_tmp.add_subparsers()

    parser = subparsers2.add_parser(
        'create', help="share files into linshare")
    parser.add_argument(
        'uuids',
        nargs='+',
        help="document's uuids you want to share."
        ).completer = DefaultCompleter()
    gparser = parser.add_argument_group(
        "Recipients",
        "You must at least use one of these options")
    gparser.add_argument(
        '-m', '--mail', action="append", dest="mails",
        help="Recipient mails.").completer = DefaultCompleter("complete_mail")
    gparser.add_argument(
        '--contact-list', action="append", dest="contact_list",
        help="list of contact list uuids")
    parser.add_argument('--expiration-date', action="store")
    parser.add_argument('--secured', action="store_true", default=None)
    parser.add_argument('--no-secured', action="store_false", default=None,
                        dest="secured")
    parser.add_argument(
        '--USDA', action="store_true",
        help=(
            "USDA aka Undownloaded Shared Document Alert.\n"
            "If enable, you will receive a email containing a report about "
            "the sharing after N days.\n"
            "This report will list document by document the recipients and if "
            "they had downloaded the document."
        ),
        default=None, dest="enable_USDA")
    parser.add_argument(
        '--no-USDA', action="store_false",
        help="Disable USDA report",
        default=None, dest="enable_USDA")
    parser.add_argument(
        '--force-anonymous-sharing', action="store_true",
        help=(
            "If enable, you will receive a email containing a resume of the "
            "sharing, with the lists of all recipients and documents."
        ),
        default=None)
    parser.add_argument(
        '--no-force-anonymous-sharing', action="store_false", default=None,
        help="Disable forced usage of anonymous sharing if it is enabled on the server.",
        dest="force_anonymous_sharing")
    parser.add_argument(
        '--sharing-acknowledgement', action="store_true", default=None,
        help=(
            "If enable, you will receive a email containing a resume of the "
            "sharing, with the lists of all recipients and documents."
        ),
        dest="sharing_acknowledgement")
    parser.add_argument(
        '--no-sharing-acknowledgement', action="store_false", default=None,
        help="Disable sharing acknowledgement if it is enabled on the server.",
        dest="sharing_acknowledgement")
    parser.add_argument('--message', action="store")
    parser.add_argument('--subject', action="store")
    parser.set_defaults(__func__=SharesCommand(config, gparser))
