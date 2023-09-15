import bpy
import logging
import subprocess
import sys
import os
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from . import main

bl_info = {
    'name': 'TCA-Exporter',
    'blender': (2, 80, 0),
    'category': 'Import-Export',
    'version': (1, 0, 0),
    'description': 'Addon that converts Blender objects to Unity prefabs.',
    'location': "File > Export > TCA Exporter",
    'doc_url': 'https://github.com/DuckMallard/TCA-Exporter'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class TCA_Exporter(Operator, ExportHelper):
    """TCA assetbundle export"""
    bl_idname = 'tca.export'
    bl_label = 'Export'
    filename_ext = ''

    def execute(self, context):
        return main.export(context, self.filepath)


def menu_func_export(self, _context):
    self.layout.operator(TCA_Exporter.bl_idname, text="TCA Exporter")


def register():

    logger.debug('Starting addon registration')

    main.register()

    bpy.utils.register_class(TCA_Exporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    logger.debug('Addon registration complete')


def unregister():
    bpy.utils.unregister_class(TCA_Exporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    main.unregister()

    logger.debug('Unregistration completed')
