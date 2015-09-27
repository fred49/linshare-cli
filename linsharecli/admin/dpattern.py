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

from linshareapi.cache import Time
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from argtoolbox import DefaultCompleter as Completer


# -----------------------------------------------------------------------------
class DomainPatternsListCommand(DefaultCommand):
    """ List all domain patterns."""
    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"

    @Time('linsharecli.domains', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPatternsListCommand, self).__call__(args)
        cli = self.ls.domain_patterns
        table = self.get_table(args, cli, self.IDENTIFIER)
        json_obj = cli.list()
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.identifiers, True)]
        return self._list(args, cli, table, json_obj, filters=filters)

    def complete(self, args, prefix):
        super(DomainPatternsListCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class DomainPatternsUpdateCommand(DefaultCommand):
    """ Update a domain pattern."""

    def __call__(self, args):
        super(DomainPatternsUpdateCommand, self).__call__(args)
        resource = None
        for model in self.ls.domain_patterns.list():
            if model.get('identifier') == args.identifier:
                resource = model
                break
        if resource is None:
            raise ValueError("Domain resource idenfier not found")
        rbu = self.ls.domain_patterns.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            self.ls.domain_patterns.update,
            "The following domain pattern '%(identifier)s' was successfully \
updated",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainPatternsUpdateCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class DomainPatternsCreateCommand(DefaultCommand):
    """ Create a domain pattern."""

    def __call__(self, args):
        super(DomainPatternsCreateCommand, self).__call__(args)
        rbu = self.ls.domain_patterns.get_rbu()
        if args.model:
            json_obj = self.ls.domain_patterns.list(True)
            for model in json_obj:
                if model.get('identifier') == args.model:
                    rbu.copy(model)
                    # reset identifier
                    rbu.set_value('identifier', "")
                    break
        rbu.load_from_args(args)
        return self._run(
            self.ls.domain_patterns.create,
            "The following domain pattern '%(identifier)s' was successfully \
created",
            args.identifier,
            rbu.to_resource())

    def complete(self, args, prefix):
        super(DomainPatternsCreateCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list(True)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class DomainPatternsDeleteCommand(DefaultCommand):
    """ List all domain patterns."""

    def __call__(self, args):
        super(DomainPatternsDeleteCommand, self).__call__(args)
        return self._delete(
            self.ls.domain_patterns.delete,
            "The following domain pattern '" + args.identifier + "' was \
successfully deleted",
            args.identifier,
            args.identifier)

    def complete(self, args, prefix):
        super(DomainPatternsDeleteCommand, self).__call__(args)
        json_obj = self.ls.domain_patterns.list(False)
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    """Add all domain pattern sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list domain patterns.")
    parser.add_argument('identifiers', nargs="*",
        help="Filter domain patterns by their names")
    parser.add_argument('-m', '--model', action="store_true",
                        help="show model of domain patterns")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=DomainPatternsListCommand())

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create domain pattern.")
    parser_tmp2.add_argument('identifier', action="store", help="")
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
    parser_tmp2.set_defaults(__func__=DomainPatternsCreateCommand())

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete domain pattern.")
    parser_tmp2.add_argument('identifier', action="store",
                             help="").completer = Completer()
    parser_tmp2.set_defaults(__func__=DomainPatternsDeleteCommand())

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
    parser_tmp2.set_defaults(__func__=DomainPatternsUpdateCommand())
