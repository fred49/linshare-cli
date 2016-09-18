#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

# -----------------------------------------------------------------------------
# Imports

import logging
import urllib2
from mock import patch
from mock import Mock
from copy import deepcopy
from linsharecli.tests.core import MockServerResults
from linsharecli.tests.core import LinShareTestCase

from linsharecli.user.document import add_parser as add_document_parser
from linsharecli.user.share import add_parser as add_share_parser
from linsharecli.user.rshare import add_parser as add_received_share_parser
from linsharecli.user.thread import add_parser as add_threads_parser
from linsharecli.user.user import add_parser as add_users_parser

LOG = logging.getLogger("documents")

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

DATA_CREATED_SHARE = [
      {
              "ciphered": None,
              "creationDate": 1440945179751,
              "description": None,
              "document": {
                "ciphered": False,
                "creationDate": 1413644784988,
                "description": "",
                "expirationDate": None,
                "metaData": None,
                "modificationDate": 1440945181335,
                "name": "fortest_499",
                "sha256sum": None,
                "size": 898,
                "type": "text/plain",
                "uuid": "09159704-c17b-46ef-ae26-6f9cce4e9d9a"
              },
              "downloaded": None,
              "expirationDate": 1448893979725,
              "message": None,
              "modificationDate": 1440945179751,
              "name": "fortest_499",
              "recipient": {
                        "domain": "topdomain",
                        "firstName": "Bart",
                        "lastName": "Simpson",
                        "mail": "bart.simpson@nodomain.com",
                        "uuid": "27573c44-f896-42e7-ba0d-7bec7ba67568"
                      },
              "sender": None,
              "size": None,
              "type": None,
              "uuid": "9487e4f3-978e-4496-8bb6-1e7b283df0cc"
            }
]


# -----------------------------------------------------------------------------
@patch('linshareapi.core.CoreCli.auth', return_value=True)
@patch('linshareapi.user.documents.Documents.list',
       new_callable=MockServerResults(DATA_DOCUMENTS))
class TestDocumentsList(LinShareTestCase):

    ##########################
    # * header : 3 lines
    # * content : 6 documents
    # * footer : 3 line
    DATA_DOCUMENTS_HEIGHT = 12
    DATA_DOCUMENTS_WIDTH = 100

    def setUp(self):
        super(TestDocumentsList, self).setUp()
        add_document_parser(self.subparsers, "documents",
                            "Documents management",
                            self.config)
        add_threads_parser(self.subparsers, "threads", "threads management",
                           self.config)
        add_share_parser(self.subparsers, "shares",
                         "Created shares management",
                         self.config)
        add_received_share_parser(self.subparsers,
                                  "received_shares",
                                  "Received shares management", self.config)
        add_received_share_parser(self.subparsers,
                                  "rshares",
                                  "Alias of received_share command",
                                  self.config)
        add_users_parser(self.subparsers, "users", "users", self.config)

    def test_documents_list(self, *args):
        """retrieve default documents list"""
        command = "documents list"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)

    def test_documents_list2(self, *args):
        """retrieve documents list sorted by name"""
        command = "documents list --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)
        self.assertRegexpMatches(output[-4], "^\| file5.*")

    def test_documents_list3(self, *args):
        """retrieve documents list reversed sorted by name"""
        command = "documents list -r --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)
        self.assertRegexpMatches(output[-4], "^\| file0.*")

    def test_documents_list4(self, *args):
        """retrieve documents list with csv output"""
        command = "documents list --csv"
        output = self.run_default0(command)
        # documents + header + footer = 6 + 0 + 2
        self.assertEqual(len(output), 9)
        self.assertEqual(len(output[0]), 45)
        self.assertEqual(len(output[1]), 86)
        # first file
        self.assertRegexpMatches(output[1], "file5.*")
        self.assertRegexpMatches(output[-5], "file1.*")

    def test_documents_list4b(self, *args):
        """retrieve documents list with csv output and no headers"""
        command = "documents list --csv --no-headers"
        output = self.run_default0(command)
        # documents + header + footer = 6 + 0 + 2
        self.assertEqual(len(output), 8)
        self.assertEqual(len(output[0]), 86)
        self.assertRegexpMatches(output[-3], "file3.*")

    def test_documents_list4c(self, *args):
        """retrieve documents list with csv output and no headers"""
        command = "documents list --raw"
        output = self.run_default0(command)
        # documents + header + footer = 6 + 3 + 3
        self.assertEqual(len(output), 12)
        self.assertEqual(len(output[0]), 94)
        self.assertRegexpMatches(output[-4], "file3.*")
        self.assertRegexpMatches(output[-5], "2097152.*1423939308912.*")

    def test_documents_list5(self, *args):
        """retrieve documents with vertical list"""
        command = "documents list -t"
        output = self.run_default0(command)
        # 38 lines
        self.assertEqual(len(output), 38)
        # 58 characters for the first line
        self.assertEqual(len(output[0]), 58)
        self.assertRegexpMatches(output[-3], ".*2015-02-14 19:41:49$")
        self.assertRegexpMatches(output[-8], ".*RECORD 6.*")

    def test_documents_list6(self, *args):
        """retrieve documents list with extened mode"""
        command = "documents list --extended"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), 251)

    def test_documents_list7(self, *args):
        """retrieve documents list and count them"""
        command = "documents list --count"
        output = self.run_default0(command)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], "Documents found : 6\n")

    @patch('linshareapi.user.documents.Documents.download',
           return_value=('ffffffff', 18))
    def test_documents_list8(self, *args):
        """retrieve documents list and download them"""
        command = "documents list --download "
        output = self.run_default0(command)
        self.assertEqual(len(output), 7)

    @patch('linshareapi.user.documents.Documents.download',
           side_effect=urllib2.HTTPError(404, 'Boom!', None, None, None))
    def test_documents_list9(self, *args):
        """retrieve documents list and try to download them (all failed)"""
        command = "documents list --download "
        output = self.run_default0(command)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], "6 documents can not be downloaded.\n")

    @patch('linshareapi.user.documents.Documents.delete', return_value=deepcopy(
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
           }))
    def test_documents_list10(self, *args):
        """retrieve documents list and try to delete them"""
        command = "documents list --delete"
        output = self.run_default0(command)
        self.assertEqual(len(output), 7)

    @patch('linshareapi.user.documents.Documents.delete',
           side_effect=urllib2.HTTPError(404, 'Boom!', None, None, None))
    def test_documents_list11(self, *args):
        """retrieve documents list and try to download them (all failed)"""
        command = "documents list --delete "
        output = self.run_default0(command)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], "6 document(s) can not be deleted.\n")

    def test_documents_list12(self, *args):
        """retrieve documents list and try to download them (all should failed)"""
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

    @patch('linshareapi.user.shares.Shares.share',
           return_value=(204, "coucou", 2))
    def test_documents_list13(self, *args):
        """retrieve documents list and download them"""
        command = "documents list file5 --share --mail bart.simpson@localhost"
        if self.api_version == 1:
            return True

        # self.assertRaises(ValueError, self.run_default0(command))
        try:
            self.run_default0(command)
            self.assertTrue(False)
        except ValueError:
            self.assertTrue(True)

    @patch('linshareapi.user.shares.Shares2.create',
           new_callable=MockServerResults(DATA_CREATED_SHARE))
    def test_documents_list13b(self, *args):
        """retrieve documents list and share them"""
        command = "documents list file5 --share --mail bart.simpson@localhost"
        if self.api_version == 0:
            return True

        output = self.run_default0(command)
        self.assertRegexpMatches("".join(output), ".*Bart Simpson.*")
        self.assertRegexpMatches("".join(output),
                                 ".*The following documents :.*")
        if self.debug >= 2:
            self.assertEqual(len(output), 45)
        else:
            self.assertEqual(len(output), 9)
