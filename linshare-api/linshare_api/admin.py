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
import json

from linshare_api.core import CoreCli
from linshare_api.core import ResourceBuilder


# pylint: disable=C0111
# Missing docstring
# -----------------------------------------------------------------------------
class GenericAdminClass(object):
    def __init__(self, corecli):
        self.core = corecli
        self.log = logging.getLogger('linshare-api.admin.rbu')

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


class DomainAdmins(GenericAdminClass):

    def list(self):
        return self.core.list("domains")

    def create(self, data):
        self.debug(data)
        if data.get('label') is None:
            data['label'] = data.get('identifier')
        self._check(data)
        if data.get('type') in ["GUESTDOMAIN", "SUBDOMAIN"]:
            if data.get('parent') is None:
                raise ValueError(
                    "parent identifier is required for GuestDomain / SubDomain")
        return self.core.create("domains", data)

    def update(self, data):
        self.debug(data)
        return self.core.update("domains", data)

    def delete(self, identifier):
        if identifier:
            identifier = identifier.strip(" ")
        if not identifier:
            raise ValueError("identifier is required")
        data = {"identifier":  identifier}
        return self.core.delete("domains", data)

    def options_language(self):
        return self.core.options("enums/language")

    def options_role(self):
        # pylint: disable=R0201
        return ['ADMIN', 'SIMPLE']

    def options_type(self):
        # pylint: disable=R0201
        return ['GUESTDOMAIN', 'SUBDOMAIN', 'TOPDOMAIN']


    def get_rbu(self):
        rbu = ResourceBuilder("domains")
        rbu.add_field('identifier', required=True)
        rbu.add_field('label', required=True)
        rbu.add_field('policy', value={"identifier": "DefaultDomainPolicy"},
                      hidden=True)
        rbu.add_field('type', "domain_type", value="TOPDOMAIN")
        rbu.add_field('parent', "parent_id")
        rbu.add_field('language', value="ENGLISH")
        rbu.add_field('userRole', "role", value="SIMPLE")
        rbu.add_field('mailConfigUuid',
                      value="946b190d-4c95-485f-bfe6-d288a2de1edd",
                      extended=True)
        rbu.add_field('mimePolicyUuid',
                      value="3d6d8800-e0f7-11e3-8ec0-080027c0eef0",
                      extended=True)
        rbu.add_field('description', value="")
        rbu.add_field('authShowOrder', value="1", extended=True)
        rbu.add_field('providers', value=[], extended=True)
        return rbu


class DomainPatternsAdmin(GenericAdminClass):

    def list(self, model=False):
        if model:
            return self.core.list("domain_patterns/models")
        else:
            return self.core.list("domain_patterns")

    def create(self, data):
        self.debug(data)
        self._check(data)
        return self.core.create("domain_patterns", data)

    def update(self, data):
        self.debug(data)
        return self.core.update("domain_patterns", data)

    def delete(self, identifier):
        if identifier:
            identifier = identifier.strip(" ")
        if not identifier:
            raise ValueError("identifier is required")
        data = {"identifier":  identifier}
        return self.core.delete("domain_patterns", data)

    def get_rbu(self):
        rbu = ResourceBuilder("domain_patterns", required=True)
        rbu.add_field('identifier')
        rbu.add_field('description', value="")
        rbu.add_field('userFirstName', 'first_name', extended=True)
        rbu.add_field('userLastName', 'last_name', extended=True)
        rbu.add_field('userMail', 'mail', extended=True)
        rbu.add_field('ldapUid', extended=True)
        rbu.add_field("authCommand", extended=True)
        rbu.add_field("searchUserCommand", extended=True)
        rbu.add_field("autoCompleteCommandOnAllAttributes", extended=True)
        rbu.add_field("autoCompleteCommandOnFirstAndLastName", extended=True)
        rbu.add_field('completionPageSize', extended=True, e_type=int)
        rbu.add_field('completionSizeLimit', extended=True, e_type=int)
        rbu.add_field('searchPageSize', extended=True, e_type=int)
        rbu.add_field('searchSizeLimit', extended=True, e_type=int)
        return rbu


class LdapConnectionsAdmin(GenericAdminClass):

    def list(self):
        return self.core.list("ldap_connections")

    def create(self, data):
        self.debug(data)
        self._check(data)
        return self.core.create("ldap_connections", data)

    def update(self, data):
        self.debug(data)
        return self.core.update("ldap_connections", data)

    def delete(self, identifier):
        if identifier:
            identifier = identifier.strip(" ")
        if not identifier:
            raise ValueError("identifier is required")
        data = {"identifier":  identifier}
        return self.core.delete("ldap_connections", data)

    def get_rbu(self):
        rbu = ResourceBuilder("ldap_connection")
        rbu.add_field('identifier', required=True)
        rbu.add_field('providerUrl', required=True)
        rbu.add_field('securityPrincipal', "principal")
        rbu.add_field('securityCredentials', "credential")
        return rbu


# -----------------------------------------------------------------------------
class ThreadsAdmin(GenericAdminClass):

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
class ThreadsMembersAdmin(GenericAdminClass):

    def list(self, thread_uuid):
        url = "thread_members/%s" % thread_uuid
        return self.core.list(url)

    def get_rbu(self):
        rbu = ResourceBuilder("thread_members")
        return rbu


# -----------------------------------------------------------------------------
class UsersAdmin(GenericAdminClass):

    def search(self, firstname=None, lastname=None, mail=None):
        criteria = {"firstName": firstname,
                    "lastName": lastname,
                    "mail": mail}
        return self.core.create("users/search", criteria)

    def autocomplete(self, pattern):
        if not pattern:
            raise ValueError("missing mandatory parameter : pattern")
        return self.core.list("users/autocomplete/%s" % pattern)

    def internals(self, pattern):
        if not pattern:
            raise ValueError("missing mandatory parameter : pattern")
        return self.core.list("users/search/internals/%s" % pattern)

    def guests(self, pattern):
        if not pattern:
            raise ValueError("missing mandatory parameter : pattern")
        return self.core.list("users/search/guests/%s" % pattern)

    def inconsistents(self):
        return self.core.list("users/inconsistent")

    def get_rbu(self):
        rbu = ResourceBuilder("users")
        rbu.add_field('firstName', required=True)
        rbu.add_field('lastName', required=True)
        rbu.add_field('mail', required=True)
        rbu.add_field('uuid')
        rbu.add_field('domain')
        rbu.add_field('guest')
        rbu.add_field('role')
        rbu.add_field('locale')
        rbu.add_field('creationDate')
        rbu.add_field('modificationDate')
        rbu.add_field('canUpload', extended=True)
        rbu.add_field('canCreateGuest', extended=True)
        rbu.add_field('restricted', extended=True)
        rbu.add_field('expirationDate', extended=True)
        rbu.add_field('comment', extended=True)
        rbu.add_field('restrictedContacts', extended=True)
        return rbu

# -----------------------------------------------------------------------------
class FunctionalityAdmin(GenericAdminClass):

    def list(self, domain_id=None):
        if domain_id is None:
            domain_id = "LinShareRootDomain"
        json_obj = self.core.list("functionalities?domainId=" + domain_id)
        return [row for row in json_obj if row.get('displayable') == True]

    def get(self, func_id, domain_id=None):
        if domain_id is None:
            domain_id = "LinShareRootDomain"
        json_obj = self.core.get("functionalities/"+ func_id +"?domainId=" +
                                 domain_id)
        return json_obj

    def update(self, data):
        self.debug(data)
        return self.core.update("functionalities", data)

    def reset(self, data):
        self.debug(data)
        return self.core.delete("functionalities", data)

    def options_policies(self):
        return self.core.options("enums/policies")

    def get_rbu(self):
        rbu = ResourceBuilder("functionality")
        rbu.add_field('identifier', required=True)
        rbu.add_field('type')
        rbu.add_field('parentAllowParametersUpdate')
        rbu.add_field('parameters', extended=True)
        rbu.add_field('parentIdentifier', extended=True)
        rbu.add_field('domain', extended=True, required=True)
        return rbu

# -----------------------------------------------------------------------------
class AdminCli(CoreCli):
    # pylint: disable=R0902
    def __init__(self, *args, **kwargs):
        super(AdminCli, self).__init__(*args, **kwargs)
        self.base_url = "linshare/webservice/rest/admin"
        self.threads = ThreadsAdmin(self)
        self.thread_members = ThreadsMembersAdmin(self)
        self.users = UsersAdmin(self)
        self.domains = DomainAdmins(self)
        self.ldap_connections = LdapConnectionsAdmin(self)
        self.domain_patterns = DomainPatternsAdmin(self)
        self.funcs = FunctionalityAdmin(self)
