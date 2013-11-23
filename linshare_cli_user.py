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
# Copyright 2013 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

import os , re , sys
import argparse
import logging
import logging.handlers

from linshare_cli.user import DefaultCommand
from fmatoolbox import Base64DataHook , Config , Element , Section , myDebugFormat , streamHandler , DefaultCompleter
from linshare_cli.user import add_document_parser , add_share_parser , add_received_share_parser , add_threads_parser , add_users_parser , add_config_parser

# ---------------------------------------------------------------------------------------------------------------------
class TestCommand(DefaultCommand):

	def __call__(self, args):
		super(TestCommand, self).__call__(args)
		self.verbose = args.verbose
		self.debug = args.debug

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

# ---------------------------------------------------------------------------------------------------------------------
config = Config("linshare-cli-user" , desc="""An user cli for LinShare, using its REST API.""")
section_server = config.add_section(Section("server"))
section_server.add_element(Element('host', default = 'http://localhost:8080/linshare'))
section_server.add_element(Element('realm', desc=argparse.SUPPRESS))
section_server.add_element(Element('user'))
section_server.add_element(Element('password', hidden = True, desc = "user password to linshare" , hooks = [ Base64DataHook(),] ))
section_server.add_element(Element('application_name' , desc="Default value is 'linshare' (extracted from http:/x.x.x.x/linshare)"))
section_server.add_element(Element('nocache' , e_type=bool, default=False , desc=argparse.SUPPRESS))
section_server.add_element(Element('verbose'))
section_server.add_element(Element('debug' , e_type=int, default=0 , desc="""(default: 0)
# 0 : debug off
# 1 : debug on
# 2 : debug on and request result is printed (pretty json)
# 3 : debug on and urllib debug on and http headers and request are printed
"""))

config.load()



####################################################################################
# create the top-level parser
parser = config.get_parser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-d',			action="count",		**config.server.debug.get_arg_parse_arguments())
parser.add_argument('-v', '--verbose',		action="store_true", default=False)
parser.add_argument('-s', dest='server_section', action="store", help="This option let you select the server section in the ini file you want to load (server section is always load first as default configuration). You just need to specify a number like '4' for section 'server-4'.")
parser.add_argument('-p', 			action="store_true", default=False, dest="ask_password", help="If set, the program will ask you your password.")


# reloading configuration with optional arguments
args , argv = parser.parse_known_args()
# if section_server is defined, we need no modify the suffix attribute of server Section object. 
# And then reload the configuration.
if args.server_section :
	config.server.suffix = args.server_section
config.reload(args)

parser.add_argument('-u', '--user',		action="store",		**config.server.user.get_arg_parse_arguments())
parser.add_argument('-P', '--password',		action="store",		**config.server.password.get_arg_parse_arguments())
parser.add_argument('-H', '--host',		action="store",		**config.server.host.get_arg_parse_arguments())
parser.add_argument('-r', '--realm',		action="store",		**config.server.realm.get_arg_parse_arguments())
parser.add_argument('--nocache',		action="store_true",	**config.server.nocache.get_arg_parse_arguments())
parser.add_argument('-a', '--appname',		action="store",		**config.server.application_name.get_arg_parse_arguments())

####################################################################################
subparsers = parser.add_subparsers()

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

	if getattr(args, 'debug'):
		log.setLevel(logging.DEBUG)
		streamHandler.setFormatter(myDebugFormat)
		print "------------- config ------------------"
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
sys.exit(0)
