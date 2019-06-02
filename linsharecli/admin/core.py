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

from __future__ import unicode_literals

import json
import urllib2


from linshareapi.admin import AdminCli
from linshareapi.core import LinShareException
import linsharecli.common.core as common

import argtoolbox


class DefaultCommand(common.DefaultCommand):
    """ Default command object use by the serer API. If you want to add a new
    command to the command line interface, your class should extend this class.
    """

    def __get_cli_object(self, args):
        api_version = self.config.server.api_version.value
        self.log.debug("using api version : " + str(api_version))
        cli = AdminCli(args.host, args.user, args.password, args.verbose,
                       args.debug, api_version=api_version)
        if args.base_url:
            cli.base_url = args.base_url
        return cli

    def _run(self, method, message_ok, err_suffix, *args):
        try:
            json_obj = method(*args)
            self.log.info(message_ok, json_obj)
            if self.debug:
                self.pretty_json(json_obj)
            return True
        except LinShareException as ex:
            self.log.debug("LinShareException : " + str(ex.args))
            self.log.error(ex.args[1] + " : " + err_suffix)
        return False


class NotYetImplementedCommand(argtoolbox.DefaultCommand):
    """Just for test. Print test to stdout"""
    # pylint: disable=too-few-public-methods

    def __call__(self, args):
        print "Not Yet Implemented."


class TestCommand(argtoolbox.DefaultCommand):
    """Just for test. Print test to stdout"""
    # pylint: disable=too-few-public-methods

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
        self.log.info("End of test command.")


class RawCommand(DefaultCommand):
    """Just call raw http urls"""
    # pylint: disable=too-few-public-methods

    def __call__(self, args):
        super(RawCommand, self).__call__(args)
        self.verbose = args.verbose
        self.debug = args.debug
        self.log.info("Begin of raw command.")
        print unicode(self.config)
        print args
        if args.url:
            core = self.ls.raw.core
            for i in range(1, args.repeat + 1):
                url = core.get_full_url(args.url)
                self.log.debug("list url:%s: %s", i, url)
                if args.data:
                    post_data = json.loads(args.data)
                    post_data = json.dumps(post_data)
                    post_data = post_data.encode("UTF-8")
                    request = urllib2.Request(url, post_data)
                else:
                    request = urllib2.Request(url)
                request.add_header('Content-Type', 'application/json; charset=UTF-8')
                request.add_header('Accept', 'application/json')
                request.get_method = lambda: 'GET'
                if args.method:
                    request.get_method = lambda: args.method
                res = core.do_request(request)
                self.log.info(
                    "list url:%(cpt)s: %(url)s : request time : %(time)s",
                    {
                        "cpt": i,
                        "url": url,
                        "time": core.last_req_time
                    }
                )
                self.log.info("result:")
                self.log.info(json.dumps(res, sort_keys=True, indent=2))
        self.log.info("End of raw command.")
        return True


class ListConfigCommand(DefaultCommand):
    """TODO"""

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


def add_parser(subparsers, config):
    """Add test commands."""
    parser = subparsers.add_parser('test', add_help=False)
    parser.add_argument('files', nargs='*')
    parser.set_defaults(__func__=TestCommand(config))

    parser = subparsers.add_parser('raw', add_help=True)
    parser.add_argument('url')
    parser.add_argument('-r', '--repeat', default=1, help="default=1", type=int)
    parser.add_argument(
        '-m', '--method',
        choices=["GET", "POST", "DELETE", "HEAD", "OPTIONS", "PUT"])
    parser.add_argument('--data')
    parser.set_defaults(__func__=RawCommand(config))

    parser = subparsers.add_parser('list')
    parser.set_defaults(__func__=ListConfigCommand(config))
