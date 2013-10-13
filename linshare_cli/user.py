#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import logging
import urllib2
import getpass

import common
from core import UserCli

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
		print "File names : "
		print "------------"
		self.formatDate(jObj, 'creationDate')
		#self.addDateObject(jObj, 'creationDate')
		self.addLegend(jObj)
		firstLine = True
		for f in jObj:
			if firstLine:
				firstLine=False
				print "{0[name]:60s}{0[creationDate]:30s}{0[uuid]:30s}".format(f)
			else:
				print "{name:60s}{creationDateD:30s}{uuid:30s}".format(**f)

	def complete(self, prefix):
		jObj = self.ls.documents.list()
		return (v.get('uuid') for v in jObj if v.get('uuid').startswith(prefix))



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

# ----------------- Received Shares ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class ReceivedSharesListCommand(DefaultCommand):

	def __call__(self, args):
		super(ReceivedSharesListCommand, self).__call__(args)
		jObj = self.ls.rshares.list()

		print "Received Shares: "
		print "------------"
		self.addLegend(jObj)
		for f in jObj:
			print "%(name)-60s\t %(uuid)s" % f


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


# -------------------------- Threads ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class ThreadsListCommand(DefaultCommand):
	""" List all threads store into LinShare."""

	def __call__(self, args):
		super(ThreadsListCommand, self).__call__(args)

		jObj = self.ls.threads.list()
		#self.printPrettyJson(jObj)
		print "\nThread names : "
		print "--------------"
		self.addLegend(jObj)
		for f in jObj:
			print "%(name)-60s\t %(uuid)s" % f
		print ""

class ThreadsListAutoCompleteCommand(DefaultCommand):
	""" List all threads store into LinShare."""

	def __call__(self, args):
		super(ThreadsListAutoCompleteCommand, self).__call__(args)

		jObj = self.ls.threads.list()
		return (v.get('uuid') for v in jObj)

# ---------------------------------------------------------------------------------------------------------------------
class ThreadMembersListCommand(DefaultCommand):
	""" List all thread members store from a thread."""

	def __call__(self, args):
		super(ThreadMembersListCommand, self).__call__(args)

		jObj = self.ls.thread_members.list(args.uuid)
		#self.printPrettyJson(jObj)
		print "\nThread members : "
		print "------------------"
		self.addLegend(jObj)
		for f in jObj:
			print "%(firstName)-10s %(lastName)-10s\t %(admin)-10s\t %(readonly)-10s\t %(id)s" % f
		print ""




