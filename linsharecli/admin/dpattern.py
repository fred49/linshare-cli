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
# Copyright 2014 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



from linshareapi.cache import Time
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.actions import CreateAction
from linsharecli.common.tables import TableBuilder
from argtoolbox import DefaultCompleter as Completer


class DomainPatternsCommand(DefaultCommand):
    """For  api >= 1.9"""
    # pylint: disable=too-many-instance-attributes
    IDENTIFIER = "label"
    DEFAULT_SORT = "label"
    RESOURCE_IDENTIFIER = "uuid"

    DEFAULT_TOTAL = "Domain pattern found : %(count)s"
    MSG_RS_NOT_FOUND = "No domain pattern could be found."
    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The domain pattern '%(label)s' (%(uuid)s) was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The domain pattern '%(label)s'  '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s domain pattern(s) can not be deleted."
    MSG_RS_UPDATED = "The domain pattern '%(label)s' (%(uuid)s) was successfully updated."
    MSG_RS_CREATED = (
        "The domain pattern '%(label)s' (%(uuid)s) "
        "was successfully created. (%(_time)s s)"
    )

    def init_old_language_key(self):
        """For  api >= 1.6 and api <= 1.8"""
        # pylint: disable=invalid-name
        self.IDENTIFIER = "identifier"
        self.DEFAULT_SORT = "identifier"
        self.RESOURCE_IDENTIFIER = "identifier"

        self.DEFAULT_TOTAL = "Domain pattern found : %(count)s"
        self.MSG_RS_NOT_FOUND = "No domain pattern could be found."
        self.MSG_RS_DELETED = "The domain pattern '%(identifier)s' was deleted. (%(time)s s)"
        self.MSG_RS_DELETED = (
            "%(position)s/%(count)s: "
            "The domain pattern '%(identifier)s' was deleted. (%(time)s s)"
        )
        self.MSG_RS_CAN_NOT_BE_DELETED = "The domain pattern '%(identifier)s' can not be deleted."
        self.MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s domain pattern(s) can not be deleted."
        self.MSG_RS_UPDATED = "The domain pattern '%(identifier)s' was successfully updated."
        self.MSG_RS_CREATED = "The domain pattern '%(identifier)s' was successfully created."

    def complete_identifier(self, args, prefix):
        """TODO"""
        super(DomainPatternsCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))

    def complete(self, args, prefix):
        super(DomainPatternsCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        json_obj = self.ls.domain_patterns.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


class DomainPatternsListCommand(DomainPatternsCommand):
    """ List all domain patterns."""

    @Time('linsharecli.dpattern', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPatternsListCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        endpoint = self.ls.domain_patterns
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.identifiers, True),
        )
        return tbu.build().load_v2(endpoint.list(args.model)).render()

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(DomainPatternsListCommand, self).__call__(args)
        cli = self.ls.domain_patterns
        return cli.get_rbu().get_keys(True)


class DomainPatternsUpdateCommand(DomainPatternsCommand):
    """ Update a domain pattern."""

    def __call__(self, args):
        super(DomainPatternsUpdateCommand, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        cli = self.ls.domain_patterns
        resource = cli.get(args.identifier)
        rbu = cli.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            cli.update,
            self.MSG_RS_UPDATED,
            args.identifier,
            rbu.to_resource())


class DomainPatternsCreateCommand(DomainPatternsCommand):
    """ Create a domain pattern."""

    def __call__(self, args):
        super(DomainPatternsCreateCommand, self).__call__(args)
        self.init_old_language_key()
        rbu = self.ls.domain_patterns.get_rbu()
        if args.model:
            json_obj = self.ls.domain_patterns.list(True)
            for model in json_obj:
                if model.get('identifier') == args.model:
                    rbu.copy(model)
                    # reset identifier
                    rbu.set_value('identifier', "")
                    rbu.set_value('description', "")
                    break
        rbu.load_from_args(args)
        act = CreateAction(self, self.ls.domain_patterns)
        return act.load(args).execute(rbu.to_resource())


class DomainPatternsCreateCommand2(DomainPatternsCommand):
    """ Create a domain pattern."""

    def __call__(self, args):
        super(DomainPatternsCreateCommand2, self).__call__(args)
        if self.api_version == 0:
            self.init_old_language_key()
        rbu = self.ls.domain_patterns.get_rbu()
        if args.model:
            json_obj = self.ls.domain_patterns.list(True)
            for model in json_obj:
                if model.get('uuid') == args.model:
                    rbu.copy(model)
                    # reset description
                    rbu.set_value('description', "")
                    break
        rbu.load_from_args(args)
        act = CreateAction(self, self.ls.domain_patterns)
        return act.load(args).execute(rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainPatternsCreateCommand2, self).__call__(args)
        json_obj = self.ls.domain_patterns.list(True)
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))


class DomainPatternsDeleteCommand(DomainPatternsCommand):
    """ List all domain patterns."""

    def __call__(self, args):
        super(DomainPatternsDeleteCommand, self).__call__(args)
        cli = self.ls.domain_patterns
        if self.api_version == 0:
            return self._delete(
                args,
                cli,
                args.identifier)
        return self._delete_all(args, cli, args.uuids)

    def complete(self, args, prefix):
        super(DomainPatternsDeleteCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list(False)
        identifier = 'uuid'
        if self.api_version == 0:
            identifier = 'identifier'
        return (v.get(identifier)
                for v in json_obj if v.get(identifier).startswith(prefix))


def add_parser(subparsers, name, desc, config):
    """Add all domain pattern sub commands."""
    # pylint: disable=too-many-statements
    api_version = config.server.api_version.value
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list domain patterns.")
    parser.add_argument(
        'identifiers', nargs="*",
        help="Filter domain patterns by their names")
    parser.add_argument('-m', '--model', action="store_true",
                        help="show model of domain patterns")
    if api_version == 0:
        add_list_parser_options(parser)
    else:
        add_list_parser_options(parser, delete=True, cdate=False)
    parser.set_defaults(__func__=DomainPatternsListCommand(config))

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create domain pattern.")
    parser_tmp2.add_argument('--model', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('--completion-page-size', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--completion-size-limit', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--search-page-size', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--search-size-limit', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--ldap-uid', action="store", help="")
    parser_tmp2.add_argument('--first-name', action="store", help="")
    parser_tmp2.add_argument('--last-name', action="store", help="")
    parser_tmp2.add_argument('--mail', action="store", help="")
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.add_argument('--auth-command', action="store", help="")
    parser_tmp2.add_argument('--search-user-command', action="store", help="")
    parser_tmp2.add_argument('--auto-complete-command-on-all-attributes',
                             action="store", help="")
    parser_tmp2.add_argument('--auto-complete-command-on-first-and-last-name',
                             action="store", help="")
    parser_tmp2.add_argument('--cli-mode', action="store_true", help="")
    if api_version == 0:
        parser_tmp2.add_argument('identifier', action="store", help="")
        parser_tmp2.set_defaults(__func__=DomainPatternsCreateCommand(config))
    else:
        parser_tmp2.add_argument('label', action="store", help="")
        parser_tmp2.set_defaults(__func__=DomainPatternsCreateCommand2(config))

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete domain pattern.")
    if api_version == 0:
        parser_tmp2.add_argument(
            'identifier',
            action="store",
            help="").completer = Completer()
    else:
        add_delete_parser_options(parser_tmp2)
    parser_tmp2.set_defaults(__func__=DomainPatternsDeleteCommand(config))

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update domain patterns.")
    parser_tmp2.add_argument(
        'identifier', action="store", help="").completer = Completer()
    parser_tmp2.add_argument('--completion-page-size', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--completion-size-limit', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--search-page-size', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--search-size-limit', action="store",
                             type=int, help="")
    parser_tmp2.add_argument('--ldap-uid', action="store", help="")
    parser_tmp2.add_argument('--first-name', action="store", help="")
    parser_tmp2.add_argument('--last-name', action="store", help="")
    parser_tmp2.add_argument('--mail', action="store", help="")
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.add_argument('--model', action="store",
                             help="").completer = Completer()
    parser_tmp2.add_argument('--auth-command', action="store", help="")
    parser_tmp2.add_argument('--search-user-command', action="store", help="")
    parser_tmp2.add_argument('--auto-complete-command-on-all-attributes',
                             action="store", help="")
    parser_tmp2.add_argument('--auto-complete-command-on-first-and-last-name',
                             action="store", help="")
    parser_tmp2.set_defaults(__func__=DomainPatternsUpdateCommand(config))
