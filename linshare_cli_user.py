#!/usr/bin/python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

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




import os , re , sys
import argparse
import logging
import logging.handlers




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
if False :
	log.setLevel(logging.DEBUG)
	streamHandler.setFormatter(myDebugFormat)

# global logger variable
log = logging.getLogger('linshare-cli')


from linshare_cli.common import Config
from linshare_cli.user import *


# ---------------------------------------------------------------------------------------------------------------------
class TestCommand(DefaultCommand):

	def __call__(self, args):
		super(TestCommand, self).__call__(args)
		self.verbose = args.verbose
		self.debug = args.debug

# ---------------------------------------------------------------------------------------------------------------------
####################################################################################
config = Config()

# create the top-level parser
parser = argparse.ArgumentParser( prog = "linshare_cli_user" , description="""An user cli for LinShare, using its REST API.""" )
parser = argparse.ArgumentParser( prog = "linshare_cli_user" , description="""An user cli for LinShare, using its REST API.""", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-V', '--verbose', action="store_true", default=False)
#parser.add_argument('-D', '--debug', action="count", dest="debug", default=0, help=argparse.SUPPRESS)
parser.add_argument('-D', '--debug', action="count", dest="debug", default=0, help="""(default: %(default)s)
# 0 : debug off
# 1 : debug on
# 2 : debug on and request result is printed (pretty json)
# 3 : debug on and urllib debug on and http headers and request are printed
""")
parser.add_argument('-c', '--config', action="store", help="Other configuration file.")
parser.add_argument('-s', dest='server_section', action="store", help="This option let you select the server section in the ini file you want to load (server section is always load first as default configuration). You just need to specify a number like '4' for section 'server-4'.")
parser.add_argument('-u', '--user', action="store", dest="user")
#, required=True)
parser.add_argument('-P', '--password', action="store")
parser.add_argument('-p', action="store_true", default=False, dest="ask_password", help="If set, the program will ask you your password.")
parser.add_argument('-H', '--host', action="store")
parser.add_argument('-a', '--appname', action="store", dest="application_name", help="Default value is 'linshare' (extracted from http:/x.x.x.x/linshare)")
parser.add_argument('-r', '--realm', action="store", help=argparse.SUPPRESS)
parser.add_argument('--nocache', action="store_true", help=argparse.SUPPRESS)

####################################################################################
subparsers = parser.add_subparsers()


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
	parser_tmp2.add_argument('files', nargs='+').completer = DefaultCompleter(config)
	parser_tmp2.add_argument('-m', '--mail', action="append", dest="mails", required=True, help="Recipient mails.")

	parser_tmp2 = subparsers2.add_parser('download', help="download documents from linshare")
	parser_tmp2.set_defaults(__func__=DocumentsDownloadCommand())
	parser_tmp2.add_argument('uuids', nargs='+').completer = DefaultCompleter(config)

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
	parser_tmp2.add_argument('uuids', nargs='+', help="document's uuids you want to share.").completer = DefaultCompleter(config)
	parser_tmp2.add_argument('-m', '--mail', action="append", dest="mails", required=True, help="Recipient mails.").completer = DefaultCompleter(config, "complete_mail")
	

####################################################################################
### received shares
####################################################################################
def add_received_share_parser(subparsers, name, desc):
	parser_tmp = subparsers.add_parser(name, help=desc)

	subparsers2 = parser_tmp.add_subparsers()

	parser_tmp2 = subparsers2.add_parser('download', help="download received shares from linshare")
	parser_tmp2.set_defaults(__func__=ReceivedSharesDownloadCommand())
	parser_tmp2.add_argument('uuids', nargs='+', help="share's uuids you want to download.").completer = DefaultCompleter(config)

	#group = parser_tmp2.add_mutually_exclusive_group()
	#group.add_argument('-f', '--file', action="append", dest="files)



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
	parser_tmp2.add_argument('-u', '--uuid', action="store", dest="uuid", required=True).completer = DefaultCompleter(config)
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

####################################################################################
### Adding config parsers
####################################################################################

add_document_parser(subparsers, "documents", "Documents management")
add_threads_parser(subparsers, "threads", "threads management")
add_share_parser(subparsers, "shares", "Created shares management")
add_received_share_parser(subparsers, "received_shares", "Received shares management")
add_received_share_parser(subparsers, "rshares", "Alias of received_share command")
add_config_parser(subparsers, "config",  "Config tools like autocomplete configuration or pref-file generation.")
add_users_parser(subparsers, "users",  "users")

parser_tmp = subparsers.add_parser('test', add_help=False)
parser_tmp.set_defaults(__func__=TestCommand())

####################################################################################
### MAIN
####################################################################################

if __name__ == "__main__" :
	# integration with argcomplete python module (bash completion)
	try:
		import argcomplete
		argcomplete.autocomplete(parser)
	except ImportError as e :
		pass

	# parse cli arguments
	args = parser.parse_args()
	# reloading configuration with optional arguments
	config.reload(args)
	# using values stored in config file to filled in undefined args.
	# undefind args will be filled in with default values stored into the pref file.
	config.push(args)

	if getattr(args, 'debug'):
		log.setLevel(logging.DEBUG)
		streamHandler.setFormatter(myDebugFormat)
		print config
		print "----------- processing ----------------"

		# run command
		args.__func__(args)
	else:
		try:
			# run command
			args.__func__(args)
		except ValueError as a :
			log.error("ValueError : " + str(a))
			sys.exit(1)
		except KeyboardInterrupt as a :
			log.warn("Keyboard interruption detected.")
			sys.exit(1)
		except Exception as a :
			log.error("unexcepted error : " + str(a))
			sys.exit(1)
# urllib2.HTTPError: HTTP Error 401: basic auth failed
sys.exit(0)
