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


import sys
import logging
import urllib2
import getpass

import common
from core import UserCli
from fmatoolbox import DefaultCompleter

class DefaultCommand(common.DefaultCommand):

	def _getCliObject(self, args):
		return UserCli(args.host , args.user , args.password , args.verbose, args.debug, args.realm, args.application_name)

# ---------------------------------------------------------------------------------------------------------------------
class ConfigGenerationCommand(object):
	def __call__(self, args):
		config.write_default_config_file()

# ---------------------------------------------------------------------------------------------------------------------
class ConfigAutoCompteCommand(object):
	def __call__(self, args):
		print """
This program is comptible with the python autocomplete program called argcomplete.\n
You can either install this program using :
- sudo apt-get install python-argcomplete
or
- sudo apt-get install python-pip
- sudo pip install argcomplete

Once this program is installed, you have two configuration options :

1. Global configuration
	All programs compliant with argcomplete will be detected automatically with bash >= 4.2.
	This won't work with Debian Squeeze for example.
	- sudo activate-global-python-argcomplete

2. Specific configuration
	Manually include the following command ind your ~/.bashrc :
	- eval "$(register-python-argcomplete linshare_cli_user.py)"



"""

# -------------------------- Documents ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class DocumentsListCommand(DefaultCommand):
	""" List all documents store into LinShare."""

	def __call__(self, args):
		super(DocumentsListCommand, self).__call__(args)

		jObj = self.ls.documents.list()
		d_format = "{name:60s}{creationDate:30s}{uuid:30s}"
		self.formatDate(jObj, 'creationDate')
		self.printList(jObj, d_format, "Documents")

# ---------------------------------------------------------------------------------------------------------------------
class DocumentsUploadCommand(DefaultCommand):
	""" upload a file to LinShare using its rest api. return the uploaded document uuid  """

	def __call__(self, args):
		super(DocumentsUploadCommand, self).__call__(args)

		for file_path in args.files :
			jObj = self.ls.documents.upload(file_path)
			self.log.info("The file '" + jObj.get('name') + "' ("+ jObj.get('uuid') + ") was uploaded. (" + self.ls.last_req_time + "s)")


# ---------------------------------------------------------------------------------------------------------------------
class DocumentsDownloadCommand(DefaultCommand):

	def __call__(self, args):
		super(DocumentsDownloadCommand, self).__call__(args)

		for uuid in args.uuids:
			try:
				file_name, req_time = self.ls.documents.download(uuid)
				self.log.info("The file '" + file_name  + "' was downloaded. (" + req_time + "s)")
			except urllib2.HTTPError as e :
				print "Error : "
				print e
				return

	def complete(self, args,  prefix):
		super(DocumentsDownloadCommand, self).__call__(args)

		jObj = self.ls.documents.list()
		return (v.get('uuid') for v in jObj if v.get('uuid').startswith(prefix))


# ---------------------------------------------------------------------------------------------------------------------
class DocumentsUploadAndSharingCommand(DefaultCommand):

	def __call__(self, args):
		super(DocumentsUploadAndSharingCommand, self).__call__(args)

		for file_path in args.files :
			jObj = self.ls.documents.upload(file_path)
			uuid = jObj.get('uuid')
			self.log.info("The file '" + jObj.get('name') + "' ("+ uuid + ") was uploaded. (" + self.ls.last_req_time + "s)")

			for mail in args.mails :
				code, msg , req_time = self.ls.shares.share(uuid , mail)

				if code == 204 :
					self.log.info("The document '" + uuid + "' was successfully shared with " + mail + " ( "+ req_time + "s)")
				else :
					self.log.warn("Trying to share document '" + uuid + "' with " + mail)
					self.log.error("Unexpected return code : " + str(code) + " : " + msg)

	def complete(self, args,  prefix):
		super(DocumentsUploadAndSharingCommand, self).__call__(args)

		jObj = self.ls.documents.list()
		return (v.get('uuid') for v in jObj if v.get('uuid').startswith(prefix))

# ----------------- Received Shares ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class ReceivedSharesListCommand(DefaultCommand):

	def __call__(self, args):
		super(ReceivedSharesListCommand, self).__call__(args)

		jObj = self.ls.rshares.list()
		d_format = "{name:60s}{creationDate:30s}{uuid:30s}"
		self.formatDate(jObj, 'creationDate')
		self.printList(jObj, d_format, "Received Shares")

# ---------------------------------------------------------------------------------------------------------------------
class ReceivedSharesDownloadCommand(DefaultCommand):

	def __call__(self, args):
		super(ReceivedSharesDownloadCommand, self).__call__(args)

		for uuid in args.uuids:
			try:
				file_name, req_time =  self.ls.rshares.download(uuid)
				self.log.info("The share '" + file_name  + "' was downloaded. (" + req_time + "s)")
			except urllib2.HTTPError as e :
				print "Error : "
				print e
				return


	def complete(self, args,  prefix):
		super(ReceivedSharesDownloadCommand, self).__call__(args)

		jObj = self.ls.rshares.list()
		return (v.get('uuid') for v in jObj if v.get('uuid').startswith(prefix))

# -------------------------- Shares ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class SharesCommand(DefaultCommand):

	def __call__(self, args):
		super(SharesCommand, self).__call__(args)

		for uuid in args.uuids :
			for mail in args.mails :
				code, msg , req_time = self.ls.shares.share(uuid , mail)

				if code == 204 :
					self.log.info("The document '" + uuid + "' was successfully shared with " + mail + " ( "+ req_time + "s)")
				else :
					self.log.warn("Trying to share document '" + uuid + "' with " + mail)
					self.log.error("Unexpected return code : " + str(code) + " : " + msg)

	def complete(self, args,  prefix):
		super(SharesCommand, self).__call__(args)

		jObj = self.ls.documents.list()
		return (v.get('uuid') for v in jObj if v.get('uuid').startswith(prefix))

	def complete_mail(self, args,  prefix):
		super(SharesCommand, self).__call__(args)

		if len(prefix) >= 3: 
			jObj = self.ls.users.list()
			return (v.get('mail') for v in jObj if v.get('mail').startswith(prefix))

# -------------------------- Threads ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class ThreadsListCommand(DefaultCommand):
	""" List all threads store into LinShare."""

	def __call__(self, args):
		super(ThreadsListCommand, self).__call__(args)

		jObj = self.ls.threads.list()
		d_format = "{name:60s}{creationDate:30s}{uuid:30s}"
		#self.printPrettyJson(jObj)
		self.formatDate(jObj, 'creationDate')
		self.printList(jObj, d_format, "Threads")

		#self.printTest(jObj)

# ---------------------------------------------------------------------------------------------------------------------
class ThreadMembersListCommand(DefaultCommand):
	""" List all thread members store from a thread."""

	def __call__(self, args):
		super(ThreadMembersListCommand, self).__call__(args)

		jObj = self.ls.thread_members.list(args.uuid)

		d_format = "{firstName:11s}{lastName:10s}{admin:<7}{readonly:<9}{id}"
		# print "%(firstName)-10s %(lastName)-10s\t %(admin)-10s\t %(readonly)-10s\t %(id)s"
		#self.printPrettyJson(jObj)
		self.printList(jObj, d_format, "Thread members")

	def complete(self, args,  prefix):
		super(ThreadMembersListCommand, self).__call__(args)

		jObj = self.ls.threads.list()
		return (v.get('uuid') for v in jObj if v.get('uuid').startswith(prefix))

# -------------------------- Users ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class UsersListCommand(DefaultCommand):
	""" List all users store into LinShare."""

	def __call__(self, args):
		super(UsersListCommand, self).__call__(args)

		jObj = self.ls.users.list()
		d_format = "{firstName:11s}{lastName:10s}{domain:<20}{mail}"
		#print "%(firstName)-10s %(lastName)-10s\t %(domain)s %(mail)s" % f
		#self.printPrettyJson(jObj)
		self.printList(jObj, d_format, "Users")

####################################################################################
### documents
####################################################################################
def add_document_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()

	parser_tmp2 = subparsers2.add_parser('upload', help="upload documents to linshare")
	parser_tmp2.set_defaults(__func__=DocumentsUploadCommand())
	parser_tmp2.add_argument('files', nargs='+')

	parser_tmp2 = subparsers2.add_parser('upshare', help="upload and share documents")
	parser_tmp2.set_defaults(__func__=DocumentsUploadAndSharingCommand())
	parser_tmp2.add_argument('files', nargs='+').completer = DefaultCompleter()
	parser_tmp2.add_argument('-m', '--mail', action="append", dest="mails", required=True, help="Recipient mails.")

	parser_tmp2 = subparsers2.add_parser('download', help="download documents from linshare")
	parser_tmp2.set_defaults(__func__=DocumentsDownloadCommand())
	parser_tmp2.add_argument('uuids', nargs='+').completer = DefaultCompleter()

	parser_tmp2 = subparsers2.add_parser('list', help="list documents from linshare")
	parser_tmp2.set_defaults(__func__=DocumentsListCommand())

####################################################################################
### shares
####################################################################################
def add_share_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()

	parser_tmp2 = subparsers2.add_parser('create', help="share files into linshare")
	parser_tmp2.set_defaults(__func__=SharesCommand())
	parser_tmp2.add_argument('uuids', nargs='+', help="document's uuids you want to share.").completer = DefaultCompleter()
	parser_tmp2.add_argument('-m', '--mail', action="append", dest="mails", required=True, help="Recipient mails.").completer = DefaultCompleter("complete_mail")


####################################################################################
### received shares
####################################################################################
def add_received_share_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()

	parser_tmp2 = subparsers2.add_parser('download', help="download received shares from linshare")
	parser_tmp2.set_defaults(__func__=ReceivedSharesDownloadCommand())
	parser_tmp2.add_argument('uuids', nargs='+', help="share's uuids you want to download.").completer = DefaultCompleter()

	parser_tmp2 = subparsers2.add_parser('list', help="list received shares from linshare")
	parser_tmp2.set_defaults(__func__=ReceivedSharesListCommand())

####################################################################################
###  threads
####################################################################################
def add_threads_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()
	parser_tmp2 = subparsers2.add_parser('list', help="list threads from linshare")
	parser_tmp2.set_defaults(__func__=ThreadsListCommand())

	parser_tmp2 = subparsers2.add_parser('listmembers', help="list thread members.")
	parser_tmp2.add_argument('-u', '--uuid', action="store", dest="uuid", required=True).completer = DefaultCompleter()
	parser_tmp2.set_defaults(__func__=ThreadMembersListCommand())

####################################################################################
###  users
####################################################################################
def add_users_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()
	parser_tmp2 = subparsers2.add_parser('list', help="list users from linshare")
	parser_tmp2.set_defaults(__func__=UsersListCommand())

####################################################################################
### config
####################################################################################
def add_config_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()

	parser_tmp2 = subparsers2.add_parser('generate', help="generate the default pref file")
	parser_tmp2.set_defaults(__func__=ConfigGenerationCommand())

	parser_tmp2 = subparsers2.add_parser('autocomplete', help="Print help to install and configure autocompletion module")
	parser_tmp2.set_defaults(__func__=ConfigAutoCompteCommand())
