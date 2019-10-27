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
from .documents import add_parser as add_documents_parser
from .shares import add_parser as add_shares_parser
from .rshares import add_parser as add_received_shares_parser
from .workgroups import add_parser as add_workgroups_parser
from .wg_members import add_parser as add_wg_members_parser
from .wg_documents import add_parser as add_wg_documents_parser
from .shared_spaces import add_parser as add_shared_spaces_parser
from .shared_space_members import add_parser as add_shared_space_members_parser
from .shared_space_audit import add_parser as add_shared_space_audit_parser
from .users import add_parser as add_users_parser
from .guests import add_parser as add_guests_parser
from .contactslists import add_parser as add_contactslists_parser
from .contactslistscontacts import add_parser as add_contactslistscontacts_parser
from .core import add_parser as add_core_parser
from .jwt import add_parser as add_jwt_parser
from .audit import add_parser as add_audit_parser

PARSERS = []

def add_parser(subparsers, parser, config):
    """Add some parsers to a subparser.
    subparsers: subparsers object
    parser: dict containing, name, description, add parser function.
    config: config object
    """
    name = parser.get('name')
    description = parser.get('description')
    func = parser.get('parsers')
    func(subparsers, name, description, config)

def _add_parser(name=None, description=None, parsers=None):
    PARSERS.append(
        {
            'name': name,
            'description': description,
            'parsers': parsers
        }
    )

#####
_add_parser(name='documents', description='Documents of you personal space.',
            parsers=add_documents_parser)
_add_parser(name='shares', description='Share documents in you personal space.',
            parsers=add_shares_parser)
_add_parser(name='received_shares', description='Received shares management',
            parsers=add_received_shares_parser)
_add_parser(name='rshares', description='Alias of Received shares management',
            parsers=add_received_shares_parser)
_add_parser(name='workgroups', description='Workgroups management',
            parsers=add_workgroups_parser)
_add_parser(name='wg-members', description='Workgroup members management',
            parsers=add_wg_members_parser)
_add_parser(name='wg-content', description='Workgroup content management',
            parsers=add_wg_documents_parser)
_add_parser(name='shared_spaces', description='Shared spaces management',
            parsers=add_shared_spaces_parser)
_add_parser(name='shared_space_audit', description='Shared spaces audit management',
            parsers=add_shared_space_audit_parser)
_add_parser(name='shared_space_members', description='Shared spaces members management',
            parsers=add_shared_space_members_parser)
_add_parser(name='users', description='Users management',
            parsers=add_users_parser)
_add_parser(name='guests', description='Guests management',
            parsers=add_guests_parser)
_add_parser(name='lists', description='list all lists of contacts (aka mailing lists',
            parsers=add_contactslists_parser)
_add_parser(name='lists-contacts', description='Manage contacts within a list of contacts',
            parsers=add_contactslistscontacts_parser)
_add_parser(name='jwts', description='JWT Persistent Token',
            parsers=add_jwt_parser)
_add_parser(name='audit', description='audit',
            parsers=add_audit_parser)
_add_parser(parsers=add_core_parser)
