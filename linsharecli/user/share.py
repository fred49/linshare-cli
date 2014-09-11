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

from linsharecli.user.core import DefaultCommand
from argtoolbox import DefaultCompleter


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


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc):
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
