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
import os
import sys
import argparse
import textwrap

from argtoolbox import BasicProgram
from argtoolbox import SimpleSection
from argtoolbox import Element
from argtoolbox import Base64ElementHook
from argtoolbox import SectionHook

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
from .. import __version__

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

class LinShareCliProgram(BasicProgram):
    """Main program."""

    def add_config_options(self):
        """TODO"""
        self.formatter_class = argparse.RawTextHelpFormatter

        section_server = self.config.add_section(SimpleSection("server"))

        section_server.add_element(Element(
            'host',
            required=True))
        section_server.add_element(Element(
            'api_version',
            required=True,
            default=float(os.getenv('LS_API', 2.2)),
            e_type=float,
            desc=textwrap.dedent("""
            The linshare api version to be used. Default '2'.
            * For LinShare Core = 1.7.x, use api_version=0
            * For LinShare Core >= 1.8.x, use api_version=1
            * For LinShare Core >= 2.0.x, use api_version=2
            * For LinShare Core >= 2.2.x, use api_version=2.2
            The default value can be overriden by the env variable LS_API, which can be
            overriden by this parameter.""")))

        section_server.add_element(Element('user', required=True))

        section_server.add_element(Element(
            'password',
            hidden=True,
            desc="user password to linshare. See cli help for using env variable instead."))

        section_server.add_element(Element(
            'auth_type',
            default="plain-b64",
            desc="Authentication mecanism : plain, plain-b64 or jwt"))

        section_server.add_element(Element(
            'base_url',
            desc=textwrap.dedent("""
            This parameter is dynamically computed according api_version value.
            For api_version=2, its default value will be 'linshare/webservice/rest/user/v2'.
            You can also override it according your environment.""")))

        section_server.add_element(Element(
            'verify',
            e_type=bool,
            default=True,
            desc="Disable SSL certificate verification"))

        section_server.add_element(Element(
            'nocache',
            e_type=bool,
            default=False))

        section_server.add_element(Element('verbose'))

        section_server.add_element(Element(
            'debug',
            e_type=int,
            e_type_exclude=True,
            default=int(os.getenv('LS_DEBUG', 0)),
            desc=textwrap.dedent("""
            (default: 0)
            0 : debug off
            1 : debug on
            2 : debug on and request result is printed (pretty json)
            3 : debug on and urllib debug on and http headers and request
            are printed
            The default value can be overriden by the env variable LS_DEBUG, which can be
            overriden by this parameter.""")))

    def add_pre_commands(self):
        """TODO"""
        self.parser.add_argument(
            '-s',
            action="store",
            dest='server_section',
            help=textwrap.dedent("""
            This option let you select the server section in the cfg
            file you want to load (server section is always load first as default
            configuration). You just need to specify a number like '4' for
            section 'server-4'"""))

        self.parser.add_argument(
            '-d',
            action="count",
            **self.config.server.debug.get_arg_parse_arguments())

    def reload(self):
        # If section_server is defined, we need to modify the suffix
        # attribute ofserver Section object.
        hook = SectionHook(self.config.server, "_suffix", "server_section")

        # Reloading configuration with previous optional arguments
        # (ex config file name, server section, ...)
        self.config.reload(hook)

    def add_commands(self):

        # Adding all others options.
        self.parser.add_argument(
            '-u',
            '--user',
            action="store",
            **self.config.server.user.get_arg_parse_arguments())

        password_group = self.parser.add_argument_group('Password')
        password_required = True
        if self.config.server.password is not None:
            password_required = False
        group = password_group.add_mutually_exclusive_group(
            required=password_required)
        group.add_argument(
            '-P',
            '--password',
            action="store",
            **self.config.server.password.get_arg_parse_arguments())

        group.add_argument(
            '-p',
            action="store_true",
            default=False,
            dest="ask_password",
            help="If set, the program will ask you your password.")

        group.add_argument(
            '-E',
            action="store_true",
            default=False,
            dest="env_password",
            help="If set, the program will load your password from LS_PASSWORD environement variable.")

        group.add_argument(
            '--password-from-env',
            action="store",
            help="If set, the program will load your password from a environement variable.")

        self.parser.add_argument(
            '-H',
            '--host',
            action="store",
            **self.config.server.host.get_arg_parse_arguments())

        self.parser.add_argument(
            '--no-cache',
            action="store_true",
            **self.config.server.nocache.get_arg_parse_arguments())

        # compatibility.
        self.parser.add_argument(
            '--nocache',
            dest="nocache",
            action="store_true",
            default=False,
            help=argparse.SUPPRESS)

        self.parser.add_argument(
            '--no-verify',
            action="store_false",
            **self.config.server.verify.get_arg_parse_arguments())

        self.parser.add_argument(
            '--base-url',
            action="store",
            **self.config.server.base_url.get_arg_parse_arguments())

        self.parser.add_argument('--debugger-names', action="append")
        self.parser.add_argument('--no-cell', action="store_true")

        # Adding all others parsers.
        subparsers = self.parser.add_subparsers()
        for parser in PARSERS:
            name = parser.get('name')
            description = parser.get('description')
            func = parser.get('parsers')
            func(subparsers, name, description, self.config)


CLI = LinShareCliProgram(
    "linshare-cli",
    version=__version__,
    force_debug=os.getenv('_LINSHARE_CLI_USER_DEBUG', False),
    force_debug_to_file=os.getenv('_LINSHARE_CLI_USER_DEBUG_FILE', False),
    desc="""An user cli for LinShare, using its REST API.

    In order to enable auto complete support, or generate the default
    configuration file associated with the current program,
    look at : `linsharecli-config generate -h`


Advanced documentation :
========================

API Version :
-------------

    This client support multiple LinShare server and its API version.
The default value '1' can be overriden by the env variable LS_API, which can be
set in the configuration file.
* For LinShare Core = 1.7.x, use api_version=0.
* For LinShare Core >= 1.8.x, use api_version=1.
* For LinShare Core >= 2.0.x, use api_version=2.
The default value can be overriden by the env variable LS_API, which can be
overriden by this parameter.

Advanced debug:
---------------

* If you need debug during class construction, config file loading,
you just need to export _LINSHARE_CLI_USER_DEBUG=True
* To debug auto completion, you need to export _ARC_DEBUG=1.
    * Disable warning about SSL verification : export PYTHONWARNINGS="ignore:Unverified HTTPS request"


================================================================
""")

def generate_config():
    """TODO"""
    from argtoolbox.commands import cli_generate_config
    cli_generate_config("linsharecli-config", CLI)
