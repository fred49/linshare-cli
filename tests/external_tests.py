#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


from linsharecli.tests.misc import AdminGenericTestList
import unittest
import logging

LOG = logging.getLogger('core')
LOG.info("loading tests")

VERSIONS = [0, 1]


def load_tests(loader, commands, version):
    """Create all tests"""
    suites = unittest.TestSuite()
    for key, val in commands.items():
        if val.get('skip'):
            continue
        suites.addTest(load_tests_by_version(loader, version,
                                             AdminGenericTestList, key, val))
    return suites

def load_tests_by_version(loader, version, clazz, key, value):
    """Create all tests"""
    suit = unittest.TestSuite()
    for i in loader.loadTestsFromTestCase(clazz):
        i.api_version = version
        i.set_command_to_test(key, value)
        suit.addTest(i)
    return suit


def get_all_tests():
    """Build all tests"""
    loader = unittest.TestLoader()
    suites = unittest.TestSuite()

    # version 0
    keyerror = False
    keyerror_extended = False
    commands = {
        'threads': {
            'delete': False,
            'fields': False,
            },
        'tmembers': {
            'skip': True,
            },
        'users': {
            'skip': True,
            },
        'iusers': {},
        'domains': {
            'delete': False,
            'keyerror' : keyerror,
            'keyerror_extended' : keyerror_extended,
            },
        'ldap': {
            'delete': False,
            'keyerror' : keyerror,
            'keyerror_extended' : keyerror_extended,
            },
        'dpatterns': {
            'delete': False,
            'keyerror' : keyerror,
            'keyerror_extended' : keyerror_extended,
            },
        'funcs': {
            'delete': False,
            },
        'domainpolicy': {
            'delete': False,
            },
    }
    suites.addTest(load_tests(loader, commands, 0))

    # version 1
    keyerror = True
    keyerror_extended = True
    commands = {
        'threads': {
            'delete': False,
            'fields': False,
            },
        'tmembers': {
            'skip': True,
            },
        'users': {
            'skip': True,
            },
        'iusers': {},
        'domains': {
            'delete': False,
            'keyerror' : keyerror,
            'keyerror_extended' : keyerror_extended,
            },
        'ldap': {
            'delete': False,
            'keyerror' : keyerror,
            'keyerror_extended' : keyerror_extended,
            },
        'dpatterns': {
            'delete': False,
            'keyerror' : keyerror,
            'keyerror_extended' : keyerror_extended,
            },
        'funcs': {
            'delete': False,
            },
        'domainpolicy': {
            'delete': False,
            },
    }
    suites.addTest(load_tests(loader, commands, 1))
    return suites

if __name__ == '__main__':
    suite = get_all_tests()
    unittest.TextTestRunner(verbosity=2).run(suite)
