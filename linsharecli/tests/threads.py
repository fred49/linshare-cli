#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

# -----------------------------------------------------------------------------
# Imports

import logging
from mock import patch
from mock import Mock
from copy import deepcopy
from linsharecli.tests.core import MockServerResults
from linsharecli.tests.core import LinShareTestCase

from linsharecli.user.thread import add_parser as add_threads_parser

LOG = logging.getLogger("threads")


DATA_THREADS = [
  {
    "creationDate": 1466718451738,
    "domain": "MySubDomain",
    "modificationDate": 1466718451741,
    "name": "thread1",
    "uuid": "d23a1449-f7ce-4c85-b48f-eb2dec157c87"
  },
  {
    "creationDate": 1466718453993,
    "domain": "MySubDomain",
    "modificationDate": 1466718453997,
    "name": "thread2",
    "uuid": "39c72829-5d15-4eca-b62a-9d409d5021cf"
  },
  {
    "creationDate": 1466718456795,
    "domain": "MySubDomain",
    "modificationDate": 1466718456797,
    "name": "thread3",
    "uuid": "ed5d85a6-cdc9-42b9-b697-c11ab658cc01"
  }
]


# -----------------------------------------------------------------------------
@patch('linshareapi.core.CoreCli.auth', return_value=True)
@patch('linshareapi.user.threads.Threads.list',
       new_callable=MockServerResults(DATA_THREADS))
class TestThreadsList(LinShareTestCase):

    ##########################
    # * header : 3 lines
    # * content : 3 threads
    # * footer : 3 lines
    DATA_DOCUMENTS_HEIGHT = 9
    DATA_DOCUMENTS_WIDTH = 109

    def setUp(self):
        super(TestThreadsList, self).setUp()
        add_threads_parser(self.subparsers, "threads", "threads management",
                           self.config)

    def test_threads_list(self, *args):
        """retrieve default threads list"""
        command = "threads list"
        output = self.run_default0(command)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[0]), self.DATA_DOCUMENTS_WIDTH)
