#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


from linsharecli.tests.documents import TestDocumentsList
from linsharecli.tests.threads import TestThreadsList
import unittest
import logging

LOG = logging.getLogger('core')
LOG.info("loading tests")

VERSIONS = [0, 1]


def load_tests(loader, version, clazz):
    """TODO"""
    suit = unittest.TestSuite()
    for i in loader.loadTestsFromTestCase(clazz):
        i.api_version = version
        suit.addTest(i)
    return suit

def get_all_tests():
    """TODO"""
    loader = unittest.TestLoader()
    suites = unittest.TestSuite()
    for version in VERSIONS:
        suites.addTest(load_tests(loader, version, TestDocumentsList))
        suites.addTest(load_tests(loader, version, TestThreadsList))
    return suites

if __name__ == '__main__':
    suite = get_all_tests()
    unittest.TextTestRunner(verbosity=2).run(suite)
