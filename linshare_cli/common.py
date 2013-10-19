#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import logging
import json
import getpass
import base64
import copy
import datetime
from core import UserCli
from tool import *

# ---------------------------------------------------------------------------------------------------------------------
class Config(object):
	""" Class design to store all the configuration for this application."""
	section="server"
	filepath="~/.linshare.ini"
	def __init__(self):
		# Ldap parameters
		self.fields = ['host', 'realm', 'user', 'password', 'application_name', 'config', 'server_section', 'debug' , 'nocache' ] 
		myPref = MyPref(self.filepath, self.section, expanduser=True, prefix = "\t", mandatory = False)
		self.linshare = myPref(self.fields)
		self.decode_password()

	def reload(self, args):
		if args.server_section or args.config :
			server_section_name = self.section
			if args.server_section :
				server_section_name += '-' + str(args.server_section)

			myPref = MyPref(self.filepath, server_section_name, expanduser=True, prefix = "\t", mandatory = False)
			self.linshare = myPref(self.fields)
			self.decode_password()

	def push(self, args):
		for field in self.fields:
			# checking if input args has the attribute 'field'
			if hasattr(args, field):
				# we check if it is set with something, if not we used the config file value
				if not getattr(args, field):
					setattr(args, field, getattr(self.linshare, field, None))
			else :
				# field not set, setting on using the config file value
				setattr(args, field, getattr(self.linshare, field, None))

	def write_default_config_file(self):

		log = logging.getLogger('linshare-cli')
		filepath = os.path.expanduser(self.filepath)
		if os.path.isfile(filepath) :
			log.error("Can not generate the pref file because it already exists. : " + filepath)
			return 1
		else :
			with open(filepath, 'w') as f:
				f.write("[" + self.section + "]\n")
				for field in self.fields:
					f.write(field + "=\n")

	def decode_password(self):
		try:
			if self.linshare.password :
				data = base64.b64decode(self.linshare.password)
				self.linshare.password = data
		except TypeError as e:
			print "WARN: Password is not stored in the configuration file with base64 encoding"
			print e

	def __str__(self):
		res = ""
		l = list(self.__dict__)
		l.sort()
		for i in l :
			a=""
			obj = getattr(self,i)
			if isinstance(obj, dict) :
				res += "-  " + i + " : " + "\n"
				for key,val in obj.items() :
					res += "\t"
					if isinstance(val,CPref):
						res += "-  " + key + " : " + "\n" + str(val) + "\n"
					else :
						res += "-  " + key + " : " + str(val) + "\n"
						#res += "-  " + i + " : " + a + str(getattr(self,i)) + "\n"

			else:
				res += "-  " + i + " : " + a + str(getattr(self,i)) + "\n"

		return res

# ---------------------------------------------------------------------------------------------------------------------
class DefaultCommand(object):

	def __init__(self):
		self.log = logging.getLogger('linshare-cli' + "." + str(self.__class__.__name__.lower()))

	def __call__(self, args):
		self.verbose = args.verbose
		self.debug = args.debug

		# suppress __func__ object ang password just for display

		dict_tmp=copy.copy(args)
		delattr(dict_tmp,"__func__")
		delattr(dict_tmp,"password")
		self.log.debug(str(dict_tmp))

		if args.ask_password :
			try:
				args.password = getpass.getpass("Please, enter your password : ")
			except KeyboardInterrupt as e:
				print "\nKeyboardInterrupt exception was caught. Program terminated."
				sys.exit(1)

		if not args.password:
			raise ValueError("invalid password : password is not set ! ")

		self.ls = self._getCliObject(args)
		if args.nocache:
			self.ls.nocache = True
		if not self.ls.auth():
			sys.exit(1)

	def _getCliObject(self, args):
		raise NotImplementedError("You must implement the _getCliObject method and return a object instance of CoreCli or its children in your Command class.")


	def printPrettyJson(self, obj):
			print json.dumps(obj, sort_keys = True, indent = 2)


	def addLegend(self, data):
		legend = dict()
		for i in data[0] :
			legend[i]=i.upper()
		data.insert(0, legend)

	def addDateObject(self, data, attr):
		for f in data:
			f[attr + "D"] = datetime.datetime.fromtimestamp(f.get(attr) /1000)

	def formatDate(self, data, attr, dformat="%Y-%m-%d %H:%M:%S"):
		for f in data:
			a = "{da:" + dformat + "}"
			f[attr + "D"] = a.format(da=datetime.datetime.fromtimestamp(f.get(attr) /1000))




