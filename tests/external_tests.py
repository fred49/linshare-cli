#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


from tests.misc import AdminGenericTestList
import unittest
import logging

LOG = logging.getLogger('core')
LOG.info("loading tests")

VERSIONS = [0, 1]


def load_tests(loader, version, clazz, key, value):
    """TODO"""
    suit = unittest.TestSuite()
    for i in loader.loadTestsFromTestCase(clazz):
        i.api_version = version
        i.set_command_to_test(key, value)
        suit.addTest(i)
    return suit


def get_all_tests():
    """TODO"""
    loader = unittest.TestLoader()
    suites = unittest.TestSuite()
    commands = {
        'threads': {
            'delete': False
            },
        'tmembers': {
            'skip': True
            },
        'users': {
            'skip': True
            },
        'iusers': {},
        'domains': {
            'delete': False
            },
        'ldap': {
            'delete': False
            },
        'dpatterns': {
            'delete': False
            },
        'funcs': {
            'delete': False
            },
        'domainpolicy': {
            'delete': False
            },
    }
    for key, val in commands.items():
        if val.get('skip'):
            continue
        suites.addTest(load_tests(loader, 0, AdminGenericTestList, key, val))
    return suites

if __name__ == '__main__':
    suite = get_all_tests()
    unittest.TextTestRunner(verbosity=2).run(suite)
