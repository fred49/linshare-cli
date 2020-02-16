#! /usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""TODO"""

import re
import logging
import unittest
from linsharecli.tests.core import LinShareTestCase

from linsharecli.admin import PARSERS

LOG = logging.getLogger("external_tests")


# pylint: disable=too-few-public-methods
class SkipIfDisable(object):
    """Decorator to disable unsupported tests"""

    def __init__(self, attr):
        self.attr = attr

    def __call__(self, original_func):
        def wrapper(*args, **kwargs):
            """Decorator method"""
            test_case = args[0]
            # raise unittest.SkipTest("[deactivated]")
            if not test_case.check_if_enable(self.attr):
                test_case.skipTest("[deactivated]")
            return original_func(*args, **kwargs)
        wrapper.__doc__ = original_func.__doc__
        return wrapper


# pylint: disable=unused-variable
# pylint: disable=too-many-public-methods
class AdminGenericTestList(LinShareTestCase):
    """test list sub comand for all admin commands"""

    command_to_test = None
    host = "http://127.0.0.1:8080"
    user = "root@localhost.localdomain"
    password = "adminlinshare"

    def setUp(self):
        super(AdminGenericTestList, self).setUp()
        for parser in PARSERS:
            name = parser.get('name')
            description = parser.get('description')
            func = parser.get('parsers')
            func(self.subparsers, name, description, self.config)

        if self.test_config['skip']:
            self.skipTest("[deactivated]")

    def shortDescription(self):
        """Override default method to suffix with current tested api_version"""
        doc = super(AdminGenericTestList, self).shortDescription()
        if doc:
            doc = "[{c}] {d}".format(d=doc, c=self.command_to_test)
        return doc

    def get_default_ns(self):
        """Get pre-populated argparse namespace containing
        configuration and credentials for linshare."""
        namespace = super(AdminGenericTestList, self).get_default_ns()
        namespace.host = self.host
        namespace.user = self.user
        namespace.password = self.password
        return namespace

    def set_command_to_test(self, command, config):
        """Define which command to test and testing options."""
        self.command_to_test = command
        # pylint: disable=attribute-defined-outside-init
        self.test_config = config
        if "skip" not in self.test_config:
            self.test_config['skip'] = False

    def check_if_enable(self, kind):
        """check if a test 'kind' is enable"""
        LOG.debug("kind: %s", kind)
        LOG.debug("test_config: %s", self.test_config)
        if self.test_config['skip']:
            return False
        if kind in self.test_config:
            return self.test_config.get(kind)
        else:
            LOG.debug('kind is not in config.')
        return True

    def logSystemExit(self, ex):
        LOG.error("SystemExit code: %s", ex.code)
        raise AssertionError("unexpected failure ! Unsupportted command ?")

    def test_list(self):
        """Generic tests for sub command 'list'"""
        self.assertIsNotNone(self.command_to_test, "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list")
        try:
            self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    @SkipIfDisable('keyerror')
    def test_list_key_error(self):
        """Generic tests for sub command 'list' searching for KeyError"""
        self.assertIsNotNone(self.command_to_test, "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list")
        try:
            output = self.run_default0(command)
            regex = re.compile("WARN: KeyError", re.IGNORECASE)
            for i in output:
                self.assertFalse(regex.match(i), "OUTPUT: " + i)
        except SystemExit as ex:
            self.logSystemExit(ex)

    @SkipIfDisable('keyerror_extended')
    def test_list_key_error_extended(self):
        """Generic tests for sub command 'list --extended'
        searching for KeyError"""
        self.assertIsNotNone(self.command_to_test, "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --extended")
        try:
            output = self.run_default0(command)
            regex = re.compile("WARN: KeyError", re.IGNORECASE)
            for i in output:
                self.assertFalse(regex.match(i), "OUTPUT: " + i)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_extended(self):
        """Generic tests for sub command 'list --extended'"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --extended")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_vertical(self):
        """Generic tests for sub command 'list --vertical'"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --vertical")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_vertical_extended(self):
        """Generic tests for sub command 'list --extended --vertical'"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test,
                                   s="list --vertical --extended")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_limit(self):
        """Generic tests for sub command 'list --limit 10'"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --limit 10")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_start(self):
        """Generic tests for sub command 'list --start 0'"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --start 0")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_end(self):
        """Generic tests for sub command 'list --end 0'"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --end 0")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_reverse(self):
        """Generic tests for sub command 'list --reverse '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --reverse ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_json(self):
        """Generic tests for sub command 'list --json '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --json ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_csv_no_headers(self):
        """Generic tests for sub command 'list --csv --no-headers '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test,
                                   s="list --csv --no-headers ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_csv(self):
        """Generic tests for sub command 'list --csv '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --csv ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_raw(self):
        """Generic tests for sub command 'list --raw '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --raw ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_json_raw_json(self):
        """Generic tests for sub command 'list --json --raw-json '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test,
                                   s="list --json --raw-json ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    def test_list_count(self):
        """Generic tests for sub command 'list --count '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --count ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    @SkipIfDisable('delete')
    def test_list_delete(self):
        """Generic tests for sub command 'list --delete '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list --delete ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)

    @SkipIfDisable('fields')
    def test_list_fields(self):
        """Generic tests for sub command 'list -k uuid '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list -k uuid ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)
    @SkipIfDisable('fields_i')
    def test_list_fields_identifier(self):
        """Generic tests for sub command 'list -k identifier '"""
        self.assertNotEqual(self.command_to_test, "", "Missing command to test")
        command = "{c} {s}".format(c=self.command_to_test, s="list -k identifier ")
        try:
            output = self.run_default0(command)
        except SystemExit as ex:
            self.logSystemExit(ex)
