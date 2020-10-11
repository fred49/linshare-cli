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



import base64
import json
import datetime
import argtoolbox
from requests import Request

from linshareapi.admin import AdminCli
from linshareapi.core import LinShareException
import linsharecli.common.core as common



class DefaultCommand(common.DefaultCommand):
    """ Default command object use by the serer API. If you want to add a new
    command to the command line interface, your class should extend this class.
    """

    def __get_cli_object(self, args):
        api_version = self.config.server.api_version.value
        self.log.debug("using api version : " + str(api_version))
        auth_type = self.config.server.auth_type.value
        password = args.password
        if auth_type == "plain-b64":
            if password:
                password = base64.b64decode(password)
            auth_type = "plain"
        cli = AdminCli(args.host, args.user, password, args.verbose,
                       args.debug, api_version=api_version,
                       verify=getattr(args, 'verify', True),
                      auth_type=auth_type)
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
        print("Not Yet Implemented.")


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
        print("Test")
        print((str(self.config)))
        print(args)
        self.log.info("End of test command.")


class RawCommand(DefaultCommand):
    """Just call raw http urls"""
    # pylint: disable=too-few-public-methods

    def __call__(self, args):
        super(RawCommand, self).__call__(args)
        self.verbose = args.verbose
        self.debug = args.debug
        self.log.info("Begin of raw command.")
        method = 'GET'
        if args.method:
            method = args.method
        core = self.ls.raw.core
        url = core.get_full_url(args.url)
        for i in range(1, args.repeat + 1):
            self.log.debug("list url:%s: %s", i, url)
            if args.data:
                request = Request(method, url, data=args.data)
            else:
                request = Request(method, url)
            prepped = core.session.prepare_request(request)
            starttime = datetime.datetime.now()
            request = core.session.send(prepped)
            for header in request.headers.items():
                self.log.debug("request.header: %s", header)
            endtime = datetime.datetime.now()
            last_req_time = str(endtime - starttime)
            content_type = request.headers['Content-Type']
            if content_type == 'application/json':
                res = core.process_request(request, url)
                self.log.debug("res: %s", res)
                if args.output:
                    with open(args.output, 'w') as file_stream:
                        json.dump(res, file_stream, sort_keys=True, indent=2, ensure_ascii=False)
                else:
                    self.log.info("result: %s",
                                  json.dumps(res, sort_keys=True, indent=2, ensure_ascii=False))
            else:
                if args.output:
                    with open(args.output, 'wb') as file_stream:
                        for line in request.iter_content(chunk_size=256):
                            if line:
                                file_stream.write(line)
                else:
                    self.log.error("Can not process this query, unhandled result content type: %s", content_type)
            self.log.info(
                "url:%(cpt)s:%(url)s:request time: %(time)s",
                {
                    "cpt": i,
                    "url": url,
                    "time": last_req_time
                }
            )
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
        print()
        print("Available sections:")
        print("===================")
        print()
        for i in seclist:
            if i.startswith("server-"):
                print(" - " + "-".join(i.split('-')[1:]))
        print("")


def add_parser(subparsers, name, desc, config):
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
    parser.add_argument('--output')
    parser.set_defaults(__func__=RawCommand(config))

    parser = subparsers.add_parser('list')
    parser.set_defaults(__func__=ListConfigCommand(config))
