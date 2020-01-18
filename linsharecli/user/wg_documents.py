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



import os
import argparse
from linshareapi.cache import Time
from argtoolbox import DefaultCompleter as Completer
from linsharecli.common.filters import PartialOr
from linsharecli.common.filters import PartialDate
from linsharecli.common.core import add_list_parser_options
from linsharecli.common.core import add_delete_parser_options
from linsharecli.common.core import add_download_parser_options
from linsharecli.user.core import DefaultCommand
from linsharecli.common.actions import CreateAction
from linsharecli.common.actions import UpdateAction
from linsharecli.common.cell import ComplexCell
from linsharecli.common.cell import ComplexCellBuilder
from linsharecli.common.tables import TableBuilder
from linsharecli.common.tables import Action
from linsharecli.common.tables import DeleteAction
from linsharecli.common.tables import DownloadAction


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
        for row in json_obj if row.get('type') in ["FOLDER", "DOCUMENT"]
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
            for i, j in list(kwargs.items()):
                debug("key : " + str(i))
                debug("\t - " + str(j))
            debug("\n------------ ThreadCompleter -----------------\n")
            args = kwargs.get('parsed_args')
            # FIXME
            wg_cmd = WgNodeContentListCommand(self.config)
            return wg_cmd.complete_workgroups(args, prefix)
        # pylint: disable=broad-except
        except Exception as ex:
            debug("\nERROR:An exception was caught :" + str(ex) + "\n")
            import traceback
            traceback.print_exc()
            debug("\n------\n")
            return ["comlete-error"]


class WgNodesCommand(DefaultCommand):
    """TODO"""

    MSG_RS_CREATED = ("The following folder '%(name)s' "
                      "(%(uuid)s) was successfully created")

    MSG_RS_UPDATED = ("The following folder '%(name)s' "
                      "(%(uuid)s) was successfully updated")


    CFG_DOWNLOAD_MODE = 2
    CFG_DOWNLOAD_ARG_ATTR = "wg_uuid"
    CFG_DELETE_MODE = 1
    CFG_DELETE_ARG_ATTR = "wg_uuid"

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


class TreeCell(ComplexCell):
    """TODO"""
    def __str__(self):
        if self.raw:
            return str(self.value)
        breadcrumb = []
        for path in self.value:
            breadcrumb.append(path.get('name'))
        if self.row:
            cell_name = self.row.get('name')
            breadcrumb.append(str(cell_name))
        breadcrumb = " > ".join(breadcrumb)
        return breadcrumb


class WorkgroupDocumentsUploadCommand(WgNodesCommand):
    """ Upload a file to LinShare using its rest api. return the uploaded document uuid  """

    @Time('linsharecli.document', label='Global time : %(time)s')
    def __call__(self, args):
        super(WorkgroupDocumentsUploadCommand, self).__call__(args)
        parent = None
        if args.folders:
            parent = get_uuid_from(args.folders[-1])
            self.ls.workgroup_nodes.get(args.wg_uuid, parent)
        return self.upload_files_recursif(
            args.wg_uuid,
            args.files,
            args.description,
            parent)

    def upload_files_recursif(self, wg_uuid, files, description, parent):
        """Upload a file or a folder recursivily."""
        count = len(files)
        position = 0
        cli = self.ls.workgroup_folders
        for file_path in files:
            position += 1
            self.log.debug("file_path: %s", file_path)
            if os.path.isdir(file_path):
                self.log.debug("file_path %s is a folder", file_path)
                rbu = cli.get_rbu()
                folder_name = file_path
                if folder_name[-1] == '/':
                    folder_name = folder_name[:-1]
                folder_name = folder_name.split('/')[-1]
                rbu.set_value('name', folder_name)
                rbu.set_value('workGroup', wg_uuid)
                if parent:
                    rbu.set_value('parent', parent)
                new_folder = self.ls.workgroup_folders.create(rbu.to_resource())
                folder_uuid = new_folder['uuid']
                self.log.debug("folder_uuid: %s", folder_uuid)
                files2 = []
                for path in os.listdir(file_path):
                    files2.append(file_path + "/" + path)
                self.upload_files_recursif(
                    wg_uuid,
                    files2,
                    description,
                    folder_uuid)
            else:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    self.log.warn("this file '%s' is empty. skipped.", file_path)
                    continue
                json_obj = self.ls.workgroup_nodes.upload(
                    wg_uuid, file_path, description, parent)
                if json_obj:
                    json_obj['time'] = self.ls.last_req_time
                    json_obj['position'] = position
                    json_obj['count'] = count
                    json_obj['file_path'] = file_path
                    self.log.info(
                        ("%(position)s/%(count)s: "
                         "The file '%(file_path)s' (%(uuid)s) was uploaded. "
                         "(%(time)ss)"),
                        json_obj)
        return True


class Breadcrumb(Action):
    """TODO"""

    display = True

    def init(self, args, cli, endpoint):
        super(Breadcrumb, self).init(args, cli, endpoint)
        self.display = not getattr(args, 'no_breadcrumb', False)
        if getattr(args, 'flat_mode', False):
            self.display = False

    def __call__(self, args, cli, endpoint, data):
        self.init(args, cli, endpoint)
        if self.display:
            node_uuid = self.get_last_valid_node(args)
            if node_uuid:
                node = endpoint.get(args.wg_uuid, node_uuid, tree=True)
                breadcrumb = []
                for path in node.get('treePath'):
                    breadcrumb.append(path.get('name'))
                breadcrumb.append(node.get('name'))
                print()
                print("###>", " > ".join(breadcrumb))
                print()

    def get_last_valid_node(self, args):
        """TODO"""
        if args.folders:
            nodes = reversed(args.folders)
            for node in nodes:
                parent = get_uuid_from(node)
                if self.endpoint.head(args.wg_uuid, parent):
                    return parent
        return args.wg_uuid


class WgNodeContentListCommand(WgNodesCommand):
    """List all workgroup content."""

    @Time('linsharecli.workgroups.nodes', label='Global time : %(time)s')
    def __call__(self, args):
        super(WgNodeContentListCommand, self).__call__(args)
        endpoint = self.ls.workgroup_nodes
        parent = None
        if args.folders:
            parent = get_uuid_from(args.folders[-1])
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.load_args(args)
        tbu.add_custom_cell(
            "lastAuthor",
            ComplexCellBuilder('{name}\n<{mail}>', '{name} <{mail}>'))
        tbu.add_action('download', DownloadAction(
            mode=self.CFG_DOWNLOAD_MODE,
            parent_identifier=self.CFG_DOWNLOAD_ARG_ATTR
        ))
        tbu.add_action('delete', DeleteAction(
            mode=self.CFG_DELETE_MODE,
            parent_identifier=self.CFG_DELETE_ARG_ATTR
        ))
        tbu.add_filters(
            PartialOr(self.IDENTIFIER, args.names, True),
            PartialDate("creationDate", args.cdate)
        )
        json_obj = endpoint.list(
            args.wg_uuid, parent, flat=args.flat_mode,
            node_types=args.node_types
        )
        tbu.add_pre_render_class(Breadcrumb())
        return tbu.build().load_v2(json_obj).render()

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
        endpoint = self.ls.workgroup_nodes
        tbu = TableBuilder(self.ls, endpoint, self.DEFAULT_SORT)
        tbu.vertical = True
        tbu.load_args(args)
        tbu.add_custom_cell("lastAuthor", ComplexCellBuilder('{name} <{mail}>'))
        tbu.add_custom_cell("treePath", TreeCell)
        tbu.columns = endpoint.get_rbu().get_keys(args.extended)
        tbu.columns.append('treePath')
        json_obj = []
        for node_uuid in args.nodes:
            node_uuid = get_uuid_from(node_uuid)
            node = endpoint.get(args.wg_uuid, node_uuid, tree=True)
            # self.pretty_json(node)
            json_obj.append(node)
        return tbu.build().load_v2(json_obj).render()


class WorkgroupDocumentsDownloadCommand(WgNodesCommand):
    """TODO"""

    @Time('linsharecli.workgroups.nodes', label='Global time : %(time)s')
    def __call__(self, args):
        super(WorkgroupDocumentsDownloadCommand, self).__call__(args)
        act = DownloadAction(
            mode=self.CFG_DOWNLOAD_MODE,
            parent_identifier=self.CFG_DOWNLOAD_ARG_ATTR
        )
        act.init(args, self.ls, self.ls.workgroup_nodes)
        return act.download(args.uuids)


class WorkgroupDocumentsDeleteCommand(WgNodesCommand):
    """TODO"""

    @Time('linsharecli.workgroups.nodes', label='Global time : %(time)s')
    def __call__(self, args):
        super(WorkgroupDocumentsDeleteCommand, self).__call__(args)
        act = DeleteAction(
            mode=self.CFG_DELETE_MODE,
            parent_identifier=self.CFG_DELETE_ARG_ATTR
        )
        act.init(args, self.ls, self.ls.workgroup_nodes)
        return act.delete(args.uuids)


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
    parser.add_argument('files', nargs='+', help="upload files or folders")
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
