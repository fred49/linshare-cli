
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
# Copyright 2019 Frederic MARTIN
#
# Contributors list :
#
#  Frederic MARTIN frederic.martin.fma@gmail.com
#




import json
import time
from linshareapi.core import LinShareException


class AbstractAction(object):
    """TODO"""

    MESSAGE_CONFIRM_KEY = None

    def __init__(self, command, cli):
        self.cli = cli
        self.command = command
        self.debug = command.debug
        self.log = command.log
        self.cli_mode = False
        self.err_suffix = "unknown error"
        self.rbu = None
        self.result = None

    def add_hook(self, key, hook):
        """Add a hook to transform input data beforce sending it to the server"""
        if self.rbu is None:
            self.rbu = self.cli.get_rbu()
        self.rbu.add_hook(key, hook)
        return self

    def load(self, args):
        """Load RessourceBuilder from args"""
        self.err_suffix = getattr(args, self.command.IDENTIFIER, None)
        self.cli_mode = args.cli_mode
        if self.rbu is None:
            self.rbu = self.cli.get_rbu()
        self.rbu.load_from_args(args)
        return self

    def pprint(self, msg, meta={}):
        """TODO"""
        msg = msg % meta
        self.log.debug(msg)
        print(msg)

    def pretty_json(self, obj, title=None):
        """Just a pretty printer for a json object."""
        if title:
            title += " : "
        else:
            title = ""
        self.log.debug(title + json.dumps(obj, sort_keys=True, indent=2))

    def execute(self, data=None):
        """TODO"""
        try:
            start = time.time()
            json_obj = self._execute(data)
            self.result = json_obj
            end = time.time()
            json_obj['_time'] = end - start
            if json_obj is None:
                self.log.error("Missing return statement for _execute method")
                return False
            if self.debug:
                self.pretty_json(json_obj, "Json object returned by the server")
            if self.cli_mode:
                print((json_obj.get(self.command.RESOURCE_IDENTIFIER)))
                return True
            msg = getattr(self.command, self.MESSAGE_CONFIRM_KEY)
            self.pprint(msg, json_obj)
            return True
        except LinShareException as ex:
            self.log.debug("LinShareException : " + str(ex.args))
            self.log.error(ex.args[1] + " : " + str(self.err_suffix))
        return False

    def _execute(self, data):
        raise NotImplementedError()


class CreateAction(AbstractAction):
    """TODO"""

    MESSAGE_CONFIRM_KEY = 'MSG_RS_CREATED'

    def _execute(self, data):
        if data is None:
            data = self.rbu.to_resource()
        if self.debug:
            self.pretty_json(data, "Json object sent to the server")
        return self.cli.create(data)


class UpdateAction(AbstractAction):
    """TODO"""

    MESSAGE_CONFIRM_KEY = 'MSG_RS_UPDATED'

    def _execute(self, data):
        if data is None:
            data = self.rbu.to_resource()
        if self.debug:
            self.pretty_json(data, "Json object sent to the server")
        return self.cli.update(data)
