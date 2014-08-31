#! /usr/bin/env python
# -*- coding: utf-8 -*-


# This file is part of Linshare api.
#
# LinShare api is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LinShare api is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LinShare api.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2014 Frédéric MARTIN
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
import json

from linshare_api.core import CoreCli
from linshare_api.core import ResourceBuilder


# pylint: disable=C0111
# Missing docstring
# -----------------------------------------------------------------------------
class GenericUserClass(object):
    def __init__(self, corecli):
        #classname = str(self.__class__.__name__.lower())
        self.core = corecli
        self.log = logging.getLogger('linshare-api.user.rbu')

    def get_rbu(self):
        # pylint: disable=R0201
        rbu = ResourceBuilder("generic")
        return rbu

    def get_resource(self):
        return self.get_rbu().to_resource()

    def debug(self, data):
        self.log.debug("input data :")
        self.log.debug(json.dumps(data, sort_keys=True, indent=2))

    def _check(self, data):
        rbu = self.get_rbu()
        rbu.copy(data)
        rbu.check_required_fields()


# -----------------------------------------------------------------------------
class Documents(GenericUserClass):

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

    def get_rbu(self):
        rbu = ResourceBuilder("documents")
        rbu.add_field('name')
        rbu.add_field('size')
        rbu.add_field('uuid')
        rbu.add_field('creationDate')
        rbu.add_field('modificationDate')
        rbu.add_field('type', extended=True)
        rbu.add_field('expirationDate', extended=True)
        rbu.add_field('ciphered', extended=True)
        rbu.add_field('description', extended=True)
        return rbu


# -----------------------------------------------------------------------------
class ReceivedShares(GenericUserClass):

    def list(self):
        return self.core.list("shares")

    def download(self, uuid):
        url = "shares/%s/download" % uuid
        return self.core.download(uuid, url)

    def get_rbu(self):
        rbu = ResourceBuilder("rshares")
        rbu.add_field('name')
        rbu.add_field('size')
        rbu.add_field('uuid')
        rbu.add_field('creationDate')
        rbu.add_field('modificationDate')
        rbu.add_field('type', extended=True)
        rbu.add_field('expirationDate', extended=True)
        rbu.add_field('ciphered', extended=True)
        rbu.add_field('description', extended=True)
        rbu.add_field('message', extended=True)
        rbu.add_field('downloaded', extended=True)
        return rbu


# -----------------------------------------------------------------------------
class Shares(GenericUserClass):

    # pylint: disable=R0903
    # Too few public methods (1/2)
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
class Threads(GenericUserClass):

    # pylint: disable=R0903
    # Too few public methods (1/2)
    def list(self):
        return self.core.list("threads")

    def get_rbu(self):
        rbu = ResourceBuilder("threads")
        rbu.add_field('name', required=True)
        rbu.add_field('domain')
        rbu.add_field('uuid')
        rbu.add_field('creationDate')
        rbu.add_field('modificationDate')
        return rbu


# -----------------------------------------------------------------------------
class ThreadsMembers(GenericUserClass):

    # pylint: disable=R0903
    # Too few public methods (1/2)
    def list(self, thread_uuid):
        url = "thread_members/%s" % thread_uuid
        return self.core.list(url)


# -----------------------------------------------------------------------------
class Users(GenericUserClass):

    # pylint: disable=R0903
    # Too few public methods (1/2)
    def list(self):
        return self.core.list("users")

    def get_rbu(self):
        rbu = ResourceBuilder("users")
        rbu.add_field('firstName', required=True)
        rbu.add_field('lastName', required=True)
        rbu.add_field('mail', required=True)
        rbu.add_field('uuid')
        rbu.add_field('domain')
        rbu.add_field('guest')
        return rbu


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
