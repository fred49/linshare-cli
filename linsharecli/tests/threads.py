#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""TODO"""

import logging
from mock import patch

from linsharecli.tests.core import load_data
from linsharecli.tests.core import MockServerResults
from linsharecli.tests.core import LinShareTestCase

from linsharecli.user.workgroups import add_parser as add_threads_parser

LOG = logging.getLogger("threads")


@patch('linshareapi.core.CoreCli.auth', return_value=True)
@patch('linshareapi.user.threads.Threads.list',
       new_callable=MockServerResults(load_data('threads.list.json')))
class TestThreadsList(LinShareTestCase):
    """TODO"""

    ##########################
    # * header : 3 lines
    # * content : 3 threads
    # * footer : 3 lines
    DATA_DOCUMENTS_HEIGHT = 14
    DATA_DOCUMENTS_WIDTH = 95

    def setUp(self):
        super(TestThreadsList, self).setUp()
        add_threads_parser(self.subparsers, "threads", "threads management",
                           self.config)

    # pylint: disable=unused-argument
    def test_threads_list(self, *args):
        """retrieve default threads list"""
        command = "threads list"
        output = self.run_default0(command)
        LOG.error(output)
        self.assertEqual(len(output), self.DATA_DOCUMENTS_HEIGHT)
        self.assertEqual(len(output[3]), self.DATA_DOCUMENTS_WIDTH)
