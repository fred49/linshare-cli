#! /usr/bin/env python
#! /home/fred/.virtualenvs/migration-linshare-cc/bin/python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from __future__ import unicode_literals

import sys
import os
import unittest
import argparse
import codecs
import logging
import re
import urllib2
from mock import patch
from copy import deepcopy

from linsharecli.user.document import add_parser as add_document_parser
from linsharecli.user.share import add_parser as add_share_parser
from linsharecli.user.rshare import add_parser as add_received_share_parser
from linsharecli.user.thread import add_parser as add_threads_parser
from linsharecli.user.user import add_parser as add_users_parser

DEBUG_LEVEL = int(os.getenv('_TEST_LINSHARE_CLI_USER_DEBUG', 0))
LOG = logging.getLogger()
LOG.setLevel(logging.FATAL)
if DEBUG_LEVEL > 0:
    LOG.setLevel(logging.DEBUG)
DEBUG_LOGGING_FORMAT = logging.Formatter(
    "%(levelname)-8s %(asctime)s %(name)s:%(funcName)s:%(message)s",
    "%H:%M:%S")
#STREAMHANDLER = logging.StreamHandler(sys.stdout)
STREAMHANDLER = logging.StreamHandler(sys.stderr)
STREAMHANDLER.setFormatter(DEBUG_LOGGING_FORMAT)
LOG.addHandler(STREAMHANDLER)

DATA_DOCUMENTS = [
{
    "ciphered": False,
    "creationDate": 1423939307964,
    "description": "",
    "expirationDate": 1431628907886,
    "metaData": None,
    "modificationDate": 1423939308129,
    "name": "file0",
    "sha256sum": "30e14955ebf1352266dc2ff867e6810467e750abb9d3b36582b8af909fcb58",
    "size": 1048576,
    "type": "application/octet-stream",
    "uuid": "bb6cc9c8-ca7c-4d59-a5eb-8cb700ee3810"
},
{
    "ciphered": False,
    "creationDate": 1423939308392,
    "description": "",
    "expirationDate": 1431628908366,
    "metaData": None,
    "modificationDate": 1423939308429,
    "name": "file1",
    "sha256sum": "30e14955ebf1352266dc2ff867e6810467e750abb9d3b36582b8af909fcb58",
    "size": 1048576,
    "type": "application/octet-stream",
    "uuid": "aa1c3d54-5f84-4b6d-8c84-62f5b230135e"
  },
  {
    "ciphered": False,
    "creationDate": 1423939308880,
    "description": "",
    "expirationDate": 1431628908779,
    "metaData": None,
    "modificationDate": 1423939308912,
    "name": "file2",
    "sha256sum": "5647f05ec18958947d32874eeb788fa396a05dbab7c1b71f112ceb7e9b31eee",
    "size": 2097152,
    "type": "application/octet-stream",
    "uuid": "fe2ee707-3c02-45a9-ae08-d88c47fb9aef"
  },
  {
    "ciphered": False,
    "creationDate": 1423939309188,
    "description": "",
    "expirationDate": 1431628909147,
    "metaData": None,
    "modificationDate": 1423939309267,
    "name": "file3",
    "sha256sum": "30e14955ebf1352266dc2ff867e6810467e750abb9d3b36582b8af909fcb58",
    "size": 1048576,
    "type": "application/octet-stream",
    "uuid": "47cadd7a-4548-467a-8079-42b9681671e3"
  },
  {
    "ciphered": False,
    "creationDate": 1423939307567,
    "description": "",
    "expirationDate": None,
    "metaData": None,
    "modificationDate": 1423944517141,
    "name": "file4",
    "sha256sum": "30e14955ebf1352266dc2ff867e6810467e750abb9d3b36582b8af909fcb58",
    "size": 1048576,
    "type": "application/octet-stream",
    "uuid": "b2ab14b0-2070-4a50-b51b-0bbe61861d3e"
  },
  {
    "ciphered": False,
    "creationDate": 1423939305959,
    "description": "",
    "expirationDate": None,
    "metaData": None,
    "modificationDate": 1423958403408,
    "name": "file5",
    "sha256sum": "30e14955ebf1352266dc2ff867e6810467e750abb9d3b36582b8af909fcb58",
    "size": 1048576,
    "type": "application/octet-stream",
    "uuid": "26b3adbb-6e59-48fc-bd73-c84c01afb5de"
  }
]

def get_document_data():
    return deepcopy(DATA_DOCUMENTS)

# -----------------------------------------------------------------------------
class LinShareTest(unittest.TestCase):

    def setUp(self):
        # debug level superior or equal to three may have side effect
        # during output parsing (stdout)
        self.debug = DEBUG_LEVEL

        self.parser = argparse.ArgumentParser(prog="test")

        # Adding all others parsers.
        subparsers = self.parser.add_subparsers()
        add_document_parser(subparsers, "documents", "Documents management")
        add_threads_parser(subparsers, "threads", "threads management")
        add_share_parser(subparsers, "shares", "Created shares management")
        add_received_share_parser(subparsers,
                                  "received_shares",
                                  "Received shares management")
        add_received_share_parser(subparsers,
                                  "rshares",
                                  "Alias of received_share command")
        add_users_parser(subparsers, "users", "users")

    def get_default_ns(self):
        ns = argparse.Namespace()
        ns.verbose = True
        # debug level superior or equal to three may have side effect
        # during output parsing (stdout)
        ns.debug = self.debug
        ns.ask_password = False
        ns.nocache = True
        ns.base_url = None
        ns.host = "http://192.168.1.106:8081"
        ns.user = "homer.simpson@nodomain.com"
        ns.password = "secret"
        return ns

    def run_default0(self, command):
        if self.debug >= 2:
            return self.run_default_sub2(command)
        else:
            return self.run_default_sub1(command)

    def run_default1(self, command):
        f = codecs.open(os.devnull, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = f
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        args.__func__(args)

    def run_default2(self, command):
        f = codecs.open(os.devnull, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = f
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        try:
            return args.__func__(args)
        except Exception as ex:
            sys.stdout = sys.stdout2
            #log.error(ex)
            print ex
            return False

    def run_default_sub1(self, command):
        file_path = '/tmp/toto'
        f = codecs.open(file_path, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = f
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        args.__func__(args)
        f.close()
        sys.stdout = sys.stdout2
        f = codecs.open(file_path, "r", "utf-8")
        output = f.readlines()
        f.close()
        if self.debug >= 2:
            LOG.debug("STDOUT:BEGIN")
            LOG.debug(output)
            LOG.debug("STDOUT:END")
        else:
            os.remove(file_path)
        return output

    def run_default_sub2(self, command):
        file_path = '/tmp/toto'
        f = codecs.open(file_path, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = f
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        try:
            args.__func__(args)
            f.close()
            sys.stdout = sys.stdout2
            f = codecs.open(file_path, "r", "utf-8")
            output = f.readlines()
            f.close()
            if self.debug >= 2:
                LOG.debug("STDOUT:BEGIN")
                for i in output:
                    LOG.debug(i.strip('\n'))
                LOG.debug("STDOUT:END")
            else:
                os.remove(file_path)
            return output
        except Exception as ex:
            print ex
            sys.stdout = sys.stdout2
            f.close()
            raise ex
        #finally:

    def debug_arg(self, args):
        for i in args.__dict__:
            print i + " : " + str(getattr(args, i))


# -----------------------------------------------------------------------------
class TestDocumentsList(LinShareTest):

    ##########################
    # * header : 3 lines
    # * content : 6 documents
    # * footer : 3 line
    DATA_DOCUMENTS_HEIGHT = 12
    DATA_DOCUMENTS_WIDTH = 100

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list(self, *args):
        """retrieve default documents list"""
        command = "documents list"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list2(self, *args):
        """retrieve documents list sorted by name"""
        command = "documents list --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)
        self.assertRegexpMatches(output[-4], "^\| file5.*")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list3(self, *args):
        """retrieve documents list reversed sorted by name"""
        command = "documents list -r --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)
        self.assertRegexpMatches(output[-4], "^\| file0.*")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list4(self, *args):
        """retrieve documents list with csv output"""
        command = "documents list --csv"
        output = self.run_default0(command)
        # documents + header + footer = 6 + 0 + 2
        self.assertEqual(len(output), 9)
        self.assertEqual(len(output[0]), 45)
        self.assertEqual(len(output[1]), 86)
        self.assertRegexpMatches(output[1], "file0.*")
        self.assertRegexpMatches(output[-5], "file3.*")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list4b(self, *args):
        """retrieve documents list with csv output and no headers"""
        command = "documents list --csv --no-headers"
        output = self.run_default0(command)
        # documents + header + footer = 6 + 0 + 2
        self.assertEqual(len(output), 8)
        self.assertEqual(len(output[0]), 86)
        self.assertRegexpMatches(output[-3], "file5.*")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list4c(self, *args):
        """retrieve documents list with csv output and no headers"""
        command = "documents list --raw"
        output = self.run_default0(command)
        # documents + header + footer = 6 + 3 + 3
        self.assertEqual(len(output), 12)
        self.assertEqual(len(output[0]), 94)
        self.assertRegexpMatches(output[-4], "file3.*")
        self.assertRegexpMatches(output[-5], "2097152.*1423939308912.*")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list5(self, *args):
        """retrieve documents with vertical list"""
        command = "documents list -t"
        output = self.run_default0(command)
        self.assertEqual(len(output), 38)
        self.assertEqual(len(output[0]), 59)
        self.assertRegexpMatches(output[-3], ".*2015-02-14 19:41:49$")
        self.assertRegexpMatches(output[-8], ".*RECORD 6.*")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list6(self, *args):
        """retrieve documents list with extened mode"""
        command = "documents list --extended"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), 174)

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list7(self, *args):
        """retrieve documents list and count them"""
        command = "documents list --count"
        output = self.run_default0(command)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], "Documents found : 6\n")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    @patch('linshareapi.user.documents.Documents.download',
           return_value=('ffffffff', 18))
    def test_documents_list8(self, *args):
        """retrieve documents list and download them"""
        command = "documents list --download "
        output = self.run_default0(command)
        self.assertEqual(len(output), 7)

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    @patch('linshareapi.user.documents.Documents.download',
           side_effect=urllib2.HTTPError(404, 'Boom!', None, None, None))
    def test_documents_list9(self, *args):
        """retrieve documents list and try to download them (all failed)"""
        command = "documents list --download "
        output = self.run_default0(command)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], "6 documents can not be downloaded.\n")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.delete', return_value=
           {
             "ciphered": False,
             "creationDate": 1424735870159,
             "description": "",
             "expirationDate": 1432425468866,
             "metaData": None,
             "modificationDate": 1424735870385,
             "name": "aa",
             "sha256sum":
               "916e2eab1fbc18c548a1ac89eb157b7a44e313f8116958984eca2d99eaba6d",
             "size": 10140,
             "type": "text/plain",
             "uuid": "f62a1fad-0692-4ec8-8cde-68f1cc3f9b49"
           })
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list10(self, *args):
        """retrieve documents list and try to delete them"""
        command = "documents list --delete"
        output = self.run_default0(command)
        self.assertEqual(len(output), 7)

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    @patch('linshareapi.user.documents.Documents.delete',
           side_effect=urllib2.HTTPError(404, 'Boom!', None, None, None))
    def test_documents_list11(self, *args):
        """retrieve documents list and try to download them (all failed)"""
        command = "documents list --delete "
        output = self.run_default0(command)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], "6 document(s) can not be deleted.\n")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    def test_documents_list12(self, *args):
        """retrieve documents list and try to download them (all failed)"""
        FIRST_LINE = 3
        LAST_LINE = -4
        # start
        command = "documents list --start 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 10)
        self.assertRegexpMatches(output[FIRST_LINE], "^\| file4.*")
        self.assertRegexpMatches(output[LAST_LINE], "^\| file3.*")
        # start and sort by name
        command = "documents list --start 2 --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), 10)
        self.assertRegexpMatches(output[FIRST_LINE], "^\| file2.*")
        self.assertRegexpMatches(output[LAST_LINE], "^\| file5.*")

        # end
        command = "documents list --end 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[FIRST_LINE], "^\| file2.*")
        self.assertRegexpMatches(output[LAST_LINE], "^\| file3.*")
        # end and sort by name
        command = "documents list --end 2 --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[FIRST_LINE], "^\| file4.*")
        self.assertRegexpMatches(output[LAST_LINE], "^\| file5.*")

        # limit and start
        command = "documents list --start 2 --limit 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[FIRST_LINE], "^\| file4.*")
        self.assertRegexpMatches(output[LAST_LINE], "^\| file1.*")
        # limit and  end
        command = "documents list --end 3 --limit 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[FIRST_LINE], "^\| file1.*")
        self.assertRegexpMatches(output[LAST_LINE], "^\| file2.*")

    @patch('linshareapi.core.CoreCli.auth', return_value=True)
    @patch('linshareapi.user.documents.Documents.list',
           return_value=get_document_data())
    @patch('linshareapi.user.shares.Shares.share',
           return_value=(204, "coucou", 2))
    def test_documents_list13(self, *args):
        """retrieve documents list and download them"""
        command = "documents list file5 --share --mail bart.simpson@localhost"
        output = self.run_default0(command)
        self.assertEqual(len(output), 2)
        self.assertRegexpMatches(output[0], ".*26b3adbb-6e59-48fc-bd73-c84c01afb5de.*bart.simpson.*")

    #def test_threads_list(self):
    #    self.assertTrue(self.run_default("threads list"))

    #def test_users_list(self):
    #    self.assertTrue(self.run_default("users list"))


if __name__ == '__main__':
    unittest.main()
#
