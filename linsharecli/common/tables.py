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


from __future__ import unicode_literals


import json
import types
import logging

from ordereddict import OrderedDict
from veryprettytable import VeryPrettyTable
from linshareapi.cache import Time
from linsharecli.common.cell import CellBuilder

class AbstractTable(object):
    """TODO"""

    log = None
    vertical = False
    csv = False
    json = False
    debug = 0
    raw = False
    no_cell = False
    cbu = CellBuilder(False, False, 0)
    keys = []
    _filters = []
    _formatters = []

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
        data = dict()
        for key in self.keys:
            if self.debug >= 2:
                self.log.debug("key: %s ", key)
            value = None
            if key in json_row:
                value = json_row[key]
            else:
                self.log.debug("key not found: %s", key)
            data[key] = value
            if not off:
                data[key] = self.cbu(key, value, data)
        if self.debug >= 2:
            self.log.debug("end row")
        return data

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        raise NotImplementedError()


class BaseTable(AbstractTable):
    """TODO"""

    vertical = True
    start = 0
    end = 0
    _pref_start = 0
    _pref_end = 0
    _pref_limit = 0
    raw_json = False
    args = None
    _pref_no_csv_headers = False
    cli = None
    endpoint = None

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

    @Time('linsharecli.core.load', label='time : %(time)s')
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
                    data_str = str(data).decode('utf-8')
                    record.append(data_str)
            records.append(";".join(record))
        return "\n".join(records)


class VTable(BaseTable):
    """TODO"""

    vertical = True

    @Time('linsharecli.core.show_table', label='time : %(time)s')
    def show_table(self, json_obj, filters=None, formatters=None,
                   ignore_exceptions=None):
        # pylint: disable=unused-argument
        # Only for compatibility with older lines of code.
        """TODO"""
        self.render()

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        if self.json:
            print self.get_json()
            return True
        if self.csv:
            print self.get_csv()
            return True
        out = self.get_string()
        print unicode(out)
        return True

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
                    t_format = u"{key:" + str(self._maxlengthkey) + u"s} | {value:s}"
                    dataa = None
                    column_data = row.get(k)
                    if isinstance(column_data, types.UnicodeType):
                        dataa = {"key": k, "value": column_data}
                    else:
                        column_data_str = str(column_data).decode('utf-8')
                        dataa = {"key": k, "value": column_data_str}
                    t_record = (t_format).format(**dataa)
                    record.append(t_record)
                    max_length_line = max(max_length_line, len(t_record))
                except UnicodeEncodeError as ex:
                    self.log.error("UnicodeEncodeError: %s", ex)
                    dataa = {"key": k, "value": "UnicodeEncodeError"}
                    # msg = ex.msg.decode('unicode-escape').strip('"')
                    t_record = unicode(t_format).format(**dataa)
                    record.append(t_record)
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


class ActionTable(VTable):
    """TODO"""

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        print "Default action table: noop."
        for row in self.get_raw():
            print row
        print "-----"
        print self.cli
        print self.endpoint
        return True


class ConsoleTable(BaseTable):
    """TODO"""

    vertical = False

    @Time('linsharecli.core.show_table', label='time : %(time)s')
    def show_table(self, json_obj, filters=None, formatters=None,
                   ignore_exceptions=None):
        # pylint: disable=unused-argument
        # Only for compatibility with older lines of code.
        """TODO"""
        self.render()

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        if self.json:
            print self.get_json()
            return True
        if self.csv:
            print self.get_csv()
            return True
        for row in self.get_raw():
            record = []
            for k in self.keys:
                try:
                    t_format = u"{value:s}"
                    column_data = row.get(k)
                    if isinstance(column_data, types.UnicodeType):
                        t_record = t_format.format(value=column_data)
                    else:
                        t_record = t_format.format(value=column_data)
                    record.append(t_record)
                except UnicodeEncodeError as ex:
                    self.log.error("UnicodeEncodeError: %s", ex)
                    record.append("UnicodeEncodeError")
            print unicode(" ".join(record))
        return True


class HTable(VeryPrettyTable, AbstractTable):
    """TODO"""

    def _transform_to_cell(self, json_row, off=False):
        """TODO"""
        self.log.debug("begin row")
        data = OrderedDict()
        for key in self.keys:
            self.log.debug("key: %s", key)
            value = None
            if key in json_row:
                value = json_row[key]
            else:
                self.log.debug("key not found: %s", key)
            data[key] = value
            if not off:
                data[key] = self.cbu(key, value, data)
        self.log.debug("end row")
        return data

    @Time('linsharecli.core.load', label='time : %(time)s')
    def load(self, json_obj, filters=None, formatters=None):
        """TODO"""
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger(classname)
        self.log.debug("json_obj size: %s", len(json_obj))
        self.log.debug("keys: %s", self.keys)
        for json_row in json_obj:
            data = self._transform_to_cell(json_row, self.no_cell)
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
                   ignore_exceptions=None):
        # pylint: disable=unused-argument
        # Only for compatibility with older lines of code.
        """TODO"""
        self.render()

    @Time('linsharecli.core.render', label='render time : %(time)s')
    def render(self):
        """TODO"""
        out = self.get_string(fields=self.keys)
        print unicode(out)
        return True

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


class TableBuilder(object):
    """TODO"""

    def __init__(self, cli, endpoint, first_column=None):
        """TODO"""
        self.cli = cli
        self.endpoint = endpoint
        self.args = None
        self.columns = None
        self.fields = None
        self.cli_mode = False
        self.first_column = first_column
        self.vertical = False
        self.json = False
        self.raw = False
        self.raw_json = False
        self.csv = False
        self.sort_by = None
        self.reverse = False
        self.extended = False
        self.no_cell = False
        self.start = 0
        self.end = 0
        self.limit = 0
        self.no_headers = False
        self._vertical_clazz = VTable
        self._horizontal_clazz = HTable
        self._actions_clazz = {
            'delete' : ActionTable,
            'download' : ActionTable,
            'share' : ActionTable,
            'count_only' : ActionTable,
        }
        self._custom_cells = {}
        self.filters = []
        self.formatters = []

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

    def add_action(self, action, clazz):
        """Add some custom action."""
        self._actions_clazz[action] = clazz

    def add_formatters(self, *formatters):
        """Add some formatters."""
        for formatter in formatters:
            self.formatters.append(formatter)

    def add_filters(self, *filters):
        """Add some filters."""
        for filterr in filters:
            self.filters.append(filterr)

    def build(self):
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

        for action, clazz in self._actions_clazz.items():
            if getattr(self.args, action, False):
                table = clazz(self.columns)
                self.no_cell = True
                self.raw = True
                break
        if table is None:
            if self.vertical:
                table = self._vertical_clazz(self.columns)
            else:
                table = self._horizontal_clazz(self.columns)
                # styles
                if self.first_column and self.first_column in self.columns:
                    table.align[self.first_column] = "l"
                table.padding_width = 1
        attrs = [
            "vertical", "json", "raw", "raw_json", "csv", "cli", "endpoint",
            "reverse", "extended", "no_cell", "debug", "verbose", "cli_mode",
        ]
        for attr in attrs:
            setattr(table, attr, getattr(self, attr))
        if self.sort_by is None:
            if self.first_column and self.first_column in self.columns:
                table.sortby = self.first_column
        else:
            table.sortby = self.sort_by
        table.reversesort = self.reverse
        table._pref_start = self.start
        table._pref_end = self.end
        table._pref_limit = self.limit
        table._pref_no_csv_headers = self.no_headers
        if self._custom_cells:
            for column, clazz in self._custom_cells.items():
                table.cbu.custom_cells[column] = clazz
        table.cbu.raw = self.raw
        table.cbu.vertical = self.vertical
        table.cbu.debug = self.debug
        table._formatters = self.formatters
        table._filters = self.filters
        # compat
        table.args = self.args
        table.keys = self.columns
        return table
