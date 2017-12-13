#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""
TODO
"""


import json
import logging
import urllib2

from mock import patch
# from mock import Mock
from copy import deepcopy
import pkg_resources
from linsharecli.tests.core import MockServerResults
from linsharecli.tests.core import LinShareTestCase

from linsharecli.user.document import add_parser as add_document_parser
from linsharecli.user.share import add_parser as add_share_parser
from linsharecli.user.rshare import add_parser as add_received_share_parser
from linsharecli.user.thread import add_parser as add_threads_parser
from linsharecli.user.user import add_parser as add_users_parser

LOG = logging.getLogger("documents")


def load_data(file_name):
    """read file, parse content and return json object."""
    template = pkg_resources.resource_stream(__name__, file_name)
    return json.load(template)


@patch('linshareapi.core.CoreCli.auth', return_value=True)
@patch('linshareapi.user.documents.Documents.list',
       new_callable=MockServerResults(load_data('documents.list.json')))
# pylint: disable=unused-argument
class TestDocumentsList(LinShareTestCase):
    """TODO"""

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
        self.assertRegexpMatches(output[-4], r"^\| file5.*")

    def test_documents_list3(self, *args):
        """retrieve documents list reversed sorted by name"""
        command = "documents list -r --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)
        self.assertRegexpMatches(output[-4], r"^\| file0.*")

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
        first_line = output[0]
        # tests data are now store in a file.
        first_line = first_line.strip('\n')
        self.assertEqual(len(first_line), 58)
        # time shift ?
        # self.assertRegexpMatches(output[-3], ".*2015-02-14 19:41:49$")
        self.assertRegexpMatches(output[-3], ".*2015-02-14 18:41:49$")
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
        """
        retrieve documents list and try to download them (all should failed)
        """

        first_line = 3
        last_line = -4
        # start
        command = "documents list --start 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 10)
        self.assertRegexpMatches(output[first_line], r"^\| file4.*")
        self.assertRegexpMatches(output[last_line], r"^\| file3.*")
        # start and sort by name
        command = "documents list --start 2 --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), 10)
        self.assertRegexpMatches(output[first_line], r"^\| file2.*")
        self.assertRegexpMatches(output[last_line], r"^\| file5.*")

        # end
        command = "documents list --end 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[first_line], r"^\| file2.*")
        self.assertRegexpMatches(output[last_line], r"^\| file3.*")
        # end and sort by name
        command = "documents list --end 2 --sort-name"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[first_line], r"^\| file4.*")
        self.assertRegexpMatches(output[last_line], r"^\| file5.*")

        # limit and start
        command = "documents list --start 2 --limit 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[first_line], r"^\| file4.*")
        self.assertRegexpMatches(output[last_line], r"^\| file1.*")
        # limit and  end
        command = "documents list --end 3 --limit 2"
        output = self.run_default0(command)
        self.assertEqual(len(output), 8)
        self.assertRegexpMatches(output[first_line], r"^\| file1.*")
        self.assertRegexpMatches(output[last_line], r"^\| file2.*")

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
           new_callable=MockServerResults(load_data('documents.create.json')))
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
