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
# Copyright 2014 Frédéric MARTIN
#
# Contributors list :
#
#  Frédéric MARTIN frederic.martin.fma@gmail.com
#

from __future__ import unicode_literals

import argparse
from argparse import ArgumentError
from argtoolbox import DefaultCompleter as Completer
from linshareapi.cache import Time
from linshareapi.core import LinShareException
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.formatters import DateFormatter
from linsharecli.common.formatters import SizeFormatter
from linsharecli.common.formatters import LastAuthorFormatter
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import add_download_parser_options
from linsharecli.user.core import DefaultCommand
from linsharecli.common.formatters import Formatter
from linsharecli.common.actions import CreateAction
from linsharecli.common.actions import UpdateAction


INVALID_CHARS = [
    (" ", "."),
    (" ", "."),
    ("é", "e"),
    ("è", "e"),
    ("ê", "e"),
    ("à", "a"),
    ("[", "."),
    ("]", "."),
    ("(", "."),
    (")", "."),
    ("{", "."),
    ("}", "."),
    ("'", "."),
    ("!", "."),
    ("?", "."),
    ("¿", "."),
    ("¦", "."),
    ("'", "."),
    ("&", ".and."),
    ("¡", "."),
    ("–", "-"),
    ("—", "-"),
    ("…", "."),
    ("⁄", "."),
    ("#", ""),
    ("@", ""),
    ("’", ""),
    (",", "."),
    (":", "."),
    (";", "."),
    ("...", "."),
    ("..", "."),
]

def format_record_for_autocomplete(row):
    """Build one result from uuid and sanitysed name"""
    uuid = row.get('uuid')
    sep = "@@@"
    name = row.get('name')
    for char, replace in INVALID_CHARS:
        name = name.replace(char, replace)
    return uuid + sep + name.strip(".")

def get_uuid_from(record):
    """TODO"""
    return record.split('@@@')[0]

def convert_to_list(json_obj, parent, prefix):
    """Convert json_obj to a list ready to use for completion"""
    from argcomplete import debug
    debug("\n>----------- convert_to_list - 1  -----------------")
    debug("parent: ", parent)
    debug("prefix: ", prefix)
    debug("RAW", json_obj)
    json_obj = list(
        format_record_for_autocomplete(row)
        for row in json_obj if row.get('type') == "FOLDER"
    )
    debug("UUIDS", json_obj)
    debug("------------ convert_to_list - 1 ----------------<\n")
    return json_obj

def convert_to_list_nodes(json_obj):
    """TODO"""
    return list(
        format_record_for_autocomplete(row)
        for row in json_obj if row.get('type') in [
            "FOLDER", "DOCUMENT"
        ]
    )


class WorkgroupCompleter(object):
    """TODO"""
    # pylint: disable=too-few-public-methods

    def __init__(self, config):
        self.config = config

    def __call__(self, prefix, **kwargs):
        from argcomplete import debug
        try:
            debug("\n------------ ThreadCompleter -----------------")
            debug("Kwargs content :")
            for i, j in kwargs.items():
                debug("key : " + str(i))
                debug("\t - " + str(j))
            debug("\n------------ ThreadCompleter -----------------\n")
            args = kwargs.get('parsed_args')
            # FIXME
            wg_cmd = WgNodeContentListCommand(self.config)
            return wg_cmd.complete_workgroups(args, prefix)
        # pylint: disable-msg=W0703
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")
            import traceback
            traceback.print_exc()
            debug("\n------\n")
            return ["comlete-error"]


class WgNodesCommand(DefaultCommand):
    """TODO"""

    DEFAULT_TOTAL = "Documents found : %(count)s"
    MSG_RS_NOT_FOUND = "No documents could be found."
    MSG_RS_DELETED = ("%(position)s/%(count)s: "
                      "The document '%(name)s' (%(uuid)s) was deleted. "
                      "(%(time)s s)")
    MSG_RS_CAN_NOT_BE_DELETED = "The document '%(uuid)s' can not be deleted."
    MSG_RS_CAN_NOT_BE_DELETED_M = "%(count)s document(s) can not be deleted."
    MSG_RS_DOWNLOADED = ("%(position)s/%(count)s: "
                         "The document '%(name)s' (%(uuid)s) was downloaded. "
                         "(%(time)s s)")
    MSG_RS_CAN_NOT_BE_DOWNLOADED = "One document can not be downloaded."
    MSG_RS_CAN_NOT_BE_DOWNLOADED_M = ("%(count)s "
                                      "documents can not be downloaded.")
    MSG_RS_CREATED = ("The following folder '%(name)s' "
                      "(%(uuid)s) was successfully created")

    MSG_RS_UPDATED = ("The following folder '%(name)s' "
                      "(%(uuid)s) was successfully updated")


    CFG_DOWNLOAD_MODE = 2
    CFG_DOWNLOAD_ARG_ATTR = "wg_uuid"
    CFG_DELETE_MODE = 1
    CFG_DELETE_ARG_ATTR = "wg_uuid"

    ACTIONS = {
        'delete': '_delete_all',
        'download': '_download_all',
        'count_only': '_count_only',
    }

    def complete_root_only(self, args, prefix):
        """Autocomplete on every node in the current folder, file or folder"""
        super(WgNodesCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        json_obj = cli.list(args.wg_uuid)
        # only root folder is supported for now.
        # json_obj = cli.list(args.wg_uuid, args.folders)
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))

    def complete_workgroups(self, args, prefix):
        """TODO"""
        super(WgNodesCommand, self).__call__(args)
        json_obj = self.ls.threads.list()
        return (v.get('uuid')
                for v in json_obj if v.get('uuid').startswith(prefix))

    def complete(self, args, prefix):
        """TODO"""
        from argcomplete import debug
        super(WgNodesCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        debug("folders : ", args.folders)
        if args.folders:
            debug("len folders : ", len(args.folders))
        debug("prefix : ", prefix)
        debug("len prefix : ", len(prefix))

        if args.folders:
            parent = get_uuid_from(args.folders[-1])
            if len(parent) >= 36:
                json_obj = cli.list(args.wg_uuid, parent)
                res = convert_to_list(json_obj, parent, prefix)
                return res
            else:
                if len(args.folders) >= 2:
                    parent = get_uuid_from(args.folders[-2])
                else:
                    parent = None
                json_obj = cli.list(args.wg_uuid, parent)
                return convert_to_list(json_obj, parent, prefix)
        else:
            parent = None
            json_obj = cli.list(args.wg_uuid)
            res = convert_to_list(json_obj, parent, prefix)
            return res

    def complete_nodes(self, args, prefix):
        """TODO"""
        from argcomplete import debug
        super(WgNodesCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        debug("nodes : ", args.nodes)
        if args.nodes:
            debug("len nodes : ", len(args.nodes))
        debug("prefix : ", prefix)
        debug("len prefix : ", len(prefix))
        if args.nodes:
            parent = get_uuid_from(args.nodes[-1])
            if len(parent) >= 36:
                json_obj = cli.list(args.wg_uuid, parent)
                return convert_to_list_nodes(json_obj)
            else:
                if len(args.nodes) >= 2:
                    parent = get_uuid_from(args.nodes[-2])
                else:
                    parent = None
                json_obj = cli.list(args.wg_uuid, parent)
                return convert_to_list_nodes(json_obj)
        else:
            parent = None
            json_obj = cli.list(args.wg_uuid)
            return convert_to_list_nodes(json_obj)

    def check_required_options(self, args, required_fields, options):
        """Check if at least one option is set among the required_fields list"""
        one_set = False
        for i in required_fields:
            if getattr(args, i, None) is not None:
                one_set = True
                break
        if not one_set:
            msg = "You need to choose at least one option among : "
            msg += " or ".join(options)
            raise ArgumentError(None, msg)


# pylint: disable=too-few-public-methods
class TreePathFormatter(Formatter):
    """TODO"""

    def __init__(self, prop):
        super(TreePathFormatter, self).__init__(prop)

    def __call__(self, row, context=None):
        parameter = row.get(self.prop)
        if parameter:
            breadcrumb = []
            for path in parameter:
                breadcrumb.append(path.get('name'))
            breadcrumb.append(row.get('name'))
            row[self.prop] = " > ".join(breadcrumb)


class WorkgroupDocumentsUploadCommand(WgNodesCommand):
    """ Upload a file to LinShare using its rest api. return the uploaded document uuid  """

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(WorkgroupDocumentsUploadCommand, self).__call__(args)
        count = len(args.files)
        position = 0
        parent = None
        if args.folders:
            parent = get_uuid_from(args.folders[-1])
            self.ls.workgroup_nodes.get(args.wg_uuid, parent)
        for file_path in args.files:
            position += 1
            json_obj = self.ls.workgroup_nodes.upload(
                args.wg_uuid, file_path, args.description, parent)
            if json_obj:
                json_obj['time'] = self.ls.last_req_time
                json_obj['position'] = position
                json_obj['count'] = count
                self.log.info(
                    ("%(position)s/%(count)s: "
                     "The file '%(name)s' (%(uuid)s) was uploaded. "
                     "(%(time)ss)"),
                    json_obj)
        return True


class WgNodeContentListCommand(WgNodesCommand):
    """ List all workgroup content."""

    def get_last_valid_node(self, cli, args):
        """TODO"""
        if args.folders:
            nodes = reversed(args.folders)
            for node in nodes:
                parent = get_uuid_from(node)
                if cli.head(args.wg_uuid, parent):
                    return parent
        return args.wg_uuid

    def show_breadcrumb(self, cli, args):
        """TODO"""
        if not getattr(args, 'no_breadcrumb', False):
            node_uuid = self.get_last_valid_node(cli, args)
            if node_uuid:
                node = cli.get(args.wg_uuid, node_uuid, tree=True)
                breadcrumb = []
                for path in node.get('treePath'):
                    breadcrumb.append(path.get('name'))
                breadcrumb.append(node.get('name'))
                print
                print "###>", " > ".join(breadcrumb)
                print

    @Time('linsharecli.workgroups.nodes', label='Global time : %(time)s')
    def __call__(self, args):
        super(WgNodeContentListCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        table = self.get_table(args, cli, self.IDENTIFIER, args.fields)
        parent = None
        if args.folders:
            parent = get_uuid_from(args.folders[-1])
        self.show_breadcrumb(cli, args)
        json_obj = cli.list(args.wg_uuid, parent, flat=args.flat_mode,
                            node_types=args.node_types)
        # Filters
        filters = [PartialOr(self.IDENTIFIER, args.names, True),
                   PartialDate("creationDate", args.cdate)]
        # Formatters
        formatters = [DateFormatter('creationDate'),
                      DateFormatter('uploadDate'),
                      SizeFormatter('size', "-"),
                      LastAuthorFormatter('lastAuthor'),
                      DateFormatter('modificationDate')]
        ignore_exceptions = {'size': True, 'uploadDate':True}
        return self._list(args, cli, table, json_obj, formatters, filters,
                          ignore_exceptions=ignore_exceptions)

    def complete_fields(self, args, prefix):
        """TODO"""
        # pylint: disable=unused-argument
        super(WgNodeContentListCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        return cli.get_rbu().get_keys(True)


class WgNodeContentDisplayCommand(WgNodesCommand):
    """ List all thread members."""

    @Time('linsharecli.workgroups.nodes', label='Global time : %(time)s')
    def __call__(self, args):
        super(WgNodeContentDisplayCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        json_obj = []
        for node_uuid in args.nodes:
            node_uuid = get_uuid_from(node_uuid)
            node = cli.get(args.wg_uuid, node_uuid, tree=True)
            # self.pretty_json(node)
            json_obj.append(node)
        args.vertical = True
        table = self.get_table(args, cli, self.IDENTIFIER)
        keys = cli.get_rbu().get_keys(args.extended)
        keys.append('treePath')
        table = self.get_raw_table(args, cli, self.IDENTIFIER, keys)
        # useless and required ! Design flaw ?
        table.sortby = self.IDENTIFIER
        formatters = [DateFormatter('creationDate'),
                      DateFormatter('uploadDate'),
                      SizeFormatter('size', "-"),
                      LastAuthorFormatter('lastAuthor'),
                      TreePathFormatter('treePath'),
                      DateFormatter('modificationDate')]
        ignore_exceptions = {'size': True, 'uploadDate':True}
        return self._list(args, cli, table, json_obj, formatters,
                          ignore_exceptions=ignore_exceptions)


class WorkgroupDocumentsDownloadCommand(WgNodesCommand):
    """TODO"""

    @Time('linsharecli.workgroups.nodes', label='Global time : %(time)s')
    def __call__(self, args):
        super(WorkgroupDocumentsDownloadCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        return self._download_all(args, cli, args.uuids)


class WorkgroupDocumentsDeleteCommand(WgNodesCommand):
    """TODO"""

    @Time('linsharecli.workgroups.nodes', label='Global time : %(time)s')
    def __call__(self, args):
        super(WorkgroupDocumentsDeleteCommand, self).__call__(args)
        cli = self.ls.workgroup_nodes
        return self._delete_all(args, cli, args.uuids)


class FolderCreateCommand(WgNodesCommand):
    """TODO"""

    @Time('linsharecli.threads', label='Global time : %(time)s')
    def __call__(self, args):
        super(FolderCreateCommand, self).__call__(args)
        cli = self.ls.workgroup_folders
        act = CreateAction(self, cli)
        rbu = cli.get_rbu()
        rbu.load_from_args(args)
        if args.folders:
            parent = get_uuid_from(args.folders[-1])
            rbu.set_value('parent', parent)
        return act.load(args).execute(rbu.to_resource())


class NodeUpdateCommand(WgNodesCommand):
    """TODO"""

    @Time('linsharecli.threads', label='Global time : %(time)s')
    def __call__(self, args):
        super(NodeUpdateCommand, self).__call__(args)
        self.check_required_options(
            args,
            ['description', 'meta_data', 'name'],
            ["--name", "--description"])
        cli = self.ls.workgroup_folders
        uuid = get_uuid_from(args.nodes[-1])
        node = cli.get(args.wg_uuid, uuid)
        act = UpdateAction(self, cli)
        rbu = cli.get_rbu()
        rbu.copy(node)
        rbu.load_from_args(args)
        # workaround
        rbu.set_value('parent', None)
        return act.load(args).execute(rbu.to_resource())


def add_parser(subparsers, name, desc, config):
    """TODO"""
    parser_tmp = subparsers.add_parser(name, help=desc)
    parser_tmp.add_argument(
        'wg_uuid',
        help="workgroup uuid"
        ).completer = WorkgroupCompleter(config)

    subparsers2 = parser_tmp.add_subparsers()

    # command : list
    parser = subparsers2.add_parser(
        'list',
        help="list workgroup nodes from linshare")
    parser.add_argument(
        '-f', '--filter', action="append", dest="names",
        help="Filter documents by their names")
    parser.add_argument(
        '--flat', action="store_true", dest="flat_mode",
        help="Flat document mode : list all documents in every folders in a workgroup")
    parser.add_argument(
        '--type', action="append", dest="node_types", default=None,
        choices=["DOCUMENT", "FOLDER", "ROOT_FOLDER", "DOCUMENT_REVISION"],
        help="Filter the returned objects by type.")
    parser.add_argument(
        '--no-breadcrumb', action="store_true",
        help="Do not display breadcrumb.")
    parser.add_argument(
        'folders', nargs="*",
        help="Browse folders'content: folder_uuid, folder_uuid, ..."
        ).completer = Completer()
    add_list_parser_options(
        parser, download=True, delete=True, cdate=True)
    parser.set_defaults(__func__=WgNodeContentListCommand(config))

    # command : show
    parser = subparsers2.add_parser(
        'show',
        help="show workgroup nodes (folders, documents, ...)")
    parser.add_argument(
        'nodes', nargs="*",
        help="Display folders'content: folder_uuid, folder_uuid, ..."
        )
    parser.add_argument(
        '--extended', action="store_true",
        help="Display results using extended format.")
    parser.add_argument('--json', action="store_true", help="Json output")
    parser.add_argument(
        '--raw-json', action="store_true",
        help="Display every attributes for json output.")
    parser.add_argument(
        '--raw', action="store_true",
        help="Disable all data formatters (time, size, ...)")
    parser.set_defaults(__func__=WgNodeContentDisplayCommand(config))

    # command : delete
    parser = subparsers2.add_parser(
        'delete',
        help="delete workgroup nodes (folders, documents, ...)")
    add_delete_parser_options(parser, 'complete_root_only')
    parser.set_defaults(__func__=WorkgroupDocumentsDeleteCommand(config))

    # command : download
    parser = subparsers2.add_parser(
        'download',
        help="download documents from linshare")
    add_download_parser_options(parser, 'complete_root_only')
    parser.set_defaults(__func__=WorkgroupDocumentsDownloadCommand(config))

    # command : upload
    parser = subparsers2.add_parser(
        'upload',
        help="upload documents to linshare")
    parser.add_argument('--desc', action="store", dest="description",
                        required=False, help="Optional description.")
    parser.add_argument('files', nargs='+')
    parser.add_argument(
        '-f', '--folders', action="append",
        help="""The new files will be uploaded in the last folder in the list.
        Otherwise it will be create at the root of the workgroup"""
        ).completer = Completer()
    parser.set_defaults(__func__=WorkgroupDocumentsUploadCommand(config))

    # command : create
    parser = subparsers2.add_parser(
        'create', help="create a folder.")
    parser.add_argument('name', action="store", help="")
    parser.add_argument('--cli-mode', action="store_true",
                        help="""Cli mode will format output to be used in
                        a script, by returning only identifiers or numbers
                        without any information messages.""")
    parser.add_argument(
        'folders', nargs="*",
        help="""The new folder will be created in the last folder list.
        Otherwise it will be create at the root of the workgroup"""
        ).completer = Completer()
    parser.set_defaults(__func__=FolderCreateCommand(config))

    # command : update
    parser = subparsers2.add_parser(
        'update', help="update a folder.")
    parser.add_argument(
        'nodes', nargs="*",
        help="Browse files and folders'content: node_uuid, node_uuid, ..."
        ).completer = Completer('complete_nodes')
    # parser.add_argument( 'uuid', action="store", help="")
    group = parser.add_argument_group('properties')
    group.add_argument('--name', action="store", help="")
    group.add_argument('--description', action="store", help="")
    group.add_argument('--meta-data', action="store", help=argparse.SUPPRESS)
    parser.add_argument('--cli-mode', action="store_true",
                        help="""Cli mode will format output to be used in
                        a script, by returning only identifiers or numbers
                        without any information messages.""")
    parser.set_defaults(__func__=NodeUpdateCommand(config))
