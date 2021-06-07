#! /usr/bin/env python
# -*- coding: utf-8 -*-
""""TODO"""
# FIXME fix all these warning
# pylint: disable=dangerous-default-value
# pylint: disable=protected-access
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=no-member
# pylint: disable=too-many-instance-attributes
# pylint: disable=attribute-defined-outside-init


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




import sys
import os
import logging
import json
import getpass
import datetime
import locale
import urllib.error
import copy
from warnings import warn
from argparse import ArgumentError
from humanfriendly import format_size
from argtoolbox import DefaultCompleter as Completer
from argtoolbox import DefaultCommand as DefaultCommandArgtoolbox
from linshareapi.core import LinShareException


def hook_file_content(path, context):
    """Return the content of the file pointed by path"""
    # pylint: disable=unused-argument
    with open(path, 'r') as fde:
        return fde.read()


class DefaultCommand(DefaultCommandArgtoolbox):
    """ If you want to add a new command to the command line interface, your
    class should extend this class.
    """
    # pylint: disable=line-too-long
    # pylint: disable=too-many-public-methods
    IDENTIFIER = "name"
    DEFAULT_SORT = "creationDate"
    DEFAULT_TOTAL = "Ressources found : %(count)s"
    RESOURCE_IDENTIFIER = "uuid"
    MSG_RS_NOT_FOUND = "No resources could be found."
    MSG_RS_DELETED = "%(position)s/%(count)s: The resource '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DELETED = "The resource '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s resource(s) can not be deleted."
    MSG_RS_DOWNLOADED = "%(position)s/%(count)s: The resource '%(name)s' (%(uuid)s) was downloaded. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One resource can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%(count)s resources can not be downloaded."
    MSG_RS_UPDATED = "The resource '%(name)s' (%(uuid)s) was successfully updated. (%(time)s s)"
    MSG_RS_CAN_NOT_BE_UPDATED = "One resource can not be updated."
    MSG_RS_CAN_NOT_BE_UPDATED_M = "%(count)s resources can not be updated."
    MSG_RS_CREATED = "The resource '%(name)s' (%(uuid)s) was successfully created. (%(_time)s s)"

    CFG_DOWNLOAD_MODE = 0
    CFG_DOWNLOAD_ARG_ATTR = "parent_uuid"
    CFG_DELETE_MODE = 0
    CFG_DELETE_ARG_ATTR = "parent_uuid"

    def __init__(self, config):
        super(DefaultCommand, self).__init__(config)
        self.api_version = config.server.api_version.value
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linsharecli.' + classname)
        self.verbose = False
        self.debug = False
        # pylint: disable=invalid-name
        self.ls = None
        self.enable_auth = True

    def __call__(self, args):
        super(DefaultCommand, self).__call__(args)
        self.verbose = args.verbose
        self.debug = args.debug

        if self.verbose:
            print("\nAPI VERSION:", self.api_version, "(See env variable LS_API).\n")

        if args.env_password:
            args.password = os.getenv('LS_PASSWORD')
        if args.password_from_env:
            args.password = os.getenv(args.password_from_env.upper())
        if args.ask_password:
            try:
                args.password = getpass.getpass("Please enter your password :")
            except KeyboardInterrupt:
                print("""\nKeyboardInterrupt exception was caught.
                Program terminated.""")
                sys.exit(1)

        if not args.password:
            raise ValueError("invalid password : password is not set ! ")

        self.ls = self.__get_cli_object(args)
        if args.nocache:
            self.ls.nocache = True
        if self.enable_auth:
            if not self.ls.auth():
                sys.exit(1)

    def __get_cli_object(self, args):
        """You must implement this method and return a object instance of
        CoreCli or its children in your Command class."""
        raise NotImplementedError(
            "You must implement the __get_cli_object method.")

    def _apply_to_all(self, args, cli, uuids, msg_m, func):
        warn("This method is deprecated, use DownloadAction instead",
             DeprecationWarning,
             stacklevel=2)
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            status = func(args, cli, uuid, position, count)
            # convert Boolean to integer, 0 ok, 1 fail
            res += abs(status - 1)
        if res > 0:
            meta = {'count': res}
            self.pprint(msg_m, meta)
            return False
        return True

    def _download_all(self, args, cli, uuids):
        warn("This method is deprecated, use DownloadAction instead",
             DeprecationWarning,
             stacklevel=2)
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            if self.CFG_DOWNLOAD_MODE == 0:
                status = self._download(args, cli, uuid, position, count)
            elif self.CFG_DOWNLOAD_MODE == 1:
                status = self._download_with_parent(args, cli, uuid, position, count)
            elif self.CFG_DOWNLOAD_MODE == 2:
                status = self._download_folder_with_parent(args, cli, uuid, position, count)
            else:
                raise NotImplementedError()
            res += abs(status - 1)
        if res > 0:
            meta = {'count': res}
            self.pprint(self.MSG_RS_CAN_NOT_BE_DOWNLOADED_M, meta)
            return False
        return True

    def _download(self, args, cli, uuid, position=None, count=None):
        warn("This method is deprecated, use DownloadAction instead",
             DeprecationWarning,
             stacklevel=2)
        directory = getattr(args, "directory", None)
        if directory:
            if not os.path.isdir(directory):
                os.makedirs(directory)
        meta = {}
        meta['uuid'] = uuid
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        progress_bar = not getattr(args, 'no_progress', False)
        cli_mode = getattr(args, 'cli_mode', False)
        if cli_mode:
            progress_bar = False
        try:
            if getattr(args, "dry_run", False):
                json_obj = cli.get(uuid)
                meta['name'] = json_obj.get('name')
            else:
                file_name, req_time = cli.download(uuid, directory,
                                                   progress_bar=progress_bar)
                meta['name'] = file_name
                meta['time'] = req_time
            if getattr(args, 'cli_mode', False):
                print(uuid)
            else:
                self.pprint(self.MSG_RS_DOWNLOADED, meta)
            return True
        except urllib.error.HTTPError as ex:
            meta['code'] = ex.code
            meta['ex'] = str(ex)
            if ex.code == 404:
                self.pprint_error("http error : %(ex)s", meta)
                self.pprint_error("Can not download the missing document : %(uuid)s", meta)
            return False

    def _download_with_parent(self, args, cli, uuid, position=None, count=None):
        warn("This method is deprecated, use DownloadAction instead",
             DeprecationWarning,
             stacklevel=2)
        directory = getattr(args, "directory", None)
        if directory:
            if not os.path.isdir(directory):
                os.makedirs(directory)
        meta = {}
        meta['uuid'] = uuid
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        try:
            parent_uuid = getattr(args, self.CFG_DOWNLOAD_ARG_ATTR, None)
            if not parent_uuid:
                raise ValueError("missing required arg : " + self.CFG_DOWNLOAD_ARG_ATTR)
            if getattr(args, "dry_run", False):
                json_obj = cli.get(parent_uuid, uuid)
                meta['name'] = json_obj.get('name')
            else:
                file_name, req_time = cli.download(parent_uuid, uuid, directory)
                meta['name'] = file_name
                meta['time'] = req_time
            self.pprint(self.MSG_RS_DOWNLOADED, meta)
            return True
        except urllib.error.HTTPError as ex:
            self.log.debug("http error : %s", ex.code)
            meta['code'] = ex.code
            meta['ex'] = str(ex)
            if ex.code == 404:
                self.pprint_error("Can not find and download the document : %(uuid)s", meta)
            elif ex.code == 400:
                json_obj = cli.core.get_json_result(ex)
                meta.update(json_obj)
                self.pprint_error("%(message)s : %(uuid)s (error: %(errCode)s)", meta)
            return False

    def _download_folder_with_parent(self, args, cli, uuid, position=None, count=None):
        warn("This method is deprecated, use DownloadAction instead",
             DeprecationWarning,
             stacklevel=2)
        meta = {}
        meta['uuid'] = uuid
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        dry_run = getattr(args, "dry_run", False)
        try:
            parent_uuid = getattr(args, self.CFG_DOWNLOAD_ARG_ATTR, None)
            if not parent_uuid:
                raise ValueError("missing required arg : " + self.CFG_DOWNLOAD_ARG_ATTR)
            json_obj = cli.get(parent_uuid, uuid)
            meta['name'] = json_obj.get('name')
            if json_obj.get('type') == "FOLDER":
                # recursive
                args_copy = copy.copy(args)
                directory = getattr(args_copy, "directory", None)
                if directory:
                    directory += "/" + json_obj.get('name')
                else:
                    directory = json_obj.get('name')
                if not os.path.isdir(directory) and not dry_run:
                    os.makedirs(directory)
                args_copy.directory = directory
                res = 0
                for nested in cli.list(parent_uuid, uuid):
                    if nested.get('type') == "FOLDER":
                        # dirty way to manage folder in folder. :(
                        # TODO Need full revamping of download methods.
                        args_copy2 = copy.copy(args_copy)
                        directory += "/" + json_obj.get('name')
                        self.pprint("Downloading folder : %(name)s (%(uuid)s)",
                                    nested)
                        status = self._download_folder_with_parent(
                            args_copy2, cli, nested.get('uuid'),
                            position, count)
                        continue
                    status = self._download_with_parent(args_copy, cli,
                                                        nested.get('uuid'), position, count)
                    res += abs(status - 1)
                if res > 0:
                    meta = {'count': res}
                    self.pprint(self.MSG_RS_CAN_NOT_BE_DOWNLOADED_M, meta)
                    return False
                return True
            elif json_obj.get('type') == "DOCUMENT":
                return self._download_with_parent(args, cli, uuid, position, count)
            else:
                return False
        except urllib.error.HTTPError as ex:
            self.log.debug("http error : %s", ex.code)
            meta['code'] = ex.code
            meta['ex'] = str(ex)
            if ex.code == 404:
                self.pprint_error("Can not find and download the document : %(uuid)s", meta)
            elif ex.code == 400:
                json_obj = cli.core.get_json_result(ex)
                meta.update(json_obj)
                self.pprint_error("%(message)s : %(uuid)s (error: %(errCode)s)", meta)
            return False

    def _delete_all(self, args, cli, uuids):
        warn("This method is deprecated, use DeleteAction instead",
             DeprecationWarning,
             stacklevel=2)
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            if self.CFG_DELETE_MODE == 0:
                status = self._delete(args, cli, uuid, position, count)
            elif self.CFG_DELETE_MODE == 1:
                status = self._delete_with_parent(args, cli, uuid, position, count)
            else:
                raise NotImplementedError()
            res += abs(status - 1)
        if res > 0:
            meta = {'count': res}
            cli_mode = getattr(args, 'cli_mode', False)
            if not cli_mode:
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED_M, meta)
            return False
        return True

    def _delete(self, args, cli, uuid, position=None, count=None):
        warn("This method is deprecated, use DeleteAction instead",
             DeprecationWarning,
             stacklevel=2)
        cli_mode = getattr(args, 'cli_mode', False)
        try:
            if not position:
                position = 1
                count = 1
            meta = {}
            meta['uuid'] = uuid
            meta[self.RESOURCE_IDENTIFIER] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            if getattr(args, "dry_run", False):
                json_obj = cli.get(uuid)
            else:
                json_obj = cli.delete(uuid)
                meta['time'] = self.ls.last_req_time
            if not json_obj:
                meta = {'uuid': uuid}
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED, meta)
                return False
            if cli_mode:
                print((json_obj.get(self.RESOURCE_IDENTIFIER)))
            else:
                meta[self.IDENTIFIER] = json_obj.get(self.IDENTIFIER)
                self.pprint(self.MSG_RS_DELETED, meta)
            return True
        except (urllib.error.HTTPError, LinShareException) as ex:
            self.log.error("Delete error : %s", ex)
            return False

    def _delete_with_parent(self, args, cli, uuid, position=None, count=None):
        warn("This method is deprecated, use DeleteAction instead",
             DeprecationWarning,
             stacklevel=2)
        try:
            if not position:
                position = 1
                count = 1
            meta = {}
            meta['uuid'] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            parent_uuid = getattr(args, self.CFG_DELETE_ARG_ATTR, None)
            if not parent_uuid:
                raise ValueError("missing required arg : " + self.CFG_DELETE_ARG_ATTR)
            if getattr(args, "dry_run", False):
                json_obj = cli.get(parent_uuid, uuid)
            else:
                json_obj = cli.delete(parent_uuid, uuid)
                meta['time'] = self.ls.last_req_time
            if not json_obj:
                meta = {'uuid': uuid}
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED, meta)
                return False
            meta[self.IDENTIFIER] = json_obj.get(self.IDENTIFIER)
            self.pprint(self.MSG_RS_DELETED, meta)
            return True
        except (urllib.error.HTTPError, LinShareException) as ex:
            self.log.error("Delete error : %s", ex)
            return False

    def _update(self, args, cli, resource, position=None, count=None):
        warn("This method is deprecated, use TableAction instead",
             DeprecationWarning,
             stacklevel=2)
        try:
            if not position:
                position = 1
                count = 1
            meta = {}
            if resource.get(self.IDENTIFIER) is None:
                raise ValueError("missing resource uuid/identifier")
            meta[self.IDENTIFIER] = resource.get(self.IDENTIFIER)
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            if getattr(args, "dry_run", False):
                json_obj = resource
            else:
                json_obj = cli.update(resource)
                meta['time'] = self.ls.last_req_time
            if not json_obj:
                self.pprint(self.MSG_RS_CAN_NOT_BE_UPDATED, meta)
                return False
            meta[self.IDENTIFIER] = json_obj.get(self.IDENTIFIER)
            self.pprint(self.MSG_RS_UPDATED, meta)
            return True
        except (urllib.error.HTTPError, LinShareException) as ex:
            self.log.error("Update error : %s", ex)
            return False

    def _run(self, method, message_ok, err_suffix, *args):
        warn("This method is deprecated, use TableAction instead",
             DeprecationWarning,
             stacklevel=2)
        try:
            json_obj = method(*args)
            if self.debug:
                self.pretty_json(json_obj)
            self.log.info(message_ok, json_obj)
            return True
        except LinShareException as ex:
            self.log.debug("LinShareException : %s", ex.args)
            self.log.error(ex.args[1] + " : " + err_suffix)
        return False

    def pprint(self, msg, meta={}):
        """TODO"""
        msg = msg % meta
        self.log.debug(msg)
        print(msg)

    def pprint_warn(self, msg, meta={}):
        """TODO"""
        msg = "WARN: " + msg % meta
        self.log.warning(msg)
        print(msg)

    def pprint_error(self, msg, meta={}):
        """TODO"""
        msg = "ERROR: " + msg % meta
        self.log.error(msg)
        print(msg)

    # pylint: disable=no-self-use
    def pretty_json(self, obj):
        """Just a pretty printer for a json object."""
        print((json.dumps(obj, sort_keys=True, indent=2)))

    def get_legend(self, data):
        """Extract the key of the first row of the input dict. Then it
        builds a title for every key and store them in a dictionary
        which will be return as result."""
        legend = dict()
        for line in data:
            for i in line:
                legend[i] = i.upper()
            break
        return legend

    def add_legend(self, data):
        """Adding title for column to the input data"""
        data.insert(0, self.get_legend(data))

    def format_date(self, data, attr, dformat="%Y-%m-%d %H:%M:%S"):
        """The current fied is replaced by a formatted date. The previous
        field is saved to a new field called 'field_raw'."""

        for row in data:
            date = "{da:" + dformat + "}"
            row[attr + "_raw"] = row[attr]
            ldate = row.get(attr)
            if not  ldate:
                row[attr] = ""
            else:
                row[attr] = date.format(
                    da=datetime.datetime.fromtimestamp(ldate / 1000))

    def format_filesize(self, data, attr):
        """The current fied is replaced by a formatted date. The previous
        field is saved to a new field called 'field_raw'."""
        for row in data:
            row[attr + "_raw"] = row[attr]
            row[attr] = format_size(row[attr])

    def getmaxlength(self, data):
        """TODO"""
        maxlength = {}
        for row in data:
            for key, val in list(row.items()):
                if not  maxlength.get(key, False):
                    maxlength[key] = len(repr(val))
                else:
                    maxlength[key] = max((len(repr(val)), maxlength[key]))
        self.log.debug(str(maxlength))
        return maxlength

    def getdatatype(self, data):
        """TODO"""
        res = {}
        fields = self.get_legend(data)
        if fields:
            row = data[0]
            for field in list(row.keys()):
                res[field] = type(row[field])
        return res

    def build_on_field(self, name, maxlength, datatype, factor=1.3,
                       suffix="s}  "):
        """TODO"""
        if datatype[name] == int:
            return "{" + name + "!s:" + str(int(maxlength[name] *
                                                factor)) + suffix
        if datatype[name] == int:
            return "{" + name + "!s:" + str(int(maxlength[name] *
                                                factor)) + suffix
        if datatype[name] == bool:
            return "{" + name + "!s:" + str(int(maxlength[name] *
                                                factor)) + suffix
        return "{" + name + ":" + str(int(maxlength[name] *
                                          factor)) + suffix

    def print_fields(self, data):
        """TODO"""
        fields = self.get_legend(data)
        if fields:
            _title = "Available returned fields :"
            print(("\n" + _title))
            print((self.get_underline(_title)))
            if data:
                row = data[0]
                keys = sorted(list(row.keys()))
                maxlengh = int(max([len(x) for x in keys]) * 1.3)
                d_format = "{field:" + str(maxlengh) + "s}{typ:^10s}"
                for field in keys:
                    print((str(d_format).format(**{
                        'field': field,
                        'typ': type(row[field]),
                    })))

    def get_underline(self, title):
        """Return a string with the '-' character, used to underline a title.
        the first argument is the title to underline."""
        sub = ""
        # pylint: disable=unused-variable
        for i in range(0, len(title)):
            sub += "-"
        return sub

    def print_title(self, data, title):
        """Just print to stdout a list of data with its title."""
        _title = title.strip() + " : (" + str(len(data)) + ")"
        print(("\n" + _title))
        print((self.get_underline(_title)))

    def print_list(self, data, d_format, title=None, t_format=None,
                   no_legend=False):
        """The input list is printed out using the d_format parametter.
        A Legend is built using field names."""

        if not t_format:
            t_format = d_format
        if title:
            self.print_title(data, title)
        if not  no_legend:
            legend = self.get_legend(data)
            if legend:
                print((t_format.format(**legend)))
        for row in data:
            print((str(d_format).format(**row)))
        if title:
            print("")

    def print_test(self, data):
        """Just for test"""
        # test
        # compute max lengh by column.
        res = {}
        for i in data:
            for j in i:
                res[j] = max([len(str(i.get((j)))), res.get(j, 0)])
        print(res)

    def print_table_test_1(self, json_obj, sortby, reverse=False, keys=[],
                           output_format=None, no_title=False,
                           no_legend=False):
        """TODO"""
        # computing data for presentation
        maxlength = self.getmaxlength(json_obj)
        datatype = self.getdatatype(json_obj)

        # computing string format
        d_format = ""
        if output_format:
            d_format = output_format
            d_format = d_format.decode(locale.getpreferredencoding())
        else:
            for key in keys:
                d_format += self.build_on_field(key, maxlength, datatype)

        if sortby:
            json_obj = sorted(json_obj, reverse=reverse, key=lambda x: x.get(sortby))

        if no_title:
            self.print_list(json_obj, d_format, no_legend=no_legend)
        else:
            self.print_list(json_obj, d_format, "Documents",
                            no_legend=no_legend)

    def check_required_options(self, args, required_fields, options):
        """Check if at least one option is set among the required_fields list"""
        one_set = False
        for i in required_fields:
            if getattr(args, i, None) is not None:
                one_set = True
                break
        if not one_set:
            msg = "You need to choose at least one option among : "
            msg += " or ".join(options)
            raise ArgumentError(None, msg)

    def check_required_options_v2(self, args, parser):
        """TODO"""
        options = []
        one_set = False
        for i in getattr(parser, '_group_actions'):
            options += i.option_strings
            if getattr(args, i.dest, None) is not None:
                one_set = True
                break
        if not one_set:
            msg = "You need to choose at least one option among:"
            msg += " or ".join(options)
            raise ArgumentError(None, msg)


def add_list_parser_options(parser, download=False, delete=False, cdate=False):
    """Add default argparse options for all ListCommands."""
    # filters
    filter_group = parser.add_argument_group('Filters')
    filter_group.add_argument(
        '--start', action="store", type=int, default=0,
        help="Print all left rows after the first n rows.")
    filter_group.add_argument(
        '--end', action="store", type=int, default=0,
        help="Print the last n rows.")
    filter_group.add_argument(
        '--limit', action="store", type=int, default=0,
        help="Used to limit the number of row to print.")
    if cdate:
        filter_group.add_argument(
            '--date', action="store", dest="cdate",
            help="Filter on creation date")
    filter_group.add_argument(
        '-k', '--field', action='append', dest="fields"
        ).completer = Completer("complete_fields")

    # sort
    sort_group = parser.add_argument_group('Sort')
    sort_group.add_argument(
        '-r', '--reverse', action="store_true",
        help="Reverse order while sorting")
    sort_group.add_argument(
        '--sort-by', action="store", default=None,
        help="Sort by column.")

    format_group = add_list_parser_options_format(parser)

    # actions
    actions_group = parser.add_argument_group('Actions')
    download_group = parser.add_argument_group('Downloading options')
    actions_group.add_argument(
        '-c', '--count', action="store_true", dest="count_only",
        help="Just display number of results instead of results.")
    if download or delete:
        if download:
            download_group.add_argument(
                '-o', '--output-dir', action="store",
                dest="directory")
            download_group.add_argument('--no-progress', action="store_true",
                                        help="disable progress bar.",
                                        default=False)
        if download and delete:
            group = actions_group.add_mutually_exclusive_group()
            if download:
                group.add_argument('-d', '--download', action="store_true")
            if delete:
                group.add_argument('-D', '--delete', action="store_true")
        else:
            if download:
                actions_group.add_argument('-o', '--output-dir',
                                           action="store", dest="directory")
                actions_group.add_argument(
                    '-d', '--download', action="store_true")
            if delete:
                actions_group.add_argument(
                    '-D', '--delete', action="store_true")
        actions_group.add_argument('--dry-run', action="store_true")
    return filter_group, sort_group, format_group, actions_group

def add_list_parser_options_format(parser):
    """Add formatting argparse options for all ListCommands."""
    # format
    format_group = parser.add_argument_group('Format')
    format_group.add_argument(
        '--extended', action="store_true",
        help="Display results using extended format.")
    format_group.add_argument(
        '-t', '--vertical', action="store_true",
        help="Display results using vertical output mode")
    format_group.add_argument('--json', action="store_true", help="Json output")
    format_group.add_argument(
        '--raw-json', action="store_true",
        help="Display every attributes for json output.")
    format_group.add_argument('--csv', action="store_true", help="Csv output")
    format_group.add_argument(
        '--no-headers', action="store_true",
        help="Do not display csv headers.")
    format_group.add_argument(
        '--raw', action="store_true",
        help="Disable all data formatters (time, size, ...)")
    format_group.add_argument('--cli-mode', action="store_true",
                              help="""Cli mode will format output to be used in
                              a script, by returning only identifiers or numbers
                              without any information messages.""")
    return format_group

def add_delete_parser_options(parser, method=None):
    """TODO"""
    if method:
        parser.add_argument('uuids', nargs='+').completer = Completer(method)
    else:
        parser.add_argument('uuids', nargs='+').completer = Completer()
    parser.add_argument('--dry-run', action="store_true")

def add_download_parser_options(parser, method=None):
    """TODO"""
    if method:
        parser.add_argument('uuids', nargs='+').completer = Completer(method)
    else:
        parser.add_argument('uuids', nargs='+').completer = Completer()
    parser.add_argument('--dry-run', action="store_true")
    parser.add_argument('-o', '--output-dir', action="store", dest="directory")
    parser.add_argument('--no-progress', action="store_true",
                        help="Do not display progress bar.")
