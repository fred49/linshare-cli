#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


from tests.documents import TestDocumentsList
from tests.threads import TestThreadsList
import unittest
import logging

LOG = logging.getLogger('core')
LOG.info("loading tests")


def get_all_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for version in [0, 1]:
        for i in loader.loadTestsFromTestCase(TestDocumentsList):
            i.api_version = version
            suite.addTest(i)
        for i in loader.loadTestsFromTestCase(TestThreadsList):
            i.api_version = version
            suite.addTest(i)
    return suite

if __name__ == '__main__':
    suite = get_all_tests()
    unittest.TextTestRunner(verbosity=2).run(suite)
