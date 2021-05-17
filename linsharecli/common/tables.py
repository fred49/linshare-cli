#! /usr/bin/env python
# -*- coding: utf-8 -*-
""""TODO"""

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
# Copyright 2019 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#





import os
import json
import types
import logging
import urllib.request, urllib.error, urllib.parse

from linshareapi.cache import Time
from linshareapi.core import LinShareException
from collections import OrderedDict
from veryprettytable import VeryPrettyTable
from linsharecli.common.cell import CellFactory

class AbstractTable(object):
    """TODO"""

    DEFAULT_TOTAL = "\nRessources found : %(count)s"

    log = None
    vertical = False
    csv = False
    json = False
    debug = 0
    verbose = False
    extended = False
    raw = False
    no_cell = False
    cli_mode = False
    cfa = CellFactory(False, False, 0)
    keys = []
    args = None
    cli = None
    endpoint = None
    _filters = []
    _formatters = []
    _pre_render_classes = []

    def filters(self, row, filters):
        """TODO"""
        if filters is not None:
            if isinstance(filters, list):
                matches = 0
                enabled_filters = 0
                for func in filters:
                    self.log.debug("filter: %s (enabled=%s)", func, func.is_enable())
                    if func.is_enable():
                        enabled_filters += 1
                        if func(row):
                            matches += 1
                self.log.debug("matches: %s", matches)
                self.log.debug("enabled_filters: %s", enabled_filters)
                if enabled_filters == 0:
                    return True
                if matches == enabled_filters:
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

    def load(self, json_obj, filters=None, formatters=None):
        """TODO"""
        raise NotImplementedError()

    def load_v2(self, json_list):
        """Load list of json objects into the table"""
        self.load(json_list, self._filters, self._formatters)
        return self

    def _transform_to_cell(self, json_row, off=False):
        """TODO"""
        if off:
            return json_row
        if self.debug >= 2:
            self.log.debug("begin row")
        row_full = OrderedDict()
        row_light = OrderedDict()
        keys = list(self.keys)
        keys += list(json_row.keys())
        keys = list(OrderedDict.fromkeys(keys))
        if self.debug >= 2:
            self.log.debug("all keys: %s ", keys)
        for key in keys:
            value = None
            if key in json_row:
                value = json_row[key]
            else:
                self.log.debug("key not found: %s", key)
            if self.debug >= 2:
                self.log.debug("key: %s ", key)
            cell = self.cfa(key, value, row_full)
            # FIXME
            cell.hidden = False
            cell.extended = self.extended
            row_full[key] = cell
            if key in self.keys:
                row_light[key] = cell
            else:
                cell.hidden = True
        if self.debug >= 2:
            self.log.debug("end row")
        return row_light

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        raise NotImplementedError()

    def get_string(self):
        """TODO"""
        raise NotImplementedError()

    def pprint(self, msg, meta=None):
        """TODO"""
        if meta:
            msg = msg % meta
        self.log.debug(msg)
        print(msg)

    def _display_nb_elts(self):
        """TODO"""
        if self.verbose:
            meta = {'count': len(self.get_raw())}
            self.pprint(self.DEFAULT_TOTAL, meta)
        return True

    def _pre_render(self):
        """Trigger some classes before rendering filtered data."""
        for clazz in self._pre_render_classes:
            self.log.debug(clazz)
            clazz(self.args, self.cli, self.endpoint, self.get_raw())

    def add_pre_render_class(self, clazz):
        """TODO"""
        self._pre_render_classes.append(clazz)


class BaseTable(AbstractTable):
    """TODO"""
    # pylint: disable=too-many-instance-attributes
    vertical = True
    start = 0
    end = 0
    _pref_start = 0
    _pref_end = 0
    _pref_limit = 0
    raw_json = False
    _pref_no_csv_headers = False

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
        self.no_cell = False
        for k in keys:
            self.sortby = k
            break
        self.log.debug("sortby(first column): %s", self.sortby)

    def load(self, data, filters=None, formatters=None,
             ignore_exceptions=None):
        # pylint: disable=unused-argument
        # Only for compatibility with older lines of code.
        """TODO"""
        self.log.debug("keys: %s", self.keys)
        for row in data:
            row = self._transform_to_cell(row, self.no_cell)
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
            self.start = 0
            self.end = 0 + self._pref_limit

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
                if isinstance(data, str):
                    record.append(data)
                else:
                    data_str = str(data)
                    record.append(data_str)
            records.append(";".join(record))
        return "\n".join(records)

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        if self.json:
            print(self.get_json())
            return True
        if self.csv:
            print(self.get_csv())
            return True
        out = self.get_string()
        self._pre_render()
        print(str(out))
        self._display_nb_elts()
        return True


class VTable(BaseTable):
    """TODO"""

    vertical = True

    def get_string(self):
        """TODO"""
        max_length_line = 0
        records = []
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger(classname)
        for row in self.get_raw():
            record = []
            for k in self.keys:
                try:
                    t_format = "{key:" + str(self._maxlengthkey) + "s} | {value:s}"
                    dataa = None
                    column_data = row.get(k)
                    if isinstance(column_data, str):
                        dataa = {"key": k, "value": column_data}
                    else:
                        column_data_str = str(column_data)
                        dataa = {"key": k, "value": column_data_str}
                    t_record = t_format.format(**dataa)
                    record.append(t_record)
                    max_length_line = max(max_length_line, len(t_record))
                except UnicodeEncodeError as ex:
                    self.log.error("UnicodeEncodeError: %s", ex)
                    dataa = {"key": k, "value": "UnicodeEncodeError"}
                    t_record = str(t_format).format(**dataa)
                    record.append(t_record)
            records.append("\n".join(record))
        out = []
        cptline = 0
        for record in records:
            cptline += 1
            header = "-[ RECORD " + str(cptline) + " ]-"
            # pylint: disable=unused-variable
            header += "".join(["-" for i in range(max_length_line - len(header))])
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

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        if self.json:
            print(self.get_json())
            return True
        if self.csv:
            print(self.get_csv())
            return True
        self._pre_render()
        for row in self.get_raw():
            record = []
            for k in self.keys:
                try:
                    t_format = "{value:s}"
                    column_data = row.get(k)
                    if isinstance(column_data, str):
                        t_record = t_format.format(value=column_data)
                    else:
                        t_record = t_format.format(value=column_data)
                    record.append(t_record)
                except UnicodeEncodeError as ex:
                    self.log.error("UnicodeEncodeError: %s", ex)
                    record.append("UnicodeEncodeError")
            print(str(" ".join(record)))
        self._display_nb_elts()
        return True


class HTable(BaseTable):
    """TODO"""
    # pylint: disable=too-many-instance-attributes

    def get_string(self):
        """TODO"""
        table = VeryPrettyTable()
        table.field_names = self.keys
        table.align = 'l'
        for row in self.get_raw():
            data = []
            for colum in self.keys:
                data.append(row.get(colum))
            table.add_row(data)
        return table.get_string()


class Action(object):
    """TODO"""

    no_cell = True

    def __init__(self):
        self.cli_mode = False
        self.verbose = False
        self.dry_run = False
        self.debug = 0
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linsharecli.' + classname)
        self.cli = None
        self.endpoint = None

    def init(self, args, cli, endpoint):
        """Init object members with values in args object"""
        self.cli = cli
        self.endpoint = endpoint
        for att in ['cli_mode', 'verbose', 'debug', 'dry_run']:
            if hasattr(args, att):
                setattr(self, att, getattr(args, att))

    def pprint(self, msg, meta=None):
        """TODO"""
        if meta:
            msg = msg % meta
        self.log.debug(msg)
        print(msg)

    def pprint_warn(self, msg, meta=None):
        """TODO"""
        if meta is None:
            meta = {}
        msg = "WARN: " + msg % meta
        self.log.warn(msg)
        print(msg)

    def pprint_error(self, msg, meta=None):
        """TODO"""
        if meta is None:
            meta = {}
        msg = "ERROR: " + msg % meta
        self.log.error(msg)
        print(msg)

    def pretty_json(self, obj):
        """Just a pretty printer for a json object."""
        # pylint: disable=no-self-use
        print((json.dumps(obj, sort_keys=True, indent=2)))

    def __call__(self, args, cli, endpoint, data):
        raise NotImplementedError()


class CountAction(Action):
    """TODO"""
    # pylint: disable=too-few-public-methods

    DEFAULT_TOTAL = "Ressources found : %(count)s"

    def __call__(self, args, cli, endpoint, data):
        """TODO"""
        self.init(args, cli, endpoint)
        if self.cli_mode:
            print((len(data)))
        else:
            meta = {'count': len(data)}
            self.pprint(self.DEFAULT_TOTAL, meta)
        return True


class CliModeAction(Action):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, identifier="uuid"):
        super(CliModeAction, self).__init__()
        self.identifier = identifier

    def __call__(self, args, cli, endpoint, data):
        """TODO"""
        self.init(args, cli, endpoint)
        for row in data:
            print((str(row.get(self.identifier))))
        return True


class SampleAction(Action):
    """TODO"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, name):
        super(SampleAction, self).__init__()
        self.name = name

    def __call__(self, args, cli, endpoint, data):
        """TODO"""
        self.init(args, cli, endpoint)
        print(("ACTION:", self.name))
        print(cli)
        print(endpoint)
        print(">--- Filtered data ----")
        for row in data:
            print(row)
        print("---- Filtered data ---<")
        return True


class DeleteAction(Action):
    """TODO"""

    MSG_RS_DELETED = (
        "%(position)s/%(count)s: "
        "The resource '%(name)s' (%(uuid)s) was deleted. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DELETED = "The resource '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s resource(s) can not be deleted."

    def __init__(self, mode=0,
                 identifier="name",
                 resource_identifier="uuid",
                 parent_identifier="parent_uuid"
                ):
        super(DeleteAction, self).__init__()
        self.cfg_mode = mode
        self.parent_uuid = None
        self.identifier = identifier
        self.resource_identifier = resource_identifier
        self.parent_identifier_attr = parent_identifier

    def init(self, args, cli, endpoint):
        super(DeleteAction, self).init(args, cli, endpoint)
        if self.cfg_mode == 1:
            self.parent_uuid = getattr(args, self.parent_identifier_attr, None)
            if not self.parent_uuid:
                raise ValueError("missing required arg : " + self.parent_identifier_attr)
        return self

    def delete(self, uuids):
        """TODO"""
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            if self.cfg_mode == 0:
                status = self._delete(uuid, position, count)
            elif self.cfg_mode == 1:
                status = self._delete_with_parent(uuid, position, count)
            else:
                raise NotImplementedError()
            res += abs(status - 1)
        if res > 0:
            meta = {'count': res}
            if not self.cli_mode:
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED_M, meta)
            return False
        return True

    def __call__(self, args, cli, endpoint, data):
        """TODO"""
        self.init(args, cli, endpoint)
        uuids = [row.get(self.resource_identifier) for row in data]
        return self.delete(uuids)

    def _delete(self, uuid, position=None, count=None):
        try:
            if not position:
                position = 1
                count = 1
            meta = {}
            meta['uuid'] = uuid
            meta[self.resource_identifier] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            if self.dry_run:
                json_obj = self.endpoint.get(uuid)
            else:
                json_obj = self.endpoint.delete(uuid)
                meta['time'] = self.cli.last_req_time
            if not json_obj:
                meta = {'uuid': uuid}
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED, meta)
                return False
            if self.cli_mode:
                print((json_obj.get(self.resource_identifier)))
            else:
                meta[self.identifier] = json_obj.get(self.identifier)
                self.pprint(self.MSG_RS_DELETED, meta)
            return True
        except (urllib.error.HTTPError, LinShareException) as ex:
            self.log.error("Delete error : %s", ex)
            return False

    def _delete_with_parent(self, uuid, position=None, count=None):
        try:
            if not position:
                position = 1
                count = 1
            meta = {}
            meta['uuid'] = uuid
            meta['time'] = " -"
            meta['position'] = position
            meta['count'] = count
            if self.dry_run:
                json_obj = self.endpoint.get(self.parent_uuid, uuid)
            else:
                json_obj = self.endpoint.delete(self.parent_uuid, uuid)
                meta['time'] = self.cli.last_req_time
            if not json_obj:
                meta = {'uuid': uuid}
                self.pprint(self.MSG_RS_CAN_NOT_BE_DELETED, meta)
                return False
            meta[self.identifier] = json_obj.get(self.identifier)
            self.pprint(self.MSG_RS_DELETED, meta)
            return True
        except (urllib.error.HTTPError, LinShareException) as ex:
            self.log.error("Delete error : %s", ex)
            return False


class DownloadAction(Action):
    """TODO"""

    MSG_RS_DOWNLOADED = (
        "%(position)s/%(count)s: "
        "The resource '%(name)s' (%(uuid)s) was downloaded. (%(time)s s)"
    )
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One resource can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = "%(count)s resources can not be downloaded."

    def __init__(self, mode=0,
                 identifier="name",
                 resource_identifier="uuid",
                 parent_identifier="parent_uuid"
                ):
        super(DownloadAction, self).__init__()
        self.cfg_mode = mode
        self.parent_uuid = None
        self.directory = None
        self.progress_bar = True
        self.identifier = identifier
        self.resource_identifier = resource_identifier
        self.parent_identifier_attr = parent_identifier

    def init(self, args, cli, endpoint):
        super(DownloadAction, self).init(args, cli, endpoint)
        if self.cfg_mode == 1 or self.cfg_mode == 2:
            self.parent_uuid = getattr(args, self.parent_identifier_attr, None)
            if not self.parent_uuid:
                raise ValueError("missing required arg : " + self.parent_identifier_attr)
        self.directory = getattr(args, "directory", None)
        if self.cli_mode:
            self.progress_bar = False
        else:
            self.progress_bar = not getattr(args, 'no_progress', False)
        return self

    def __call__(self, args, cli, endpoint, data):
        """TODO"""
        self.init(args, cli, endpoint)
        uuids = [row.get(self.resource_identifier) for row in data]
        return self.download(uuids)

    def download(self, uuids):
        """TODO"""
        count = len(uuids)
        position = 0
        res = 0
        for uuid in uuids:
            position += 1
            if self.cfg_mode == 0:
                status = self._download(uuid, position, count)
            elif self.cfg_mode == 1:
                status = self._download_with_parent(uuid, position, count)
            elif self.cfg_mode == 2:
                status = self._download_folder_with_parent(uuid, position, count)
            else:
                raise NotImplementedError()
            res += abs(status - 1)
        if res > 0:
            meta = {'count': res}
            self.pprint(self.MSG_RS_CAN_NOT_BE_DOWNLOADED_M, meta)
            return False
        return True

    def _download(self, uuid, position=None, count=None):
        if self.directory:
            if not os.path.isdir(self.directory):
                os.makedirs(self.directory)
        meta = {}
        meta['uuid'] = uuid
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        try:
            if self.dry_run:
                json_obj = self.endpoint.get(uuid)
                meta['name'] = json_obj.get('name')
            else:
                file_name, req_time = self.endpoint.download(
                    uuid, self.directory, progress_bar=self.progress_bar)
                meta['name'] = file_name
                meta['time'] = req_time
            if self.cli_mode:
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

    def _download_with_parent(self, uuid, position=None, count=None, directory=None):
        if not directory:
            directory = self.directory

        if directory:
            if not os.path.isdir(directory):
                os.makedirs(directory)
        meta = {}
        meta['uuid'] = uuid
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count
        try:
            if self.dry_run:
                json_obj = self.endpoint.get(self.parent_uuid, uuid)
                meta['name'] = json_obj.get('name')
            else:
                file_name, req_time = self.endpoint.download(self.parent_uuid, uuid, directory)
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
                json_obj = self.endpoint.core.get_json_result(ex)
                meta.update(json_obj)
                self.pprint_error("%(message)s : %(uuid)s (error: %(errCode)s)", meta)
            return False

    def _download_folder_with_parent(self, uuid, position=None, count=None, directory=None):
        meta = {}
        meta['uuid'] = uuid
        meta['time'] = " -"
        meta['position'] = position
        meta['count'] = count

        if not directory:
            directory = self.directory

        try:
            json_obj = self.endpoint.get(self.parent_uuid, uuid)
            meta['name'] = json_obj.get('name')
            if json_obj.get('type') == "FOLDER":
                # recursive
                if directory:
                    directory += "/" + json_obj.get('name')
                else:
                    directory = json_obj.get('name')
                if not os.path.isdir(directory) and not self.dry_run:
                    os.makedirs(directory)
                res = 0
                for nested in self.endpoint.list(self.parent_uuid, uuid):
                    if nested.get('type') == "FOLDER":
                        self.pprint("Downloading folder : %(name)s (%(uuid)s)",
                                    nested)
                        status = self._download_folder_with_parent(
                            nested.get('uuid'),
                            position,
                            count,
                            directory=directory
                        )
                        continue
                    status = self._download_with_parent(
                        nested.get('uuid'), position, count, directory=directory)
                    res += abs(status - 1)
                if res > 0:
                    meta = {'count': res}
                    self.pprint(self.MSG_RS_CAN_NOT_BE_DOWNLOADED_M, meta)
                    return False
                return True
            elif json_obj.get('type') == "DOCUMENT":
                return self._download_with_parent(uuid, position, count, directory=directory)
            else:
                return False
        except urllib.error.HTTPError as ex:
            self.log.debug("http error : %s", ex.code)
            meta['code'] = ex.code
            meta['ex'] = str(ex)
            if ex.code == 404:
                self.pprint_error("Can not find and download the document : %(uuid)s", meta)
            elif ex.code == 400:
                json_obj = self.endpoint.core.get_json_result(ex)
                meta.update(json_obj)
                self.pprint_error("%(message)s : %(uuid)s (error: %(errCode)s)", meta)
            return False


class ActionTable(VTable):
    """TODO"""
    # pylint: disable=too-many-instance-attributes

    action = Action()

    def render(self):
        """Call the action method with filtered data."""
        return self.action(self.args, self.cli, self.endpoint, self.get_raw())


class TableBuilder(object):
    """TODO"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, cli, endpoint, default_sort_column=None,
                 default_actions=True, cli_mode_identifier="uuid"):
        """TODO"""
        # pylint: disable=too-many-arguments
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linsharecli.' + classname)
        self.cli = cli
        self.endpoint = endpoint
        self.args = None
        self.columns = None
        self.fields = None
        self.cli_mode = False
        self.cli_mode_identifier = cli_mode_identifier
        self.default_sort_column = default_sort_column
        self.vertical = False
        self.json = False
        self.raw = False
        self.raw_json = False
        self.csv = False
        self.sort_by = None
        self.reverse = False
        self.extended = False
        self.no_cell = False
        self.debug = 0
        self.start = 0
        self.end = 0
        self.limit = 0
        self.no_headers = False
        self._vertical_clazz = VTable
        self._horizontal_clazz = HTable
        self._action_classes = OrderedDict()
        self._action_table = ActionTable
        if default_actions:
            self._action_classes['count_only'] = CountAction()
            self._action_classes['delete'] = DeleteAction()
            self._action_classes['download'] = DownloadAction()
        self._custom_cells = {}
        self.filters = []
        self.formatters = []
        self._pre_render_classes = []

    @property
    def horizontal_clazz(self):
        """TODO"""
        return self._horizontal_clazz

    @horizontal_clazz.setter
    def horizontal_clazz(self, horizontal_clazz):
        """TODO"""
        self._horizontal_clazz = horizontal_clazz

    def load_args(self, args):
        """load builder attributes from args."""
        attrs = [
            "vertical", "json", "raw", "raw_json", "csv",
            "sort_by", "reverse", "extended", "no_cell", "verbose", "cli_mode",
            "no_headers", "debug", "start", "end", "limit", "fields"
        ]
        for attr in attrs:
            if hasattr(args, attr):
                setattr(self, attr, getattr(args, attr))
        self.args = args
        return self

    def add_custom_cell(self, column, clazz):
        """Add specific cell class to format a column."""
        self._custom_cells[column] = clazz

    def add_action(self, flag, clazz):
        """Add some custom action class trigger by a flag."""
        self._action_classes[flag] = clazz

    def add_formatters(self, *formatters):
        """Add some formatters."""
        for formatter in formatters:
            self.formatters.append(formatter)

    def add_filter_cond(self, cond, *filters):
        """Add some filters only if cond is true"""
        if cond:
            for filterr in filters:
                self.filters.append(filterr)

    def add_filters(self, *filters):
        """Add some filters."""
        for filterr in filters:
            self.filters.append(filterr)

    def add_pre_render_class(self, clazz):
        """TODO"""
        self._pre_render_classes.append(clazz)

    def build(self):
        # pylint: disable=too-many-branches
        # This method is a little bit diry, need some refactoring.
        """Build table object"""
        if self.json or self.csv:
            self.vertical = True
        if self.json:
            self.raw = True
            self.no_cell = True
        if self.fields:
            self.columns = self.fields
        if not self.columns:
            self.columns = self.endpoint.get_rbu().get_keys(self.extended)
        table = None
        action_classes = OrderedDict(self._action_classes)
        action_classes['cli_mode'] = CliModeAction(self.cli_mode_identifier)
        self.log.debug("action_classes: %s", action_classes)
        for flag, action in list(action_classes.items()):
            if getattr(self.args, flag, False):
                table = self._action_table(self.columns)
                # a little bit ugly. :(
                table.action = action
                # if no_cell property does not exist, we keep the old behaviour
                self.no_cell = getattr(action, 'no_cell', True)
                self.raw = True
                break
        if table is None:
            if self.vertical:
                table = self._vertical_clazz(self.columns)
            else:
                table = self._horizontal_clazz(self.columns)
                table.padding_width = 1
            for clazz in self._pre_render_classes:
                table.add_pre_render_class(clazz)
        attrs = [
            "vertical", "json", "raw", "raw_json", "csv", "cli", "endpoint",
            "reverse", "extended", "no_cell", "debug", "verbose", "cli_mode",
        ]
        for attr in attrs:
            setattr(table, attr, getattr(self, attr))
        if self.sort_by is None:
            if self.default_sort_column and self.default_sort_column in self.columns:
                table.sortby = self.default_sort_column
        else:
            if self.sort_by in self.columns:
                table.sortby = self.sort_by
        self.log.debug("default_sort_column: %s", self.default_sort_column)
        self.log.debug("sort_by: %s", self.sort_by)
        self.log.debug("final sortby: %s", table.sortby)
        # very ugly. need big refactoring of all tables.
        table.reversesort = self.reverse
        table._pref_start = self.start
        table._pref_end = self.end
        table._pref_limit = self.limit
        table._pref_no_csv_headers = self.no_headers
        if self._custom_cells:
            for column, clazz in list(self._custom_cells.items()):
                table.cfa.custom_cells[column] = clazz
        table.cfa.raw = self.raw
        table.cfa.vertical = self.vertical
        table.cfa.debug = self.debug
        table._formatters = self.formatters
        table._filters = self.filters
        # compat
        table.args = self.args
        table.keys = self.columns
        return table
