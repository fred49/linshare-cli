#! /usr/bin/env python
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


from __future__ import unicode_literals

import logging
import logging.handlers
import urllib2
import datetime
from linshare_api.core import CoreCli


# pylint: disable=C0111
# Missing docstring
# -----------------------------------------------------------------------------
class Documents(object):
    def __init__(self, corecli):
        self.core = corecli

    def list(self):
        """ List all documents store into LinShare."""
        return self.core.list("documents")

    def upload(self, file_path, description=None):
        """ Upload a file to LinShare using its rest api.
        The uploaded document uuid will be returned"""
        return self.core.upload(file_path, "documents", description)

    def download(self, uuid):
        url = "documents/%s/download" % uuid
        return self.core.download(uuid, url)

    def delete(self, uuid):
        url = "documents/%s" % uuid
        return self.core.delete(url)



# -----------------------------------------------------------------------------
class ReceivedShares(object):
    def __init__(self, corecli):
        self.core = corecli

    def list(self):
        return self.core.list("shares")

    def download(self, uuid):
        url = "shares/%s/download" % uuid
        return self.core.download(uuid, url)


# -----------------------------------------------------------------------------
class Shares(object):
    # pylint: disable=R0903
    # Too few public methods (1/2)
    def __init__(self, corecli):
        self.core = corecli
        classname = str(self.__class__.__name__.lower())
        self.log = logging.getLogger('linshare-cli.' + classname)

    def share(self, uuid, mail):
        url = self.core.get_full_url(
            "shares/sharedocument/%s/%s" % (mail, uuid))
        self.log.debug("share url : " + url)
        # Building request
        request = urllib2.Request(url)
        # request start
        starttime = datetime.datetime.now()
        try:
            # doRequest
            resultq = urllib2.urlopen(request)
        except urllib2.HTTPError as ex:
            print ex
            print ex.code
            print url
            raise ex
        # request end
        endtime = datetime.datetime.now()
        code = resultq.getcode()
        msg = resultq.msg
        self.core.last_req_time = str(endtime - starttime)
        self.log.debug("share url : %(url)s : request time : %(time)s",
                       {"url": url,
                        "time": self.core.last_req_time})
        self.log.debug("the result is : " + str(code) + " : " + msg)
        return (code, msg, self.core.last_req_time)


# -----------------------------------------------------------------------------
class Threads(object):
    # pylint: disable=R0903
    # Too few public methods (1/2)
    def __init__(self, corecli):
        self.core = corecli

    def list(self):
        return self.core.list("threads")


# -----------------------------------------------------------------------------
class ThreadsMembers(object):
    # pylint: disable=R0903
    # Too few public methods (1/2)
    def __init__(self, corecli):
        self.core = corecli

    def list(self, thread_uuid):
        url = "thread_members/%s" % thread_uuid
        return self.core.list(url)


# -----------------------------------------------------------------------------
class Users(object):
    # pylint: disable=R0903
    # Too few public methods (1/2)
    def __init__(self, corecli):
        self.core = corecli

    def list(self):
        return self.core.list("users")


# -----------------------------------------------------------------------------
class UserCli(CoreCli):
    def __init__(self, *args, **kwargs):
        super(UserCli, self).__init__(*args, **kwargs)
        self.base_url = "linshare/webservice/rest"
        self.documents = Documents(self)
        self.rshares = ReceivedShares(self)
        self.shares = Shares(self)
        self.threads = Threads(self)
        self.thread_members = ThreadsMembers(self)
        self.users = Users(self)
