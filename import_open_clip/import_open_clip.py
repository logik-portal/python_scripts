'''
Script Name: Import Open Clip
Script Version: 2.0
Flame Version: 2020.3
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 05.26.19
Update Date: 05.25.21

Custom Action Type: Batch

Description:

    Imports open clip created by selected write node into Batch/Open clip schematic reel
    or Batch Renders shelf reel

    Right-click on write node in batch -> Import... -> Import Openclip to Batch
    Right-click on write node in batch -> Import... -> Import Openclip to Renders Reel

To install:

    Copy script into /opt/Autodesk/shared/python/import_open_clip

Updates:

v2.0 05.25.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.5 09.19.20

    Pops up message box when open clip doesn't exist

v1.4 07.01.20

    Open clips can be imported to Batch Renders shelf reel - Batch group must have shelf reel called Batch Renders

    Added token for version name

v1.3 11.01.19

    Right-click menu now appears under Import...

v1.1 09.29.19

    Code cleanup
'''

from __future__ import print_function

VERSION = 'v2.0'

class Import(object):

    def __init__(self, selection, *args, **kwargs):
        import flame
        import os

        self.batchgroup = flame.batch
        print ('batchgroup_name:', self.batchgroup.name)

        # Translate write node tokens

        for self.write_node in selection:
            media_path = str(self.write_node.media_path)[1:-1]
            print ('media path:', media_path)
            openclip_path = str(self.write_node.create_clip_path)[1:-1]
            project = str(flame.project.current_project.name)
            batch_iteration = str(flame.batch.current_iteration.name)
            batch_name = str(flame.batch.name)[1:-1]
            ext = str(self.write_node.format_extension)[1:-1]
            name = str(self.write_node.name)[1:-1]
            shot_name = str(self.write_node.shot_name)[1:-1]

            token_dict = {'<project>': project,
                          '<batch iteration>': batch_iteration,
                          '<batch name>': batch_name,
                          '<ext>': ext,
                          '<name>': name,
                          '<shot name>':shot_name,
                          '<version name>': batch_iteration,}

            for token, value in token_dict.items():
                openclip_path = openclip_path.replace(token, value)
            self.openclip_path = os.path.join(media_path, openclip_path) + '.clip'

    def batch_import(self):
        import flame
        import os

        if not os.path.isfile(self.openclip_path):
            return message_box('Open Clip not found')

        # Import openclip to batch
        # Create Openclip schematic reel if doesn't exist

        if 'Openclip' not in [r.name for r in flame.batch.reels]:
            flame.batch.create_reel('Openclip')

        # Import open clip

        self.openclip = flame.batch.import_clip(self.openclip_path, 'Openclip')

        print ('\n>>> imported %s <<<\n' % str(self.write_node.name)[1:-1])

    def renders_reel_import(self):
        import flame
        import os

        if not os.path.isfile(self.openclip_path):
            return message_box('Open Clip not found')

        # Import open clip to Batch Renders reel
        # Create Batch Renders shelf reel if doesn't exist

        if 'Batch Renders' not in [r.name for r in flame.batch.shelf_reels]:
            flame.batch.create_shelf_reel('Batch Renders')

        # Create temp reel for open clip import

        flame.batch.create_reel('temp_openclip')

        # Import open clip

        flame.batch.import_clip(self.openclip_path, 'temp_openclip')

        # Get reel numbers

        renders_reel_num = [r for r, x in enumerate(self.batchgroup.shelf_reels) if x.name == 'Batch Renders'][0]
        openclip_reel_num = [r for r, x in enumerate(self.batchgroup.reels) if x.name == 'temp_openclip'][0]

        # Move imported clip from temp reel to Batch Renders Reel

        flame.media_panel.move(self.batchgroup.reels[openclip_reel_num].clips[0], self.batchgroup.shelf_reels[renders_reel_num])

        # Delete temp reel

        flame.delete(self.batchgroup.reels[openclip_reel_num])

        print ('\n>>> imported %s <<<\n' % str(self.write_node.name)[1:-1])

def message_box(message):
    from PySide2 import QtWidgets, QtCore

    msg_box = QtWidgets.QMessageBox()
    msg_box.setText('<center>%s' % message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 24))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; color: #9a9a9a}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
    msg_box.exec_()

    message = message.replace('<br>', '-')

    print ('\n>>> %s <<<\n' % message)

def batch_import(selection):

    print ('\n', '>' * 20, 'import openclip %s - batch import' % VERSION, '<' * 20, '\n')

    script = Import(selection)
    script.batch_import()

def renders_reel_import(selection):

    print ('\n', '>' * 20, 'import openclip %s - batch renders reel import' % VERSION, '<' * 20, '\n')

    script = Import(selection)
    script.renders_reel_import()

def scope_batch_renders_reel(selection):
    import flame

    for item in selection:
        if item.type == 'Write File':
            if 'Batch Renders' in [r.name for r in flame.batch.shelf_reels]:
                return True
    return False

def scope_write_node(selection):

    for item in selection:
        if item.type == 'Write File':
            return True
    return False

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Import...',
            'actions': [
                {
                    'name': 'Import Open Clip to Batch',
                    'isVisible': scope_write_node,
                    'execute': batch_import,
                    'minimumVersion': '2020.3'
                },
                {
                    'name': 'Import Open Clip to Renders Reel',
                    'isVisible': scope_batch_renders_reel,
                    'execute': renders_reel_import,
                    'minimumVersion': '2020.3'
                }
            ]
        }
    ]
