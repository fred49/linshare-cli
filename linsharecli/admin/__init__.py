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
import os
import sys
import argparse
import textwrap

from argtoolbox import BasicProgram
from argtoolbox import SimpleSection
from argtoolbox import Element
from argtoolbox import Base64ElementHook
from argtoolbox import SectionHook
from .threads import add_parser as add_threads_parser
from .tmembers import add_parser as add_thread_members_parser
from .shared_spaces import add_parser as add_shared_spaces_parser
from .shared_space_members import add_parser as add_shared_space_members_parser
from .user import add_parser as add_users_parser
from .iuser import add_parser as add_iusers_parser
from .domain import add_parser as add_domains_parser
from .ldap import add_parser as add_ldap_connections_parser
from .dpattern import add_parser as add_domain_patterns_parser
from .func import add_parser as add_functionalities_parser
from .core import add_parser as add_core_parser
from .domainpolicies import add_parser as add_domain_policies
from .upgrade_tasks import add_parser as add_upgrade_tasks
from .welcome_messages import add_parser as add_welcome_messages
from .public_keys import add_parser as add_public_keys
from .jwt import add_parser as add_jwt
from .authentication import add_parser as add_authentication
from .mail_configs import add_parser as add_mail_configs
from .mail_attachments import add_parser as add_mail_attachments
from .. import __version__

# if you want to debug argcomplete completion,
# you just need to export _ARC_DEBUG=True

PARSERS = []

def _add_parser(name=None, description=None, parsers=None):
    PARSERS.append(
        {
            'name': name,
            'description': description,
            'parsers': parsers
        }
    )


_add_parser(name="threads", description="threads management", parsers=add_threads_parser)
_add_parser(name="tmembers", description="thread member management", parsers=add_thread_members_parser)
_add_parser(name="shared_spaces", description="shared spaces", parsers=add_shared_spaces_parser)
_add_parser(name="shared_space_members", description="shared spaces members", parsers=add_shared_space_members_parser)
_add_parser(name="users", description="users", parsers=add_users_parser)
_add_parser(name="iusers", description="inconsistent users", parsers=add_iusers_parser)
_add_parser(name="domains", description="domains", parsers=add_domains_parser)
_add_parser(name="ldap", description="ldap connections", parsers=add_ldap_connections_parser)
_add_parser(name="dpatterns", description="domain patterns", parsers=add_domain_patterns_parser)
_add_parser(name="funcs", description="Functionalities", parsers=add_functionalities_parser)
_add_parser(name="domainpolicy", description="Domain Policies", parsers=add_domain_policies)
_add_parser(name="upgrade", description="upgrade tasks", parsers=add_upgrade_tasks)
_add_parser(name="welcome", description="welcome messages", parsers=add_welcome_messages)
_add_parser(name="pubkeys", description="welcome messages", parsers=add_public_keys)
_add_parser(name="jwts", description="JWT Persistent Token", parsers=add_jwt)
_add_parser(name="auth", description="Authentication", parsers=add_authentication)
_add_parser(name="mail_configs", description="mail_configs", parsers=add_mail_configs)
_add_parser(name="mail_attachments", description="mail_attachments", parsers=add_mail_attachments)
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
            desc=textwrap.dedent("""The linshare api version to be used. Default '1'.
            * For LinShare Core >= 1.6.x, use api_version=0
            * For LinShare Core >= 1.9.x, use api_version=1
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
            desc="Default value is 'linshare/webservice/rest/admin'"))

        section_server.add_element(Element(
            'verify',
            e_type=bool,
            default=True,
            desc="Disable SSL certificate verification"))

        section_server.add_element(Element(
            'nocache',
            e_type=bool,
            default=False,
            desc=argparse.SUPPRESS))

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

    def add_commands(self):
        """TODO"""
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
            help="If set, the program will load your password from this environement variable.")

        self.parser.add_argument(
            '-H',
            '--host',
            action="store",
            **self.config.server.host.get_arg_parse_arguments())

        self.parser.add_argument(
            '--nocache',
            action="store_true",
            **self.config.server.nocache.get_arg_parse_arguments())

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

    def reload(self):
        """TODO"""
        # If section_server is defined, we need to modify the suffix
        # attribute ofserver Section object.
        hook = SectionHook(self.config.server, "_suffix", "server_section")

        # Reloading configuration with previous optional arguments
        # (ex config file name, server section, ...)
        self.config.reload(hook)


# if you need debug during class construction, config file loading,
# you just need to export _LINSHARE_CLI_ADMIN_DEBUG=True
CLI = LinShareCliProgram(
    "linshare-admin-cli",
    version=__version__,
    force_debug=os.getenv('_LINSHARE_CLI_ADMIN_DEBUG', False),
    force_debug_to_file=os.getenv('_LINSHARE_CLI_ADMIN_DEBUG_FILE', False),
    desc="""An user cli for LinShare, using its REST API.

    In order to enable auto complete support, or generate the default
    configuration file associated with the current program,
    look at : `linshareadmcli-config generate -h`


Advanced documentation :
========================

API Version :
-------------

    This client support multiple LinShare server and its API version.
The default value '1' can be overriden by the env variable LS_API, which can be
set in the configuration file.
* For LinShare Core >= 1.6.x, use api_version=0.
* For LinShare Core >= 1.9.x, use api_version=1.

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
    cli_generate_config("linshareadmcli-config", CLI)
