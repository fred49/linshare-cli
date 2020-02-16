#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""TODO"""


from linsharecli.tests.misc import AdminGenericTestList
import unittest
import logging
import json
from io import StringIO
from argtoolbox import DefaultCommand
from argtoolbox import BasicProgram
from argtoolbox import Element
from argtoolbox import query_yes_no

LOG = logging.getLogger('core')
LOG.info("loading tests")


class LaunchTestsCommand(DefaultCommand):
    """Launchtests command"""

    def load_tests_by_version(self, loader, version, clazz, key, value):
        """Create all tests"""
        suit = unittest.TestSuite()
        for i in loader.loadTestsFromTestCase(clazz):
            i.api_version = version
            i.set_command_to_test(key, value)
            suit.addTest(i)
        return suit

    def load_tests(self, loader, commands, version):
        """Create all tests"""
        suites = unittest.TestSuite()
        for key, val in list(commands.items()):
            if val.get('skip'):
                continue
            suites.addTest(self.load_tests_by_version(
                loader, version, AdminGenericTestList, key, val))
        return suites

    def get_options(self, api_version, command, extra_opts):
        """TODO"""
        options = {}
        LOG.debug("command: %s", command)
        commands = self.get_all_commands(api_version)
        if command in commands:
            options.update(commands[command])
        LOG.debug("options: %s", options)
        if "skip" not in options:
            options['skip'] = False
        if extra_opts:
            options.update(json.load(StringIO(extra_opts)))
        LOG.debug("options: %s", options)
        return options

    def get_all_commands(self, version):
        """TODO"""
        if version == 0:
            return self.get_all_commands_v0()
        return self.get_all_commands_v1()

    def get_all_commands_v0(self):
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
                'keyerror': keyerror,
                'keyerror_extended': keyerror_extended,
                'fields': False,
                },
            'ldap': {
                'delete': False,
                'keyerror': keyerror,
                'keyerror_extended': keyerror_extended,
                },
            'dpatterns': {
                'delete': False,
                'keyerror': keyerror,
                'keyerror_extended': keyerror_extended,
                },
            'funcs': {
                'delete': False,
                'fields': False,
                },
            'domainpolicy': {
                'delete': False,
                'fields': False,
                },
        }
        return commands

    def get_all_commands_v1(self):
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
                'keyerror': keyerror,
                'keyerror_extended': keyerror_extended,
                'fields': False,
                },
            'ldap': {
                'delete': False,
                'keyerror': keyerror,
                'keyerror_extended': keyerror_extended,
                },
            'dpatterns': {
                'delete': False,
                'keyerror': keyerror,
                'keyerror_extended': keyerror_extended,
                },
            'funcs': {
                'delete': False,
                'fields': False,
                },
            'domainpolicy': {
                'delete': False,
                'fields': False,
                },
        }
        return commands

    def get_all_tests(self):
        """Build all tests"""
        loader = unittest.TestLoader()
        suites = unittest.TestSuite()
        suites.addTest(self.load_tests(loader, self.get_all_commands_v0(), 0))
        suites.addTest(self.load_tests(loader, self.get_all_commands_v1(), 1))
        return suites


class LaunchAllTestsCommand(LaunchTestsCommand):
    """Launchtests command"""

    def __call__(self, args):
        super(LaunchAllTestsCommand, self).__call__(args)
        AdminGenericTestList.host = args.server
        AdminGenericTestList.password = args.password
        suite = self.get_all_tests()
        print("Detected testcases : " + str(suite.countTestCases()))
        if query_yes_no("Do you want to continue ?"):
            unittest.TextTestRunner(verbosity=2).run(suite)
        return True


class ListCommandTestsCommand(LaunchTestsCommand):
    """Launchtests command"""

    def __call__(self, args):
        super(ListCommandTestsCommand, self).__call__(args)
        version0 = self.get_all_commands_v0()
        version1 = self.get_all_commands_v1()
        if args.command:
            version0 = version0[args.command]
            version1 = version1[args.command]
        elif not args.all_details:
            version0 = list(version0.keys())
            version1 = list(version1.keys())
        print("Version : 0")
        print(json.dumps(version0, sort_keys=True, indent=2))
        print()
        print("Version : 1")
        print(json.dumps(version1, sort_keys=True, indent=2))
        print()


class LaunchOneCommandTestsCommand(LaunchTestsCommand):
    """Launchtests command"""

    def __call__(self, args):
        super(LaunchOneCommandTestsCommand, self).__call__(args)
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        AdminGenericTestList.host = args.server
        AdminGenericTestList.password = args.password
        options = self.get_options(args.api_version, args.command, args.options)
        for testcase in loader.loadTestsFromTestCase(AdminGenericTestList):
            testcase.api_version = int(args.api_version)
            testcase.set_command_to_test(args.command, options)
            suite.addTest(testcase)
        print("Detected testcases : " + str(suite.countTestCases()))
        if query_yes_no("Do you want to continue ?"):
            unittest.TextTestRunner(verbosity=2).run(suite)
        return True


class ListMethodTestsCommand(LaunchTestsCommand):
    """Launchtests command"""

    def __call__(self, args):
        super(ListMethodTestsCommand, self).__call__(args)
        loader = unittest.TestLoader()
        print()
        for testcase in loader.loadTestsFromTestCase(AdminGenericTestList):
            print(" - ", testcase)
        print()


class LaunchOneMethodTestsCommand(LaunchTestsCommand):
    """Launchtests command"""

    def __call__(self, args):
        super(LaunchOneMethodTestsCommand, self).__call__(args)
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        AdminGenericTestList.host = args.server
        AdminGenericTestList.password = args.password
        options = self.get_options(args.api_version, args.command, args.options)
        for testcase in loader.loadTestsFromTestCase(AdminGenericTestList):
            if testcase._testMethodName in args.method:
                print("Found : ", testcase)
                testcase.api_version = int(args.api_version)
                testcase.set_command_to_test(args.command, options)
                suite.addTest(testcase)
        print("Detected testcases : " + str(suite.countTestCases()))
        if query_yes_no("Do you want to continue ?"):
            unittest.TextTestRunner(verbosity=2).run(suite)
        return True


class LaunchTestProgram(BasicProgram):
    """Main program."""

    def add_config_options(self):
        super(LaunchTestProgram, self).add_config_options()

        # To be removed if useless : samples
        section = self.config.get_default_section()
        section.add_element(Element('server', default="http://127.0.0.1:8080"))
        section.add_element(Element('password', default="adminlinshare"))

    def add_commands(self):
        super(LaunchTestProgram, self).add_commands()
        self.parser.add_argument(
            "--password",
            help="default adminlinshare",
            **self.config.default.password.get_arg_parse_arguments())
        self.parser.add_argument(
            "--server",
            help="default http://127.0.0.1:8080",
            **self.config.default.server.get_arg_parse_arguments())
        subparsers = self.parser.add_subparsers()

        # command: launch all commands
        pat = subparsers.add_parser(
            'all',
            help="Launch all tests")
        pat.set_defaults(__func__=LaunchAllTestsCommand(self.config))

        # command: test one command
        pat = subparsers.add_parser(
            'command',
            help="Launch all tests for one command")
        pat.add_argument(
            "command",
            help="See linshareadmcli -h, like users, to get a valid command.")
        pat.add_argument("-a", "--api-version",
                         default=0, help="Available values : 0, 1",
                         type=int)
        pat.add_argument("-o", "--options", help='Sample: {"delete": false}')
        # pat.add_argument("--classname",
        # help="exmaple : AdminGenericTestList", default=AdminGenericTestList)
        pat.set_defaults(__func__=LaunchOneCommandTestsCommand(self.config))

        # command: test one test method for a command
        pat = subparsers.add_parser(
            'method',
            help="Launch one test method for one command")
        pat.add_argument(
            "command",
            help="See linshareadmcli -h, like users, to get a valid command.")
        pat.add_argument(
            "method", nargs="+",
            help="See linshareadmcli -h, like users, to get a valid command.")
        pat.add_argument("-a", "--api-version",
                         default=0, help="Available values : 0, 1",
                         type=int)
        pat.add_argument("-o", "--options")
        pat.set_defaults(__func__=LaunchOneMethodTestsCommand(self.config))

        # command: test one test method for a command
        pat = subparsers.add_parser(
            'methods',
            help="only list available tests")
        pat.set_defaults(__func__=ListMethodTestsCommand(self.config))
        # command: test one test method for a command
        pat = subparsers.add_parser(
            'commands',
            help="only list available commands and config")
        pat.add_argument(
            "command", nargs="?",
            help="See linshareadmcli -h, like users, to get a valid command.")
        pat.add_argument("-a", "--all_details", help="all details",
                         action="store_true")
        pat.set_defaults(__func__=ListCommandTestsCommand(self.config))


PROG = LaunchTestProgram(
    "LaunchTestProgram",
    desc="main tool to launch external tests on a real server")
if __name__ == "__main__":
    PROG()
