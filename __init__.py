bl_info = {
    'name': 'TCA-Exporter',
    'blender': (2, 80, 0),
    'category': 'Import-Export',
    'version': (1, 0, 0),
    'description': 'Addon that converts Blender objects to Unity prefabs.',
    'location': "File > Export > TCA Exporter",
    'doc_url': 'https://github.com/DuckMallard/TCA-Exporter'
}

import os, sys, subprocess, bpy

from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator

from exporter import main

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

class TCA_Exporter(Operator, ExportHelper):
    """TCA assetbundle export"""
    bl_idname = 'tca.export'
    bl_label = 'Export'
    filename_ext = ''

    def execute(self, context):
        return main(context, self.filepath)

def menu_func_export(self, _context):
    self.layout.operator(TCA_Exporter.bl_idname, text="TCA Exporter")

def register():

    logger.debug('Starting addon registration')

    venv_site_pkg_file_path = os.path.join(os.path.dirname(__file__), '.venv/Lib/site-packages')

    logger.debug(f'Looking for site packages at: {venv_site_pkg_file_path}')

    if not os.path.exists(venv_site_pkg_file_path):
        exe_file_path = sys.executable
        venv_file_path = os.path.join(os.path.dirname(__file__), '.venv')
        logger.debug(f'Site packages not found, now installing venv at: {venv_file_path}')
        subprocess.run([exe_file_path, '-m' 'venv', venv_file_path])

        _venv_exe_file_path = os.path.join(os.path.dirname(__file__), '.venv/Scripts/python.exe')
        venv_pip_file_path = os.path.join(os.path.dirname(__file__), '.venv/Scripts/pip.exe')

        subprocess.run([venv_pip_file_path, 'install', 'UnityPy'])
    else:
        logger.debug(f'Site packages found at: {venv_site_pkg_file_path}, skipping install')
    sys.path.append(venv_site_pkg_file_path)

    bpy.utils.register_class(TCA_Exporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    logger.debug('Addon registration complete')

def unregister():
    bpy.utils.unregister_class(TCA_Exporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    venv_file_path = os.path.join(os.path.dirname(__file__), '.venv')
    
    logger.debug(f'Removing venv at : {venv_file_path}')

    try:
        subprocess.run(['rmdir', f'"{venv_file_path}"', '/q', '/s'])#
    except(Exception):
        logger.warn('Failed to remove .venv')

    logger.debug('Unregistration completed')