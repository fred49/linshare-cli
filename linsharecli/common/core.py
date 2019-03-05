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


from __future__ import unicode_literals

import sys
import os
import logging
import json
import getpass
import datetime
import locale
import urllib2
import types
import copy
from veryprettytable import VeryPrettyTable
from ordereddict import OrderedDict
from hurry.filesize import size as filesize
from linshareapi.core import LinShareException
from linshareapi.cache import Time
import argtoolbox
from argtoolbox import DefaultCompleter as Completer


def hook_file_content(path, context):
    """Return the content of the file pointed by path"""
    # pylint: disable=unused-argument
    with open(path, 'r') as fde:
        return fde.read()


class DefaultCommand(argtoolbox.DefaultCommand):
    """ If you want to add a new command to the command line interface, your
    class should extend this class.
    """
    # pylint: disable=line-too-long
    IDENTIFIER = "name"
    DEFAULT_SORT = "creationDate"
    DEFAULT_SORT_SIZE = "size"
    DEFAULT_SORT_NAME = "name"
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

    ACTIONS = {
        'delete' : '_delete_all',
        'download' : '_download_all',
        'count_only' : '_count_only',
    }

    def __init__(self, config):
        super(DefaultCommand, self).__init__(config)
        self.api_version = config.server.api_version.value
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linsharecli.' + classname)
        self.verbose = False
        self.debug = False
        #pylint: disable=C0103
        self.ls = None

    def __call__(self, args):
        super(DefaultCommand, self).__call__(args)
        self.verbose = args.verbose
        self.debug = args.debug

        if args.env_password:
            args.password = os.getenv('LS_PASSWORD')
        if args.ask_password:
            try:
                args.password = getpass.getpass("Please enter your password :")
            except KeyboardInterrupt:
                print """\nKeyboardInterrupt exception was caught.
                Program terminated."""
                sys.exit(1)

        if not args.password:
            raise ValueError("invalid password : password is not set ! ")

        self.ls = self.__get_cli_object(args)
        if args.nocache:
            self.ls.nocache = True
        if not self.ls.auth():
            sys.exit(1)

    def __get_cli_object(self, args):
        """You must implement this method and return a object instance of
        CoreCli or its children in your Command class."""
        raise NotImplementedError(
            "You must implement the __get_cli_object method.")

    def _list(self, args, cli, table, json_obj, formatters=None, filters=None,
              ignore_exceptions={}):
        self.log.debug("table.sortby : %s", table.sortby)
        if table.sortby is None:
            table.sortby = self.DEFAULT_SORT
        # sort by size
        if getattr(args, 'sort_size', False):
            json_obj = sorted(json_obj, reverse=args.reverse, key=lambda x: x.get(self.DEFAULT_SORT_SIZE))
        if getattr(args, 'sort_name', False):
            table.sortby = self.DEFAULT_SORT_NAME
        cli_mode = getattr(args, 'cli_mode', False)
        self.log.debug("final table.sortby : %s", table.sortby)
        for key in self.ACTIONS:
            if getattr(args, key, False):
                table.load(json_obj, filters, formatters, ignore_exceptions)
                rows = table.get_raw()
                if key == 'count_only':
                    if cli_mode:
                        print len(rows)
                    else:
                        meta = {'count': len(rows)}
                        self.pprint(self.DEFAULT_TOTAL, meta)
                    return True
                else:
                    if len(rows) == 0:
                        if not cli_mode:
                            self.pprint(self.MSG_RS_NOT_FOUND)
                        return True
                    uuids = [row.get(self.RESOURCE_IDENTIFIER) for row in rows]
                    method = getattr(self, self.ACTIONS.get(key))
                    return method(args, cli, uuids)
        if cli_mode:
            keys = [self.RESOURCE_IDENTIFIER, ]
            if args.fields:
                keys = args.fields
            for json_row in json_obj:
                output = []
                for key in keys:
                    data = json_row.get(key)
                    if isinstance(data, types.UnicodeType):
                        output.append(data)
                    else:
                        output.append(str(data))
                print " ".join(output)
            return True
        table.show_table(json_obj, filters, formatters, ignore_exceptions)
        meta = {'count': len(table.get_raw())}
        self.pprint(self.DEFAULT_TOTAL, meta)
        return True

    def _apply_to_all(self, args, cli, uuids, msg_m, func):
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
                print uuid
            else:
                self.pprint(self.MSG_RS_DOWNLOADED, meta)
            return True
        except urllib2.HTTPError as ex:
            meta['code'] = ex.code
            meta['ex'] = str(ex)
            if ex.code == 404:
                self.pprint_error("http error : %(ex)s", meta)
                self.pprint_error("Can not download the missing document : %(uuid)s", meta)
            return False

    def _download_with_parent(self, args, cli, uuid, position=None, count=None):
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
        except urllib2.HTTPError as ex:
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
        except urllib2.HTTPError as ex:
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
                print json_obj.get(self.RESOURCE_IDENTIFIER)
            else:
                meta[self.IDENTIFIER] = json_obj.get(self.IDENTIFIER)
                self.pprint(self.MSG_RS_DELETED, meta)
            return True
        except (urllib2.HTTPError, LinShareException) as ex:
            self.log.error("Delete error : %s", ex)
            return False

    def _delete_with_parent(self, args, cli, uuid, position=None, count=None):
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
        except (urllib2.HTTPError, LinShareException) as ex:
            self.log.error("Delete error : %s", ex)
            return False

    def _update(self, args, cli, resource, position=None, count=None):
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
        except (urllib2.HTTPError, LinShareException) as ex:
            self.log.error("Update error : %s", ex)
            return False

    def _run(self, method, message_ok, err_suffix, *args):
        try:
            json_obj = method(*args)
            if self.debug:
                self.pretty_json(json_obj)
            self.log.info(message_ok, json_obj)
            return True
        except LinShareException as ex:
            self.log.debug("LinShareException : " + str(ex.args))
            self.log.error(ex.args[1] + " : " + err_suffix)
        return False

    def pprint(self, msg, meta={}):
        """TODO"""
        msg = msg % meta
        self.log.debug(msg)
        print msg

    def pprint_warn(self, msg, meta={}):
        """TODO"""
        msg = "WARN: " + msg % meta
        self.log.warn(msg)
        print msg

    def pprint_error(self, msg, meta={}):
        """TODO"""
        msg = "ERROR: " + msg % meta
        self.log.error(msg)
        print msg

    #pylint: disable=R0201
    def pretty_json(self, obj):
        """Just a pretty printer for a json object."""
        print json.dumps(obj, sort_keys=True, indent=2)

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
            row[attr + u"_raw"] = row[attr]
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
            row[attr + u"_raw"] = row[attr]
            row[attr] = filesize(row[attr])

    def getmaxlength(self, data):
        """TODO"""
        maxlength = {}
        for row in data:
            for key, val in row.items():
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
            for field in row.keys():
                res[field] = type(row[field])
        return res

    def build_on_field(self, name, maxlength, datatype, factor=1.3,
                       suffix=u"s}  "):
        """TODO"""
        if datatype[name] == int:
            return u"{" + name + u"!s:" + str(int(maxlength[name] *
                                                  factor)) + suffix
        elif datatype[name] == long:
            return u"{" + name + u"!s:" + str(int(maxlength[name] *
                                                  factor)) + suffix
        elif datatype[name] == bool:
            return u"{" + name + u"!s:" + str(int(maxlength[name] *
                                                  factor)) + suffix
        return u"{" + name + u":" + str(int(maxlength[name] *
                                            factor)) + suffix

    def print_fields(self, data):
        """TODO"""
        fields = self.get_legend(data)
        if fields:
            _title = "Available returned fields :"
            print "\n" + _title
            print self.get_underline(_title)
            if data:
                row = data[0]
                keys = row.keys()
                keys.sort()
                maxlengh = int(max([len(x) for x in keys]) * 1.3)
                d_format = u"{field:" + str(maxlengh) + u"s}{typ:^10s}"
                for field in keys:
                    print unicode(d_format).format(**{
                        'field': field,
                        'typ': type(row[field]),
                    })

    def get_underline(self, title):
        """Return a string with the '-' character, used to underline a title.
        the first argument is the title to underline."""
        sub = ""
        # pylint: disable=unused-variable
        for i in xrange(0, len(title)):
            sub += "-"
        return sub

    def print_title(self, data, title):
        """Just print to stdout a list of data with its title."""
        _title = title.strip() + " : (" + str(len(data)) + ")"
        print "\n" + _title
        print self.get_underline(_title)

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
                print t_format.format(**legend)
        for row in data:
            print unicode(d_format).format(**row)
        if title:
            print ""

    def print_test(self, data):
        """Just for test"""
        # test
        # compute max lengh by column.
        res = {}
        for i in data:
            for j in i:
                res[j] = max([len(str(i.get((j)))), res.get(j, 0)])
        print res

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

    def get_table(self, args, cli, first_column, in_keys=None, other_table=None):
        """TODO"""
        keys = []
        args.vertical = getattr(args, "vertical", False)
        if not args.vertical:
            if getattr(args, "json", False):
                args.vertical = True
            elif getattr(args, "csv", False):
                args.vertical = True
            else:
                for key in self.ACTIONS:
                    if getattr(args, key, False):
                        args.vertical = True
        args.reverse = getattr(args, "reverse", False)
        args.extended = getattr(args, "extended", False)
        if in_keys:
            keys += in_keys
            if self.IDENTIFIER not in in_keys:
                keys.insert(0, self.IDENTIFIER)
        else:
            keys = cli.get_rbu().get_keys(args.extended)
        table = None
        if args.vertical:
            table = VTable(keys, debug=self.debug)
        else:
            if other_table:
                table = ConsoleTable(keys, debug=self.debug)
            else:
                table = HTable(keys)
                # styles
                table.align[first_column] = "l"
                table.padding_width = 1
        table.sortby = None
        table.reversesort = args.reverse
        table.keys = keys
        table.json = getattr(args, "json", False)
        table.raw_json = getattr(args, "raw_json", False)
        table.csv = getattr(args, "csv", False)
        table.raw = getattr(args, "raw", False)
        table._pref_start = getattr(args, "start", 0)
        table._pref_end = getattr(args, "end", 0)
        table._pref_limit = getattr(args, "limit", 0)
        table._pref_no_csv_headers = getattr(args, "no_headers", True)
        # just backup args into table
        table.args = args
        return table

    def get_raw_table(self, args, cli, first_column, keys, other_table=None):
        """TODO"""
        # pylint: disable=unused-argument
        args.reverse = getattr(args, "reverse", False)
        args.extended = getattr(args, "extended", False)
        table = None
        if args.vertical:
            table = VTable(keys, debug=self.debug)
        else:
            if other_table:
                table = ConsoleTable(keys, debug=self.debug)
            else:
                table = HTable(keys)
                # styles
                table.align[first_column] = "l"
                table.padding_width = 1
        table.sortby = None
        table.reversesort = args.reverse
        table.keys = keys
        table.json = getattr(args, "json", False)
        table.raw_json = getattr(args, "raw_json", False)
        table.csv = getattr(args, "csv", False)
        table.raw = getattr(args, "raw", False)
        table._pref_start = getattr(args, "start", 0)
        table._pref_end = getattr(args, "end", 0)
        table._pref_limit = getattr(args, "limit", 0)
        table._pref_no_csv_headers = getattr(args, "no_headers", True)
        # just backup args into table
        table.args = args
        return table


def add_list_parser_options(parser, download=False, delete=False, cdate=False, ssize=False):
    """TODO"""
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
        '--sort-name', action="store_true",
        help="Sort by name")
    if ssize:
        sort_group.add_argument(
            '--sort-size', action="store_true",
            help="Sort by size")

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

# -----------------------------------------------------------------------------
def add_delete_parser_options(parser, method=None):
    """TODO"""
    if method:
        parser.add_argument('uuids', nargs='+').completer = Completer(method)
    else:
        parser.add_argument('uuids', nargs='+').completer = Completer()
    parser.add_argument('--dry-run', action="store_true")

# -----------------------------------------------------------------------------
def add_download_parser_options(parser, method=None):
    """TODO"""
    if method:
        parser.add_argument('uuids', nargs='+').completer = Completer(method)
    else:
        parser.add_argument('uuids', nargs='+').completer = Completer()
    parser.add_argument('--dry-run', action="store_true")
    parser.add_argument('-o', '--output-dir', action="store", dest="directory")


class AbstractTable(object):
    """TODO"""

    # pylint: disable=inconsistent-return-statements
    def filters(self, row, filters):
        """TODO"""
        # pylint: disable=no-self-use
        if filters is not None:
            if isinstance(filters, list):
                cpt = 0
                for func in filters:
                    if func.is_enable():
                        cpt += 1
                        if func(row):
                            return True
                if cpt == 0:
                    return True
            else:
                if filters.is_enable():
                    if filters(row):
                        return True
                else:
                    return True
        else:
            return True

    def formatters(self, row, formatters):
        """TODO"""
        if formatters is not None:
            if isinstance(formatters, list):
                for func in formatters:
                    func(row, context=self)
            else:
                formatters(row, context=self)

    def get_raw(self):
        """TODO"""
        raise NotImplementedError()

    def get_json(self):
        """TODO"""
        raise NotImplementedError()

    def get_csv(self):
        """TODO"""
        raise NotImplementedError()

    def load(self, json_obj, filters=None, formatters=None,
             ignore_exceptions={}):
        """TODO"""
        raise NotImplementedError()


class BaseTable(AbstractTable):
    """TODO"""

    vertical = True

    def __init__(self, keys=[], reverse=False, debug=0):
        self.debug = debug
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linsharecli.' + classname)
        self.keys = keys
        # field only use for compatibility with HTable
        self.align = {}
        self.start = None
        self.end = None
        self._rows = []
        self._maxlengthkey = 0
        self.reversesort = reverse
        for k in keys:
            self.sortby = k
            break

    @Time('linsharecli.core.load', label='time : %(time)s')
    def load(self, data, filters=None, formatters=None,
             ignore_exceptions={}):
        """TODO"""
        for row in data:
            if self.filters(row, filters):
                if not self.raw:
                    self.formatters(row, formatters)
                self.add_row(row)
        if self._pref_start > 0:
            self.start = self._pref_start
            limit = self._pref_limit
            if limit > 0:
                self.end = self.start + limit
        elif self._pref_end > 0:
            self.start = len(self._rows) - self._pref_end
            limit = self._pref_limit
            if limit > 0:
                self.end = self.start + limit
        elif self._pref_limit > 0:
            self.start = 1
            self.end = 1 + self._pref_limit

    def add_row(self, row):
        """TODO"""
        if self.debug >= 2:
            self.log.debug(row)
        if not isinstance(row, dict):
            raise ValueError("every row should be a dict")
        self._rows.append(row)

    def get_raw(self):
        """TODO"""
        if self.sortby:
            try:
                self._rows = sorted(self._rows, reverse=self.reversesort,
                                    key=lambda x: x.get(self.sortby))
            except KeyError as ex:
                self.log.warn("missing sortby key : " + str(ex))
        source = self._rows
        if self.start:
            source = source[self.start:]
            if self.end:
                source = source[:self.end - self.start]
        elif self.end:
            source = source[:self.end]
        return source

    def get_json(self):
        """TODO"""
        records = []
        if self.raw_json:
            return json.dumps(self.get_raw(), sort_keys=True, indent=2)
        for row in self.get_raw():
            record = {}
            for k in self.keys:
                record[k] = row.get(k)
            records.append(record)
        return json.dumps(records, sort_keys=True, indent=2)

    def get_csv(self):
        """TODO"""
        records = []
        if not self._pref_no_csv_headers:
            records.append(";".join(self.keys))
        for row in self.get_raw():
            record = []
            for k in self.keys:
                data = row.get(k)
                if isinstance(data, types.UnicodeType):
                    record.append(data)
                else:
                    record.append(str(data))
            records.append(";".join(record))
        return "\n".join(records)


class VTable(BaseTable):
    """TODO"""

    vertical = True

    @Time('linsharecli.core.show_table', label='time : %(time)s')
    def show_table(self, json_obj, filters=None, formatters=None,
                   ignore_exceptions={}):
        """TODO"""
        self.load(json_obj, filters, formatters, ignore_exceptions)
        if self.json:
            print self.get_json()
            return
        if self.csv:
            print self.get_csv()
            return
        out = self.get_string()
        print unicode(out)

    def get_string(self):
        """TODO"""
        max_length_line = 0
        records = []
        for row in self.get_raw():
            record = []
            for k in self.keys:
                t_format = u"{key:" + unicode(str(self._maxlengthkey)) + u"s} | {value:s}"
                dataa = None
                column_data = row.get(k)
                if isinstance(column_data, types.UnicodeType):
                    dataa = {"key": k, "value": column_data}
                else:
                    dataa = {"key": k, "value": str(column_data)}
                t_record = unicode(t_format).format(**dataa)
                record.append(t_record)
                max_length_line = max(max_length_line, len(t_record))
            records.append("\n".join(record))
        out = []
        cptline = 0
        for record in records:
            cptline += 1
            header = "-[ RECORD " + str(cptline) + " ]-"
            # pylint: disable=unused-variable
            header += "".join(["-" for i in xrange(max_length_line - len(header))])
            out.append(header)
            out.append(record)
        return "\n".join(out)

    def add_row(self, row):
        """TODO"""
        super(VTable, self).add_row(row)
        self.update_max_lengthkey(row)

    def update_max_lengthkey(self, row):
        """TODO"""
        for k in row:
            self._maxlengthkey = max((len(repr(k)), self._maxlengthkey))


class ConsoleTable(BaseTable):
    """TODO"""

    vertical = False

    @Time('linsharecli.core.show_table', label='time : %(time)s')
    def show_table(self, json_obj, filters=None, formatters=None,
                   ignore_exceptions={}):
        """TODO"""
        self.load(json_obj, filters, formatters, ignore_exceptions)
        if self.json:
            print self.get_json()
            return
        if self.csv:
            print self.get_csv()
            return
        for row in self.get_raw():
            record = []
            for k in self.keys:
                t_format = u"{value:s}"
                column_data = row.get(k)
                if isinstance(column_data, types.UnicodeType):
                    t_record = t_format.format(value=column_data)
                else:
                    t_record = t_format.format(value=str(column_data))
                record.append(t_record)
            print unicode(" ".join(record))


class HTable(VeryPrettyTable, AbstractTable):
    """TODO"""

    vertical = False

    @Time('linsharecli.core.load', label='time : %(time)s')
    def load(self, json_obj, filters=None, formatters=None,
             ignore_exceptions={}):
        """TODO"""
        for json_row in json_obj:
            data = OrderedDict()
            for key in self.keys:
                try:
                    data[key] = json_row[key]
                except KeyError as ex:
                    data[key] = None
                    if not ignore_exceptions.get(key, None):
                        ignore_exceptions[key] = True
                        print "WARN: KeyError: " + str(ex)
            if self.filters(data, filters):
                if not self.raw:
                    self.formatters(data, formatters)
                self.add_row(data.values())
        if self._pref_start > 0:
            self.start = self._pref_start
            limit = self._pref_limit
            if limit > 0:
                self.end = self.start + limit
        elif self._pref_end > 0:
            self.start = len(self._rows) - self._pref_end
            limit = self._pref_limit
            if limit > 0:
                self.end = self.start + limit

    @Time('linsharecli.core.show_table', label='time : %(time)s')
    def show_table(self, json_obj, filters=None, formatters=None,
                   ignore_exceptions={}):
        """TODO"""
        self.load(json_obj, filters, formatters, ignore_exceptions)
        out = self.get_string(fields=self.keys)
        print unicode(out)

    def get_raw(self):
        """TODO"""
        options = self._get_options({'fields': self.keys})
        return self._get_rows(options)

    def get_json(self):
        """TODO"""
        raise NotImplementedError()

    def get_csv(self):
        """TODO"""
        raise NotImplementedError()
