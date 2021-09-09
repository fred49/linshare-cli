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
from vhatable.core import TableFactory
from vhatable.core import Action


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


class TableBuilder(TableFactory):
    # pylint: disable=too-few-public-methods
    """TODO"""

    def __init__(self, *args, **kwargs):
        """TODO"""
        super(TableBuilder, self).__init__(*args, **kwargs)
        if "default_actions" in kwargs:
            if kwargs['default_actions']:
                self.add_action('delete', DeleteAction())
                self.add_action('download', DownloadAction())
        else:
            self.add_action('delete', DeleteAction())
            self.add_action('download', DownloadAction())
