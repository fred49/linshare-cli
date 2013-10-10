#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import logging
import urllib2
import getpass

from linshare_cli.core import LinShareCli
from linshare_cli.common import DefaultCommand


# ---------------------------------------------------------------------------------------------------------------------
class DefaultCommand(object):

        def __init__(self):
		self.log = logging.getLogger('linshare-cli' + "." + str(self.__class__.__name__.lower()))
		#self.log.debug(str(self.__class__.__name__))

        def __call__(self, args):
		self.ls = LinShareCli(args.host , args.user , args.password , args.verbose, args.debug)
                self.verbose = args.verbose
                self.debug = args.debug

                # suppress __func__ object ang password just for display
                dict_tmp=args
                delattr(dict_tmp,"__func__")
                delattr(dict_tmp,"password")
                self.log.debug(str(dict_tmp))

		if args.ask_password :
			try:
				self.ls.password = getpass.getpass("Please, enter your password : ")
			except KeyboardInterrupt as e:
				print "\nKeyboardInterrupt exception was caught. Program terminated."
				sys.exit(1)

		if not self.ls.password:
			raise ValueError("invalid password : password is not set ! ")
		if not args.realm:
			self.ls.realm = args.realm
		if args.application_name:
			self.ls.application_name=args.application_name

		if not self.ls.auth():
			sys.exit(1)


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

		jObj = self.ls.listDocument()
		print "File names : "
		print "------------"
		for f in jObj:
			print "%(name)-60s\t %(uuid)s" % f
			#print "File names : %(name)-60s\t %(uuid)s" % f

# ---------------------------------------------------------------------------------------------------------------------
class DocumentsUploadCommand(DefaultCommand):
	""" upload a file to LinShare using its rest api. return the uploaded document uuid  """

	def __call__(self, args):
		super(DocumentsUploadCommand, self).__call__(args)

		for file_path in args.files : 
			jObj = self.ls.uploadFile(file_path)
			self.log.info("The file '" + jObj.get('name') + "' ("+ jObj.get('uuid') + ") was uploaded. (" + self.ls.last_req_time + "s)")


# ---------------------------------------------------------------------------------------------------------------------
class DocumentsDownloadCommand(DefaultCommand):

	def __call__(self, args):
		super(DocumentsDownloadCommand, self).__call__(args)

		for uuid in args.uuids:
			try:
				file_name, req_time = self.ls.downloadDocument(uuid)
				self.log.info("The file '" + file_name  + "' was downloaded. (" + req_time + "s)")
			except urllib2.HTTPError as e :
				print "Error : "
				print e
				return

# ----------------- Received Shares ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class ReceivedSharesListCommand(DefaultCommand):

	def __call__(self, args):
		super(ReceivedSharesListCommand, self).__call__(args)
		jObj = self.ls.listReceivedShares()

		print "Received Shares: "
		print "------------"
		for f in jObj:
			print "%(name)-60s\t %(uuid)s" % f
			#print "File names : %(name)-60s\t %(uuid)s" % f


# ---------------------------------------------------------------------------------------------------------------------
class ReceivedSharesDownloadCommand(DefaultCommand):

	def __call__(self, args):
		super(ReceivedSharesDownloadCommand, self).__call__(args)

		for uuid in args.uuids:
			try:
				file_name, req_time =  self.ls.downloadReceivedShares(uuid)
				self.log.info("The share '" + file_name  + "' was downloaded. (" + req_time + "s)")
			except urllib2.HTTPError as e :
				print "Error : "
				print e
				return



# -------------------------- Shares ------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class ShareCommand(DefaultCommand): 

	def __call__(self, args):
		super(ShareCommand, self).__call__(args)

		for uuid in args.uuids :
			for mail in args.mails :
				code, msg , req_time = self.ls.shareOneDoc(uuid , mail)

				if code == 204 : 
					self.log.info("The document '" + uuid + "' was successfully shared with " + mail + " ( "+ req_time + "s)")
				else :
					self.log.warn("Trying to share document '" + uuid + "' with " + mail)
					self.log.error("Unexpected return code : " + str(code) + " : " + msg)


