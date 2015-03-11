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

import linsharecli.common.core as common
from linshareapi.user import UserCli
import argtoolbox


# pylint: disable=C0111
# Missing docstring
# -----------------------------------------------------------------------------
class DefaultCommand(common.DefaultCommand):
    """ Default command object use by the ser API. If you want to add a new
    command to the command line interface, your class should extend this one.
    """

    IDENTIFIER = "name"
    DEFAULT_SORT_NAME = "name"
    RESOURCE_IDENTIFIER = "uuid"

    def __get_cli_object(self, args):
        cli = UserCli(args.host, args.user, args.password, args.verbose,
                      args.debug, api_version=args.api_version)
        if args.base_url:
            cli.base_url = args.base_url
        return cli


# -----------------------------------------------------------------------------
class TestCommand(argtoolbox.DefaultCommand):
    """Just for test. Print test to stdout"""

    def __init__(self, config=None):
        super(TestCommand, self).__init__(config)
        self.verbose = False
        self.debug = False

    def __call__(self, args):
        self.verbose = args.verbose
        self.debug = args.debug
        print "Test"
        print unicode(self.config)
        print args
        print ""


# -----------------------------------------------------------------------------
class ListConfigCommand(DefaultCommand):
    """"""

    def __init__(self, config=None):
        super(ListConfigCommand, self).__init__(config)
        self.verbose = False
        self.debug = False

    def __call__(self, args):
        self.verbose = args.verbose
        self.debug = args.debug
        seclist = self.config.file_parser.sections()
        print
        print "Available sections:"
        print "==================="
        print
        for i in seclist:
            if i.startswith("server-"):
                print " - " + "-".join(i.split('-')[1:])
        print ""

# -----------------------------------------------------------------------------
def add_parser(subparsers, config):
    parser = subparsers.add_parser('test', add_help=False)
    parser.add_argument('files', nargs='*')
    parser.set_defaults(__func__=TestCommand(config))
    parser = subparsers.add_parser('list')
    parser.set_defaults(__func__=ListConfigCommand(config))
