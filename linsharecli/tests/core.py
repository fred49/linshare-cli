#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""TODO"""


import sys
import os
import json
import unittest
import argparse
import codecs
import logging
import uuid
import tempfile
from copy import deepcopy
import mock
import pkg_resources


# debug level superior or equal to three may have side effect
# during output parsing (stdout)
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


def load_data(file_name):
    """read file, parse content and return json object."""
    template = pkg_resources.resource_stream(__name__, file_name)
    return json.load(template)


# pylint: disable=too-few-public-methods
class MockServerResults(object):
    """TODO"""

    def __init__(self, data):
        self.data = data

    def __call__(self):
        # pylint: disable=unused-argument
        def get_data_copy(*args):
            """TODO"""
            return deepcopy(self.data)
        return get_data_copy


class LinShareTestCase(unittest.TestCase):
    """TODO"""

    api_version = int(os.getenv('_TEST_LINSHARE_CLI_USER_API_VERSION', 0))

    def shortDescription(self):
        """Override default method to suffix with current tested api_version"""
        doc = super(LinShareTestCase, self).shortDescription()
        if doc:
            doc = "{d} [api_version={v}]".format(d=doc, v=self.api_version)
        return doc

    def setUp(self):
        # debug level superior or equal to three may have side effect
        # during output parsing (stdout)
        self.debug = DEBUG_LEVEL
        LOG.debug("current api_version: %s", self.api_version)

        # mocking default config
        self.config = mock.Mock(name="config mock")
        # print "api_version used : ", self.api_version
        self.config.server.api_version.value = self.api_version
        self.parser = argparse.ArgumentParser(prog="test")
        self.subparsers = self.parser.add_subparsers()

    def get_default_ns(self):
        """Get pre-populated argparse namespace containing
        configuration and credentials for linshare."""
        namespace = argparse.Namespace()
        namespace.verbose = True
        # debug level superior or equal to three may have side effect
        # during output parsing (stdout)
        namespace.debug = self.debug
        namespace.ask_password = False
        namespace.password_from_env = False
        namespace.nocache = True
        namespace.base_url = None
        namespace.host = "http://192.168.1.106:8081"
        namespace.user = "homer.simpson@nodomain.com"
        namespace.password = "secret"
        namespace.auth_type = "plain"
        namespace.env_password = False
        return namespace

    def run_default0(self, command):
        """TODO"""
        if self.debug >= 2:
            return self.run_default_sub2(command)
        else:
            return self.run_default_sub1(command)

    def run_default1(self, command):
        """TODO"""
        stdout = codecs.open(os.devnull, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = stdout
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        args.__func__(args)

    def run_default2(self, command):
        """TODO"""
        stdout = codecs.open(os.devnull, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = stdout
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        try:
            return args.__func__(args)
        # pylint: disable=broad-except
        except Exception as ex:
            sys.stdout = sys.stdout2
            print(ex)
            return False


    # pylint: disable=no-self-use
    def get_temp_file(self):
        """TODO"""
        dest = os.path.join(
            tempfile.gettempdir(),
            str(uuid.uuid4()).replace("-", "") + ".tmp")
        return dest

    def run_default_sub1(self, command):
        """TODO"""
        file_path = self.get_temp_file()
        stdout = codecs.open(file_path, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = stdout
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        args.__func__(args)
        stdout.close()
        sys.stdout = sys.stdout2
        stdout = codecs.open(file_path, "r", "utf-8")
        output = stdout.readlines()
        stdout.close()
        if self.debug >= 2:
            LOG.debug("STDOUT:BEGIN")
            LOG.debug(output)
            LOG.debug("STDOUT:END")
        else:
            os.remove(file_path)
        return output

    def run_default_sub2(self, command):
        """TODO"""
        file_path = self.get_temp_file()
        stdout = codecs.open(file_path, "w", "utf-8")
        sys.stdout2 = sys.stdout
        sys.stdout = stdout
        args = self.parser.parse_args(
            command.split(),
            self.get_default_ns())
        try:
            args.__func__(args)
            stdout.close()
            sys.stdout = sys.stdout2
            stdout = codecs.open(file_path, "r", "utf-8")
            output = stdout.readlines()
            stdout.close()
            if self.debug >= 2:
                LOG.debug("STDOUT:BEGIN")
                for i in output:
                    LOG.debug(i.strip('\n'))
                LOG.debug("STDOUT:END")
            else:
                os.remove(file_path)
            return output
        except Exception as ex:
            print(ex)
            sys.stdout = sys.stdout2
            stdout.close()
            raise ex

    def debug_arg(self, args):
        """TODO"""
        for i in args.__dict__:
            print((i + " : " + str(getattr(args, i))))
