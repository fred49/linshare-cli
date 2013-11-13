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


import os , sys
import logging
import ConfigParser

# ---------------------------------------------------------------------------------------------------------------------
#
#
class PrefFile(object):
	"""extract a specific value from the configuration file
	"""

	# ---------------------------------------------------------------------------------------------------------------------
	def __init__(self , file , section , field ,  expanduser = False ) :
		self.section = section
		self.field = field
		self._result = None
		if expanduser :
			self.file = os.path.expanduser(file)
		else :
			self.file = file


	def __call__(self):

		# Le champ result permet la mise en cache du résultat de cette fonction.
		if self._result != None :
			return self._result

		if os.path.isfile( self.file ) :
			fileParser = ConfigParser.ConfigParser()
			fileParser.read( [ self.file ] )

			# Read the field from the config file            
			#try:
			self._result =  fileParser.get( self.section , self.field )
			return self._result
			#except ConfigParser.NoOptionError:
		else :
			print "pref file was not found : " + self.file
			print
			sys.exit(1)
	def __repr__(self):
		return str(self())


class CPref(object):
	def __init__(self, prefix):
		self._prefix = prefix

	def __str__(self):
		res = ""
		l = list(self.__dict__)
		l.sort()
		for i in l :
			if i == "password":
				continue
			if i != "_prefix":
				res += self._prefix + "-  " + i + " : " + repr(getattr(self,i)) + "\n"
		return res


class MyPref(PrefFile):
	"""Class design to extract preferences from a configuration file and return a object with all fields."""

	def __init__(self , file , section ,  expanduser = False , prefix = "", mandatory = True) :
		""" set up preference file path and the section you want to search in."""
		
		self.section = section
		if expanduser :
			self.file = os.path.expanduser(file)
		else :
			self.file = file
		self.prefix = prefix
		self.mandatory = mandatory


	def __call__(self, fields = []):
		""" fields is a list of all the keywords you want to extract from the configuration file."""
		
		#c = type('CPref' , (object,) , dict())
		c = CPref(self.prefix)
		log = logging.getLogger('linshare-cli')

		if os.path.isfile( self.file ) :
			fileParser = ConfigParser.ConfigParser()
			fileParser.read( [ self.file ] )

			# Read the field from the config file            
			for field in fields:
				try:
					value = fileParser.get( self.section , field )
					setattr(c, field, value)
				except ConfigParser.NoOptionError :
					log.debug("Not found : " + field ) 
					setattr(c, field, None)
			return c
					
		else :
			if self.mandatory :
				print "pref file was not found : " + self.file
				print
				sys.exit(1)


			for field in fields:
				setattr(c, field, None)
			return c
