'''
Script Name: Import Write Node
Script Version: 2.3
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 05.26.19
Update Date: 04.13.22

Custom Action Type: Batch

Description:

    Import open clip created by selected write node into batch schematic reel or
    shelf reel or auto-import write node image sequence when render is complete

Menus:

    Setup:

        Flame Main Menu -> pyFlame -> Import Write Node Setup

    To import open clips:

        Right-click on write file node in batch -> Import... -> Import Open Clip to Batch
        Right-click on write file node in batch -> Import... -> Import Open Clip to Renders Reel

To install:

    Copy script into /opt/Autodesk/shared/python/import_write_node

Updates:

    v2.3 04.13.22

        Script renamed to: Import Write Node

        Updated UI for Flame 2023

        Moved UI widgets to external file

    v2.1 09.24.21

        Added token translation for project nickname

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

from PySide2 import QtWidgets
import xml.etree.ElementTree as ET
import os, ast
from flame_widgets_import_write_node import FlameLabel, FlameLineEdit, FlamePushButton, FlameButton, FlameMessageWindow, FlameWindow

VERSION = 'v2.3'

SCRIPT_PATH = '/opt/Autodesk/shared/python/import_write_node'

class ImportWriteNode(object):

    def __init__(self, selection, *args, **kwargs):
        import flame

        print ('\n')
        print ('>' * 20, f'import open clip {VERSION}', '<' * 20, '\n')

        self.selection = selection

        # Load config settings

        self.config()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('import_write_node_settings'):
                self.schematic_reel = setting.find('schematic_reel').text
                self.shelf_reel = setting.find('shelf_reel').text
                self.import_after_render = ast.literal_eval(setting.find('import_after_render').text)
                self.schematic_reel_import = ast.literal_eval(setting.find('schematic_reel_import').text)
                self.shelf_reel_import = ast.literal_eval(setting.find('shelf_reel_import').text)
                self.import_again = ast.literal_eval(setting.find('import_again').text)

            print ('--> config loaded \n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder:<br><br>{self.config_path}<br><br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file \n')

                config = '''
<settings>
    <import_write_node_settings>
        <schematic_reel>Renders</schematic_reel>
        <shelf_reel>Batch Renders</shelf_reel>
        <import_after_render>True</import_after_render>
        <schematic_reel_import>True</schematic_reel_import>
        <shelf_reel_import>True</shelf_reel_import>
        <import_again>False</import_again>
    </import_write_node_settings>
</settings>'''

                with open(self.config_xml, 'a') as config_file:
                    config_file.write(config)
                    config_file.close()

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        if os.path.isfile(self.config_xml):
            get_config_values()
        else:
            create_config_file()
            if os.path.isfile(self.config_xml):
                get_config_values()

    def translate_write_node_path(self):
        import flame

        print ('--> translating write node path:\n')

        # Translate write node tokens

        for self.write_node in self.selection:
            media_path = str(self.write_node.media_path)[1:-1]
            print ('    media path:', media_path)
            pattern = str(self.write_node.create_clip_path)[1:-1]
            print ('    pattern:', pattern)
            project = str(flame.project.current_project.name)
            project_nickname = str(flame.project.current_project.nickname)
            batch_iteration = str(flame.batch.current_iteration.name)
            batch_name = str(flame.batch.name)[1:-1]
            ext = str(self.write_node.format_extension)[1:-1]
            name = str(self.write_node.name)[1:-1]
            shot_name = str(self.write_node.shot_name)[1:-1]

            token_dict = {'<project>': project,
                          '<project nickname>': project_nickname,
                          '<batch iteration>': batch_iteration,
                          '<batch name>': batch_name,
                          '<ext>': ext,
                          '<name>': name,
                          '<shot name>':shot_name,
                          '<version name>': batch_iteration,}

            for token, value in token_dict.items():
                pattern = pattern.replace(token, value)

            translated_path = os.path.join(media_path, pattern) + '.clip'
            print ('    open clip translated path:', translated_path, '\n')

            return translated_path

    # -------------------------------------------- #

    def setup(self):

        def save_config():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            schematic_reel = root.find('.//schematic_reel')
            schematic_reel.text = self.schematic_reel_lineedit.text()

            shelf_reel = root.find('.//shelf_reel')
            shelf_reel.text = self.shelf_reel_lineedit.text()

            import_after_render = root.find('.//import_after_render')
            import_after_render.text = str(self.import_after_render_push_button.isChecked())

            schematic_reel_import = root.find('.//schematic_reel_import')
            schematic_reel_import.text = str(self.schematic_reel_import_push_button.isChecked())

            shelf_reel_import = root.find('.//shelf_reel_import')
            shelf_reel_import.text = str(self.shelf_reel_import_push_button.isChecked())

            import_again = root.find('.//import_again')
            import_again.text = str(self.import_again_push_button.isChecked())

            xml_tree.write(self.config_xml)

            print ('--> config saved \n')

            self.setup_window.close()

            print ('done.\n')

        gridbox = QtWidgets.QGridLayout()
        self.setup_window = FlameWindow(f'Import Write Node - Setup <small>{VERSION}</small>', gridbox, 1000, 360)

        # Labels

        self.import_settings_label = FlameLabel('Import Destination Reels', label_type='underline')
        self.auto_import_options_label = FlameLabel('Write File Image Sequence Automatic Import Options', label_type='underline')
        self.schematic_reel_label = FlameLabel('Schematic Reel Name', label_width=110)
        self.batch_shelf_label = FlameLabel('Batch Shelf Name', label_width=110)
        self.import_dest_label = FlameLabel('Import Destination', label_width=110)
        self.clip_exists_label = FlameLabel('If clip exists in dest', label_width=110)

        # LineEdit

        self.schematic_reel_lineedit = FlameLineEdit(self.schematic_reel, max_width=300)
        self.shelf_reel_lineedit = FlameLineEdit(self.shelf_reel, max_width=300)

        # Push buttons

        def import_toggle():

            if self.import_after_render_push_button.isChecked():
                self.schematic_reel_import_push_button.setEnabled(True)
                self.shelf_reel_import_push_button.setEnabled(True)
                self.import_dest_label.setEnabled(True)
                self.clip_exists_label.setEnabled(True)
                self.import_again_push_button.setEnabled(True)
            else:
                self.schematic_reel_import_push_button.setEnabled(False)
                self.shelf_reel_import_push_button.setEnabled(False)
                self.shelf_reel_import_push_button.setEnabled(False)
                self.import_dest_label.setEnabled(False)
                self.clip_exists_label.setEnabled(False)
                self.import_again_push_button.setEnabled(False)

        self.import_after_render_push_button = FlamePushButton('Import After Render', self.import_after_render)
        self.import_after_render_push_button.clicked.connect(import_toggle)

        self.schematic_reel_import_push_button = FlamePushButton('Schematic Reel', self.schematic_reel_import)
        self.shelf_reel_import_push_button = FlamePushButton('Shelf Reel', self.shelf_reel_import)
        self.import_again_push_button = FlamePushButton('Import Again', self.import_again)

        #  Buttons

        self.save_btn = FlameButton('Save', save_config)
        self.cancel_btn = FlameButton('Cancel', self.setup_window.close)

        import_toggle()

        # Setup window layout

        gridbox.setMargin(20)

        gridbox.setRowMinimumHeight(1, 30)
        gridbox.setRowMinimumHeight(3, 30)
        gridbox.setRowMinimumHeight(6, 30)

        gridbox.setColumnMinimumWidth(3, 25)

        gridbox.addWidget(self.import_settings_label, 0 ,0, 1, 2)

        gridbox.addWidget(self.schematic_reel_label, 1 ,0)
        gridbox.addWidget(self.schematic_reel_lineedit, 1, 1)

        gridbox.addWidget(self.batch_shelf_label, 2 ,0)
        gridbox.addWidget(self.shelf_reel_lineedit, 2 ,1)

        gridbox.addWidget(self.auto_import_options_label, 0 ,4, 1, 3)

        gridbox.addWidget(self.import_after_render_push_button, 1 ,4)

        gridbox.addWidget(self.import_dest_label, 2 ,5)

        gridbox.addWidget(self.schematic_reel_import_push_button, 2 ,6)
        gridbox.addWidget(self.shelf_reel_import_push_button, 3 ,6)

        gridbox.addWidget(self.clip_exists_label, 4 ,5)
        gridbox.addWidget(self.import_again_push_button, 4 ,6)

        gridbox.addWidget(self.save_btn, 12, 6)
        gridbox.addWidget(self.cancel_btn, 13, 6)

        self.setup_window.show()

        return self.setup_window

    def import_to_schematic_reel(self):

        open_clip_path = self.translate_write_node_path()

        if not os.path.isfile(open_clip_path):
            return FlameMessageWindow('Import Write Node - Error', 'error', 'Open clip not found<br><br>Write node export path:<br><br>' + open_clip_path)

        self.create_schematic_reel()

        self.import_schematic_reel(open_clip_path)

    def import_to_shelf_reel(self):

        open_clip_path = self.translate_write_node_path()

        if not os.path.isfile(open_clip_path):
            return FlameMessageWindow('Import Write Node - Error', 'error', 'Open clip not found')

        self.create_shelf_reel()

        self.import_shelf_reel(open_clip_path)

    def post_render_import(self):

        if self.import_after_render:

            image_seq_path = os.path.join(self.selection["exportPath"], self.selection["resolvedPath"])

            clip_name = image_seq_path.rsplit('/', 1)[1]
            clip_name = clip_name.rsplit('.', 2)[0]

            # Import image seq to schematic/shelf reel if Import After Render is selected in Setup
            # If Import Again is selected, import clip again
            # If not then check if clip is already imported to reel, if not, import

            # Import to schematic reel

            if self.schematic_reel_import:
                self.create_schematic_reel()

                if self.import_again:
                    self.import_schematic_reel(image_seq_path)
                else:
                    if not [clip for clip in self.schematic_reel_for_import.clips if clip.name == clip_name]:
                        self.import_schematic_reel(image_seq_path)

            # Import to shelf reel

            if self.shelf_reel_import:
                self.create_shelf_reel()

                # Import to shelf reel

                if self.import_again:
                    self.import_shelf_reel(image_seq_path)
                else:
                    if not [clip for clip in self.shelf_reel_for_import.clips if clip.name == clip_name]:
                        self.import_shelf_reel(image_seq_path)

            print ('--> imported write node image sequence \n')

            print ('done.\n')

    # -------------------------------------------- #

    def create_schematic_reel(self):
        import flame

        # Create Open clip schematic reel if doesn't exist

        if self.schematic_reel not in [reel.name for reel in flame.batch.reels]:
            self.schematic_reel_for_import = flame.batch.create_reel(self.schematic_reel)
        else:
            self.schematic_reel_for_import = [reel for reel in flame.batch.reels if reel.name == self.schematic_reel][0]

    def create_shelf_reel(self):
        import flame

        # Create Batch Renders shelf reel if doesn't exist

        if self.shelf_reel not in [reel.name for reel in flame.batch.shelf_reels]:
            self.shelf_reel_for_import = flame.batch.create_shelf_reel(self.shelf_reel)
        else:
            self.shelf_reel_for_import = import_reel = [reel for reel in flame.batch.shelf_reels if reel.name == self.shelf_reel][0]

    def import_schematic_reel(self, path):
        import flame

        # Import to schematic reel

        flame.batch.import_clip(path, self.schematic_reel)

    def import_shelf_reel(self, path):
        import flame

        # Import to shelf reel

        flame.import_clips(path, self.shelf_reel_for_import)

# -------------------------------------------- #

def schematic_import(selection):

    script = ImportWriteNode(selection)
    script.import_to_schematic_reel()

    print ('--> open clip imported \n')
    print ('done.\n')

def shelf_import(selection):

    script = ImportWriteNode(selection)
    script.import_to_shelf_reel()

    print ('--> open clip imported \n')
    print ('done.\n')

def setup(selection):

    script = ImportWriteNode(selection)
    script.setup()

# -------------------------------------------- #

def scope_write_node(selection):

    for item in selection:
        if item.type == 'Write File':
            return True
    return False

# -------------------------------------------- #

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Import Write Node Setup',
                    'execute': setup,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Import...',
            'actions': [
                {
                    'name': 'Import Open Clip to Batch',
                    'isVisible': scope_write_node,
                    'execute': schematic_import,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Import Open Clip to Renders Reel',
                    'isVisible': scope_write_node,
                    'execute': shelf_import,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def batch_export_end(info, userData, *args, **kwargs):

    script = ImportWriteNode(info)
    script.post_render_import()
