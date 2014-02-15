#!/usr/bin/python
# -*- coding: utf-8 -*-


# This file is part of Linshare user cli.
#
# LinShare user cli is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LinShare user cli is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LinShare user cli.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2013 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#


import os
import sys
import logging
import json
import getpass
import copy
import datetime
from core import UserCli
import fmatoolbox


# -----------------------------------------------------------------------------
class DefaultCommand(fmatoolbox.DefaultCommand):

    def __init__(self, config=None):
        self.config = config
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linshare-cli.' + classname)

    def __call__(self, args):
        super(DefaultCommand, self).__call__(args)
        self.verbose = args.verbose
        self.debug = args.debug

        if args.ask_password:
            try:
                args.password = getpass.getpass("Please enter your password :")
            except KeyboardInterrupt as e:
                print """\nKeyboardInterrupt exception was caught.
                Program terminated."""
                sys.exit(1)

        if not args.password:
            raise ValueError("invalid password : password is not set ! ")

        self.ls = self._getCliObject(args)
        if args.nocache:
            self.ls.nocache = True
        if not self.ls.auth():
            sys.exit(1)

    def _getCliObject(self, args):
        raise NotImplementedError("""You must implement the _getCliObject
        method and return a object instance of CoreCli or its children in
        your Command class.""")

    def printPrettyJson(self, obj):
            print json.dumps(obj, sort_keys=True, indent=2)

    def getLegend(self, data):
        legend = dict()
        for i in data[0]:
            legend[i] = i.upper()
        return legend

    def addLegend(self, data):
        data.insert(0, self.getLegend(data))

    def formatDate(self, data, attr, dformat="%Y-%m-%d %H:%M:%S"):
        """The current fied is replaced by a formatted date. The previous
        field is saved to a new field called 'field_orig'."""

        for f in data:
            a = "{da:" + dformat + "}"
            f[attr + "_orig"] = f[attr]
            f[attr] = a.format(
                da=datetime.datetime.fromtimestamp(f.get(attr) / 1000))

    def getUnderline(self, title):
        sub = ""
        for i in xrange(0, len(title)):
            sub += "-"
        return sub

    def printTitle(self, data, title):
        _title = title.strip() + " : (" + str(len(data)) + ")"
        print "\n" + _title
        print self.getUnderline(_title)

    def printList(self, data, d_format, title=None, t_format=None):
        """The input list is printed out using the d_format parametter.
        A Legend is built using field names."""

        if not t_format:
            t_format = d_format
        if title:
            self.printTitle(data, title)
        legend = self.getLegend(data)
        print t_format.format(**legend)
        for f in data:
            print d_format.format(**f)
        print ""

    def printTest(self, data):
        # test
        # compute max lengh by column.
        a = {}
        for i in data:
            for j in i:
                a[j] = max([len(str(i.get((j)))), a.get(j, 0)])
        print a
