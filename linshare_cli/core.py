#!/usr/bin/python
# -*- coding: utf-8 -*-


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
from datetime import datetime
from progressbar import *
import getpass



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

# ---------------------------------------------------------------------------------------------------------------------
class LinShareCli(object):

        def __init__(self, host, user, password, verbose=False, debug=0, realm="Name Of Your LinShare Realm", application_name="linshare"):
		self.log = logging.getLogger('linshare-cli' + "." + str(self.__class__.__name__.lower()))
                self.verbose	= verbose
                self.debug	= debug
		self.password	= password
		self.user	= user
		self.last_req_time	= None

		if not host:
			raise ValueError("invalid host : host url is not set !")
		if not user:
			raise ValueError("invalid user : " + str(user))
		if not password:
			raise ValueError("invalid password : password is not set ! ")

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


	def auth(self):
		url = self.root_url + "authentication/authorized"

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
# ---------------------------------------------------------------------------------------------------------------------

	def listDocument(self):
		""" List all documents store into LinShare."""
		return self._list("documents.json")

	def uploadFile(self, file_path):
		""" Upload a file to LinShare using its rest api. return the uploaded document uuid  """
		return self._upload(file_path , "documents.json" )

	def downloadDocument(self, uuid):
		url = "documents/%s/download" % uuid
		return self._download(uuid, url)

# ---------------------------------------------------------------------------------------------------------------------

	def listReceivedShares(self):
		return self._list("shares.json")

	def downloadReceivedShares(self, uuid):
		url = "shares/download/%s" % uuid
		return self._download(uuid, url)



# ---------------------------------------------------------------------------------------------------------------------

	def shareOneDoc(self, uuid , mail):

		url = self.root_url + "shares/sharedocument/%s/%s"  % ( mail , uuid  )
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

		self.last_req_time = str(endtime - starttime)
		self.log.debug("share url : " + url + " : request time : " + self.last_req_time)
		self.log.debug("the result is : " + str(code) + " : " + msg)
		return ( code, msg , self.last_req_time )
# ---------------------------------------------------------------------------------------------------------------------

