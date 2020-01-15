#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""TODO"""


# This file is part of Linshare cli.
#
# LinShare cli is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LinShare cli is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LinShare cli.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#



from linshareapi.cache import Time
from linshareapi.core import LinShareException
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.tables import ConsoleTable
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.filters import Equals
from linsharecli.admin.core import DefaultCommand
from linsharecli.common.tables import TableBuilder
from linsharecli.common.cell import ComplexCell
from argtoolbox import DefaultCompleter as Completer



class UpgradeTasksCommand(DefaultCommand):
    """TODO"""

    IDENTIFIER = "identifier"
    DEFAULT_SORT = "taskOrder"
    RESOURCE_IDENTIFIER = "identifier"

    DEFAULT_TOTAL = "Upgrade task found : %(count)s"
    MSG_RS_NOT_FOUND = "No upgrade task could be found."
    MSG_RS_UPDATED = "The upgrade task '%(identifier)s' was successfully triggered."
    # MSG_RS_CREATED = "The upgrade task '%(identifier)s' was successfully created. (%(_time)s s)"

    def complete(self, args, prefix):
        super(UpgradeTasksCommand, self).__call__(args)
        json_obj = self.ls.upgrade_tasks.list()
        return (v.get(self.RESOURCE_IDENTIFIER)
                for v in json_obj if v.get(self.RESOURCE_IDENTIFIER).startswith(prefix))


class CriticityCell(ComplexCell):
    """TODO"""

    def __unicode__(self):
        if self.raw:
            return str(self.value)
        if self.value is None:
            return self.none
        return '{v:5s}'.format(v=self.value)


class UpgradeTasksListCommand(UpgradeTasksCommand):
    """ List all upgrade_tasks."""

    @Time('linsharecli.upgrade_tasks', label='Global time : %(time)s')
    def __call__(self, args):
        super(UpgradeTasksListCommand, self).__call__(args)
        endpoint = self.ls.upgrade_tasks
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell("criticity", CriticityCell)
        tbu.add_filters(
            PartialDate("creationDate", args.cdate),
        )
        tbu.add_filter_cond(
            not args.identifier,
            PartialOr(self.IDENTIFIER, [args.identifier], True)
        )
        tbu.add_filter_cond(
            args.identifier and args.run,
            Equals("criticity", args.criticity)
        )
        json_obj = None
        if args.identifier:
            if args.run:
                tbu.endpoint = self.ls.upgrade_tasks.async_tasks.console
                json_obj = tbu.endpoint.list(args.identifier, args.run)
                tbu.horizontal_clazz = ConsoleTable
            else:
                tbu.endpoint = self.ls.upgrade_tasks.async_tasks
                json_obj = tbu.endpoint.list(args.identifier)
        else:
            json_obj = endpoint.list()
        return tbu.build().load_v2(json_obj).render()


    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(UpgradeTasksListCommand, self).__call__(args)
        cli = self.ls.upgrade_tasks
        return cli.get_rbu().get_keys(True)

    def complete_async_tasks(self, args, prefix):
        """TODO"""
        super(UpgradeTasksListCommand, self).__call__(args)
        cli = self.ls.upgrade_tasks.async_tasks
        json_obj = cli.list(args.identifier)
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))


class UpgradeTasksTriggerCommand(UpgradeTasksCommand):
    """Trigger welcome message."""

    def __call__(self, args):
        super(UpgradeTasksTriggerCommand, self).__call__(args)
        cli = self.ls.upgrade_tasks
        # resource = cli.get(args.identifier)
        try:
            json_obj = cli.trigger(args.identifier, args.force)
            if self.debug:
                self.pretty_json(json_obj)
            self.log.info(self.MSG_RS_UPDATED, json_obj)
            return True
        except LinShareException as ex:
            self.log.debug("can trigger upgrade task : %s", args.identifier, exc_info=1)
            self.log.error(ex.args)
        return False


def add_parser(subparsers, name, desc, config):
    """Add all upgrade tasks sub commands."""
    # api_version = config.server.api_version.value
    parser_tmp = subparsers.add_parser(name, help=desc)
    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list', help="list all upgrade tasks.")
    parser.add_argument('identifier', nargs="?",
                        help="""<Upgrade task identifier>. It will display all
                        previous runs for this upgrade task.""").completer = Completer()
    parser.add_argument(
        'run',
        nargs="?",
        help="<Run uuid>. It will display the content of one run (console)"
    ).completer = Completer('complete_async_tasks')
    parser.add_argument('--criticity', action="append",
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
                        help="Applied only when displaying run data.")
    add_list_parser_options(parser, cdate=True)
    parser.set_defaults(__func__=UpgradeTasksListCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update welcome message.")
    parser.add_argument('identifier').completer = Completer()
    parser.add_argument('--force', action="store_true")
    parser.set_defaults(__func__=UpgradeTasksTriggerCommand(config))
