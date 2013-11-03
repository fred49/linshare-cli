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
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#


import os
import logging
import argparse
import ConfigParser
import logging
import logging.handlers
import base64
import urllib2 , cookielib
import json
import poster
import time
import copy
from datetime import datetime
from time import time
from progressbar import *
import getpass
import hashlib



# ---------------------------------------------------------------------------------------------------------------------
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


def cli_get_cache(user_function):
	cache = {}
	cachedir="~/.linshare-cache"
	cachedir = os.path.expanduser(cachedir)
	if not os.path.isdir(cachedir) :
		os.makedirs(cachedir)

	log = logging.getLogger('linshare-cli.cli_get_cache')

	def log_exec_time(fn, *args):
		start = time.time()
		res = fn(*args)
		end = time.time()
		log.debug("function time : " + str (end - start))
		return res

	def get_data(fn, cachefile,  *args):
		res = log_exec_time(fn, *args)
		with open(cachefile , 'wb') as f :
			json.dump(res , f)
		return res

	def _load_data(cachefile):
		if os.path.isfile(cachefile) :
			with open(cachefile , 'rb') as f :
				res = json.load(f)
			return res
		else:
			raise ValueError("no file found.")

	def load_data(cachefile):
		return log_exec_time(_load_data, cachefile)


	def decorating_function(*args):
		cli = args[0]
		url = cli.getFullUrl(args[1])
		cli.log.debug("cache url : "+ url)
		key = hashlib.sha256(url + "|" + cli.user).hexdigest()
		cli.log.debug("key: "+ key)
		cachefile = cachedir + "/" + key

		cache_time = cli.cache_time
		nocache = cli.nocache

		res = None
		if nocache :
			log.debug("cache disabled.")
			return log_exec_time(user_function, *args)

		if os.path.isfile(cachefile) :
			file_time = os.stat(cachefile).st_mtime
			a = "{da:%Y-%m-%d %H:%M:%S}"
			log.debug("cached data : "  + str(a.format(da=datetime.fromtimestamp(file_time))))

			if time.time() - cache_time > file_time:
				log.debug("refreshing cached data.")
				res = get_data(user_function, cachefile, *args)
			if not res :
				try:
					res = load_data(cachefile)
				except ValueError as e :
					log.debug("error : " + str(e))
		if not res :
			res = get_data(user_function, cachefile, *args)
		return res

	return decorating_function


# ---------------------------------------------------------------------------------------------------------------------
class CoreCli(object):

        def __init__(self, host, user, password, verbose=False, debug=0, realm="Name Of Your LinShare Realm", application_name="linshare"):
		self.log = logging.getLogger('linshare-cli' + "." + str(self.__class__.__name__.lower()))
                self.verbose	= verbose
                self.debug	= debug
		self.password	= password
		self.user	= user
		self.last_req_time	= None
		self.cache_time = 60
		self.nocache = False

		if not host:
			raise ValueError("invalid host : host url is not set !")
		if not user:
			raise ValueError("invalid user : " + str(user))
		if not password:
			raise ValueError("invalid password : password is not set ! ")

		if not application_name :
			application_name="linshare"
		if not realm :
			realm="Name Of Your LinShare Realm"

		self.root_url = host + "/" + application_name + "/" + "webservice/rest/"


		self.debuglevel = 0
		# 0 : debug off
		# 1 : debug on
		# 2 : debug on, request result is printed (pretty json)
		# 3 : debug on, urllib debug on,  http headers and request are printed
		httpdebuglevel = 0
		if self.debug :
			try:
				self.debuglevel = int(self.debug)
			except ValueError as e :
				self.debuglevel = 1

			if self.debuglevel >= 3 :
				httpdebuglevel = 1

		# We declare all the handlers useful here.
		auth_handler = urllib2.HTTPBasicAuthHandler()
		auth_handler.add_password(realm=realm,
			uri=host,
			user=user,
			passwd=password)

		handlers = [poster.streaminghttp.StreamingHTTPSHandler(debuglevel=httpdebuglevel),
			auth_handler,
			urllib2.HTTPSHandler(debuglevel=httpdebuglevel),
			urllib2.HTTPHandler(debuglevel=httpdebuglevel),
			poster.streaminghttp.StreamingHTTPHandler(debuglevel=httpdebuglevel),
			poster.streaminghttp.StreamingHTTPRedirectHandler(),
			urllib2.HTTPCookieProcessor(cookielib.CookieJar())]

		# Setting handlers
		urllib2.install_opener(urllib2.build_opener(*handlers))

	def getFullUrl(self, url_frament):
		return self.root_url + url_frament

	def auth(self):
		url = self.getFullUrl("authentication/authorized")
		self.log.debug("list url : "+ url)

		# Building request
		request = urllib2.Request(url)

		# doRequest
		try:
			resultq = urllib2.urlopen(request)

			code=resultq.getcode()
			if code == 200 :
				self.log.debug("auth url : ok")
				return True

		except urllib2.HTTPError as e :
			if e.code == 401 :
				self.log.error(e.msg + " (" + str(e.code) + ")")
			else:
				self.log.error(e.msg + " (" + str(e.code) + ")")
		return False 


	def add_auth_header(self, request ):
		base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')
		request.add_header("Authorization", "Basic %s" % base64string)
		#request.add_header("Cookie", "JSESSIONID=")


	@cli_get_cache
	def _list(self , url):
		""" List all documents store into LinShare."""
		self.last_req_time = None
		url = self.root_url + url
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

		jObj = json.loads(result)
		if self.debuglevel >= 2 : 
			self.log.debug("the result is : ")
			self.log.debug(json.dumps(jObj, sort_keys = True, indent = 2))

		self.last_req_time = str(endtime - starttime)
		self.log.debug("list url : " + url + " : request time : " + self.last_req_time)
		return jObj

	def _upload(self, file_path, url):
		self.last_req_time = None
		url = self.root_url + url
		self.log.debug("upload url : "+ url)

		# Generating datas and headers
		file_size = os.path.getsize(file_path)
		file_name = file_path.split("/")[-1]
		self.log.debug("file_name is : " + file_name)


		widgets = [FileTransferSpeed(),' <<<', Bar(), '>>> ', Percentage(),' ', ETA()]
	        pbar = ProgressBar(widgets=widgets, maxval=file_size)
		stream = file_with_callback(file_path, 'rb', pbar.update, file_size, file_path)
		
		p = poster.encode.MultipartParam("file", filename=file_name, fileobj=stream)

		datagen, headers = poster.encode.multipart_encode( [ p,] )
		#datagen, headers = poster.encode.multipart_encode( [ p, ("comment", self.comment)] )

		# Building request
		request = urllib2.Request(url,datagen, headers)

		# request start
	        pbar.start()
		starttime = datetime.now()

		try:
			# doRequest
		        resultq = urllib2.urlopen(request)
		except urllib2.HTTPError as e :
			self.log.error("Http error : " + e.msg)
			self.log.error("error code : " + e.code)

		        # request end
		        endtime = datetime.now()
		        pbar.finish()

		        self.last_req_time = str(endtime - starttime)
		        self.log.error("The file '" + file_name + "' was uploaded (" + self.last_req_time + "s) but the proxy cut the connexion. No server acquitment was received.")
		        return None


		# request end
		endtime = datetime.now()
	        pbar.finish()
		result = resultq.read()

		jObj = json.loads(result)
		if self.debuglevel >= 2 : 
			self.log.debug("the result is : ")
			self.log.debug(json.dumps(jObj, sort_keys = True, indent = 2))

		self.last_req_time = str(endtime - starttime)
		self.log.debug("list url : " + url + " : request time : " + self.last_req_time)
		return jObj


	def _download(self, uuid, url):
		""" download a file from LinShare using its rest api.
This method could throw exceptions like urllib2.HTTPError."""
		self.last_req_time = None
		url = self.root_url + url
		self.log.debug("download url : "+ url)

		# Building request
		request = urllib2.Request(url)

		# request start
		starttime =datetime.now()

		# doRequest
		resultq = urllib2.urlopen(request)

		code=resultq.getcode()
		file_name = uuid
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
		self.last_req_time = str(endtime - starttime)
		self.log.debug("list url : " + url + " : request time : " + self.last_req_time)
		return (file_name, self.last_req_time)

# ---------------------------------------------------------------------------------------------------------------------
# USER API
# ---------------------------------------------------------------------------------------------------------------------
class Documents(object):
        def __init__(self, corecli):
		self.core = corecli

	def list(self):
		""" List all documents store into LinShare."""
		return self.core._list("documents.json")

	def upload(self, file_path):
		""" Upload a file to LinShare using its rest api. return the uploaded document uuid  """
		return self.core._upload(file_path , "documents.json" )

	def download(self, uuid):
		url = "documents/%s/download" % uuid
		return self.core._download(uuid, url)

# ---------------------------------------------------------------------------------------------------------------------
class ReceivedShares(object):
        def __init__(self, corecli):
		self.core = corecli

	def list(self):
		return self.core._list("shares.json")

	def download(self, uuid):
		url = "shares/%s/download" % uuid
		return self.core._download(uuid, url)

# ---------------------------------------------------------------------------------------------------------------------
class Shares(object):
        def __init__(self, corecli):
		self.core = corecli
		self.log = logging.getLogger('linshare-cli' + "." + str(self.__class__.__name__.lower()))

	def share(self, uuid , mail):

		url = self.core.root_url + "shares/sharedocument/%s/%s"  % ( mail , uuid  )
		self.log.debug("share url : "+ url)

		# Building request
		request = urllib2.Request(url)

		# request start
		starttime =datetime.now()

		try:
			# doRequest
		        resultq = urllib2.urlopen(request)
		except urllib2.HTTPError as e :
		        print e
		        print e.code
			print url
			raise e

		# request end
		endtime = datetime.now()
		code = resultq.getcode()
		msg = resultq.msg

		self.core.last_req_time = str(endtime - starttime)
		self.log.debug("share url : " + url + " : request time : " + self.core.last_req_time)
		self.log.debug("the result is : " + str(code) + " : " + msg)
		return ( code, msg , self.core.last_req_time )


# ---------------------------------------------------------------------------------------------------------------------
class Threads(object):
        def __init__(self, corecli):
		self.core = corecli

	def list(self):
		return self.core._list("threads.json")

# ---------------------------------------------------------------------------------------------------------------------
class ThreadsMembers(object):
        def __init__(self, corecli):
		self.core = corecli

	def list(self, threadUuid):
		url = "thread_members/%s.json" % threadUuid
		return self.core._list(url)

# ---------------------------------------------------------------------------------------------------------------------
class Users(object):
        def __init__(self, corecli):
		self.core = corecli

	def list(self):
		return self.core._list("users.json")

# ---------------------------------------------------------------------------------------------------------------------
class UserCli(CoreCli):
        def __init__(self, *args , **kwargs):
		super(UserCli, self).__init__(*args , **kwargs)
		self.documents = Documents(self)
		self.rshares = ReceivedShares(self)
		self.shares = Shares(self)
		self.threads = Threads(self)
		self.thread_members = ThreadsMembers(self)
		self.users = Users(self)


# ---------------------------------------------------------------------------------------------------------------------
# ADMIN API
# ---------------------------------------------------------------------------------------------------------------------

class ThreadsAdmin(object):
        def __init__(self, corecli):
		self.core = corecli

	def list(self):
		return self.core._list("threads.json")

# ---------------------------------------------------------------------------------------------------------------------
class AdminCli(CoreCli):
        def __init__(self, *args , **kwargs):
		super(AdminCli, self).__init__(*args , **kwargs)
		self.threads = Threads(self)



