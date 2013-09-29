#!/usr/bin/python
# -*- coding: utf-8 -*-


import os , re , sys
import subprocess , shlex
import logging
import argparse
import ConfigParser
import logging
import logging.handlers
import shlex
import subprocess
import hashlib
from base64 import encodestring as encode
import base64
import urllib2 , cookielib
import json
import poster
import time
from datetime import datetime
from progressbar import *


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
		log.error('pouet')

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

class Config(object):
	""" Class design to store all the configuration for this application."""
	def __init__(self):
		# Ldap parameters
		self.fields = ['host', 'realm', 'user', 'password', 'application_name', 'config', 'server_section', 'debug' ] 
		myPref = MyPref("~/.linshare.ini", 'server', expanduser=True, prefix = "\t", mandatory = False)
		self.linshare = myPref(self.fields)
		self.decode_password()

	def reload(self, args):
		if args.server_section or args.config :
			server_section_name = 'server'
			if args.server_section :
				server_section_name += '-' + str(args.server_section)
		
			myPref = MyPref("~/.linshare.ini", server_section_name, expanduser=True, prefix = "\t", mandatory = False)
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
	
	def decode_password(self):
		try:
			if self.linshare.password :
				data = base64.b64decode(self.linshare.password)
				self.linshare.password = data
		except Exception as e:
			print "WARN: Password is not stored in the configuration file with  base64 encoding"
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

# ---------------------------------------------------------------------------------------------------------------------
log = logging.getLogger()
log.setLevel(logging.INFO)
# logger formats
myFormat = logging.Formatter("%(asctime)s %(levelname)-8s: %(message)s", "%H:%M:%S")
myDebugFormat = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s:%(funcName)s:%(message)s", "%H:%M:%S")
# logger handlers
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(myFormat)
log.addHandler(streamHandler)
# debug mode
# if you need debug during class construction, file config loading, ...,  you need to modify the logger level here.
if True : 
	log.setLevel(logging.DEBUG)
	streamHandler.setFormatter(myDebugFormat)

# global logger variable
log = logging.getLogger('linshare-cli')

# ---------------------------------------------------------------------------------------------------------------------
class DefaultCommand(object):

        def __init__(self):
		self.log = logging.getLogger('linshare-cli' + "." + str(self.__class__.__name__.lower()))
		#self.log.debug(str(self.__class__.__name__))

        def __call__(self, args):
                self.verbose = args.verbose
                self.debug = args.debug

                # suppress __func__ object just for display
                dict_tmp=args
                delattr(dict_tmp,"__func__")
		password=args.password
                delattr(dict_tmp,"password")
                self.log.debug(str(dict_tmp))


		if not args.user:
			raise ValueError("invalid user : " + str(args.user))

		if not password:
			raise ValueError("invalid password : " + str(password))

		if not args.host:
			raise ValueError("invalid host : " + str(args.host))

		if not args.realm:
			args.realm = "Name Of Your LinShare Realm"
		if not args.application_name:
			args.application_name="linshare"

		self.user = args.user
		self.password = password
		self.root_url = args.host + "/" + args.application_name + "/" + "webservice/rest/"


		#self.fragment_upload = "documents/upload"
		#if self.fragment_upload[-1] != "/" :
		#	self.fragment_upload += "/" 
		self.fragment_upload = "documents/upload"
		self.fragment_upload = "documents"
		self.fragment_list = "documents"
		self.fragment_download = "documents/%s/download"

		# /rest/authentication/authorized


		# We declare all the handlers useful here.
		debuglevel = 0
		if self.debug :
			debuglevel = 1

		auth_handler = urllib2.HTTPBasicAuthHandler()
		auth_handler.add_password(realm=args.realm,
			uri=args.host,
			user=self.user,
			passwd=self.password)

		handlers = [poster.streaminghttp.StreamingHTTPSHandler(debuglevel=debuglevel),
			auth_handler,
			urllib2.HTTPSHandler(debuglevel=debuglevel),
			urllib2.HTTPHandler(debuglevel=debuglevel),
			poster.streaminghttp.StreamingHTTPHandler(debuglevel=debuglevel),
			poster.streaminghttp.StreamingHTTPRedirectHandler(),
			urllib2.HTTPCookieProcessor(cookielib.CookieJar())]

		# Setting handlers
		urllib2.install_opener(urllib2.build_opener(*handlers))



	def add_auth_header(self, request ):
		base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')
		request.add_header("Authorization", "Basic %s" % base64string)
		#request.add_header("Cookie", "JSESSIONID=3AF1BB555CAFFEC7A3CA11DE805BB031")




class TestCommand(DefaultCommand):

	def __call__(self, args):
		super(TestCommand, self).__call__(args)
		self.verbose = args.verbose
		self.debug = args.debug


def extract_file_name(content_dispo):
	file_name = ""
	for key_val in content_dispo.split(';') :
		param = key_val.strip().split('=')
		if param[0] == "filename":
			file_name =  param[1]
		if param[0] == "filename*":
			file_name =  param[1].split("'")[2]
	return file_name


class file_with_callback(file):
	def __init__(self, path, mode, callback, size=None, *args):
		file.__init__(self, path, mode)
		if size :
			self._total = size
		else:
			self.seek(0, os.SEEK_END)
			self._total = self.tell()
		self.seek(0)
		self._callback = callback
		self._args = args
		self._seen = 0.0
		
	def __len__(self):
		return self._total
	
	def read(self, size):
		data = file.read(self, size)
		self._seen += size
		if self._seen > self._total :
			self._callback(self._total)
		else:
			self._callback(self._seen)
		return data

	def write(self, data):
		if data :
			self._seen += len(data)
		if self._seen > self._total :
			self._callback(self._total)
		else:
			self._callback(self._seen)
		data = file.write(self, data)

		
			
class UploadFileCommand(DefaultCommand):

	def __call__(self, args):
		super(UploadFileCommand, self).__call__(args)

		for f in args.files : 
			self.uploadFile(f)

	def uploadFile(self, file_name):
		""" upload a file to LinShare using its rest api. return the uploaded document uuid  """
		url = self.root_url + self.fragment_upload + ".json"
		self.log.debug("upload url : "+ url)

		# Generating datas and headers
		file_size = os.path.getsize(file_name)

		widgets = [FileTransferSpeed(),' <<<', Bar(), '>>> ', Percentage(),' ', ETA()]
	        pbar = ProgressBar(widgets=widgets, maxval=file_size)
		stream = file_with_callback(file_name, 'rb', pbar.update, file_size, file_name)
		
		p = poster.encode.MultipartParam("file", filename=file_name, fileobj=stream)

		datagen, headers = poster.encode.multipart_encode( [ p,] )
		#datagen, headers = poster.encode.multipart_encode( [ p, ("comment", self.comment)] )

		# Building request
		request = urllib2.Request(url,datagen, headers)

		# request start
	        pbar.start()
		starttime =datetime.now()

		# doRequest
		resultq = urllib2.urlopen(request)

		# request end
		endtime = datetime.now()
	        pbar.finish()
		result = resultq.read()

		self.log.debug("the result is : " + str(result))
		jObj = json.loads(result)

		req_time = str(endtime - starttime)
		self.log.info("The file '" + jObj.get('name') + "' ("+ jObj.get('uuid') + ") was uploaded. (" + req_time + "s)")



class DownloadFileCommand(DefaultCommand):

	def __call__(self, args):
		super(DownloadFileCommand, self).__call__(args)

		for f in args.files : 
			pass
			self.downloadFile(f)

	def downloadFile(self, file_uuid):
		""" download a file from LinShare using its rest api. """
		url = self.root_url + self.fragment_download % file_uuid
		self.log.debug("download url : "+ url)

		
		# Building request
		request = urllib2.Request(url)

		# request start
		starttime =datetime.now()

		# doRequest
		try:
			resultq = urllib2.urlopen(request)
		except urllib2.HTTPError as e :
			print "Error : "
			print e
			return

		code=resultq.getcode()
		file_name = file_uuid
		self.log.debug("ret code : '" + str(code) + "'")
		if code == 200 :
			content_lenth = resultq.info().getheader('Content-Length')
			if not content_lenth :
				print "ERRRRRRRRRRRRRRRRRRROOOOOOOOOOOOORR"
				result = resultq.read()
				print result
				return
			file_size = int(resultq.info().getheader('Content-Length').strip())
			content_dispo = resultq.info().getheader('Content-disposition').strip()
			file_name = extract_file_name(content_dispo)

			if os.path.isfile(file_name):
				cpt=1
				while 1:
					if not os.path.isfile(file_name + "." + str(cpt)):
						file_name += "." + str(cpt)
						break	
					cpt+=1
				
					
			widgets = [FileTransferSpeed(),' <<<', Bar(), '>>> ', Percentage(),' ', ETA()]
	        	pbar = ProgressBar(widgets=widgets, maxval=file_size)
			stream = file_with_callback(file_name, 'w', pbar.update, file_size, file_name)
	        	pbar.start()
	
			chunk_size=8192
			chunk_size=4096
			chunk_size=2048
			chunk_size=1024
			chunk_size=256
			while 1:
				chunk = resultq.read(chunk_size)
 				if not chunk:
					break
				stream.write(chunk)
			stream.flush()
			stream.close()
	        	pbar.finish()
		

		# request end
		endtime = datetime.now()
		req_time = str(endtime - starttime)
		self.log.info("The file '" + file_name  + "' was downloaded. (" + req_time + "s)")


class ListFileCommand(DefaultCommand):

	def __call__(self, args):
		super(ListFileCommand, self).__call__(args)
		#self.log.debug(str(self.__class__))

		self.listFile()

	def listFile(self):
		""" upload a file to LinShare using its rest api. return the uploaded document uuid  """
		url = self.root_url + self.fragment_list + ".json"
		self.log.debug("list url : "+ url)


		# Building request
		request = urllib2.Request(url)

		# request start
		starttime =datetime.now()

		# doRequest
		resultq = urllib2.urlopen(request)

		# request end
		endtime = datetime.now()
		result = resultq.read()

		self.log.debug("the result is : " + str(result))
		jObj = json.loads(result)

		req_time = str(endtime - starttime)
	#	self.log.info("The file '" + jObj.get('name') + "' ("+ jObj.get('uuid') + ") was uploaded. (" + req_time + "s)")
		print "File names : "
		print "------------"
		for f in jObj:
			print "%(name)-60s\t %(uuid)s" % f
			#print "File names : %(name)-60s\t %(uuid)s" % f


# ---------------------------------------------------------------------------------------------------------------------
####################################################################################
config = Config()


# create the top-level parser
parser = argparse.ArgumentParser(description="""An user cli for LinShare, using its REST API.""")

parser.add_argument('-V', '--verbose', action="store_true", default=False)
parser.add_argument('-D', '--debug', action="store_true", default=False, help=argparse.SUPPRESS)
parser.add_argument('-c', '--config', action="store", help="other configuration file.")
parser.add_argument('-s', dest='server_section', action="store", help="This option let you select the server section in the ini file you want to load (server section is always load first as default configuration). You just need to specify a number like '4' for section 'server-4'.")

#parser.add_argument('-u', '--user', action="store", default=config.linshare.user, dest="user")
##, required=True)
#parser.add_argument('-p', '--password', action="store", default=config.linshare.password)
#parser.add_argument('-H', '--host', action="store", default=config.linshare.host)
#parser.add_argument('-a', '--appname', action="store", default=config.linshare.application_name, dest="application_name")
#parser.add_argument('-r', '--realm', action="store", help=argparse.SUPPRESS, default=config.linshare.realm)


parser.add_argument('-u', '--user', action="store", dest="user")
#, required=True)
parser.add_argument('-p', '--password', action="store")
parser.add_argument('-H', '--host', action="store")
parser.add_argument('-a', '--appname', action="store", dest="application_name")
parser.add_argument('-r', '--realm', action="store", help=argparse.SUPPRESS)

####################################################################################
subparsers = parser.add_subparsers()


####################################################################################
### document
####################################################################################
def add_download_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()
	parser_tmp2 = subparsers2.add_parser('upload', help="upload files to linshare")
	parser_tmp2.set_defaults(__func__=UploadFileCommand())
	parser_tmp2.add_argument('-f', '--file', action="append", dest="files", required=True)


	parser_tmp2 = subparsers2.add_parser('download', help="download files from linshare")
	parser_tmp2.set_defaults(__func__=DownloadFileCommand())
	parser_tmp2.add_argument('-f', '--file', action="append", dest="files", required=True)

	parser_tmp2 = subparsers2.add_parser('list', help="list files from linshare")
	parser_tmp2.set_defaults(__func__=ListFileCommand())


add_download_parser(subparsers, "document", "document tools")


#parser_tmp = subparsers.add_parser('date',  help="Find new aired episodes.")
#parser_tmp.set_defaults(__func__=SearchForNewEpisodeCommand())
#parser_tmp.add_argument('-t', '--root-directory', action="store", default=config.root_directory)
#parser_tmp.add_argument('-d', '--directory', action="store")
#parser_tmp.add_argument('-s', '--season', action="store", required=True, type=int)
#parser_tmp.add_argument('-e', '--episode', action="store", default=0, type=int)


####################################################################################
### TEST
####################################################################################
parser_tmp = subparsers.add_parser('test', add_help=False)
parser_tmp.set_defaults(__func__=TestCommand())

####################################################################################
### MAIN
####################################################################################

if __name__ == "__main__" :
	# parse cli arguments
	args = parser.parse_args()
	# reloading configuration with optional arguments
	config.reload(args)
	# using values stored in config file to filled in undefined args.
	config.push(args)

	if getattr(args, 'debug'):
		log.setLevel(logging.DEBUG)
		streamHandler.setFormatter(myDebugFormat)
		print config
		#print args
		print "----------- processing ----------------"


		# run command
		args.__func__(args)
	else:
		# run command
		try:
			args.__func__(args)
		except Exception as a :
			log.error("unexcepted error : " + str(a))

sys.exit(0)
