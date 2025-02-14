# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import os
import json

import bpy
import bmesh
from bpy.props import (
        StringProperty,
        CollectionProperty,
        IntProperty,
        )
from bpy.types import (
        Operator,
        OperatorFileListElement,
        )

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.modules import sv_bmesh
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator


class SvFilePathFinder(bpy.types.Operator, SvGenericNodeLocator):
    '''Select Files from browser window'''
    bl_idname = "node.sv_file_path"
    bl_label = "Select Files/Folder"

    files: CollectionProperty(name="File Path", type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    filepath: bpy.props.StringProperty(
        name="File Path", description="Filepath used for writing waveform files",
        maxlen=1024, default="", subtype='FILE_PATH')

    def execute(self, context):
        node = self.get_node(context)
        if not node: return {'CANCELLED'}

        node.set_data(self.directory, self.files)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvFilePathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: OS file path
    Tooltip:  get path file from OS
    """

    bl_idname = "SvFilePathNode"
    bl_label = "File Path"
    bl_icon = "FILE"

    files_num: IntProperty(name='files number ', default=0)
    files: CollectionProperty(name="File Path", type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH', update=updateNode)

    def sv_init(self, context):

        self.outputs.new('SvFilePathSocket', "File Path")

    def draw_buttons(self, context, layout):

        op = 'node.sv_file_path'
        self.wrapper_tracked_ui_draw_op(layout, op, icon='FILE', text='')
        if self.files_num == 0:
            layout.label(text=self.directory)
        elif self.files_num == 1:
            layout.label(text=self.files[0].name)
        else:
            layout.label(text="%d files at %s" % (len(self.files), self.directory))

    def set_data(self, dirname, files):

        self.files.clear()
        for file_elem in files:

            item = self.files.add()
            for k, v in file_elem.items():
                item[k] = v
        self.directory = dirname
        if len(files) == 1 and not files[0].name:
            self.files_num = 0
        else:
            self.files_num = len(files)

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return
        directory = self.directory
        if self.files:
            files = []
            for file_elem in self.files:
                filepath = os.path.join(directory, file_elem.name)
                files.append(filepath)
            self.outputs['File Path'].sv_set([files])
        else:
            self.outputs['File Path'].sv_set([[self.directory]])

    # iojson stuff

    def load_from_json(self, node_dict: dict, import_version: float):
        '''function to get data when importing from json''' 

        if import_version <= 0.08:
            strings_json = node_dict['string_storage']
            filenames = json.loads(strings_json)['filenames']
            directory = json.loads(strings_json)['directory']

            self.set_data(directory, filenames)


classes = [SvFilePathNode, SvFilePathFinder]
register, unregister = bpy.utils.register_classes_factory(classes)
