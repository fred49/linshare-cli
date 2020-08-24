#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""TODO"""


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
# Copyright 2019 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



from linshareapi.cache import Time
from argtoolbox import DefaultCompleter as Completer
from linsharecli.common.actions import CreateAction as CCreateAction
from linsharecli.common.actions import UpdateAction as UUpdateAction
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.common.tables import TableBuilder
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.cell import ComplexCellBuilder


class CreateAction(CCreateAction):
    """TODO"""

    def __init__(self, command, cli):
        super(CreateAction, self).__init__(command, cli)
        self.logo = None
        self.name = None

    def load(self, args):
        super(CreateAction, self).load(args)
        self.logo = args.logo
        self.name = args.name
        return self

    def _execute(self, data):
        if data is None:
            data = self.rbu.to_resource()
        if self.debug:
            self.pretty_json(data, "Json object sent to the server")
        return self.cli.create(self.logo, data, self.name)


class UpdateAction(UUpdateAction):
    """TODO"""

    def _execute(self, data):
        if data is None:
            data = self.rbu.to_resource()
        # we remove this field because server expects an obejct not a simple
        # string. It is transform into a string by the ResourceBuilder.copy
        # method.
        del data['mailConfig']
        if self.debug:
            self.pretty_json(data, "Json object sent to the server")
        return self.cli.update(data)


class MailAttachmentsCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "cid"
    DEFAULT_SORT = "cid"
    RESOURCE_IDENTIFIER = "uuid"

    # pylint: disable=line-too-long
    DEFAULT_TOTAL = "Mail attachments found : %(count)s"
    MSG_RS_NOT_FOUND = "No mail attachment could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The mail attachment '%(cid)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The mail attachment '%(cid)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s mail attachment(s) can not be deleted."
    MSG_RS_UPDATED = "The mail attachment '%(name)s - %(cid)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = "The mail attachment '%(name)s - %(cid)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    def complete(self, args, prefix):
        super(MailAttachmentsCommand, self).__call__(args)
        json_obj = self.ls.public_keys.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))

    # pylint: disable=unused-argument
    def complete_fields(self, args, prefix):
        """TODO"""
        super(MailAttachmentsCommand, self).__call__(args)
        cli = self.ls.public_keys
        return cli.get_rbu().get_keys(True)

    def complete_domain(self, args, prefix):
        """TODO"""
        super(MailAttachmentsCommand, self).__call__(args)
        json_obj = self.ls.domains.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete_configs(self, args, prefix):
        """TODO"""
        super(MailAttachmentsCommand, self).__call__(args)
        json_obj = self.ls.mail_configs.list()
        return (v.get('identifier')
                for v in json_obj if v.get('uuid').startswith(prefix))


class MailAttachmentsListCommand(MailAttachmentsCommand):
    """ List all public keys."""

    @Time('linsharecli.publickeys', label='Global time : %(time)s')
    def __call__(self, args):
        super(MailAttachmentsListCommand, self).__call__(args)
        endpoint = self.ls.mail_attachments
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell(
            "mailConfig",
            ComplexCellBuilder(
                '{name}\n({uuid:.8})',
                '{name} ({uuid:})',
                '{name}',
            )
        )
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        return tbu.build().load_v2(endpoint.list(args.mail_config)).render()


class MailAttachmentsCreateCommand(MailAttachmentsCommand):
    """Create mail attachments."""

    def __call__(self, args):
        super(MailAttachmentsCreateCommand, self).__call__(args)
        act = CreateAction(self, self.ls.mail_attachments)
        return act.load(args).execute()


class MailAttachmentsUpdateCommand(MailAttachmentsCommand):
    """Update mail attachments."""

    def __init__(self, config, parser):
        super(MailAttachmentsUpdateCommand, self).__init__(config)
        self.parser = parser

    def __call__(self, args):
        super(MailAttachmentsUpdateCommand, self).__call__(args)
        self.check_required_options_v2(args, self.parser)
        endpoint = self.ls.mail_attachments
        act = UpdateAction(self, endpoint)
        act.rbu = endpoint.get_rbu()
        act.rbu.copy(endpoint.get(args.uuid))
        return act.load(args).execute()


def add_parser(subparsers, name, desc, config):
    """Add all mail configs commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    parser_tmp.add_argument(
        'mail_config',
        help="Mail config uuid"
    ).completer = Completer("complete_configs")

    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list mail configs")
    parser.add_argument('identifiers', nargs="*", help="")
    add_list_parser_options(parser, delete=True, cdate=False)
    parser.add_argument('--parent',
                        action="store_true",
                        help="Display also mail configs from parent domains")
    parser.add_argument('--domain',
                       ).completer = Completer("complete_domain")
    parser.set_defaults(__func__=MailAttachmentsListCommand(config))

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create public key.")
    parser.add_argument('logo', action="store",
                        help="Path to the file (logo) to upload")
    parser.add_argument(
        '--cid',
        action="store",
        help=("Content id for the mail attachment.\n"
              "Use the 'logo.linshare@linshare.org' CID to override the default "
              "LinShare logo. "
              "If you are using your own CID, you must create your own mail "
              "layout and reference it."))
    parser.add_argument('--name', action="store")
    parser.add_argument('--description', action="store")
    parser.add_argument(
        '--language', action="store",
        choices=["ENGLISH", "FRENCH", "RUSSIAN"],
        help=(
            "By default, the new logo will be used with all languages.\n"
            "If set, you will override only one language."
        ))
    parser.add_argument('--alt', action="store")
    parser.add_argument('--disable', action="store_false", dest="enable",
                        help=(
                            "When enabled, mail attachment will be used during "
                            "server side mail rendering.\n"
                            "By default, mail attachments are enabled."
                        ))
    parser.add_argument('--cli-mode', action="store_true",
                        help="It will only display the created resource uuid.")
    parser.set_defaults(__func__=MailAttachmentsCreateCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update mail attachments.")
    parser.add_argument('uuid', action="store")
    parser.add_argument('--cli-mode', action="store_true", help="")
    gparser = parser.add_argument_group(
        "Properties",
        "You must at least use one of these options")
    gparser.add_argument('--cid', action="store")
    gparser.add_argument('--name', action="store")
    gparser.add_argument('--description', action="store")
    gparser.add_argument('--language', action="store", choices=["ENGLISH", "FRENCH", "RUSSIAN"])
    gparser.add_argument('--enable', action="store", choices=["True", "False"])
    gparser.add_argument('--enable-for-all', action="store", choices=["True", "False"])
    parser.set_defaults(__func__=MailAttachmentsUpdateCommand(config, gparser))
