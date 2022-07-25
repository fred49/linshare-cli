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
import logging
import argtoolbox
from requests import Request

from argtoolbox import DefaultCompleter as Completer
from linshareapi.admin import AdminCli
from linshareapi.core import trace_session
from linshareapi.core import trace_request
from linshareapi.core import LinShareException
from linsharecli.common.core import add_list_parser_options
import linsharecli.common.core as common
from vhatable.core import TableFactory
from vhatable.cell import DateCell
from vhatable.cell import SizeCell
from vhatable.cell import ComplexCellBuilder


class DefaultCommand(common.DefaultCommand):
    """ Default command object use by the serer API. If you want to add a new
    command to the command line interface, your class should extend this class.
    """

    IDENTIFIER = "name"
    RESOURCE_IDENTIFIER = "uuid"

    def __get_cli_object(self, args):
        api_version = self.config.server.api_version.value
        self.log.debug("using api version : " + str(api_version))
        auth_type = args.auth_type
        password = args.password
        self.log.debug("auth_type: %s", auth_type)
        self.log.debug("password: %s...", password[0:2])
        if auth_type == "plain-b64":
            if password:
                self.log.debug(
                        "converting base64 encoded password to plain text.")
                password = base64.b64decode(password).decode('utf-8')
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
        if args.jq:
            self.log.setLevel(logging.ERROR)
        self.log.info("Begin of raw command.")
        core = self.ls.raw.core
        trace_session(core.session)
        method = 'GET'
        if args.method:
            method = args.method
        url = core.get_full_url(args.url)
        for i in range(1, args.repeat + 1):
            self.log.debug("list url:%s: %s", i, url)
            if args.data:
                request = Request(method, url, data=args.data)
            else:
                request = Request(method, url)
            prepped = core.session.prepare_request(request)
            if args.headers:
                headers = {}
                for item in args.headers:
                    key, val = item.split(':')
                    headers[key] = val.rstrip()
                prepped.headers.update(headers)
            starttime = datetime.datetime.now()
            for header in prepped.headers.items():
                self.log.debug("prepped.header: %s", header)
            request = core.session.send(prepped)
            endtime = datetime.datetime.now()
            trace_request(request)
            last_req_time = str(endtime - starttime)
            content_type = request.headers.get('Content-Type')
            headers = [
                'Total-Elements',
                'Total-Pages',
                'Current-Page',
                'Current-Page-Size',
                'First',
                'Last'
            ]
            for header in headers:
                value = request.headers.get(header)
                if value:
                    self.log.info(header + ": " + str(value))
            if content_type == 'application/json':
                res = core.process_request(request, url)
                self.log.debug("res: %s", res)
                if args.output:
                    with open(args.output, 'w') as file_stream:
                        json.dump(res, file_stream, sort_keys=True, indent=2,
                                  ensure_ascii=False)
                elif not args.silent:
                    self.log.info("result: %s",
                                  json.dumps(res, sort_keys=True, indent=2,
                                             ensure_ascii=False))
                if args.jq:
                    print(json.dumps(res, sort_keys=True, ensure_ascii=False))
                if args.verbose:
                    self.log.info("Count: %s", len(res))
            else:
                if args.output:
                    with open(args.output, 'wb') as file_stream:
                        for line in request.iter_content(chunk_size=256):
                            if line:
                                file_stream.write(line)
                else:
                    self.log.warning("Can not process this query !")
                    self.log.warning(
                            "Unhandled result content type: %s", content_type)
                    self.log.warning("data: %s", request.text)
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


class AutoDiscoveryCommand(DefaultCommand):
    """Just call raw http urls"""
    # pylint: disable=too-few-public-methods

    def __call__(self, args):
        super().__call__(args)
        self.verbose = args.verbose
        self.debug = args.debug
        endpoint = self.ls.raw.core
        trace_session(endpoint.session)
        url = endpoint.get_full_url(args.url)
        request = endpoint.session.get(url)
        trace_request(request)
        res = endpoint.process_request(request, url)
        self.log.debug("res: %s", res)
        tbu = TableFactory(self.ls, endpoint)
        tbu.load_args(args)
        if len(res) == 0:
            print("No data to display")
            return True
        tbu.columns = list(res[0].keys())
        tbu.columns.sort()
        self.log.debug("colums: %s", tbu.columns)
        if "uuid" in tbu.columns:
            tbu.columns.remove("uuid")
            tbu.columns.insert(0, "uuid")
        # tbu.add_filters(PartialOr(self.IDENTIFIER, args.names, True))
        for cell in args.complex_cells:
            tbu.add_custom_cell(
                cell,
                ComplexCellBuilder('{name} ({uuid:.8})', '{name} ({uuid})')
            )
        for cell in args.date_cells:
            tbu.add_custom_cell(cell, DateCell)
        for cell in args.size_cells:
            tbu.add_custom_cell(cell, SizeCell)
        return tbu.build().load_v2(res).render()


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
    parser.add_argument(
            '-r', '--repeat', default=1,
            help="default=1", type=int)
    parser.add_argument(
        '-m', '--method',
        choices=["GET", "POST", "DELETE", "HEAD", "OPTIONS", "PUT"])
    parser.add_argument('--data')
    parser.add_argument('-H', '--header', action="append", dest="headers")
    parser.add_argument('--output')
    parser.add_argument(
            '-s', '--silent', action="store_true",
            help="Do not display the payload")
    parser.add_argument(
            '--jq', action="store_true",
            help="pure json only")
    parser.set_defaults(__func__=RawCommand(config))

    parser = subparsers.add_parser('auto')
    parser.add_argument('url')
    parser.add_argument(
        '-x', '--complex-cells', action="append",
        default=[],
        help=(
            "Wil try to format these cells with default complex cell"
            " formatter: {name} ({uuid})"
        )
    ).completer = Completer("complete_fields")
    parser.add_argument(
        '-z', '--size-cells', action="append",
        default=[],
        help="Will try to format these cells with default size cell formatter"
    ).completer = Completer("complete_fields")
    parser.add_argument(
        '-a', '--date-cells', action="append",
        default=[],
        help="Will try to format these cells with default size cell formatter"
    ).completer = Completer("complete_fields")
    add_list_parser_options(parser)
    parser.set_defaults(__func__=AutoDiscoveryCommand(config))

    parser = subparsers.add_parser('list')
    parser.set_defaults(__func__=ListConfigCommand(config))
