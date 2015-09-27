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
from linsharecli.common.filters import PartialOr
from linsharecli.admin.core import DefaultCommand
from argtoolbox import DefaultCompleter as Completer
from linsharecli.common.core import add_list_parser_options


# -----------------------------------------------------------------------------
class DomainPoliciesCommand(DefaultCommand):
    """ List all domain policies store into LinShare."""

    IDENTIFIER = "identifier"
    DEFAULT_SORT = "identifier"
    DEFAULT_SORT_NAME = "identifier"
    RESOURCE_IDENTIFIER = "identifier"
    DEFAULT_TOTAL = "Domain policies found : %(count)s"
    MSG_RS_NOT_FOUND = "No domain policies could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The domain policy '%(uuid)s' was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The domain policy '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%s domain policy(s) can not be deleted."
    MSG_RS_DOWNLOADED = "%(position)s/%(count)s: The domain policy '%(name)s' (%(uuid)s) was downloaded. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One domain policy can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%s domain policies can not be downloaded."

    def complete(self, args, prefix):
        super(DomainPoliciesCommand, self).__call__(args)
        json_obj = self.ls.domain_policies.list()
        return (v.get('identifier')
                for v in json_obj if v.get('identifier').startswith(prefix))


# -----------------------------------------------------------------------------
class DomainPoliciesListCommand(DomainPoliciesCommand):
    """ List all domain policies."""

    @Time('linshareadmcli.domainpolicies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesListCommand, self).__call__(args)
        cli = self.ls.domain_policies
        table = self.get_table(args, cli, self.IDENTIFIER)
        json_obj = cli.list()
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.identifiers, True)]
        return self._list(args, cli, table, json_obj, filters=filters)


# -----------------------------------------------------------------------------
class DomainPoliciesCreateCommand(DomainPoliciesCommand):
    """Create domain policy."""

    @Time('linshareadmcli.domain_policies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesCreateCommand, self).__call__(args)
        rbu = self.ls.domain_policies.get_rbu()
        rbu.load_from_args(args)
        return self._run(
            self.ls.domain_policies.create,
            "The following domain policy '%(identifier)s' was successfully \
created",
            args.identifier,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class DomainPoliciesUpdateCommand(DomainPoliciesCommand):
    """Update domain policy."""

    @Time('linshareadmcli.domain_policies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesUpdateCommand, self).__call__(args)
        resource = self.ls.domain_policies.get(args.identifier)
        if resource is None:
            raise ValueError("Domain policy idenfier not found")
        rbu = self.ls.domain_policies.get_rbu()
        rbu.copy(resource)
        rbu.load_from_args(args)
        return self._run(
            self.ls.domain_policies.update,
            "The following domain policy '%(identifier)s' was successfully \
updated",
            args.identifier,
            rbu.to_resource())


# -----------------------------------------------------------------------------
class DomainPoliciesDeleteCommand(DomainPoliciesCommand):
    """Delete domain policy."""

    @Time('linshareadmcli.domain_policies', label='Global time : %(time)s')
    def __call__(self, args):
        super(DomainPoliciesDeleteCommand, self).__call__(args)
        cli = self.ls.domain_policies
        return self._delete_all(args, cli, args.identifiers)


# -----------------------------------------------------------------------------
def add_parser(subparsers, name, desc, config):
    """Add all domain policies sub commands."""
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list domain policies")
    parser.add_argument(
        'identifiers', nargs="*",
        help="Filter domain policies by their identifiers")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=DomainPoliciesListCommand())

    # command : delete
    parser_tmp2 = subparsers2.add_parser(
        'delete', help="delete domain policies.")
    parser_tmp2.add_argument('identifiers',
                             nargs="*",
                             action="store",
                             help="").completer = Completer()
    parser_tmp2.set_defaults(__func__=DomainPoliciesDeleteCommand())

    # command : create
    parser_tmp2 = subparsers2.add_parser(
        'create', help="create domain policies.")
    parser_tmp2.add_argument('identifier', action="store", help="")
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.set_defaults(__func__=DomainPoliciesCreateCommand())

    # command : update
    parser_tmp2 = subparsers2.add_parser(
        'update', help="update domain policies.")
    parser_tmp2.add_argument(
        'identifier', action="store", help="").completer = Completer()
    parser_tmp2.add_argument('--description', action="store", help="")
    parser_tmp2.set_defaults(__func__=DomainPoliciesUpdateCommand())
