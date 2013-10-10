#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import logging
import getpass

# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
class DefaultCommand(object):

        def __init__(self):
		self.log = logging.getLogger('linshare-cli' + "." + str(self.__class__.__name__.lower()))

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




