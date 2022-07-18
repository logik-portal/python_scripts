'''
Script Name: Create Shot
Script Version: 4.7
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 06.09.18
Update Date: 05.02.22

Custom Action Type: Media Panel / Media Hub / Timeline

Description:

    Create custom shot folders, batch groups, desktops, and system folders.

    Structures of the shot folders, batch groups, reel groups, desktops, and system folders can all be customized
    in Create Shot Setup. These can be saved as a preset that can either be applied globally across all
    Flame projects or Flame projects individually.

Menus:

    Flame Main Menu:

        Flame Main Menu -> pyFlame -> Create Shot Setup

    Media Panel:

        Right-click anywhere in Media Panel -> Create Shot... -> Folders
        Right-click on selected clips in Media Panel -> Create Shot... -> Clips to Shot
        Right-click on selected clips in Media Panel -> Create Shot... -> Clips to Shot - All Clips / One Shot
        Right-click on selected clips in Media Panel -> Create Shot... -> Custom Shots

    Media Hub Files:

        Right-click anywhere in Media Hub Files -> Create Shot... -> Folders
        Right-click on selected files in Media Hub Files -> Create Shot... -> Import to Shot
        Right-click on selected files in Media Hub Files -> Create Shot... -> Import to Shot - All Clips / One Batch

    Timeline:

        Right-click on selected clips -> Create Shot... -> Clips to Shot
        Right-click on selected clips -> Create Shot... -> Clips to Shot w/Timeline FX
        Right-click on selected clips -> Create Shot... -> Custom Shots

To install:

    Copy script into /opt/Autodesk/shared/python/create_shot

Updates:

    v4.7 05.02.22

        Fixed error when importing plates to create shots

    v4.6 03.24.22

        Moved UI widgets to external file

    v4.5 02.27.22

        Updated UI for Flame 2023

    v4.4 02.09.22

        Shots can be created from timeline - clips will be extracted with or without timeline fx

    v4.3 02.05.22

        Added ability to export plates when creating file system shot folders

        Fixed issues with render/write nodes not rendering properly when batch start frame was set to anything other than 1

        Removed menus to create shots from either shot name or clip name. This can now be set in the preset options.

    v4.2 01.06.22

        Added new window to create, duplicate, edit, delete presets

        Render/Write file nodes added from batch templates now get render range, timecode, and shot name from shot clip

        Render nodes now get Tape Name from clip

        Updated getting Flame version

        Added project nickname token to write node setup token menus

        Write file compression button properly updates now when reloading write node setup window

    v4.1 08.19.21

        Major rewrite / Merged Shot Folder Creator script with Clip to Batch Group script.

        Config file now in xml format

        Added help button

        Added ability to create shots by selecting clips in Media Panel or Media Hub. Selected clips will be added to folders and
        batch groups.

        Settings are applied globally through settings in Setup. Custom settings can be applied through Custom Shots menu when
        right clicking on clips

        Shots can now be created by selecting clips in Media Panel or Media Hub file view.

        Batch templates can be applied when creating shot batch groups

        Added compression options to write node format option in the write node setup window

        Shot name is now added to render/write node

        Destination for newly created batch groups can now be set when only creating batch groups. Destination can be current
        desktop or a new library

        Folders, Schematic/Shelf/Reel Group reels will not automatically sort when being created. A button has been added to the setup
        menu to manually apply sorting.

        Destination folders and schematic reels can be set for clips in the Setup window using either the Set Clip Dest button or by
        right-clicking on a folder or schematic reel.

    v4.0 06.03.21

        Updated to be compatible with Flame 2022/Python 3.7

        UI Updates/Calculator fixes

        Fixed adding folders to in setup to file system folder structure

        Added ability to create shot desktops

    v3.2 11.11.20

        Updates to paths and description for Logik Portal

    v3.1 11.10.20

        Fixed bug when creating system shot folders that incorrectly used media hub folder template - thanks John!

    v3.0 10.13.20

        Updated and simplified UI

        Added ability to create file system shot folders

        Code cleanup
'''

import os, re, ast, shutil, webbrowser, platform, subprocess
from functools import partial
import xml.etree.ElementTree as ET
from PySide2 import QtWidgets, QtCore, QtGui
from flame_widgets_create_shot import FlameButton, FlameLabel, FlameLineEdit, FlamePushButton, FlamePushButtonMenu, FlameTokenPushButton, FlameSlider, FlameWindow, FlameMessageWindow

VERSION = 'v4.7'

SCRIPT_PATH = '/opt/Autodesk/shared/python/create_shot'

# ------------------------------------- #

class CreateShotFolders(object):

    def __init__(self, selection):
        import flame

        print ('''
  _____                _         _____ _           _
 / ____|              | |       / ____| |         | |
| |     _ __ ___  __ _| |_ ___ | (___ | |__   ___ | |_
| |    | '__/ _ \/ _` | __/ _ \ \___ \| '_ \ / _ \| __|
| |____| | |  __/ (_| | ||  __/ ____) | | | | (_) | |_
 \_____|_|  \___|\__,_|\__\___||_____/|_| |_|\___/ \__|
        ''')

        print ('>' * 19, f'create shot {VERSION}', '<' * 19, '\n')

        self.selection = selection

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')
        self.preset_path = os.path.join(self.config_path, 'preset')
        self.project_config_path = os.path.join(self.config_path, 'project')

        # Load config file

        self.config()

        print ('--> config loaded \n')

        # Get flame variables

        self.ws = flame.projects.current_project.current_workspace
        self.desktop = self.ws.desktop
        self.current_flame_tab = flame.get_current_tab()

        self.project_name = flame.projects.current_project.name
        self.project_nick_name = flame.projects.current_project.nickname
        self.flame_prj_name = self.project_name # Needed for preset selector window

        # Get flame version

        self.flame_version = flame.get_version()

        if 'pr' in self.flame_version:
            self.flame_version = self.flame_version.rsplit('.pr', 1)[0]

        if len(self.flame_version) > 6:
            self.flame_version = self.flame_version[:6]
        self.flame_version = float(self.flame_version)
        print ('flame_version:', self.flame_version, '\n')

        self.reel_group_tree = ''
        self.shot_folder_name = ''
        self.batch_group = ''
        self.lib = ''

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get global setting

            for setting in root.iter('global_setting'):
                self.global_default = setting.find('global_default').text

            # Get UI settings

            for setting in root.iter('create_shot_ui_settings'):

                self.shot_naming = setting.find('shot_naming').text
                self.num_of_shots = int(setting.find('number_of_shots').text)
                self.starting_shot = int(setting.find('starting_shot').text)
                self.shot_increments = int(setting.find('shot_increments').text)
                self.create_custom_folders = ast.literal_eval(setting.find('create_folders').text)
                self.create_custom_batch_groups = ast.literal_eval(setting.find('create_batch_groups').text)
                self.create_custom_desktops = ast.literal_eval(setting.find('create_desktops').text)
                self.create_custom_system_folders = ast.literal_eval(setting.find('create_system_folders').text)
                self.reveal_in_finder = ast.literal_eval(setting.find('reveal_in_finder').text)

            # Settings for Custom Shot from Selected clips UI

            for setup_setting in root.iter('custom_ui'):
                self.all_clips = ast.literal_eval(setup_setting.find('all_clips').text)
                self.shot_name = ast.literal_eval(setup_setting.find('shot_name').text)
                self.clip_name = ast.literal_eval(setup_setting.find('clip_name').text)
                self.custom_folders = ast.literal_eval(setup_setting.find('custom_folders').text)
                self.custom_batch_group = ast.literal_eval(setup_setting.find('custom_batch_group').text)
                self.custom_desktop = ast.literal_eval(setup_setting.find('custom_desktop').text)
                self.custom_system_folders = ast.literal_eval(setup_setting.find('custom_system_folders').text)
                self.custom_export_plates = ast.literal_eval(setup_setting.find('custom_export_plates').text)
                self.custom_export_preset = setup_setting.find('custom_export_preset').text
                self.custom_foreground_export = ast.literal_eval(setup_setting.find('custom_foreground_export').text)
                self.custom_system_folders_path = setup_setting.find('custom_system_folders_path').text
                self.custom_apply_batch_template = ast.literal_eval(setup_setting.find('custom_apply_batch_template').text)
                self.custom_batch_template_path = setup_setting.find('custom_batch_template_path').text
                self.custom_batch_group_dest = setup_setting.find('custom_batch_group_dest').text
                self.custom_batch_start_frame = int(setup_setting.find('custom_batch_start_frame').text)
                self.custom_batch_additional_naming = setup_setting.find('custom_batch_additional_naming').text

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.preset_path)
                    os.makedirs(self.project_config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder:<br>{self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file \n')

                config = """
<settings>
    <global_setting>
        <global_default></global_default>
    </global_setting>
    <create_shot_ui_settings>
        <shot_naming>PYT_&lt;ShotNum####&gt;</shot_naming>
        <number_of_shots>10</number_of_shots>
        <starting_shot>10</starting_shot>
        <shot_increments>10</shot_increments>
        <create_folders>True</create_folders>
        <create_batch_groups>False</create_batch_groups>
        <create_desktops>False</create_desktops>
        <create_system_folders>False</create_system_folders>
        <reveal_in_finder>False</reveal_in_finder>
    </create_shot_ui_settings>
    <custom_ui>
        <all_clips>False</all_clips>
        <shot_name>True</shot_name>
        <clip_name>False</clip_name>
        <custom_folders>True</custom_folders>
        <custom_batch_group>False</custom_batch_group>
        <custom_desktop>False</custom_desktop>
        <custom_system_folders>False</custom_system_folders>
        <custom_export_plates>False</custom_export_plates>
        <custom_export_preset>Select Preset</custom_export_preset>
        <custom_foreground_export>False</custom_foreground_export>
        <custom_system_folders_path>/opt/Autodesk</custom_system_folders_path>
        <custom_apply_batch_template>False</custom_apply_batch_template>
        <custom_batch_template_path>/opt/Autodesk</custom_batch_template_path>
        <custom_batch_start_frame>1</custom_batch_start_frame>
        <custom_batch_additional_naming>_comp</custom_batch_additional_naming>
        <custom_batch_group_dest>Desktop</custom_batch_group_dest>
    </custom_ui>
</settings>"""

                with open(self.config_xml, 'a') as config_file:
                    config_file.write(config)
                    config_file.close()

        if os.path.isfile(self.config_xml):
            get_config_values()
        else:
            create_config_file()
            if os.path.isfile(self.config_xml):
                get_config_values()

    # ------------------------------------- #
    # Preset Selector

    def load_preset(self, preset_path):

        print ('Loading preset:\n')

        print ('    preset_path:', preset_path, '\n')

        # Load settings from preset file

        xml_tree = ET.parse(preset_path)
        root = xml_tree.getroot()

        # Assign values from preset file to variables

        for setting in root.iter('create_shot_preset'):
            self.preset_name = setting.find('preset_name').text
            self.shot_name_from = setting.find('shot_name_from').text

            self.folder_dict = ast.literal_eval(setting.find('shot_folders').text)
            self.file_system_folder_dict = ast.literal_eval(setting.find('file_system_folders').text)
            self.schematic_reel_dict = ast.literal_eval(setting.find('schematic_reels').text)
            self.shelf_reel_dict = ast.literal_eval(setting.find('shelf_reels').text)
            self.reel_group_dict = ast.literal_eval(setting.find('reel_group_reels').text)

            self.add_reel_group = ast.literal_eval(setting.find('add_reel_group').text)
            self.add_render_node = ast.literal_eval(setting.find('add_render_node').text)
            self.add_write_file_node = ast.literal_eval(setting.find('add_write_node').text)

            self.export_dest_folder = setting.find('export_dest_folder').text

            self.write_file_media_path = setting.find('write_file_media_path').text
            self.write_file_pattern = setting.find('write_file_pattern').text
            self.write_file_create_open_clip = ast.literal_eval(setting.find('write_file_create_open_clip').text)
            self.write_file_include_setup = ast.literal_eval(setting.find('write_file_include_setup').text)
            self.write_file_create_open_clip_value = setting.find('write_file_create_open_clip_value').text
            self.write_file_include_setup_value = setting.find('write_file_include_setup_value').text
            self.write_file_image_format = setting.find('write_file_image_format').text
            self.write_file_compression = setting.find('write_file_compression').text
            self.write_file_padding = setting.find('write_file_padding').text
            self.write_file_frame_index = setting.find('write_file_frame_index').text
            self.write_file_iteration_padding = setting.find('write_file_iteration_padding').text
            self.write_file_version_name = setting.find('write_file_version_name').text

            self.create_shot_type_folders = ast.literal_eval(setting.find('create_shot_type_folders').text)
            self.create_shot_type_batch_group = ast.literal_eval(setting.find('create_shot_type_batch_group').text)
            self.create_shot_type_desktop = ast.literal_eval(setting.find('create_shot_type_desktop').text)
            self.create_shot_type_system_folders = ast.literal_eval(setting.find('create_shot_type_system_folders').text)
            # self.create_shot_cache_on_import = ast.literal_eval(setting.find('create_shot_cache_on_import').text)
            self.create_shot_export_plates = ast.literal_eval(setting.find('create_shot_export_plates').text)
            self.create_shot_export_plate_preset = setting.find('create_shot_export_plate_preset').text
            if not self.create_shot_export_plate_preset:
                self.create_shot_export_plate_preset = 'Select Preset'
            self.create_shot_fg_export = ast.literal_eval(setting.find('create_shot_fg_export').text)

            self.system_shot_folders_path = setting.find('system_shot_folders_path').text
            self.clip_dest_folder = setting.find('clip_destination_folder').text
            self.clip_dest_reel = setting.find('clip_destination_reel').text
            self.apply_batch_template = ast.literal_eval(setting.find('setup_batch_template').text)
            self.batch_template_path = setting.find('setup_batch_template_path').text
            self.batch_group_dest = setting.find('setup_batch_group_dest').text
            self.batch_start_frame = int(setting.find('setup_batch_start_frame').text)
            self.batch_additional_naming = setting.find('setup_batch_additional_naming').text

        # Convert reel dictionaries to lists

        self.schematic_reels = self.convert_reel_dict(self.schematic_reel_dict)
        self.shelf_reels = self.convert_reel_dict(self.shelf_reel_dict)
        self.reel_group = self.convert_reel_dict(self.reel_group_dict)

        print (f'    preset loaded: {self.preset_name}\n')

    def load_preset_values(self):

        presets_exist = os.listdir(self.preset_path)
        if not presets_exist:
            FlameMessageWindow('Create Preset', 'message', 'No Create Shot presets exist.<br><br>Hit Ok to open script setup.<br><br>Once a preset is saved, try again.')
            self.preset_selector()
            return False

        # Check for existing project preset

        try:
            project_preset = [f[:-4] for f in os.listdir(self.project_config_path) if f[:-4] == self.flame_prj_name][0]
        except:
            project_preset = False

        if project_preset:
            preset_name = self.load_project_preset(os.path.join(self.project_config_path, project_preset + '.xml'))
            preset_path = os.path.join(self.preset_path, preset_name + '.xml')
            self.load_preset(preset_path)
        else:
            preset_path = os.path.join(self.preset_path, self.global_default + '.xml')
            self.load_preset(preset_path)

        return True

    def load_project_preset(self, project_preset_path):

        # Load settings from project file

        xml_tree = ET.parse(project_preset_path)
        root = xml_tree.getroot()

        # Assign values from config file to variables

        for setting in root.iter('global_setting'):
            preset_name = setting.find('preset_name').text

        return preset_name

    def preset_selector(self):

        def build_preset_list():

            self.config()

            preset_list = []

            for f in os.listdir(self.preset_path):
                f = f[:-4]
                if f == self.global_default:
                    f = f + '*'
                preset_list.append(f)

            return preset_list

        def load_config():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('global_setting'):
                self.global_default = setting.find('global_default').text

            # Check for existing project preset

            try:
                project_preset = [f[:-4] for f in os.listdir(self.project_config_path) if f[:-4] == self.flame_prj_name][0]
            except:
                project_preset = False

            if project_preset:

                # Get current project preset name from project file

                preset_name = self.load_project_preset(os.path.join(self.project_config_path, project_preset + '.xml'))

                if preset_name == self.global_default:
                    preset_name = preset_name + '*'

                self.current_preset_push_btn.setText(preset_name)
            else:
                if os.listdir(self.preset_path):
                    self.current_preset_push_btn.setText(self.global_default + '*')
                else:
                    self.current_preset_push_btn.setText('')

            print ('--> config loaded \n')

        def new_preset():

            # Assign default settings

            self.preset_name = ''
            self.shot_name_from = 'Shot Name'

            self.folder_dict = {'Shot_Folder': {'Elements': {}, 'Plates': {}, 'Ref': {}, 'Renders': {}}}
            self.file_system_folder_dict = {'Shot_Folder': {'Elements': {}, 'Plates': {}, 'Ref': {}, 'Renders': {}}}
            self.schematic_reel_dict = {'Schematic Reels': {'Plates': {}, 'PreRenders': {}, 'Elements': {}, 'Ref': {}}}
            self.shelf_reel_dict = {'Shelf Reels': {'Batch Renders': {}}}
            self.reel_group_dict = {'Reels': {'Reel 1': {}, 'Reel 2': {}, 'Reel 3': {}, 'Reel 4': {}}}

            self.export_dest_folder = 'Shot_Folder/Plates'

            self.add_reel_group = True
            self.add_render_node = True
            self.add_write_file_node = False

            self.write_file_media_path = '/opt/Autodesk'
            self.write_file_pattern = '<name>'
            self.write_file_create_open_clip = True
            self.write_file_include_setup = True
            self.write_file_create_open_clip_value = '<name>'
            self.write_file_include_setup_value = '<name>'
            self.write_file_image_format = 'Dpx 10-bit'
            self.write_file_compression = 'Uncompressed'
            self.write_file_padding = '4'
            self.write_file_frame_index = 'Use Start Frame'
            self.write_file_iteration_padding = '2'
            self.write_file_version_name = 'v<version>'

            self.create_shot_type_folders = True
            self.create_shot_type_batch_group = False
            self.create_shot_type_desktop = False
            self.create_shot_type_system_folders = False
            self.system_shot_folders_path = '/opt/Autodesk'

            self.create_shot_export_plates = False
            self.create_shot_export_plate_preset = 'Select Preset'
            self.create_shot_fg_export = False

            self.clip_dest_folder = 'Plates'
            self.clip_dest_reel = 'Plates'
            self.apply_batch_template = False
            self.batch_template_path = '/opt/Autodesk'
            self.batch_group_dest = 'Desktop'
            self.batch_start_frame = 1
            self.batch_additional_naming = '_comp'

            # Convert reel dictionaries to lists

            self.schematic_reels = self.convert_reel_dict(self.schematic_reel_dict)
            self.shelf_reels = self.convert_reel_dict(self.shelf_reel_dict)
            self.reel_group = self.convert_reel_dict(self.reel_group_dict)

            self.setup()

        def edit_preset():

            preset_name_text = self.current_preset_push_btn.text()
            if preset_name_text.endswith('*'):
                preset_name_text = preset_name_text[:-1]

            if self.current_preset_push_btn.text():

                preset_path = os.path.join(self.preset_path, preset_name_text + '.xml')

                self.load_preset(preset_path)

                self.setup()

            else:
                FlameMessageWindow('Error', 'error', 'No presets exist to edit')

        def duplicate_preset():

            def add_copy_to_filename(preset_name):

                preset_name = preset_name + ' copy'

                return preset_name

            if self.current_preset_push_btn.text():

                current_preset = self.current_preset_push_btn.text()
                if current_preset.endswith('*'):
                    current_preset = current_preset[:-1]

                # Add 'copy' to the end of the new file being created.

                existing_presets = [f[:-4] for f in os.listdir(self.preset_path)]

                new_preset_name = add_copy_to_filename(current_preset)

                while new_preset_name in existing_presets:
                    new_preset_name = add_copy_to_filename(new_preset_name)

                # Duplicate preset

                source_file = os.path.join(self.preset_path, current_preset + '.xml')
                dest_file = os.path.join(self.preset_path, new_preset_name + '.xml')
                shutil.copyfile(source_file, dest_file)

                self.selector_window.close()

                # Save new preset name to duplicate preset file

                xml_tree = ET.parse(dest_file)
                root = xml_tree.getroot()

                preset_name = root.find('.//preset_name')
                preset_name.text = new_preset_name

                xml_tree.write(dest_file)

                print (f'Preset duplicate created: {new_preset_name}\n')

                self.preset_selector()

                self.current_preset_push_btn.setText(new_preset_name)

        def delete_preset():

            def delete():

                os.remove(preset_path)

                self.selector_window.close()

                print (f'--> Preset deleted: {preset_name} \n')

                self.preset_selector()

            preset_name = self.current_preset_push_btn.text()
            preset_path = os.path.join(self.preset_path, preset_name + '.xml')

            if preset_name.endswith('*'):
                return FlameMessageWindow('Error', 'error', 'Can not delete preset set as Global Default.<br>Set another preset to Global Default and try again.')

            # Check all project config files for current preset before deleting.
            # If the preset exists in other project files, delete project files. Confirm first.

            preset_names = []

            if os.listdir(self.project_config_path):
                for n in os.listdir(self.project_config_path):
                    saved_preset_name = self.load_project_preset(os.path.join(self.project_config_path, n))
                    preset_names.append(saved_preset_name)

                # If preset exists in other project configs, confirm deletion

                if preset_name in preset_names:
                    if FlameMessageWindow('Confirm Operation', 'warning', 'Selected preset is used by other projects. Deleting this preset will delete it for the other projects. Continue?'):
                        for preset in preset_names:
                            os.remove(os.path.join(self.project_config_path, n))
                        delete()
                    else:
                        return
                else:
                    # If preset is not found in any projects, delete. Confirm first.

                    if FlameMessageWindow('Confirm Operation', 'warning', f'Delete preset: {preset_name}?'):
                        delete()
                    else:
                        return
            else:
                # If no project configs exist, delete preset. Confirm first.

                if FlameMessageWindow('Confirm Operation', 'warning', f'Delete preset: {preset_name}?'):
                    delete()
                else:
                    return

        def save():

            preset_name_text = self.current_preset_push_btn.text()
            if preset_name_text.endswith('*'):
                preset_name_text = preset_name_text[:-1]

            if not preset_name_text:
                return FlameMessageWindow('Error', 'error', 'Preset must be created to save.')

            preset_path = os.path.join(self.project_config_path, self.flame_prj_name + '.xml')

            if preset_name_text != self.global_default:

                if os.path.isfile(preset_path):
                    os.remove(preset_path)

                # Create project preset

                preset = """
<settings>
    <global_setting>
        <preset_name></preset_name>
    </global_setting>
</settings>"""

                with open(preset_path, 'a') as xml_file:
                    xml_file.write(preset)
                    xml_file.close()

                # Update config

                xml_tree = ET.parse(preset_path)
                root = xml_tree.getroot()

                preset_name = root.find('.//preset_name')
                preset_name.text = preset_name_text

                xml_tree.write(preset_path)

                print ('--> custom project uber save preset saved \n')

                FlameMessageWindow('Create Shot - Preset Saved', 'message', f'<b>Project:</b> {self.project_name}<br><br><b>Preset:</b> {preset_name_text}')
            else:
                try:
                    os.remove(preset_path)
                except:
                    pass

            self.selector_window.close()

            print ('done.\n')

        gridbox = QtWidgets.QGridLayout()
        self.selector_window = FlameWindow(f'Create Shot - Presets <small>{VERSION}', gridbox, 600, 260)

        # Labels

        self.preset_label = FlameLabel('Create Shot Current Project Preset', label_type='underline')

        # Shot Name Type Pushbutton Menu

        preset_list = build_preset_list()
        self.current_preset_push_btn = FlamePushButtonMenu('', preset_list)
        self.current_preset_push_btn.setMaximumSize(QtCore.QSize(450, 28))

        #  Buttons

        self.new_btn = FlameButton('New', new_preset, button_width=100)
        self.edit_btn = FlameButton('Edit', edit_preset, button_width=100)
        self.delete_btn = FlameButton('Delete', delete_preset, button_width=100)
        self.duplicate_btn = FlameButton('Duplicate', duplicate_preset, button_width=100)
        self.save_btn = FlameButton('Save', save, button_width=100)
        self.exit_btn = FlameButton('Exit', self.selector_window.close, button_width=100)

        load_config()

        # Preset Selector Window layout

        gridbox.setMargin(20)

        gridbox.addWidget(self.preset_label, 1, 1, 1, 6)
        gridbox.addWidget(self.current_preset_push_btn, 2, 1, 1, 4)
        gridbox.addWidget(self.new_btn, 2, 5)
        gridbox.addWidget(self.edit_btn, 3, 5)
        gridbox.addWidget(self.delete_btn, 2, 6)
        gridbox.addWidget(self.duplicate_btn, 3, 6)

        gridbox.setRowMinimumHeight(5, 28)

        gridbox.addWidget(self.exit_btn, 6, 5)
        gridbox.addWidget(self.save_btn, 6, 6)

        self.selector_window.setLayout(gridbox)

        self.selector_window.show()

        return self.selector_window

    # ------------------------------------- #
    # Windows

    def create_shot_folder_window(self):

        def create_shot_list():

            def save_settings():

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                shot_naming = root.find('.//shot_naming')
                shot_naming.text = self.shot_name_entry.text()
                num_of_shots = root.find('.//number_of_shots')
                num_of_shots.text = self.num_of_shots_slider.text()
                starting_shot = root.find('.//starting_shot')
                starting_shot.text = self.start_shot_num_slider.text()
                shot_increments = root.find('.//shot_increments')
                shot_increments.text = self.shot_increment_slider.text()
                create_folders = root.find('.//create_folders')
                create_folders.text = str(self.create_folders_push_btn.isChecked())
                create_system_folders = root.find('.//create_system_folders')
                create_system_folders.text = str(self.create_system_folders_push_btn.isChecked())
                reveal_in_finder = root.find('.//reveal_in_finder')
                reveal_in_finder.text = str(self.reveal_in_finder_push_btn.isChecked())

                xml_tree.write(self.config_xml)

                print ('--> settings saved \n')

            # Check that at least on shot creation type is selection

            if not any ([self.create_folders_push_btn.isChecked(), self.create_system_folders_push_btn.isChecked()]):
                return FlameMessageWindow('Error', 'error', 'Select shot type to create')

            # Clear selection

            self.selection = ''

            # Save settings

            save_settings()

            # Warn if shot name field empty

            if self.shot_name_entry.text() == '':
                return FlameMessageWindow('Error', 'error', 'Enter shot naming')

            # Get values from UI

            shot_name_string = str(self.shot_name_entry.text())
            shot_padding = re.search('<ShotNum#*>', shot_name_string)
            num_of_shots = int(self.num_of_shots_slider.text())
            starting_shot = int(self.start_shot_num_slider.text())
            shot_increments = int(self.shot_increment_slider.text())
            num_folders = num_of_shots * shot_increments + starting_shot

            # Create list of shot names

            shot_seq_text = ['<ShotNum', '[', ']']
            shot_seq = [ele for ele in shot_seq_text if(ele in shot_name_string)]

            try:
                if re.search('<ShotNum#*>', shot_name_string):

                    # Create shot list using options and token

                    shot_name_list = []

                    for x in range(starting_shot, num_folders, shot_increments):
                        shot_name = re.sub('<ShotNum#*>', str(x).zfill(int(shot_padding.group(0).count('#'))), shot_name_string)
                        shot_name_list.append(shot_name)

                elif not shot_seq:

                    # Create single shot shot_name_list if token or list not present in shot_name_entry

                    shot_name_list = [shot_name_string]

                else:

                    # Create shot list using shot numbers and shot range
                    # [0010, 0020, 0050-0090]

                    shot_name_prefix = shot_name_string.split('[', 1)[0]
                    shot_name_string = shot_name_string.split('[', 1)[1]
                    shot_name_string = shot_name_string.rsplit(']', 1)[0]
                    shot_name_string = shot_name_string.replace(' ', '')
                    shots = shot_name_string.split(',')

                    shot_name_list = [shot_name_prefix + shot for shot in shots if '-' not in shot]

                    for num in shots:
                        if '-' in num:
                            print (num)

                            # Remove number range from list
                            # shot_name_list.pop(shot_name_list.index(num))

                            num_range = num.split('-')
                            print (num_range)

                            padding = len(num_range[0])
                            print (padding)

                            stripped_numbers = []
                            for n in num_range:
                                n = n.lstrip('0')
                                stripped_numbers.append(int(n))
                            print (stripped_numbers)

                            for n in range(stripped_numbers[0], stripped_numbers[1] + shot_increments, shot_increments):
                                num_len = padding - len(str(n))
                                shot_name = shot_name_prefix + '0'*num_len + str(n)
                                shot_name_list.append(shot_name)

                    print (shot_name_list)

            except:
                return FlameMessageWindow('Error', 'error', 'Enter valid shot naming. PYT_<ShotNum####> or PYT[0010, 0020, 0050-0090] for shot lists or PYT_0010 for single shot.')

            # print ('shot_name_list:', shot_name_list)
            # print ('selection:', self.selection)

            # Get button settings

            self.create_shot_type_folders = self.create_folders_push_btn.isChecked()
            self.create_shot_type_desktop = False
            self.create_shot_type_batch_group = False
            self.create_shot_type_system_folders = self.create_system_folders_push_btn.isChecked()

            self.batch_group_dest = 'Library'

            # Turn off export plates. Plates can not be exported from this option.

            self.create_shot_export_plates = False

            # Create shots from list

            self.create_shots(shot_name_list)

            # If reveal in finder is selected open shot root path in finder

            if self.reveal_in_finder_push_btn.isChecked():
                self.reveal_path_in_finder(system_folder_path)

            self.window.close()

        def reveal_in_finder_toggle():

            if self.create_system_folders_push_btn.isChecked():
                self.reveal_in_finder_push_btn.setEnabled(True)
            else:
                self.reveal_in_finder_push_btn.setEnabled(False)

        grid = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'Create Shot Folders <small>{VERSION}', grid, 1100, 380)

        # Labels

        self.shot_naming_label = FlameLabel('Shot Folder Settings', label_type='underline')
        self.create_label = FlameLabel('Create', 'underline')
        self.shot_name_label = FlameLabel('Shot Name')
        self.num_shots_label = FlameLabel('Number of Shots')
        self.start_shot_num_label = FlameLabel('Starting Shot')
        self.shot_increment_label = FlameLabel('Shot Increments')

        self.system_folder_path_label = FlameLabel('System Folder Path')
        system_folder_path = self.translate_system_shot_folder_path('PYT_0100')
        self.system_folder_path_label2 = FlameLabel(system_folder_path, label_type='background')

        # LineEdits

        def check_shot_name_entry():

            if re.search('<ShotNum#*>', self.shot_name_entry.text()):
                self.num_of_shots_slider.setEnabled(True)
                self.num_shots_label.setEnabled(True)
                self.start_shot_num_slider.setEnabled(True)
                self.start_shot_num_label.setEnabled(True)
                self.shot_increment_label.setEnabled(True)
                self.shot_increment_slider.setEnabled(True)

            elif '[' in self.shot_name_entry.text() and ']' in self.shot_name_entry.text() and re.search('\d-\d', self.shot_name_entry.text()):
                self.num_of_shots_slider.setEnabled(False)
                self.num_shots_label.setEnabled(False)
                self.start_shot_num_slider.setEnabled(False)
                self.start_shot_num_label.setEnabled(False)
                self.shot_increment_label.setEnabled(True)
                self.shot_increment_slider.setEnabled(True)

            else:
                self.num_of_shots_slider.setEnabled(False)
                self.num_shots_label.setEnabled(False)
                self.start_shot_num_slider.setEnabled(False)
                self.start_shot_num_label.setEnabled(False)
                self.shot_increment_label.setEnabled(False)
                self.shot_increment_slider.setEnabled(False)

        self.shot_name_entry = FlameLineEdit(self.shot_naming)
        self.shot_name_entry.textChanged.connect(check_shot_name_entry)

        # Sliders

        self.num_of_shots_slider = FlameSlider(self.num_of_shots, 1, 1000, False)
        self.start_shot_num_slider = FlameSlider(self.starting_shot, 1, 10000, False)
        self.shot_increment_slider = FlameSlider(self.shot_increments, 1, 100, False)

        # Token PushButton

        shot_num_dict = {'Shot Number': '<ShotNum####>'}
        self.shot_name_token_btn = FlameTokenPushButton('Add Token', shot_num_dict, self.shot_name_entry)

        # Pushbuttons

        self.create_folders_push_btn = FlamePushButton('Folders', self.create_custom_folders)
        self.create_system_folders_push_btn = FlamePushButton('System Folders', self.create_custom_system_folders)
        self.create_system_folders_push_btn.clicked.connect(reveal_in_finder_toggle)
        self.reveal_in_finder_push_btn = FlamePushButton('Reveal in Finder', self.reveal_in_finder)

        reveal_in_finder_toggle()

        # Buttons

        help_btn = FlameButton('Help', self.help)
        create_btn = FlameButton('Create', create_shot_list)
        cancel_btn = FlameButton('Cancel', self.window.close)

        check_shot_name_entry()

        # ------------------------------------------------------------- #

        # UI Widget layout

        grid.setVerticalSpacing(5)
        grid.setHorizontalSpacing(5)
        grid.setMargin(20)

        grid.addWidget(self.shot_naming_label, 0, 1, 1, 6)

        grid.addWidget(self.shot_name_label, 1, 1)
        grid.addWidget(self.shot_name_entry, 1, 2, 1, 4)
        grid.addWidget(self.shot_name_token_btn, 1, 6)

        grid.addWidget(self.shot_increment_label, 2, 1)
        grid.addWidget(self.shot_increment_slider, 2, 2)

        grid.addWidget(self.num_shots_label, 3, 1)
        grid.addWidget(self.num_of_shots_slider, 3, 2)

        grid.addWidget(self.start_shot_num_label, 4, 1)
        grid.addWidget(self.start_shot_num_slider, 4, 2)

        grid.addWidget(self.create_label, 0, 8)
        grid.addWidget(self.create_folders_push_btn, 1, 8)
        grid.addWidget(self.create_system_folders_push_btn, 2, 8)
        grid.addWidget(self.reveal_in_finder_push_btn, 3, 8)

        grid.setRowMinimumHeight(5, 30)

        grid.addWidget(self.system_folder_path_label, 6, 1)
        grid.addWidget(self.system_folder_path_label2, 6, 2, 1, 5)

        grid.setRowMinimumHeight(7, 30)

        grid.addWidget(help_btn, 8, 1)
        grid.addWidget(cancel_btn, 8, 7)
        grid.addWidget(create_btn, 8, 8)

        self.window.setLayout(grid)

        self.window.show()

    def setup(self):

        def setup_preset_tab():

            def global_default_pressed():

                if not os.listdir(self.preset_path):
                    self.preset_global_default_pushbutton.setChecked(True)

                if self.preset_name_lineedit.text() == self.global_default:
                    self.preset_global_default_pushbutton.setChecked(True)

            def global_default_state():

                # Set global default button state

                if not os.listdir(self.preset_path):
                    self.preset_global_default_pushbutton.setChecked(True)
                if self.preset_name_lineedit.text() == self.global_default:
                    self.preset_global_default_pushbutton.setChecked(True)

            # Labels

            self.preset_setup_label = FlameLabel('Preset Setup', label_type='underline')
            self.preset_name_label = FlameLabel('Preset Name')
            self.shot_name_from_label = FlameLabel('Shot Name From')

            # LineEdits

            self.preset_name_lineedit = FlameLineEdit(self.preset_name)

            # Push Buttons

            self.preset_global_default_pushbutton = FlamePushButton('Global Default', False)
            self.preset_global_default_pushbutton.clicked.connect(global_default_pressed)
            global_default_state()

            # Push Button Menus

            shot_name_from_options = ['Shot Name', 'Clip Name']
            self.shot_name_from_push_button = FlamePushButtonMenu(self.shot_name_from, shot_name_from_options)

            # Buttons

            setup_help_btn = FlameButton('Help', self.help)
            setup_save_btn = FlameButton('Save', save_setup_settings)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close)

            # Tab layout

            self.setup_window.tab6.layout = QtWidgets.QGridLayout()
            self.setup_window.tab6.layout.setMargin(10)
            self.setup_window.tab6.layout.setVerticalSpacing(5)
            self.setup_window.tab6.layout.setHorizontalSpacing(5)

            self.setup_window.tab6.layout.setColumnMinimumWidth(5, 150)

            self.setup_window.tab6.layout.addWidget(self.preset_setup_label, 0, 1, 1, 5)

            self.setup_window.tab6.layout.addWidget(self.preset_name_label, 1, 0)
            self.setup_window.tab6.layout.addWidget(self.preset_name_lineedit, 1, 1, 1, 5)
            self.setup_window.tab6.layout.addWidget(self.preset_global_default_pushbutton, 1, 6)

            self.setup_window.tab6.layout.setRowMinimumHeight(2, 28)

            self.setup_window.tab6.layout.addWidget(self.shot_name_from_label, 3, 0)
            self.setup_window.tab6.layout.addWidget(self.shot_name_from_push_button, 3, 1)

            self.setup_window.tab6.layout.setRowMinimumHeight(12, 500)

            self.setup_window.tab6.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab6.layout.addWidget(setup_save_btn, 13, 6)
            self.setup_window.tab6.layout.addWidget(setup_cancel_btn, 14, 6)

            self.setup_window.tab6.setLayout(self.setup_window.tab6.layout)

        def setup_file_system_folders_tab():

            # Labels

            self.file_system_export_dest_label = FlameLabel('Export Dest Folder')
            self.file_system_export_dest_label_02 = FlameLabel(self.export_dest_folder, label_type='background')
            self.folders_label = FlameLabel('Folder Setup', label_type='underline')

            # File System Shot Folder Tree

            self.file_system_folder_tree = QtWidgets.QTreeWidget()
            self.file_system_folder_tree.setColumnCount(1)
            self.file_system_folder_tree.setHeaderLabel('File System Shot Folder Template')
            self.file_system_folder_tree.itemsExpandable()
            self.file_system_folder_tree.setAlternatingRowColors(True)
            self.file_system_folder_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.file_system_folder_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #1e1e1e; alternate-background-color: #242424; border: none; font: 14pt "Discreet"}'
                                                       'QHeaderView::section {color: #9a9a9a; background-color: #3a3a3a; border: none; padding-left: 10px; font: 14pt "Discreet"}'
                                                       'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #5a5a5a}'
                                                       'QTreeWidget:item:selected:active {color: #999999; border: none}'
                                                       'QTreeWidget:disabled {color: #656565; background-color: #222222}'
                                                       'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                                       'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            # Fill tree

            fill_tree(self.file_system_folder_tree, self.file_system_folder_dict)

            # Set tree top level items

            self.file_system_folder_tree_top = self.file_system_folder_tree.topLevelItem(0)
            self.file_system_folder_tree.setCurrentItem(self.file_system_folder_tree_top)

            # Buttons

            self.add_file_system_folder_btn = FlameButton('Add Folder', partial(add_tree_item, self.file_system_folder_tree_top, self.file_system_folder_tree))
            self.delete_file_system_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, self.file_system_folder_tree_top, self.file_system_folder_tree))
            self.system_folder_sort_btn = FlameButton('Sort Folders', partial(self.sort_tree_items, self.file_system_folder_tree))
            self.system_folder_export_dest_folder_btn = FlameButton('Set Export Dest Folder', partial(set_folder_as_destination, self.file_system_export_dest_label_02, self.file_system_folder_tree_top, self.file_system_folder_tree))

            setup_help_btn = FlameButton('Help', self.help)
            setup_save_btn = FlameButton('Save', save_setup_settings)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close)

            # File system shot folder tree contextual right click menus

            action_file_system_add_folder = QtWidgets.QAction('Add Folder')
            action_file_system_add_folder.triggered.connect(partial(add_tree_item, self.file_system_folder_tree_top, self.file_system_folder_tree))
            self.file_system_folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            self.file_system_folder_tree.addAction(action_file_system_add_folder)

            action_file_system_delete_folder = QtWidgets.QAction('Delete Folder')
            action_file_system_delete_folder.triggered.connect(partial(del_tree_item, self.file_system_folder_tree_top, self.file_system_folder_tree))
            self.file_system_folder_tree.addAction(action_file_system_delete_folder)

            action_set_export_folder = QtWidgets.QAction('Set Export Dest Folder')
            action_set_export_folder.triggered.connect(partial(set_folder_as_destination, self.file_system_export_dest_label_02, self.file_system_folder_tree_top, self.file_system_folder_tree))
            self.file_system_folder_tree.addAction(action_set_export_folder)

            # Tab layout

            self.setup_window.tab5.layout = QtWidgets.QGridLayout()
            self.setup_window.tab5.layout.setMargin(10)
            self.setup_window.tab5.layout.setVerticalSpacing(5)
            self.setup_window.tab5.layout.setHorizontalSpacing(5)

            self.setup_window.tab5.layout.addWidget(self.folders_label, 0, 1, 1, 3)
            self.setup_window.tab5.layout.addWidget(self.file_system_folder_tree, 1, 1, 7, 3)

            self.setup_window.tab5.layout.addWidget(self.file_system_export_dest_label, 8, 0)
            self.setup_window.tab5.layout.addWidget(self.file_system_export_dest_label_02, 8, 1, 1, 3)

            self.setup_window.tab5.layout.addWidget(self.add_file_system_folder_btn, 1, 4)
            self.setup_window.tab5.layout.addWidget(self.delete_file_system_folder_btn, 2, 4)
            self.setup_window.tab5.layout.addWidget(self.system_folder_sort_btn, 3, 4)
            self.setup_window.tab5.layout.addWidget(self.system_folder_export_dest_folder_btn, 4, 4)

            self.setup_window.tab5.layout.setRowMinimumHeight(9, 175)

            self.setup_window.tab5.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab5.layout.addWidget(setup_save_btn, 13, 4)
            self.setup_window.tab5.layout.addWidget(setup_cancel_btn, 14, 4)

            self.setup_window.tab5.setLayout(self.setup_window.tab5.layout)

        def setup_folder_tab():

            # Labels

            self.setup_folder_clip_dest_label = FlameLabel('Clip Dest Folder', label_type='underline')
            self.setup_folder_clip_dest_label_02 = FlameLabel(self.clip_dest_folder, label_type='background')
            self.folders_label = FlameLabel('Folder Setup', label_type='underline')

            # Media Panel Shot Folder Tree

            self.folder_tree = QtWidgets.QTreeWidget()
            self.folder_tree.setColumnCount(1)
            self.folder_tree.setHeaderLabel('Media Panel Shot Folder Template')
            self.folder_tree.itemsExpandable()
            self.folder_tree.setAlternatingRowColors(True)
            self.folder_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.folder_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #1e1e1e; alternate-background-color: #242424; border: none; font: 14pt "Discreet"}'
                                           'QHeaderView::section {color: #9a9a9a; background-color: #3a3a3a; border: none; padding-left: 10px; font: 14pt "Discreet"}'
                                           'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #5a5a5a}'
                                           'QTreeWidget:item:selected:active {color: #999999; border: none}'
                                           'QTreeWidget:disabled {color: #656565; background-color: #222222}'
                                           'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            # Fill tree

            fill_tree(self.folder_tree, self.folder_dict)

            # Set tree top level items

            folder_tree_top = self.folder_tree.topLevelItem(0)
            self.folder_tree.setCurrentItem(folder_tree_top)

            # Buttons

            self.folder_sort_btn = FlameButton('Sort Folders', partial(self.sort_tree_items, self.folder_tree))

            self.add_folder_btn = FlameButton('Add Folder', partial(add_tree_item, folder_tree_top, self.folder_tree))
            self.delete_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, folder_tree_top, self.folder_tree))
            self.set_clip_dest_folder_btn = FlameButton('Set Clip Dest Folder', partial(set_as_destination, self.setup_folder_clip_dest_label_02, folder_tree_top, self.folder_tree))

            setup_help_btn = FlameButton('Help', self.help)
            setup_save_btn = FlameButton('Save', save_setup_settings)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close)

            # Media panel shot folder tree contextual right click menus

            action_add_folder = QtWidgets.QAction('Add Folder')
            action_add_folder.triggered.connect(partial(add_tree_item, folder_tree_top, self.folder_tree))
            self.folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            self.folder_tree.addAction(action_add_folder)

            action_delete_folder = QtWidgets.QAction('Delete Folder')
            action_delete_folder.triggered.connect(partial(del_tree_item, folder_tree_top, self.folder_tree))
            self.folder_tree.addAction(action_delete_folder)

            action_set_dest_folder = QtWidgets.QAction('Set Clip Dest Folder')
            action_set_dest_folder.triggered.connect(partial(set_as_destination, self.setup_folder_clip_dest_label_02, folder_tree_top, self.folder_tree))
            self.folder_tree.addAction(action_set_dest_folder)

            # Tab layout

            self.setup_window.tab1.layout = QtWidgets.QGridLayout()
            self.setup_window.tab1.layout.setMargin(10)
            self.setup_window.tab1.layout.setVerticalSpacing(5)
            self.setup_window.tab1.layout.setHorizontalSpacing(5)

            self.setup_window.tab1.layout.addWidget(self.setup_folder_clip_dest_label, 1, 0)
            self.setup_window.tab1.layout.addWidget(self.setup_folder_clip_dest_label_02, 2, 0)

            self.setup_window.tab1.layout.addWidget(self.folders_label, 0, 1, 1, 3)
            self.setup_window.tab1.layout.addWidget(self.folder_tree, 1, 1, 5, 3)

            self.setup_window.tab1.layout.addWidget(self.add_folder_btn, 1, 4)
            self.setup_window.tab1.layout.addWidget(self.delete_folder_btn, 2, 4)
            self.setup_window.tab1.layout.addWidget(self.folder_sort_btn, 3, 4)
            self.setup_window.tab1.layout.addWidget(self.set_clip_dest_folder_btn, 4, 4)

            self.setup_window.tab1.layout.setRowMinimumHeight(6, 195)

            self.setup_window.tab1.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab1.layout.addWidget(setup_save_btn, 13, 4)
            self.setup_window.tab1.layout.addWidget(setup_cancel_btn, 14, 4)

            self.setup_window.tab1.setLayout(self.setup_window.tab1.layout)

        def setup_batch_group_tab():

            # Labels

            self.batch_groups_label = FlameLabel('Batch Group Reel Setup', label_type='underline')
            self.setup_batch_clip_dest_reel_label = FlameLabel('Clip Dest Reel', label_type='underline')
            self.setup_batch_clip_dest_reel_label_02 = FlameLabel(self.clip_dest_reel, label_type='background')
            self.setup_batch_start_frame_label = FlameLabel('Batch Start Frame', label_type='underline')
            self.setup_batch_additional_naming_label = FlameLabel('Additional Batch Naming', label_type='underline')

            # LineEdits

            self.setup_batch_additional_naming_lineedit = FlameLineEdit(self.batch_additional_naming)
            self.setup_batch_additional_naming_lineedit.setMaximumWidth(150)

            # Schematic Reel Tree

            self.schematic_reel_tree = QtWidgets.QTreeWidget()
            self.schematic_reel_tree.setColumnCount(1)
            self.schematic_reel_tree.setHeaderLabel('Schematic Reel Template')
            self.schematic_reel_tree.itemsExpandable()
            self.schematic_reel_tree.setDragEnabled(True)
            self.schematic_reel_tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
            self.schematic_reel_tree.setAlternatingRowColors(True)
            self.schematic_reel_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.schematic_reel_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #1e1e1e; alternate-background-color: #242424; border: none; font: 14pt "Discreet"}'
                                                   'QHeaderView::section {color: #9a9a9a; background-color: #3a3a3a; border: none; padding-left: 10px; font: 14pt "Discreet"}'
                                                   'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #5a5a5a}'
                                                   'QTreeWidget:item:selected:active {color: #999999; border: none}'
                                                   'QTreeWidget:disabled {color: #656565; background-color: #222222}'
                                                   'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                                   'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            # Shelf Reel Tree

            self.shelf_reel_tree = QtWidgets.QTreeWidget()
            self.shelf_reel_tree.setColumnCount(1)
            self.shelf_reel_tree.setHeaderLabel('Shelf Reel Template')
            self.shelf_reel_tree.itemsExpandable()
            self.shelf_reel_tree.setAlternatingRowColors(True)
            self.shelf_reel_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.shelf_reel_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #1e1e1e; alternate-background-color: #242424; border: none; font: 14pt "Discreet"}'
                                               'QHeaderView::section {color: #9a9a9a; background-color: #3a3a3a; border: none; padding-left: 10px; font: 14pt "Discreet"}'
                                               'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #5a5a5a}'
                                               'QTreeWidget:item:selected:active {color: #999999; border: none}'
                                               'QTreeWidget:disabled {color: #656565; background-color: #222222}'
                                               'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                               'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            # Fill trees

            fill_tree(self.schematic_reel_tree, self.schematic_reel_dict)
            fill_tree(self.shelf_reel_tree, self.shelf_reel_dict)

            # Set tree top level items

            batch_group_schematic_tree_top = self.schematic_reel_tree.topLevelItem(0)
            batch_group_shelf_tree_top = self.shelf_reel_tree.topLevelItem(0)

            # ------------------------------------------------------------- #

            # Batch Start Frame Slider

            self.setup_batch_start_frame_slider = FlameSlider(self.batch_start_frame, 1, 10000, False)

            # Push Buttons

            self.add_render_node_btn = FlamePushButton('Add Render Node', self.add_render_node)
            self.add_render_node_btn.clicked.connect(render_button_toggle)

            self.add_write_file_node_btn = FlamePushButton('Add Write File Node', self.add_write_file_node)
            self.add_write_file_node_btn.clicked.connect(write_file_button_toggle)

            # Buttons

            self.schematic_reels_sort_btn = FlameButton('Sort Schematic Reels', partial(self.sort_tree_items, self.schematic_reel_tree))
            self.shelf_reels_sort_btn = FlameButton('Sort Shelf Reels', partial(self.sort_tree_items, self.shelf_reel_tree))

            self.add_schematic_reel_btn = FlameButton('Add Schematic Reel', partial(add_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree))
            self.del_schematic_reel_btn = FlameButton('Delete Schematic Reel', partial(del_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree))
            self.set_clip_dest_reel_btn = FlameButton('Set Clip Dest Reel', partial(set_as_destination, self.setup_batch_clip_dest_reel_label_02, batch_group_schematic_tree_top, self.schematic_reel_tree))

            self.add_shelf_reel_btn = FlameButton('Add Shelf Reel', partial(add_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))
            self.del_shelf_reel_btn = FlameButton('Delete Shelf Reel', partial(del_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))

            self.write_file_setup_btn = FlameButton('Write File Setup', self.write_file_node_setup)
            if self.add_render_node:
                self.write_file_setup_btn.setEnabled(False)

            setup_help_btn = FlameButton('Help', self.help)
            setup_save_btn = FlameButton('Save', save_setup_settings)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close)

            # Schematic reel tree contextual right click menus

            action_add_schematic_reel = QtWidgets.QAction('Add Reel')
            action_add_schematic_reel.triggered.connect(partial(add_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree))
            self.schematic_reel_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            self.schematic_reel_tree.addAction(action_add_schematic_reel)

            action_delete_schematic_reel = QtWidgets.QAction('Delete Reel')
            action_delete_schematic_reel.triggered.connect(partial(del_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree))
            self.schematic_reel_tree.addAction(action_delete_schematic_reel)

            action_set_dest_reel = QtWidgets.QAction('Set Clip Dest Reel')
            action_set_dest_reel.triggered.connect(partial(set_as_destination, self.setup_batch_clip_dest_reel_label_02, batch_group_schematic_tree_top, self.schematic_reel_tree))
            self.schematic_reel_tree.addAction(action_set_dest_reel)

            # Shelf reel contextual right click menus

            action_add_shelf_reel = QtWidgets.QAction('Add Reel')
            action_add_shelf_reel.triggered.connect(partial(add_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))
            self.shelf_reel_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            self.shelf_reel_tree.addAction(action_add_shelf_reel)

            action_delete_shelf_reel = QtWidgets.QAction('Delete Reel')
            action_delete_shelf_reel.triggered.connect(partial(del_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))
            self.shelf_reel_tree.addAction(action_delete_shelf_reel)

            # Tab layout

            self.setup_window.tab2.layout = QtWidgets.QGridLayout()
            self.setup_window.tab2.layout.setMargin(10)
            self.setup_window.tab2.layout.setVerticalSpacing(5)
            self.setup_window.tab2.layout.setHorizontalSpacing(5)

            self.setup_window.tab2.layout.addWidget(self.batch_groups_label, 0, 1)

            self.setup_window.tab2.layout.addWidget(self.setup_batch_clip_dest_reel_label, 1, 0)
            self.setup_window.tab2.layout.addWidget(self.setup_batch_clip_dest_reel_label_02, 2, 0)

            self.setup_window.tab2.layout.addWidget(self.setup_batch_start_frame_label, 4, 0)
            self.setup_window.tab2.layout.addWidget(self.setup_batch_start_frame_slider, 5, 0)

            self.setup_window.tab2.layout.addWidget(self.setup_batch_additional_naming_label, 7, 0)
            self.setup_window.tab2.layout.addWidget(self.setup_batch_additional_naming_lineedit, 8, 0)

            self.setup_window.tab2.layout.addWidget(self.schematic_reel_tree, 1, 1, 6, 1)
            self.setup_window.tab2.layout.addWidget(self.shelf_reel_tree, 7, 1, 6, 1)

            self.setup_window.tab2.layout.addWidget(self.add_schematic_reel_btn, 1, 2)
            self.setup_window.tab2.layout.addWidget(self.del_schematic_reel_btn, 2, 2)
            self.setup_window.tab2.layout.addWidget(self.schematic_reels_sort_btn, 3, 2)
            self.setup_window.tab2.layout.addWidget(self.set_clip_dest_reel_btn, 4, 2)

            self.setup_window.tab2.layout.addWidget(self.add_shelf_reel_btn, 7, 2)
            self.setup_window.tab2.layout.addWidget(self.del_shelf_reel_btn, 8, 2)
            self.setup_window.tab2.layout.addWidget(self.shelf_reels_sort_btn, 9, 2)

            self.setup_window.tab2.layout.addWidget(self.add_render_node_btn, 10, 0)
            self.setup_window.tab2.layout.addWidget(self.add_write_file_node_btn, 11, 0)
            self.setup_window.tab2.layout.addWidget(self.write_file_setup_btn, 12, 0)

            self.setup_window.tab2.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab2.layout.addWidget(setup_save_btn, 13, 2)
            self.setup_window.tab2.layout.addWidget(setup_cancel_btn, 14, 2)

            self.setup_window.tab2.setLayout(self.setup_window.tab2.layout)

        def setup_desktop_tab():

            def del_reel_item(tree_top, tree):
                '''
                Delete Reel Group reels if number of reels is greater than four
                '''

                # Create list of exiting reels

                existing_reels = []

                iterator = QtWidgets.QTreeWidgetItemIterator(tree)
                while iterator.value():
                    item = iterator.value()
                    existing_reel = item.text(0)
                    existing_reels.append(existing_reel)
                    iterator += 1

                # Count number of reels in list

                reel_count = len(existing_reels)
                # print ('reel_count: ', reel_count)

                # Don't allow to delete reels if only 4 reels are left

                if reel_count > 5:

                    # Delete reels

                    for item in tree.selectedItems():
                        (item.parent() or tree_top).removeChild(item)
                else:
                    FlameMessageWindow('Error', 'error', 'Reel Group must have at least 4 reels')

            # Labels

            self.reel_group_label = FlameLabel('Desktop Reel Group Setup', label_type='underline')

            # Reel Group Tree

            self.reel_group_tree = QtWidgets.QTreeWidget()
            self.reel_group_tree.move(230, 170)
            self.reel_group_tree.resize(250, 140)
            self.reel_group_tree.setColumnCount(1)
            self.reel_group_tree.setHeaderLabel('Reel Group Template')
            self.reel_group_tree.setAlternatingRowColors(True)
            self.reel_group_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.reel_group_tree.setUniformRowHeights(True)
            self.reel_group_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #1e1e1e; alternate-background-color: #242424; border: none; font: 14pt "Discreet"}'
                                               'QHeaderView::section {color: #9a9a9a; background-color: #3a3a3a; border: none; padding-left: 10px; font: 14pt "Discreet"}'
                                               'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #5a5a5a}'
                                               'QTreeWidget:item:selected:active {color: #999999; border: none}'
                                               'QTreeWidget:disabled {color: #656565; background-color: #222222}'
                                               'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                               'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            # Fill trees

            fill_tree(self.reel_group_tree, self.reel_group_dict)

            # Set tree top level items

            reel_tree_top = self.reel_group_tree.topLevelItem(0)

            # Push Button

            def add_reel_group_button():
                if self.add_reel_group_btn.isChecked():
                    self.reel_group_tree.setEnabled(True)
                    self.add_reel_btn.setEnabled(True)
                    self.del_reel_btn.setEnabled(True)
                    self.reel_group_sort_btn.setEnabled(True)

                else:
                    self.reel_group_tree.setEnabled(False)
                    self.add_reel_btn.setEnabled(False)
                    self.del_reel_btn.setEnabled(False)
                    self.reel_group_sort_btn.setEnabled(False)

            self.add_reel_group_btn = FlamePushButton('Add Reel Group', self.add_reel_group)
            self.add_reel_group_btn.clicked.connect(add_reel_group_button)

            # Buttons

            self.reel_group_sort_btn = FlameButton('Sort Reels', partial(self.sort_tree_items, self.reel_group_tree))

            self.add_reel_btn = FlameButton('Add Reel', partial(add_tree_item, reel_tree_top, self.reel_group_tree))
            self.del_reel_btn = FlameButton('Delete Reel', partial(del_reel_item, reel_tree_top, self.reel_group_tree))

            setup_help_btn = FlameButton('Help', self.help)
            setup_save_btn = FlameButton('Save', save_setup_settings)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close)

            add_reel_group_button()

            # Tab layout

            self.setup_window.tab3.layout = QtWidgets.QGridLayout()
            self.setup_window.tab3.layout.setMargin(10)
            self.setup_window.tab3.layout.setVerticalSpacing(5)
            self.setup_window.tab3.layout.setHorizontalSpacing(5)

            self.setup_window.tab3.layout.addWidget(self.add_reel_group_btn, 1, 0)

            self.setup_window.tab3.layout.addWidget(self.reel_group_label, 0, 1, 1, 3)
            self.setup_window.tab3.layout.addWidget(self.add_reel_btn, 1, 4)
            self.setup_window.tab3.layout.addWidget(self.del_reel_btn, 2, 4)
            self.setup_window.tab3.layout.addWidget(self.reel_group_sort_btn, 3, 4)

            self.setup_window.tab3.layout.addWidget(self.reel_group_tree, 1, 1, 5, 3)

            self.setup_window.tab3.layout.setRowMinimumHeight(6, 195)

            self.setup_window.tab3.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab3.layout.addWidget(setup_save_btn, 13, 4)
            self.setup_window.tab3.layout.addWidget(setup_cancel_btn, 14, 4)

            self.setup_window.tab3.setLayout(self.setup_window.tab3.layout)

        def setup_options_tab():

            def folders_button_toggle():

                if self.setup_folders_pushbutton.isChecked():
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)
                else:
                    if self.setup_batch_group_pushbutton.isChecked():
                        if not self.setup_desktop_pushbutton.isChecked():
                            self.setup_batch_group_dest_label.setEnabled(True)
                            self.setup_batch_group_dest_btn.setEnabled(True)

            def batch_group_button_toggle():

                # When batch group button is selected enable batch group reel destination lineedit

                if self.setup_batch_group_pushbutton.isChecked():
                    self.setup_batch_template_pushbutton.setEnabled(True)

                    if self.setup_folders_pushbutton.isChecked():
                        self.setup_batch_group_dest_label.setEnabled(False)
                        self.setup_batch_group_dest_btn.setEnabled(False)
                    else:
                        self.setup_batch_group_dest_label.setEnabled(True)
                        self.setup_batch_group_dest_btn.setEnabled(True)

                    if self.setup_batch_template_pushbutton.isChecked():
                        self.setup_batch_template_path_label.setEnabled(True)
                        self.setup_batch_template_path_lineedit.setEnabled(True)
                        self.setup_batch_template_path_browse_button.setEnabled(True)
                    else:
                        self.setup_batch_template_path_label.setEnabled(False)
                        self.setup_batch_template_path_lineedit.setEnabled(False)
                        self.setup_batch_template_path_browse_button.setEnabled(False)


                elif self.setup_desktop_pushbutton.isChecked():
                    self.setup_batch_group_pushbutton.setChecked(True)
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)
                else:
                    self.setup_batch_template_pushbutton.setEnabled(False)
                    self.setup_batch_template_path_label.setEnabled(False)
                    self.setup_batch_template_path_lineedit.setEnabled(False)
                    self.setup_batch_template_path_browse_button.setEnabled(False)
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)

            def desktop_button_toggle():

                # When desktop button is selected enable batch group button

                if self.setup_desktop_pushbutton.isChecked():
                    self.setup_batch_group_pushbutton.setChecked(True)
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)
                    self.setup_batch_template_pushbutton.setEnabled(True)
                    if self.setup_batch_template_pushbutton.isChecked():
                        self.setup_batch_template_path_label.setEnabled(True)
                        self.setup_batch_template_path_lineedit.setEnabled(True)
                        self.setup_batch_template_path_browse_button.setEnabled(True)
                else:
                    self.setup_batch_group_pushbutton.setEnabled(True)
                    if self.setup_batch_group_pushbutton.isChecked():
                        if not self.setup_folders_pushbutton.isChecked():
                            self.setup_batch_group_dest_label.setEnabled(True)
                            self.setup_batch_group_dest_btn.setEnabled(True)

            def system_folders_toggle():

                # Toggle system folder options

                if self.setup_system_folders_pushbutton.isChecked():
                    self.setup_export_plates_pushbutton.setEnabled(True)
                else:
                    self.setup_export_plates_pushbutton.setEnabled(False)

            def export_plates_toggle():

                # Toggle Export Plate options

                if self.setup_export_plates_pushbutton.isChecked():
                    self.setup_export_preset_push_btn.setEnabled(True)
                    self.setup_foreground_export_pushbutton.setEnabled(True)
                else:
                    self.setup_export_preset_push_btn.setEnabled(False)
                    self.setup_foreground_export_pushbutton.setEnabled(False)

            def batch_template_toggle():

                if self.setup_batch_template_pushbutton.isChecked():
                    self.setup_batch_template_path_label.setEnabled(True)
                    self.setup_batch_template_path_lineedit.setEnabled(True)
                    self.setup_batch_template_path_browse_button.setEnabled(True)
                else:
                    self.setup_batch_template_path_label.setEnabled(False)
                    self.setup_batch_template_path_lineedit.setEnabled(False)
                    self.setup_batch_template_path_browse_button.setEnabled(False)

            def update_system_folder_path():

                shot_name = 'seq_0010'
                self.system_shot_folders_path = self.setup_system_shot_folders_path_lineedit.text()
                self.setup_system_folder_path_translated_label.setText(self.translate_system_shot_folder_path(shot_name))

            # Labels

            self.setup_create_shot_type_label = FlameLabel('Create', label_type='underline')
            self.setup_options_label = FlameLabel('Options', label_type='underline')
            self.setup_batch_group_options_label = FlameLabel('Batch Group Options', label_type='underline')
            self.setup_batch_template_path_label = FlameLabel('Template Path')
            self.setup_batch_group_dest_label = FlameLabel('Batch Group Dest')
            self.setup_system_folder_path_label = FlameLabel('File System Folders Path', label_type='underline')
            self.setup_system_folder_path_translated_label = FlameLabel('', label_type='background')
            self.setup_export_preset_label = FlameLabel('Export Preset')
            # self.setup_import_options_label = FlameLabel('Import Options', 'underline')

            # LineEdits

            self.setup_batch_template_path_lineedit = FlameLineEdit(self.batch_template_path)
            self.setup_system_shot_folders_path_lineedit = FlameLineEdit(self.system_shot_folders_path)
            self.setup_system_shot_folders_path_lineedit.textChanged.connect(update_system_folder_path)
            update_system_folder_path()

            # Push Buttons

            self.setup_folders_pushbutton = FlamePushButton('Folders', self.create_shot_type_folders)
            self.setup_folders_pushbutton.clicked.connect(folders_button_toggle)

            self.setup_batch_group_pushbutton = FlamePushButton('Batch Group', self.create_shot_type_batch_group)
            self.setup_batch_group_pushbutton.clicked.connect(batch_group_button_toggle)

            self.setup_desktop_pushbutton = FlamePushButton('Desktop', self.create_shot_type_desktop)
            self.setup_desktop_pushbutton.clicked.connect(desktop_button_toggle)

            self.setup_system_folders_pushbutton = FlamePushButton('System Folders', self.create_shot_type_system_folders)
            self.setup_system_folders_pushbutton.clicked.connect(system_folders_toggle)

            self.setup_batch_template_pushbutton = FlamePushButton('Batch Template', self.apply_batch_template)
            self.setup_batch_template_pushbutton.clicked.connect(batch_template_toggle)

            self.setup_export_plates_pushbutton = FlamePushButton('Export Plates', self.create_shot_export_plates)
            self.setup_export_plates_pushbutton.clicked.connect(export_plates_toggle)

            self.setup_foreground_export_pushbutton = FlamePushButton('Foreground Export', self.create_shot_fg_export)

            # self.setup_cache_on_import_pushbutton = FlamePushButton('Cache on Import', self.create_shot_cache_on_import)

            # Push Button Menus

            batch_group_dest_options = ['Desktop', 'Library']
            self.setup_batch_group_dest_btn = FlamePushButtonMenu(self.batch_group_dest, batch_group_dest_options)

            export_preset_list = self.get_export_presets()
            self.setup_export_preset_push_btn = FlamePushButtonMenu(self.create_shot_export_plate_preset, export_preset_list)

            # Token Push Button

            system_path_token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>', 'SEQUENCE NAME': '<SEQNAME>', 'Sequence Name': '<SeqName>'}
            self.system_path_token_push_button = FlameTokenPushButton('Add Token', system_path_token_dict, self.setup_system_shot_folders_path_lineedit)

            # Buttons

            self.setup_batch_template_path_browse_button = FlameButton('Browse', partial(self.batch_template_browse, self.setup_batch_template_path_lineedit))
            self.setup_system_folder_path_browse_button = FlameButton('Browse', partial(self.system_folder_browse, self.setup_system_shot_folders_path_lineedit))

            setup_help_btn = FlameButton('Help', self.help)
            setup_save_btn = FlameButton('Save', save_setup_settings)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close)

            # ----- #

            # Check button states

            batch_group_button_toggle()
            desktop_button_toggle()
            batch_template_toggle()
            folders_button_toggle()
            system_folders_toggle()
            export_plates_toggle()

            # Tab layout

            self.setup_window.tab4.layout = QtWidgets.QGridLayout()
            self.setup_window.tab4.layout.setMargin(10)
            self.setup_window.tab4.layout.setVerticalSpacing(5)
            self.setup_window.tab4.layout.setHorizontalSpacing(5)

            self.setup_window.tab4.layout.addWidget(self.setup_create_shot_type_label, 0, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_folders_pushbutton, 1, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_pushbutton, 2, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_desktop_pushbutton, 3, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_system_folders_pushbutton, 4, 0)

            self.setup_window.tab4.layout.addWidget(self.setup_export_plates_pushbutton, 4, 1)
            self.setup_window.tab4.layout.addWidget(self.setup_export_preset_label, 4, 2)
            self.setup_window.tab4.layout.addWidget(self.setup_export_preset_push_btn, 4, 2, 1, 1)
            self.setup_window.tab4.layout.addWidget(self.setup_foreground_export_pushbutton, 4, 3)

            self.setup_window.tab4.layout.addWidget(self.setup_options_label, 0, 1, 1, 3)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_pushbutton, 2, 1)

            # self.setup_window.tab4.layout.addWidget(self.setup_import_options_label, 0, 4)
            # self.setup_window.tab4.layout.addWidget(self.setup_cache_on_import_pushbutton, 1, 4)

            self.setup_window.tab4.layout.setRowMinimumHeight(5, 28)

            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_options_label, 6, 0, 1, 5)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_path_label, 7, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_path_lineedit, 7, 1, 1, 3)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_path_browse_button, 7, 4)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_dest_label, 8, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_dest_btn, 8, 1)

            self.setup_window.tab4.layout.setRowMinimumHeight(9, 28)

            self.setup_window.tab4.layout.addWidget(self.setup_system_folder_path_label, 10, 0, 1, 5)
            self.setup_window.tab4.layout.addWidget(self.setup_system_folder_path_translated_label, 11, 0, 1, 5)
            self.setup_window.tab4.layout.addWidget(self.setup_system_shot_folders_path_lineedit, 12, 0, 1, 3)
            self.setup_window.tab4.layout.addWidget(self.setup_system_folder_path_browse_button, 12, 3)
            self.setup_window.tab4.layout.addWidget(self.system_path_token_push_button, 12, 4)

            self.setup_window.tab4.layout.setRowMinimumHeight(13, 175)

            self.setup_window.tab4.layout.addWidget(setup_help_btn, 15, 0)
            self.setup_window.tab4.layout.addWidget(setup_save_btn, 14, 4)
            self.setup_window.tab4.layout.addWidget(setup_cancel_btn, 15, 4)

            self.setup_window.tab4.setLayout(self.setup_window.tab4.layout)

        # ------------------------------------------------------------- #

        def flame_version_check():

            # Disable adding file system folder setup options in versions older than 2021.2

            if self.flame_version < 2021.2:
                self.file_system_folder_tree.setDisabled(True)
                self.add_file_system_folder_btn.setDisabled(True)
                self.delete_file_system_folder_btn.setDisabled(True)

        def set_as_destination(label, tree_top, tree):

            if tree.selectedItems()[0] is not tree_top:
                label.setText(tree.selectedItems()[0].text(0))

        def set_folder_as_destination(label, tree_top, tree):

            if tree.selectedItems()[0] is not tree_top:
                selected_folder = tree.selectedItems()[0]
            else:
                return

            def get_items_recursively():

                # Create empty list for all folder paths

                self.path_list = []

                # Iterate through folders to get paths through get_tree_path

                def search_child_item(item=None):
                    if not item:
                        return
                    for m in range(item.childCount()):
                        child_item = item.child(m)
                        get_tree_path(child_item)
                        if not child_item:
                            continue
                        search_child_item(child_item)

                for i in range(tree.topLevelItemCount()):
                    item = tree.topLevelItem(i)
                    if not item:
                        continue
                    search_child_item(item)

            def get_tree_path(item):

                # Get path of each child item

                if item is selected_folder:

                    path = []

                    while item is not None:
                        path.append(str(item.text(0)))
                        item = item.parent()
                    item_path = '/'.join(reversed(path))
                    self.path_list.append(item_path)
                    self.set_export_folder_path = path

            get_items_recursively()

            label.setText(self.path_list[0])

        def fill_tree(tree_widget, tree_dict):

            def fill_item(item, value):

                # Set top level item so name can not be changed except for reel group tree

                if tree_widget == self.reel_group_tree or str(item.parent()) != 'None':
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled)
                else:
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled)

                item.setExpanded(True)

                if type(value) is dict:
                    for key, val in iter(value.items()):
                        child = QtWidgets.QTreeWidgetItem()
                        child.setText(0, key)

                        item.addChild(child)

                        fill_item(child, val)

            def fill_widget(widget, value):

                widget.clear()
                fill_item(widget.invisibleRootItem(), value)

            # Fill tree widget with dictionary

            fill_widget(tree_widget, tree_dict)

        def del_tree_item(tree_top, tree):

            def count_items(tree):

                count = 0
                iterator = QtWidgets.QTreeWidgetItemIterator(tree)  # pass your treewidget as arg
                while iterator.value():
                    item = iterator.value()

                    if item.parent():
                        if item.parent().isExpanded():
                            count += 1
                    else:
                        count += 1
                    iterator += 1
                return count

            root = tree_top

            # Last item in tree should not be deleted

            if count_items(tree) > 2:

                # Delete any tree widget items other than root item

                for item in tree.selectedItems():
                    (item.parent() or root).removeChild(item)
            else:
                return FlameMessageWindow('Error', 'error', 'Template must have at least one folder/reel')

        def add_tree_item(tree_top, tree, new_item_num=0):

            # Get list of exisiting schematic reels for new reel numbering

            existing_item_names = []

            iterator = QtWidgets.QTreeWidgetItemIterator(tree)
            while iterator.value():
                item = iterator.value()
                existing_item = item.text(0)
                # print ('existing_item:', existing_item)
                existing_item_names.append(existing_item)
                iterator += 1
            # print ('existing_item_names:', existing_item_names)

            # Set New Item name

            if tree in (self.folder_tree, self.file_system_folder_tree):
                new_item_name = 'New Folder'
            elif tree == self.schematic_reel_tree:
                new_item_name = 'New Schematic Reel'
            elif tree == self.shelf_reel_tree:
                new_item_name = 'New Shelf Reel'
            elif tree == self.reel_group_tree:
                new_item_name = 'New Reel'

            new_item = new_item_name + ' ' + str(new_item_num)

            if new_item == f'{new_item_name} 0':
                new_item = f'{new_item_name}'

            # Check if new item name exists, if it does add one to file name

            if new_item not in existing_item_names:

                if tree in (self.schematic_reel_tree, self.shelf_reel_tree, self.reel_group_tree):

                    # Select Tree Top Item

                    tree.setCurrentItem(tree_top)

                # Create new tree item

                parent = tree.currentItem()

                if tree in (self.folder_tree, self.file_system_folder_tree):

                    # Expand folder

                    tree.expandItem(parent)

                item = QtWidgets.QTreeWidgetItem(parent)
                item.setText(0, new_item)
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled)

            else:
                # Add 1 to item name and try again

                new_item_num += 1
                add_tree_item(tree_top, tree, new_item_num)

        def save_setup_settings():

            def create_dict(tree):
                '''
                Convert tree's into dictionaries to save to config
                '''

                def get_items_recursively():

                    # Create empty list for all folder paths

                    self.path_list = []

                    # Iterate through folders to get paths through get_tree_path

                    def search_child_item(item=None):
                        if not item:
                            return
                        for m in range(item.childCount()):
                            child_item = item.child(m)
                            get_tree_path(child_item)
                            if not child_item:
                                continue
                            search_child_item(child_item)

                    for i in range(tree.topLevelItemCount()):
                        item = tree.topLevelItem(i)
                        if not item:
                            continue
                        search_child_item(item)

                def get_tree_path(item):

                    # Get path of each child item

                    path = []

                    while item is not None:
                        path.append(str(item.text(0)))
                        item = item.parent()
                    item_path = '/'.join(reversed(path))
                    self.path_list.append(item_path)

                get_items_recursively()

                # Create empty dictionary for paths

                path_dict = {}

                # Convert path list to dictionary

                for path in self.path_list:
                    p = path_dict
                    for x in path.split('/'):
                        p = p.setdefault(x, {})

                return path_dict

            def clip_dest(lineedit, tree_dict):

                # Make sure entry destination exists in current folder/reel tree

                for key, value in iter(tree_dict.items()):
                    for v in value:
                        if v == str(lineedit.text()):
                            return True
                return False

            def check_tree_path(tree_top, tree):

                def get_items_recursively():

                    # Create empty list for all folder paths

                    self.file_system_folder_tree_path_list = []

                    # Iterate through folders to get paths through get_tree_path

                    def search_child_item(item=None):
                        if not item:
                            return
                        for m in range(item.childCount()):
                            child_item = item.child(m)
                            get_tree_path(child_item)
                            if not child_item:
                                continue
                            search_child_item(child_item)

                    for i in range(tree.topLevelItemCount()):
                        item = tree.topLevelItem(i)
                        if not item:
                            continue
                        search_child_item(item)

                def get_tree_path(item):

                    # Get path of each child item

                    path = []

                    while item is not None:
                        path.append(str(item.text(0)))
                        item = item.parent()
                    item_path = '/'.join(reversed(path))
                    self.file_system_folder_tree_path_list.append(item_path)
                    self.set_export_folder_path = path

                get_items_recursively()

            check_tree_path(self.file_system_folder_tree_top, self.file_system_folder_tree)
            folder_dict = create_dict(self.folder_tree)
            reel_dict = create_dict(self.schematic_reel_tree)

            if not self.preset_name_lineedit.text():
                return FlameMessageWindow('Error', 'error', 'Preset must have a name')

            if self.file_system_export_dest_label_02.text() not in self.file_system_folder_tree_path_list:
                return FlameMessageWindow('Error', 'error', 'Export Destination folder must exist in File System Shot Folder Template')

            if not clip_dest(self.setup_folder_clip_dest_label_02, folder_dict):
                return FlameMessageWindow('Error', 'error', 'Clip destination folder must exist in Shot Folder Template')

            if not clip_dest(self.setup_batch_clip_dest_reel_label_02, reel_dict):
                return FlameMessageWindow('Error', 'error', 'Clip destination reel must exist in Batch Group Template')

            if not any([self.setup_folders_pushbutton.isChecked(), self.setup_batch_group_pushbutton.isChecked(), self.setup_desktop_pushbutton.isChecked(), self.setup_system_folders_pushbutton.isChecked()]):
                return FlameMessageWindow('Error', 'error', 'At least one Create Shot Type must be selected ')

            if self.setup_batch_template_pushbutton.isChecked():
                if not self.setup_batch_template_path_lineedit.text():
                    return FlameMessageWindow('Error', 'error', 'Select batch setup to use as batch template')

                elif not os.path.isfile(self.setup_batch_template_path_lineedit.text()):
                    return FlameMessageWindow('Error', 'error', 'Select valid batch setup')

                elif not self.setup_batch_template_path_lineedit.text().endswith('.batch'):
                    return FlameMessageWindow('Error', 'error', 'Selected file should be batch setup')

            if self.setup_export_plates_pushbutton.isChecked() and self.setup_export_preset_push_btn.text() == 'Select Preset':
                return FlameMessageWindow('Error', 'error', 'An Export Preset must be selected')

            if self.setup_export_plates_pushbutton.isChecked() and self.setup_export_preset_push_btn.text() == 'No Presets Found':
                return FlameMessageWindow('Error', 'error', 'Save an export preset in Flame to be used')

            batch_group_dest = self.setup_batch_group_dest_btn.text()

            if self.setup_folders_pushbutton.isChecked() or self.setup_desktop_pushbutton.isChecked():
                batch_group_dest = 'Library'

            preset_name_text = self.preset_name_lineedit.text()

            # Check if preset already exists with current name. Give option to delete.

            if [f for f in os.listdir(self.preset_path) if f[:-4] == preset_name_text]:
                if FlameMessageWindow('Confirm Operation', 'warning', f'Overwrite existing preset: {preset_name_text}'):
                    os.remove(os.path.join(self.preset_path, preset_name_text + '.xml'))
                else:
                    return

            # Save empty preset file

            preset_name_text = self.preset_name_lineedit.text()
            preset_xml_path = os.path.join(self.preset_path, preset_name_text + '.xml')

            try:
                os.remove(os.path.join(self.preset_path, preset_name_text + '.xml'))
            except:
                pass

            # Save empty preset file

            preset = """
<settings>
    <create_shot_preset>
        <preset_name></preset_name>
        <shot_name_from></shot_name_from>

        <shot_folders></shot_folders>
        <file_system_folders></file_system_folders>
        <schematic_reels></schematic_reels>
        <shelf_reels></shelf_reels>
        <reel_group_reels></reel_group_reels>

        <export_dest_folder></export_dest_folder>

        <add_reel_group></add_reel_group>
        <add_render_node></add_render_node>
        <add_write_node></add_write_node>

        <write_file_media_path></write_file_media_path>
        <write_file_pattern></write_file_pattern>
        <write_file_create_open_clip></write_file_create_open_clip>
        <write_file_include_setup></write_file_include_setup>
        <write_file_create_open_clip_value></write_file_create_open_clip_value>
        <write_file_include_setup_value></write_file_include_setup_value>
        <write_file_image_format></write_file_image_format>
        <write_file_compression></write_file_compression>
        <write_file_padding></write_file_padding>
        <write_file_frame_index></write_file_frame_index>
        <write_file_iteration_padding></write_file_iteration_padding>
        <write_file_version_name></write_file_version_name>

        <create_shot_type_folders></create_shot_type_folders>
        <create_shot_type_batch_group></create_shot_type_batch_group>
        <create_shot_type_desktop></create_shot_type_desktop>
        <create_shot_type_system_folders></create_shot_type_system_folders>
        <create_shot_export_plates></create_shot_export_plates>
        <create_shot_export_plate_preset></create_shot_export_plate_preset>
        <create_shot_fg_export></create_shot_fg_export>

        <system_shot_folders_path></system_shot_folders_path>
        <clip_destination_folder></clip_destination_folder>
        <clip_destination_reel></clip_destination_reel>
        <setup_batch_template></setup_batch_template>
        <setup_batch_template_path></setup_batch_template_path>
        <setup_batch_group_dest></setup_batch_group_dest>
        <setup_batch_start_frame></setup_batch_start_frame>
        <setup_batch_additional_naming></setup_batch_additional_naming>
    </create_shot_preset>
</settings>"""

            with open(preset_xml_path, 'a') as xml_file:
                xml_file.write(preset)
                xml_file.close()

            # Save settings to preset file

            xml_tree = ET.parse(preset_xml_path)
            root = xml_tree.getroot()

            preset_name = root.find('.//preset_name')
            preset_name.text = preset_name_text

            shot_name_from = root.find('.//shot_name_from')
            shot_name_from.text = self.shot_name_from_push_button.text()

            shot_folders = root.find('.//shot_folders')
            shot_folders.text = str(create_dict(self.folder_tree))

            file_system_folders = root.find('.//file_system_folders')
            file_system_folders.text = str(create_dict(self.file_system_folder_tree))

            schematic_reels = root.find('.//schematic_reels')
            schematic_reels.text = str(create_dict(self.schematic_reel_tree))

            shelf_reels = root.find('.//shelf_reels')
            shelf_reels.text = str(create_dict(self.shelf_reel_tree))

            reel_group_reels = root.find('.//reel_group_reels')
            reel_group_reels.text = str(create_dict(self.reel_group_tree))

            add_reel_group = root.find('.//add_reel_group')
            add_reel_group.text = str(self.add_reel_group_btn.isChecked())

            add_render_node = root.find('.//add_render_node')
            add_render_node.text = str(self.add_render_node_btn.isChecked())

            add_write_node = root.find('.//add_write_node')
            add_write_node.text = str(self.add_write_file_node_btn.isChecked())

            export_dest_folder = root.find('.//export_dest_folder')
            export_dest_folder.text = self.file_system_export_dest_label_02.text()

            create_shot_type_folders = root.find('.//create_shot_type_folders')
            create_shot_type_folders.text = str(self.setup_folders_pushbutton.isChecked())

            create_shot_type_batch_group = root.find('.//create_shot_type_batch_group')
            create_shot_type_batch_group.text = str(self.setup_batch_group_pushbutton.isChecked())

            create_shot_type_desktop = root.find('.//create_shot_type_desktop')
            create_shot_type_desktop.text = str(self.setup_desktop_pushbutton.isChecked())

            create_shot_type_system_folders = root.find('.//create_shot_type_system_folders')
            create_shot_type_system_folders.text = str(self.setup_system_folders_pushbutton.isChecked())

            # create_shot_cache_on_import = root.find('.//create_shot_cache_on_import')
            # create_shot_cache_on_import.text = str(self.setup_cache_on_import_pushbutton.isChecked())

            create_shot_export_plates = root.find('.//create_shot_export_plates')
            create_shot_export_plates.text = str(self.setup_export_plates_pushbutton.isChecked())

            create_shot_export_plate_preset = root.find('.//create_shot_export_plate_preset')
            create_shot_export_plate_preset.text = self.setup_export_preset_push_btn.text()

            create_shot_fg_export = root.find('.//create_shot_fg_export')
            create_shot_fg_export.text = str(self.setup_foreground_export_pushbutton.isChecked())

            system_shot_folders_path = root.find('.//system_shot_folders_path')
            system_shot_folders_path.text = self.setup_system_shot_folders_path_lineedit.text()

            clip_destination_folder = root.find('.//clip_destination_folder')
            clip_destination_folder.text = str(self.setup_folder_clip_dest_label_02.text())

            clip_destination_reel = root.find('.//clip_destination_reel')
            clip_destination_reel.text = str(self.setup_batch_clip_dest_reel_label_02.text())

            setup_batch_template = root.find('.//setup_batch_template')
            setup_batch_template.text = str(self.setup_batch_template_pushbutton.isChecked())

            setup_batch_template_path = root.find('.//setup_batch_template_path')
            setup_batch_template_path.text = self.setup_batch_template_path_lineedit.text()

            setup_batch_group_dest = root.find('.//setup_batch_group_dest')
            setup_batch_group_dest.text = batch_group_dest

            setup_batch_start_frame = root.find('.//setup_batch_start_frame')
            setup_batch_start_frame.text = self.setup_batch_start_frame_slider.text()

            setup_batch_additional_naming = root.find('.//setup_batch_additional_naming')
            setup_batch_additional_naming.text = self.setup_batch_additional_naming_lineedit.text()

            # Write file values

            write_file_media_path = root.find('.//write_file_media_path')
            write_file_media_path.text = self.write_file_media_path

            write_file_pattern = root.find('.//write_file_pattern')
            write_file_pattern.text = self.write_file_pattern

            write_file_create_open_clip = root.find('.//write_file_create_open_clip')
            write_file_create_open_clip.text = str(self.write_file_create_open_clip)

            write_file_include_setup = root.find('.//write_file_include_setup')
            write_file_include_setup.text = str(self.write_file_include_setup)

            write_file_create_open_clip_value = root.find('.//write_file_create_open_clip_value')
            write_file_create_open_clip_value.text = self.write_file_create_open_clip_value

            write_file_include_setup_value = root.find('.//write_file_include_setup_value')
            write_file_include_setup_value.text = self.write_file_include_setup_value

            write_file_image_format = root.find('.//write_file_image_format')
            write_file_image_format.text = self.write_file_image_format

            write_file_compression = root.find('.//write_file_compression')
            write_file_compression.text = self.write_file_compression

            write_file_padding = root.find('.//write_file_padding')
            write_file_padding.text = self.write_file_padding

            write_file_frame_index = root.find('.//write_file_frame_index')
            write_file_frame_index.text = self.write_file_frame_index

            write_file_iteration_padding = root.find('.//write_file_iteration_padding')
            write_file_iteration_padding.text = self.write_file_iteration_padding

            write_file_version_name = root.find('.//write_file_version_name')
            write_file_version_name.text = self.write_file_version_name

            xml_tree.write(preset_xml_path)

            # Remove old preset if preset name is changed.

            if self.preset_name and preset_name_text != self.preset_name:
                os.remove(os.path.join(self.preset_path, self.preset_name + '.xml'))

            # Update config

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            if self.preset_global_default_pushbutton.isChecked():
                global_default = root.find('.//global_default')
                global_default.text = preset_name_text
                preset_name_text = preset_name_text + '*'

                xml_tree.write(self.config_xml)

            # Close setup window and reload settings

            self.setup_window.close()

            print ('--> preset saved \n')

            self.selector_window.close()

            self.preset_selector()

            self.current_preset_push_btn.setText(preset_name_text)

        def render_button_toggle():
            if self.add_render_node_btn.isChecked():
                self.add_write_file_node_btn.setChecked(False)
                self.write_file_setup_btn.setDisabled(True)
            else:
                self.add_write_file_node_btn.setChecked(True)
                self.write_file_setup_btn.setDisabled(False)

        def write_file_button_toggle():
            if self.add_write_file_node_btn.isChecked():
                self.add_render_node_btn.setChecked(False)
                self.write_file_setup_btn.setDisabled(False)
            else:
                self.add_render_node_btn.setChecked(True)
                self.write_file_setup_btn.setDisabled(True)

                vbox = QtWidgets.QVBoxLayout()

        vbox = QtWidgets.QVBoxLayout()
        self.setup_window = FlameWindow(f'Create Shot - Preset Setup <small>{VERSION}', vbox, 1000, 620)

        # Tabs

        self.main_tabs = QtWidgets.QTabWidget()

        self.setup_window.tab1 = QtWidgets.QWidget()
        self.setup_window.tab2 = QtWidgets.QWidget()
        self.setup_window.tab3 = QtWidgets.QWidget()
        self.setup_window.tab4 = QtWidgets.QWidget()
        self.setup_window.tab5 = QtWidgets.QWidget()
        self.setup_window.tab6 = QtWidgets.QWidget()

        self.main_tabs.addTab(self.setup_window.tab6, 'Preset')
        self.main_tabs.addTab(self.setup_window.tab5, 'File System Folders')
        self.main_tabs.addTab(self.setup_window.tab1, 'Media Panel Folders')
        self.main_tabs.addTab(self.setup_window.tab2, 'Batch Groups')
        self.main_tabs.addTab(self.setup_window.tab3, 'Desktops')
        self.main_tabs.addTab(self.setup_window.tab4, 'Shot Options')

        setup_preset_tab()
        setup_folder_tab()
        setup_file_system_folders_tab()
        setup_batch_group_tab()
        setup_desktop_tab()
        setup_options_tab()

        flame_version_check()

        # UI Widget Layout

        vbox.setMargin(15)

        vbox.addWidget(self.main_tabs)

        self.setup_window.show()

        return self.setup_window

    def write_file_node_setup(self):

        def media_path_browse():

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.write_file_setup_window, 'Select Directory', self.write_file_media_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.write_file_media_path_lineedit.setText(file_path)

        def set_write_file_values():

            if not self.write_file_media_path_lineedit.text():
                FlameMessageWindow('Error', 'error', 'Enter Media Path')
            elif not os.path.isdir(self.write_file_media_path_lineedit.text()):
                FlameMessageWindow('Error', 'error', 'Enter Valid Media Path')
            elif not self.write_file_pattern_lineedit.text():
                FlameMessageWindow('Error', 'error', 'Enter Pattern for image files')
            elif not self.write_file_create_open_clip_lineedit.text():
                FlameMessageWindow('Error', 'error', 'Enter Create Open Clip Naming')
            elif not self.write_file_include_setup_lineedit.text():
                FlameMessageWindow('Error', 'error', 'Enter Include Setup Naming')
            elif not self.write_file_version_name_lineedit.text():
                FlameMessageWindow('Error', 'error', 'Enter Version Naming')
            else:
                self.write_file_media_path = self.write_file_media_path_lineedit.text()
                self.write_file_pattern = self.write_file_pattern_lineedit.text()
                self.write_file_create_open_clip = self.write_file_create_open_clip_btn.isChecked()
                self.write_file_include_setup = self.write_file_include_setup_btn.isChecked()
                self.write_file_create_open_clip_value = self.write_file_create_open_clip_lineedit.text()
                self.write_file_include_setup_value = self.write_file_include_setup_lineedit.text()
                self.write_file_image_format = self.write_file_image_format_push_btn.text()
                self.write_file_compression = self.write_file_compression_push_btn.text()
                self.write_file_padding = self.write_file_padding_slider.text()
                self.write_file_frame_index = self.write_file_frame_index_push_btn.text()
                self.write_file_iteration_padding = self.write_file_iteration_padding_slider.text()
                self.write_file_version_name = self.write_file_version_name_lineedit.text()

                self.write_file_setup_window.close()

        gridbox = QtWidgets.QGridLayout()
        self.write_file_setup_window = FlameWindow(f'Create Shot - Write File Node Setup <small>{VERSION}', gridbox, 1000, 570, window_bar_color='green')

        # Labels

        self.write_file_setup_label = FlameLabel('Write File Node Setup', label_type='underline')
        self.write_file_media_path_label = FlameLabel('Media Path')
        self.write_file_pattern_label = FlameLabel('Pattern')
        self.write_file_type_label = FlameLabel('File Type')
        self.write_file_frame_index_label = FlameLabel('Frame Index')
        self.write_file_padding_label = FlameLabel('Padding')
        self.write_file_compression_label = FlameLabel('Compression')
        self.write_file_settings_label = FlameLabel('Settings', label_type='underline')
        self.write_file_iteration_padding_label = FlameLabel('Iteration Padding')
        self.write_file_version_name_label = FlameLabel('Version Name')

        # LineEdits

        self.write_file_media_path_lineedit = FlameLineEdit(self.write_file_media_path)
        self.write_file_pattern_lineedit = FlameLineEdit(self.write_file_pattern)
        self.write_file_create_open_clip_lineedit = FlameLineEdit(self.write_file_create_open_clip_value)
        self.write_file_include_setup_lineedit = FlameLineEdit(self.write_file_include_setup_value)
        self.write_file_version_name_lineedit = FlameLineEdit(self.write_file_version_name)

        # Sliders

        self.write_file_padding_slider = FlameSlider(int(self.write_file_padding), 1, 20, False)
        self.write_file_iteration_padding_slider = FlameSlider(int(self.write_file_iteration_padding), 1, 10, False)

        # Image format pushbutton

        image_format_menu = QtWidgets.QMenu(self.write_file_setup_window)
        image_format_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#2d3744; border: none; font: 14px "Discreet"}'
                                        'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.write_file_image_format_push_btn = QtWidgets.QPushButton(self.write_file_image_format)
        self.write_file_image_format_push_btn.setMenu(image_format_menu)
        self.write_file_image_format_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.write_file_image_format_push_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.write_file_image_format_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.write_file_image_format_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #2d3744; border: none; font: 14px "Discreet"}'
                                                            'QPushButton:hover {border: 1px solid #5a5a5a}'
                                                            'QPushButton:disabled {color: #747474; background-color: #2d3744; border: none}'
                                                            'QPushButton::menu-indicator { image: none; }')

        # -------------------------------------------------------------

        def compression(file_format):

            def create_menu(option):
                self.write_file_compression_push_btn.setText(option)

            compression_menu.clear()
            # compression_list = []

            self.write_file_image_format_push_btn.setText(file_format)

            if 'Dpx' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'Pixspan', 'Packed']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Jpeg' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'OpenEXR' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'Scanline', 'Multi_Scanline', 'RLE', 'PXR24', 'PIZ', 'DWAB', 'DWAA', 'B44A', 'B44']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Png' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'Sgi' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'RLE']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Targa' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'Tiff' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'RLE', 'LZW']
                self.write_file_compression_push_btn.setEnabled(True)

            for option in compression_list:
                compression_menu.addAction(option, partial(create_menu, option))

        image_format_menu.addAction('Dpx 8-bit', partial(compression, 'Dpx 8-bit'))
        image_format_menu.addAction('Dpx 10-bit', partial(compression, 'Dpx 10-bit'))
        image_format_menu.addAction('Dpx 12-bit', partial(compression, 'Dpx 12-bit'))
        image_format_menu.addAction('Dpx 16-bit', partial(compression, 'Dpx 16-bit'))
        image_format_menu.addAction('Jpeg 8-bit', partial(compression, 'Jpeg 8-bit'))
        image_format_menu.addAction('OpenEXR 16-bit fp', partial(compression, 'OpenEXR 16-bit fp'))
        image_format_menu.addAction('OpenEXR 32-bit fp', partial(compression, 'OpenEXR 32-bit fp'))
        image_format_menu.addAction('Png 8-bit', partial(compression, 'Png 8-bit'))
        image_format_menu.addAction('Png 16-bit', partial(compression, 'Png 16-bit'))
        image_format_menu.addAction('Sgi 8-bit', partial(compression, 'Sgi 8-bit'))
        image_format_menu.addAction('Sgi 16-bit', partial(compression, 'Sgi 16-bit'))
        image_format_menu.addAction('Targa 8-bit', partial(compression, 'Targa 8-bit'))
        image_format_menu.addAction('Tiff 8-bit', partial(compression, 'Tiff 8-bit'))
        image_format_menu.addAction('Tiff 16-bit', partial(compression, 'Tiff 16-bit'))

        compression_menu = QtWidgets.QMenu(self.write_file_setup_window)
        compression_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#2d3744; border: none; font: 14px "Discreet"}'
                                       'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.write_file_compression_push_btn = QtWidgets.QPushButton(self.write_file_compression)
        self.write_file_compression_push_btn.setMenu(compression_menu)
        self.write_file_compression_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.write_file_compression_push_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.write_file_compression_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.write_file_compression_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #2d3744; border: none; font: 14px "Discreet"}'
                                                           'QPushButton:hover {border: 1px solid #5a5a5a}'
                                                           'QPushButton:disabled {color: #747474; background-color: #2d3744; border: none}'
                                                           'QPushButton::menu-indicator { image: none; }')
        self.write_file_compression_push_btn.setText(self.write_file_compression)

        # Frame Index Pushbutton Menu

        frame_index = ['Use Start Frame', 'Use Timecode']
        self.write_file_frame_index_push_btn = FlamePushButtonMenu(self.write_file_frame_index, frame_index)

        # Token Push Buttons

        write_file_token_dict = {'Batch Name': '<batch name>', 'Batch Iteration': '<batch iteration>', 'Iteration': '<iteration>',
                                 'Project': '<project>', 'Project Nickname': '<project nickname>', 'Shot Name': '<shot name>', 'Clip Height': '<height>',
                                 'Clip Width': '<width>', 'Clip Name': '<name>', }

        self.write_file_pattern_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_pattern_lineedit)
        self.write_file_open_clip_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_create_open_clip_lineedit)
        self.write_file_include_setup_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_include_setup_lineedit)

        # Pushbuttons

        def write_file_create_open_clip_btn_check():
            if self.write_file_create_open_clip_btn.isChecked():
                self.write_file_create_open_clip_lineedit.setDisabled(False)
                self.write_file_open_clip_token_btn.setDisabled(False)
            else:
                self.write_file_create_open_clip_lineedit.setDisabled(True)
                self.write_file_open_clip_token_btn.setDisabled(True)

        self.write_file_create_open_clip_btn = FlamePushButton('Create Open Clip', self.write_file_create_open_clip)
        self.write_file_create_open_clip_btn.clicked.connect(write_file_create_open_clip_btn_check)
        write_file_create_open_clip_btn_check()

        def write_file_include_setup_btn_check():
            if self.write_file_include_setup_btn.isChecked():
                self.write_file_include_setup_lineedit.setDisabled(False)
                self.write_file_include_setup_token_btn.setDisabled(False)
            else:
                self.write_file_include_setup_lineedit.setDisabled(True)
                self.write_file_include_setup_token_btn.setDisabled(True)

        self.write_file_include_setup_btn = FlamePushButton('Include Setup', self.write_file_include_setup)
        self.write_file_include_setup_btn.clicked.connect(write_file_include_setup_btn_check)
        write_file_include_setup_btn_check()

        # Buttons

        self.write_file_browse_btn = FlameButton('Browse', media_path_browse)
        self.write_file_done_btn = FlameButton('Done', set_write_file_values)
        self.write_file_cancel_btn = FlameButton('Cancel', self.write_file_setup_window.close)

        # ------------------------------------------------------------- #

        compression(self.write_file_image_format_push_btn.text())
        self.write_file_compression_push_btn.setText(self.write_file_compression)

        # UI Widget layout

        gridbox.setMargin(20)
        gridbox.setVerticalSpacing(5)
        gridbox.setHorizontalSpacing(5)
        gridbox.setRowStretch(3, 2)
        gridbox.setRowStretch(6, 2)
        gridbox.setRowStretch(9, 2)

        gridbox.addWidget(self.write_file_setup_label, 0, 0, 1, 6)

        gridbox.addWidget(self.write_file_media_path_label, 1, 0)
        gridbox.addWidget(self.write_file_media_path_lineedit, 1, 1, 1, 4)
        gridbox.addWidget(self.write_file_browse_btn, 1, 5)

        gridbox.addWidget(self.write_file_pattern_label, 2, 0)
        gridbox.addWidget(self.write_file_pattern_lineedit, 2, 1, 1, 4)
        gridbox.addWidget(self.write_file_pattern_token_btn, 2, 5)

        gridbox.addWidget(self.write_file_create_open_clip_btn, 4, 0)
        gridbox.addWidget(self.write_file_create_open_clip_lineedit, 4, 1, 1, 4)
        gridbox.addWidget(self.write_file_open_clip_token_btn, 4, 5)

        gridbox.addWidget(self.write_file_include_setup_btn, 5, 0)
        gridbox.addWidget(self.write_file_include_setup_lineedit, 5, 1, 1, 4)
        gridbox.addWidget(self.write_file_include_setup_token_btn, 5, 5)

        gridbox.setRowMinimumHeight(6, 28)

        gridbox.addWidget(self.write_file_settings_label, 7, 0, 1, 5)
        gridbox.addWidget(self.write_file_frame_index_label, 8, 0)
        gridbox.addWidget(self.write_file_frame_index_push_btn, 8, 1)
        gridbox.addWidget(self.write_file_type_label, 9, 0)
        gridbox.addWidget(self.write_file_image_format_push_btn, 9, 1)
        gridbox.addWidget(self.write_file_compression_label, 10, 0)
        gridbox.addWidget(self.write_file_compression_push_btn, 10, 1)

        gridbox.addWidget(self.write_file_padding_label, 8, 3)
        gridbox.addWidget(self.write_file_padding_slider, 8, 4)
        gridbox.addWidget(self.write_file_iteration_padding_label, 9, 3)
        gridbox.addWidget(self.write_file_iteration_padding_slider, 9, 4)

        gridbox.addWidget(self.write_file_version_name_label, 10, 3)
        gridbox.addWidget(self.write_file_version_name_lineedit, 10, 4)

        gridbox.addWidget(self.write_file_done_btn, 12, 5)
        gridbox.addWidget(self.write_file_cancel_btn, 13, 5)

        self.write_file_setup_window.setLayout(gridbox)

        self.write_file_setup_window.show()

    def custom_shot_from_selected_window(self):

        def create_shots():
            import flame

            def save_settings():

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                all_clips = root.find('.//all_clips')
                all_clips.text = str(self.custom_all_clips_btn.isChecked())

                shot_name = root.find('.//shot_name')
                shot_name.text = str(self.custom_shot_name_btn.isChecked())

                clip_name = root.find('.//clip_name')
                clip_name.text = str(self.custom_clip_name_btn.isChecked())

                custom_folders = root.find('.//custom_folders')
                custom_folders.text = str(self.custom_folders_btn.isChecked())

                custom_batch_group = root.find('.//custom_batch_group')
                custom_batch_group.text = str(self.custom_batch_group_btn.isChecked())

                custom_desktop = root.find('.//custom_desktop')
                custom_desktop.text = str(self.custom_desktop_btn.isChecked())

                custom_system_folders = root.find('.//custom_system_folders')
                custom_system_folders.text = str(self.custom_system_folders_btn.isChecked())

                custom_export_plates = root.find('.//custom_export_plates')
                custom_export_plates.text = str(self.custom_export_plates_btn.isChecked())

                custom_export_preset = root.find('.//custom_export_preset')
                custom_export_preset.text = self.custom_export_preset_push_btn.text()

                custom_foreground_export = root.find('.//custom_foreground_export')
                custom_foreground_export.text = str(self.custom_foreground_export_btn.isChecked())

                custom_system_folders_path = root.find('.//custom_system_folders_path')
                custom_system_folders_path.text = self.custom_system_folders_path_lineedit.text()

                custom_apply_batch_template = root.find('.//custom_apply_batch_template')
                custom_apply_batch_template.text = str(self.custom_batch_template_btn.isChecked())

                custom_batch_template_path = root.find('.//custom_batch_template_path')
                custom_batch_template_path.text = self.custom_batch_template_lineedit.text()

                custom_batch_group_dest = root.find('.//custom_batch_group_dest')
                custom_batch_group_dest.text = self.custom_batch_group_dest_btn.text()

                custom_batch_start_frame = root.find('.//custom_batch_start_frame')
                custom_batch_start_frame.text = self.custom_batch_start_frame_slider.text()

                custom_batch_additional_naming = root.find('.//custom_batch_additional_naming')
                custom_batch_additional_naming.text = self.custom_batch_additional_naming_lineedit.text()

                xml_tree.write(self.config_xml)

                print ('\n--> settings saved \n')

            # Check that at least on shot creation type is selection

            if not any ([self.custom_folders_btn.isChecked(), self.custom_desktop_btn.isChecked(), self.custom_batch_group_btn.isChecked(), self.custom_system_folders_btn.isChecked()]):
                return FlameMessageWindow('Error', 'error', 'Select shot type to create')

            # If apply batch template is enabled, check batch path is valid

            if self.custom_batch_template_btn.isChecked():
                if not os.path.isfile(self.custom_batch_template_lineedit.text()):
                    return FlameMessageWindow('Error', 'error', 'Select valid batch setup to use as shot template')

            if self.custom_export_plates_btn.isChecked() and self.custom_export_preset_push_btn.text() == 'Select Preset':
                return FlameMessageWindow('Error', 'error', 'Select export preset')

            if self.custom_export_plates_btn.isChecked() and self.custom_export_preset_push_btn.text() == 'No Presets Found':
                return FlameMessageWindow('Error', 'error', 'Save a Flame export preset then try again')

            # Save settings

            save_settings()

            # Create list of shot names

            # shot_name_list = []

            #print ('shot_name_list:', shot_name_list)
            #print ('selection:', self.selection)

            # Apply button settings to global settings

            self.create_shot_type_folders = self.custom_folders_btn.isChecked()
            self.create_shot_type_desktop = self.custom_desktop_btn.isChecked()
            self.create_shot_type_batch_group = self.custom_batch_group_btn.isChecked()
            self.create_shot_type_system_folders = self.custom_system_folders_btn.isChecked()
            self.create_shot_export_plates = self.custom_export_plates_btn.isChecked()
            self.create_shot_export_plate_preset = self.custom_export_preset_push_btn.text()
            self.create_shot_fg_export = self.custom_foreground_export_btn.isChecked()

            self.apply_batch_template = self.custom_batch_template_btn.isChecked()
            self.batch_template_path = str(self.custom_batch_template_lineedit.text())
            self.batch_group_dest = self.custom_batch_group_dest_btn.text()
            if self.custom_folders_btn.isChecked() or self.custom_desktop_btn.isChecked():
                self.batch_group_dest = 'Library'
            self.system_shot_folders_path = self.custom_system_folders_path_lineedit.text()

            self.batch_start_frame = int(self.custom_batch_start_frame_slider.text())
            self.batch_additional_naming = self.custom_batch_additional_naming_lineedit.text()

            delete_temp_library = False

            # If selection is clips on a timeline, match out the clips to a temp library then create selection list from library

            if self.selection[0].type == 'Video Segment':

                delete_temp_library = True

                # Create temp library

                self.temp_lib = self.ws.create_library('Create_Shot_Temp_Library')

                # Match out selected clips from timeline into temporary library

                for clip in self.selection:
                    clip.match(self.temp_lib)# , include_timeline_fx = timelinefx)

                self.selection = self.temp_lib.clips

            # Create shots

            if self.custom_all_clips_btn.isChecked() and self.custom_shot_name_btn.isChecked():
                self.shot_name_from = 'Shot Name'
                self.all_clips_to_shot()

            elif self.custom_all_clips_btn.isChecked() and self.custom_clip_name_btn.isChecked():
                self.shot_name_from = 'Clip Name'
                self.all_clips_to_shot()

            elif not self.custom_all_clips_btn.isChecked() and self.custom_shot_name_btn.isChecked():
                self.shot_name_from = 'Shot Name'
                self.clips_to_shots()

            elif not self.custom_all_clips_btn.isChecked() and self.custom_clip_name_btn.isChecked():
                self.shot_name_from = 'Clip Name'
                self.clips_to_shots()

            self.custom_selected_window.close()

            # Delete temp library if one was created matching shots out of timeline

            if delete_temp_library:

                flame.delete(self.temp_lib)

        def update_system_folder_path():
            shot_name = self.selection[0]
            shot_name = str(shot_name.name)[1:-1]
            self.system_shot_folders_path = self.custom_system_folders_path_lineedit.text()
            self.custom_system_folders_path_translated_label.setText(self.translate_system_shot_folder_path(shot_name))

        def batch_group_button_toggle():
            if self.custom_desktop_btn.isChecked():
                self.custom_batch_group_btn.setChecked(True)
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)

            if self.custom_batch_group_btn.isChecked():
                self.custom_batch_template_btn.setEnabled(True)
                self.custom_batch_group_dest_label.setEnabled(True)
                self.custom_batch_group_dest_btn.setEnabled(True)
                if self.custom_batch_template_btn.isChecked():
                    self.custom_batch_group_template_path_label.setEnabled(True)
                    self.custom_batch_template_lineedit.setEnabled(True)
                    self.custom_batch_template_browse_btn.setEnabled(True)
                if self.custom_desktop_btn.isChecked() or self.custom_folders_btn.isChecked():
                    self.custom_batch_group_dest_label.setEnabled(False)
                    self.custom_batch_group_dest_btn.setEnabled(False)
            else:
                self.custom_batch_template_btn.setEnabled(False)
                self.custom_batch_group_template_path_label.setEnabled(False)
                self.custom_batch_template_lineedit.setEnabled(False)
                self.custom_batch_template_browse_btn.setEnabled(False)
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)

        def folder_toggle():
            if self.custom_folders_btn.isChecked():
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)
            else:
                if self.custom_batch_group_btn.isChecked() and not self.custom_desktop_btn.isChecked():
                    self.custom_batch_group_dest_label.setEnabled(True)
                    self.custom_batch_group_dest_btn.setEnabled(True)

        def desktop_toggle():

            # When desktop button is selected enable batch group button

            if self.custom_desktop_btn.isChecked():
                self.custom_batch_group_btn.setChecked(True)
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)
                self.custom_batch_template_btn.setEnabled(True)
                if self.custom_batch_template_btn.isChecked():
                    self.custom_batch_group_template_path_label.setEnabled(True)
                    self.custom_batch_template_lineedit.setEnabled(True)
                    self.custom_batch_template_browse_btn.setEnabled(True)
            else:
                self.custom_batch_group_btn.setEnabled(True)
                if self.custom_batch_group_btn.isChecked():
                    self.custom_batch_group_dest_label.setEnabled(True)
                    self.custom_batch_group_dest_btn.setEnabled(True)

        def shot_name_toggle():
            self.custom_shot_name_btn.setChecked(True)
            self.custom_clip_name_btn.setChecked(False)

        def clip_name_toggle():
            self.custom_clip_name_btn.setChecked(True)
            self.custom_shot_name_btn.setChecked(False)

        def batch_template_toggle():
            if self.custom_batch_template_btn.isChecked():
                self.custom_batch_group_template_path_label.setEnabled(True)
                self.custom_batch_template_lineedit.setEnabled(True)
                self.custom_batch_template_browse_btn.setEnabled(True)
            else:
                self.custom_batch_group_template_path_label.setEnabled(False)
                self.custom_batch_template_lineedit.setEnabled(False)
                self.custom_batch_template_browse_btn.setEnabled(False)

        def system_folder_toggle():
            if self.custom_system_folders_btn.isChecked():
                self.custom_system_folders_path_translated_label.setEnabled(True)
                self.custom_system_folders_path_lineedit.setEnabled(True)
                self.custom_system_folders_browse_btn.setEnabled(True)
                self.custom_system_path_token_push_button.setEnabled(True)
                self.custom_export_plates_btn.setEnabled(True)
            else:
                self.custom_system_folders_path_translated_label.setEnabled(False)
                self.custom_system_folders_path_lineedit.setEnabled(False)
                self.custom_system_folders_browse_btn.setEnabled(False)
                self.custom_system_path_token_push_button.setEnabled(False)
                self.custom_export_plates_btn.setEnabled(False)

        def export_plate_toggle():
            if self.custom_export_plates_btn.isChecked():
                self.custom_export_preset_label.setEnabled(True)
                self.custom_export_preset_push_btn.setEnabled(True)
                self.custom_foreground_export_btn.setEnabled(True)
            else:
                self.custom_export_preset_label.setEnabled(False)
                self.custom_export_preset_push_btn.setEnabled(False)
                self.custom_foreground_export_btn.setEnabled(False)

        preset_loaded = self.load_preset_values()
        if not preset_loaded:
            return

        grid = QtWidgets.QGridLayout()
        self.custom_selected_window = FlameWindow(f'Create Shot - Custom for Selected Clips <small>{VERSION}', grid, 1200, 540)

        # Labels

        self.custom_batch_options_label = FlameLabel('Batch Group Options', label_type='underline')
        self.custom_batch_group_template_path_label = FlameLabel('Template Path')
        self.custom_batch_group_dest_label = FlameLabel('Batch Group Dest')
        self.custom_batch_group_start_frame_label = FlameLabel('Batch Start Frame')
        self.custom_batch_group_additional_naming_label = FlameLabel('Additional Batch Naming')

        self.custom_system_folders_path_label = FlameLabel('File System Shot Folders Path', label_type='underline')
        self.custom_system_folders_path_translated_label = FlameLabel('', label_type='background')

        self.custom_settings_label = FlameLabel('Settings', label_type='underline')
        self.custom_shot_naming_label = FlameLabel('Shot Naming', label_type='underline')
        self.custom_create_label = FlameLabel('Create', label_type='underline')

        self.custom_export_plate_options_label = FlameLabel('Export Plate Options', label_type='underline')
        self.custom_export_preset_label = FlameLabel('Export Preset')

        # LineEdits

        self.custom_batch_template_lineedit = FlameLineEdit(self.custom_batch_template_path)
        self.custom_batch_additional_naming_lineedit = FlameLineEdit(self.custom_batch_additional_naming)
        self.custom_system_folders_path_lineedit = FlameLineEdit(self.custom_system_folders_path)
        self.custom_system_folders_path_lineedit.textChanged.connect(update_system_folder_path)
        update_system_folder_path()

        # Batch Start Frame Slider

        self.custom_batch_start_frame_slider = FlameSlider(self.custom_batch_start_frame, 1, 10000, False, slider_width=150)

        # Push Button Menus

        batch_group_dest_options = ['Desktop', 'Library']
        self.custom_batch_group_dest_btn = FlamePushButtonMenu(self.custom_batch_group_dest, batch_group_dest_options)
        self.custom_batch_group_dest_btn.setMinimumWidth(150)

        export_preset_list = self.get_export_presets()
        self.custom_export_preset_push_btn = FlamePushButtonMenu(self.custom_export_preset, export_preset_list)

        # Token push button menu

        system_path_token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>', 'SEQUENCE NAME': '<SEQNAME>', 'Sequence Name': '<SeqName>'}
        self.custom_system_path_token_push_button = FlameTokenPushButton('Add Token', system_path_token_dict, self.custom_system_folders_path_lineedit)

        # Pushbuttons

        self.custom_batch_template_btn = FlamePushButton('Batch Template', self.custom_apply_batch_template)
        self.custom_batch_template_btn.clicked.connect(batch_template_toggle)

        self.custom_all_clips_btn = FlamePushButton('All Clips/One Shot', self.all_clips)

        self.custom_shot_name_btn = FlamePushButton('Shot Name', self.shot_name)
        self.custom_shot_name_btn.clicked.connect(shot_name_toggle)

        self.custom_clip_name_btn = FlamePushButton('Clip Name', self.clip_name)
        self.custom_clip_name_btn.clicked.connect(clip_name_toggle)

        self.custom_folders_btn = FlamePushButton('Folders', self.custom_folders)
        self.custom_folders_btn.clicked.connect(folder_toggle)

        self.custom_batch_group_btn = FlamePushButton('Batch Groups', self.custom_batch_group)
        self.custom_batch_group_btn.clicked.connect(batch_group_button_toggle)

        self.custom_desktop_btn = FlamePushButton('Desktops', self.custom_desktop)
        self.custom_desktop_btn.clicked.connect(desktop_toggle)

        self.custom_system_folders_btn = FlamePushButton('System Folders', self.custom_system_folders)
        self.custom_system_folders_btn.clicked.connect(system_folder_toggle)

        self.custom_export_plates_btn = FlamePushButton('Export Plates', self.custom_export_plates)
        self.custom_export_plates_btn.clicked.connect(export_plate_toggle)

        self.custom_foreground_export_btn = FlamePushButton('Foreground Export', self.custom_foreground_export)

        # Buttons

        self.custom_batch_template_browse_btn = FlameButton('Browse', partial(self.batch_template_browse, self.custom_batch_template_lineedit, self.custom_selected_window))
        self.custom_system_folders_browse_btn = FlameButton('Browse', partial(self.system_folder_browse, self.custom_system_folders_path_lineedit, self.custom_selected_window))

        help_btn = FlameButton('Help', self.help)
        create_btn = FlameButton('Create', create_shots)
        cancel_btn = FlameButton('Cancel', self.custom_selected_window.close)

        # Check button states

        desktop_toggle()
        batch_group_button_toggle()
        batch_template_toggle()
        system_folder_toggle()
        export_plate_toggle()

        # ------------------------------------------------------------- #

        # UI Widget layout

        grid.setVerticalSpacing(5)
        grid.setHorizontalSpacing(5)
        grid.setMargin(20)

        grid.setColumnMinimumWidth(2, 30)

        grid.addWidget(self.custom_create_label, 0, 0)
        grid.addWidget(self.custom_folders_btn, 1, 0)
        grid.addWidget(self.custom_batch_group_btn, 2, 0)
        grid.addWidget(self.custom_desktop_btn, 3, 0)
        grid.addWidget(self.custom_system_folders_btn, 4, 0)
        grid.addWidget(self.custom_export_plates_btn, 5, 0)

        grid.addWidget(self.custom_settings_label, 0, 1)
        grid.addWidget(self.custom_all_clips_btn, 1, 1)
        grid.addWidget(self.custom_batch_template_btn, 2, 1)

        grid.addWidget(self.custom_shot_naming_label, 3, 1)
        grid.addWidget(self.custom_shot_name_btn, 4, 1)
        grid.addWidget(self.custom_clip_name_btn, 5, 1)

        grid.addWidget(self.custom_batch_options_label, 0, 4, 1, 5)
        grid.addWidget(self.custom_batch_group_template_path_label, 1, 4)
        grid.addWidget(self.custom_batch_template_lineedit, 1, 5, 1, 3)
        grid.addWidget(self.custom_batch_template_browse_btn, 1, 8)

        grid.addWidget(self.custom_batch_group_dest_label, 3, 4)
        grid.addWidget(self.custom_batch_group_dest_btn, 3, 5)

        grid.addWidget(self.custom_batch_group_start_frame_label, 2, 4)
        grid.addWidget(self.custom_batch_start_frame_slider, 2, 5)

        grid.addWidget(self.custom_batch_group_additional_naming_label, 2, 6)
        grid.addWidget(self.custom_batch_additional_naming_lineedit, 2, 7, 1, 2)

        grid.addWidget(self.custom_system_folders_path_label, 5, 4, 1, 5)
        grid.addWidget(self.custom_system_folders_path_translated_label, 6, 4, 1, 5)
        grid.addWidget(self.custom_system_folders_path_lineedit, 7, 4, 1, 3)
        grid.addWidget(self.custom_system_folders_browse_btn, 7, 7)
        grid.addWidget(self.custom_system_path_token_push_button, 7, 8)

        grid.setRowMinimumHeight(8, 30)

        grid.addWidget(self.custom_export_plate_options_label, 9, 4, 1, 5)
        grid.addWidget(self.custom_export_preset_label, 10, 4)
        grid.addWidget(self.custom_export_preset_push_btn, 10, 5, 1, 3)
        grid.addWidget(self.custom_foreground_export_btn, 10, 8)

        grid.setRowMinimumHeight(11, 30)

        grid.addWidget(help_btn, 12, 0)
        grid.addWidget(cancel_btn, 12, 7)
        grid.addWidget(create_btn, 12, 8)

        self.custom_selected_window.setLayout(grid)

        self.custom_selected_window.show()

    # ------------------------------------- #

    def create_shots(self, shot_name_list):
        '''
        Create shots from selected clips in media panel or media hub using shot name as shot name
        If shot names are not assigned to clips, shot name will be guessed
        '''

        import flame

        # Check for system folder path if creating system folders

        if self.create_shot_type_system_folders and not self.system_shot_folders_path:
            return FlameMessageWindow('Error', 'error', 'Enter path for creating system folders in Setup<br>Flame Main Menu -> pyFlame -> Create Shot Setup')

        if self.create_shot_type_system_folders:
            write_access = os.access(self.translate_system_shot_folder_path(shot_name_list[0]), os.W_OK)
            if not write_access:
                return FlameMessageWindow('Error', 'error', 'No write access to file system path.')

        # All clips are not going to single shot so all_clips is false

        all_clips = False

        if shot_name_list == []:
            return FlameMessageWindow('Error', 'error', 'No Shots Found')

        shot_name_list.sort()
        print ('shot_name_list:', shot_name_list, '\n')

        # If creating folders, batch groups, or desktops, switch to batch so get access to MediaPanel

        if self.current_flame_tab == 'MediaHub':
            flame.set_current_tab('batch')

        # If creating desktops is selected, backup and clear current desktop

        if self.create_shot_type_desktop:
            self.copy_current_desktop()
            self.clear_current_desktop()

        # Create shot type based on saved settings

        print ('--> creating shots:\n')

        if self.create_shot_type_folders:
            self.create_library('Folders')
            for shot_name in shot_name_list:
                self.create_media_panel_folders(shot_name, all_clips)

        elif self.create_shot_type_desktop:
            self.create_library('Desktops')
            for shot_name in shot_name_list:
                self.create_desktop(shot_name, all_clips, self.lib)

        elif self.create_shot_type_batch_group:
            self.create_library('Batch Groups')
            for shot_name in shot_name_list:
                self.create_batch_group(shot_name, all_clips, self.lib)

        # Create system folders if selected in settings

        self.system_folder_creation_errors = []

        if self.create_shot_type_system_folders:
            print ('\n')
            for shot_name in shot_name_list:
                root_folder_path = self.translate_system_shot_folder_path(shot_name)
                self.create_file_system_folders(root_folder_path, shot_name)
                if self.create_shot_export_plates:
                    self.export_plate(root_folder_path, shot_name, all_clips)

        if self.system_folder_creation_errors:
            problem_shots = ''
            for shot in self.system_folder_creation_errors:
                problem_shots = problem_shots + shot + ', '
            return FlameMessageWindow('Error', 'error', f'Could not create folders: {problem_shots[:-2]}. Folders may already exists.')

        # If desktops were created restore original desktop

        if self.create_shot_type_desktop:
            self.replace_desktop()

        print ('\ndone.\n')

    def create_shots_all_clips(self, shot_name):
        '''
        Create one shot from all selected clips in media panel or media hub.
        Uses shot name from first clip selected as shot name.
        '''

        import flame

        # Check for system folder path if creating system folders

        if self.create_shot_type_system_folders and not self.system_shot_folders_path:
                return FlameMessageWindow('Error', 'error', 'Enter path for creating system folders in Setup<br>Flame Main Menu -> pyFlame -> Create Shot Setup')

        all_clips = True

        if not shot_name:
            return FlameMessageWindow('Error', 'error', 'No Shot Found')

        # If creating folders, batch groups, or desktops, switch to batch so get access to MediaPanel

        if self.current_flame_tab == 'MediaHub':
            flame.set_current_tab('batch')

        # If creating desktops is selected, backup and clear current desktop

        if self.create_shot_type_desktop:
            self.copy_current_desktop()
            self.clear_current_desktop()

        # Create shot type based on saved settings

        print ('--> creating shot...')

        if self.create_shot_type_folders:
            self.create_library('Folders')
            self.create_media_panel_folders(shot_name, all_clips)

        elif self.create_shot_type_desktop:
            self.create_library('Desktops')
            self.create_desktop(shot_name, all_clips, self.lib)

        elif self.create_shot_type_batch_group:
            self.create_library('Batch Groups')
            self.create_batch_group(shot_name, all_clips, self.lib)

        # Create system folders if selected in settings

        self.system_folder_creation_errors = []

        if self.create_shot_type_system_folders:
            print ('\n')
            root_folder_path = self.translate_system_shot_folder_path(shot_name)
            self.create_file_system_folders(root_folder_path, shot_name)

        if self.system_folder_creation_errors:
            return FlameMessageWindow('Error', 'error', f'Could not create folders for {shot_name}. Folders may already exists.')

        # If desktops were created restore original desktop

        if self.create_shot_type_desktop:
            self.replace_desktop()

        print ('\ndone.\n')

    # ------------------------------------- #

    def clips_to_shots(self):
        '''
        Create shots for each shot name found in selected shots. One shot is created for each shot name found.
        All clips with the same shot name will be put into the same shot.
        '''

        # Build list of shot names from selected clips using either Shot Name or Clip Name

        shot_name_list = []

        if self.shot_name_from == 'Shot Name':
            for clip in self.selection:

                # Get shot name from assigned clip shot name

                if clip.versions[0].tracks[0].segments[0].shot_name != '':
                    if clip.versions[0].tracks[0].segments[0].shot_name not in shot_name_list:
                        shot_name_list.append(str(clip.versions[0].tracks[0].segments[0].shot_name)[1:-1])
                else:

                    # If shot name not assigned to clip, guess at shot name from clip name

                    new_shot_name = self.get_shot_name_from_clip_name(clip)

                    if new_shot_name not in shot_name_list:
                        shot_name_list.append(new_shot_name)

        elif self.shot_name_from == 'Clip Name':
            shot_name_list = [str(clip.name)[1:-1] for clip in self.selection]

        # Create shots from shot name list

        self.create_shots(shot_name_list)

    def all_clips_to_shot(self):
        '''
        Create one shot from all selected clips. Shot name taken from first clip in selection
        '''

        if self.shot_name_from == 'Shot Name':

            # Get first clip from selection

            clip = self.selection[0]

            # Get shot name from assigned clip shot name

            if clip.versions[0].tracks[0].segments[0].shot_name != '':
                shot_name = str(clip.versions[0].tracks[0].segments[0].shot_name)[1:-1]
            else:
                # If shot name not assigned to clip, guess at shot name from clip name

                shot_name = self.get_shot_name_from_clip_name(clip)

        elif self.shot_name_from == 'Clip Name':
            shot_name = [str(clip.name)[1:-1] for clip in self.selection][0]

        print ('shot_name:', shot_name, '\n')

        # Create shots from shot name list

        self.create_shots_all_clips(shot_name)

    def import_clips_to_shots(self):
        import flame

        # Turn off creating file system folders and exporting plates when importing from mediahub

        self.create_shot_type_system_folders = False
        self.create_shot_export_plates = False

        # Create temp library

        self.temp_lib = self.ws.create_library('-- Temp Shot Library --')
        self.temp_lib.expanded = True
        self.temp_lib_delete = self.temp_lib

        if self.shot_name_from == 'Shot Name':

            # Import selected clips to library

            for clip in self.selection:
                clip_path = str(clip.path)
                print ('clip_path:', clip_path)

                # Import clip to temp library

                flame.import_clips(clip_path, self.temp_lib)

            # Replace selection with clip in temp library

            self.selection = [clip for clip in self.temp_lib.clips]

            # Create shots from all clips in temp library

            shot_name_list = []

            for clip in self.temp_lib.clips:
                new_shot_name = self.get_shot_name_from_clip_name(clip)
                if new_shot_name not in shot_name_list:
                    shot_name_list.append(new_shot_name)

        elif self.shot_name_from == 'Clip Name':

            # Import selected clips to library

            for clip in self.selection:
                clip_path = str(clip.path)
                print ('clip_path:', clip_path)

                # Import clip to temp library

                flame.import_clips(clip_path, self.temp_lib)

            # Replace selection with clip in temp library

            self.selection = [clip for clip in self.temp_lib.clips]

            # Get list of clip names

            shot_name_list = [str(clip.name)[1:-1] for clip in self.selection]

        print ('shot_name_list:', shot_name_list, '\n')

        self.create_shots(shot_name_list)

        # Remove temp library

        flame.delete(self.temp_lib_delete)

    def import_all_clips_to_shot(self):
        import flame

        # Turn off creating file system folders and exporting plates when importing from mediahub

        self.create_shot_type_system_folders = False
        self.create_shot_export_plates = False

        # Create temp library

        self.temp_lib = self.ws.create_library('-- Temp Shot Library --')
        self.temp_lib.expanded = True
        self.temp_lib_delete = self.temp_lib

        if self.shot_name_from == 'Shot Name':

            # Import selected clips to library

            for clip in self.selection:
                clip_path = str(clip.path)
                print ('clip_path:', clip_path)

                # Import clip to batchgroup

                flame.import_clips(clip_path, self.temp_lib)

            # Replace selection with clip in temp library

            self.selection = [clip for clip in self.temp_lib.clips]

            # Create shot from clips in temp library

            clip = self.temp_lib.clips[0]
            shot_name = self.get_shot_name_from_clip_name(clip)

        elif self.shot_name_from == 'Clip Name':

            # Import selected clips to library

            for clip in self.selection:
                clip_path = str(clip.path)
                print ('clip_path:', clip_path)

                # Import clip to temp library

                flame.import_clips(clip_path, self.temp_lib)

            # Replace selection with clip in temp library

            self.selection = [clip for clip in self.temp_lib.clips]

            # Get list of clip names

            shot_name = [str(clip.name)[1:-1] for clip in self.selection][0]

        print ('shot_name:', shot_name, '\n')

        self.create_shots_all_clips(shot_name)

        # Remove temp library

        flame.delete(self.temp_lib_delete)

    # ------------------------------------- #

    def help(self):

        webbrowser.open('https://www.pyflame.com/python-scripts/create-shot')
        print ('openning www.pyflame.com/python-scripts/create-shot...\n')

    def sort_tree_items(self, tree):
        tree.sortItems(0, QtGui.Qt.AscendingOrder)

    def convert_reel_dict(self, reel_dict):

        converted_list = []

        for key, value in iter(reel_dict.items()):
            for v in value:
                converted_list.append(v)

        return converted_list

    def get_shot_name_from_clip_name(self, clip):

        clip_name = str(clip.name)[1:-1]

        # Try to get shot name from assigned clip shot name
        # If assigned shot name notr found try to get name from name of clip

        if clip.versions[0].tracks[0].segments[0].shot_name != '':
            new_shot_name = str(clip.versions[0].tracks[0].segments[0].shot_name)[1:-1]
        else:
            shot_name_split = re.split(r'(\d+)', clip_name)

            if len(shot_name_split) > 1:
                if shot_name_split[1].isalnum():
                    new_shot_name = shot_name_split[0] + shot_name_split[1]
                else:
                    new_shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]
            else:
                new_shot_name = clip_name

        return new_shot_name

    def translate_system_shot_folder_path(self, shot_name):
        import flame

        # print ('path to translate:', self.system_shot_folders_path)

        seq_name = ''
        seq_name_caps = ''

        if '<SeqName>' in self.system_shot_folders_path or '<SEQNAME>' in self.system_shot_folders_path:
            seq_name = re.split('[^a-zA-Z]', shot_name)[0]
            if '<SEQNAME>' in self.system_shot_folders_path:
                seq_name_caps = seq_name.upper()

        # Replace any tokens in system shot folder path

        root_folder_path = re.sub('<ProjectName>', flame.project.current_project.name, self.system_shot_folders_path)
        root_folder_path = re.sub('<ProjectNickName>', flame.project.current_project.nickname, root_folder_path)
        root_folder_path = re.sub('<SeqName>', seq_name, root_folder_path)
        root_folder_path = re.sub('<SEQNAME>', seq_name_caps, root_folder_path)

        # print ('translated root_folder_path:', root_folder_path)

        return root_folder_path

    def copy_current_desktop(self):
        import flame

        # Copy current desktop to Temp Library

        self.temp_lib = self.ws.create_library('Temp__Desk__Lib')

        self.desktop_name = str(self.desktop.name)[1:-1]

        self.desktop_copy = flame.media_panel.copy(self.desktop, self.temp_lib)

    def clear_current_desktop(self):
        import flame

        # Clear out current desktop

        for b in self.desktop.batch_groups:
            flame.delete(b)
        for r in self.desktop.reel_groups:
            flame.delete(r)

    def replace_desktop(self):
        import flame

        # When done creating shot desktops replace original desktop from Temp Library

        flame.media_panel.move(self.desktop_copy, self.ws.desktop)
        flame.delete(self.desktop.batch_groups[0])
        self.ws.desktop.name = self.desktop_name

        print ('TEMP LIB NAME:', self.temp_lib.name)

        for lib in self.ws.libraries:
            print (lib.name)
            if str(lib.name) == str(self.temp_lib.name):
                flame.delete(lib)

        flame.delete(self.temp_lib)

    def copy_clips(self, shot_name, all_clips, dest):
        import flame

        # Copy selected clips into media panel destination

        for clip in self.selection:
            if all_clips:
                clip_copy = flame.media_panel.copy(clip, dest)
            else:
                if shot_name in str(clip.versions[0].tracks[0].segments[0].shot_name) or shot_name in str(clip.name):
                    clip_copy = flame.media_panel.copy(clip, dest)

    def batch_template_browse(self, lineedit, parent_window):

        batch_path = QtWidgets.QFileDialog.getOpenFileName(parent_window, 'Select .batch File', lineedit.text(), 'Batch Files (*.batch)')[0]
        lineedit.setText(batch_path)

    def system_folder_browse(self, lineedit, parent_window):

        dir_path = str(QtWidgets.QFileDialog.getExistingDirectory(parent_window, 'Select Directory', lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))
        if os.path.isdir(dir_path):
            lineedit.setText(dir_path)

    def reveal_path_in_finder(self, path):

        if platform.system() == 'Darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])

        print (f'path opened in finder: {path}\n')

    def get_export_presets(self):

        def check_preset_version(preset_path):
            '''
            Check export presets for flame version compatibility.
            If preset requires newer version of flame, don't list it
            '''

            export_preset_xml_tree = ET.parse(preset_path)
            root = export_preset_xml_tree.getroot()

            # Get version export preset is currently set to

            for setting in root.iter('preset'):
                current_export_version = setting.get('version')

            # Get current flame version whole number

            flame_version = str(self.flame_version)[:4]

            # Set export version for verion of flame being used

            if flame_version == '2021':
                export_version = '10'
            elif flame_version == '2022':
                export_version = '11'
            elif flame_version == '2023':
                export_version = '11'

            # If preset version if different than current export version then update xml

            if current_export_version == export_version:
                return True
            return False

        def add_presets(path, preset_type):
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith('.xml'):
                        preset_name = preset_type + f[:-4]
                        preset_current_version = check_preset_version(os.path.join(root, f))
                        if preset_current_version:
                            export_preset_list.append(preset_name)

        export_preset_list = []

        shared_export_presets_path = '/opt/Autodesk/shared/export/presets'
        project_export_presets_path = os.path.join('/opt/Autodesk/project', self.project_name, 'export/presets/flame')

        add_presets(shared_export_presets_path, 'Shared: ')
        add_presets(project_export_presets_path, 'Project: ')

        if not export_preset_list:
            export_preset_list.append('No Presets Found')

        return export_preset_list

    # ------------------------------------- #
    # Create

    def create_library(self, create_type):

        # Create new library if destination is Library

        if self.batch_group_dest == 'Library' or create_type == 'Folders':
            new_lib_name = f'New Shot {create_type}'
            self.lib = self.ws.create_library(new_lib_name)
            self.lib.expanded = True

            print (f'    library created: {new_lib_name}\n')

    def create_media_panel_folders(self, shot_name, all_clips):
        '''
        Create Shot Folders and copy clips into shot folder
        '''

        def folder_loop(value, shot_folder):
            for k, v in iter(value.items()):
                folder = shot_folder.create_folder(k)
                if self.clip_dest_folder == k:
                    self.copy_clips(shot_name, all_clips, folder)
                folder_loop(v, folder)

        # Create shot folders

        for key1, value1 in iter(self.folder_dict.items()):
            shot_folder = self.lib.create_folder(shot_name)
            print (f'    shot folder created: {shot_name}')

            # Check if main folder is clip dest

            if self.clip_dest_folder == shot_name:
                self.copy_clips(shot_name, all_clips, shot_folder)

            # Check if creating desktop

            if self.create_shot_type_desktop:
                self.create_desktop(shot_name, all_clips, shot_folder)

            # Check if creating batch group

            elif self.create_shot_type_batch_group:
                self.create_batch_group(shot_name, all_clips, shot_folder)

            # Create sub-folders

            folder_loop(value1, shot_folder)

    def create_batch_group(self, shot_name, all_clips, dest):
        import flame

        def set_render_node_values(render_node):

            # Apply values to render node from clip

            render_node.frame_rate = clip_frame_rate
            render_node.range_end = clip.duration
            render_node.source_timecode = clip_timecode
            render_node.record_timecode = clip_timecode
            render_node.shot_name = shot_name
            render_node.tape_name = clip_tape_name
            render_node.range_start = self.batch_start_frame
            render_node.range_end = self.batch_start_frame + self.batch_group.duration - 1

        # Create batch group

        self.batch_group = flame.batch.create_batch_group(shot_name, duration=100, reels=self.schematic_reels, shelf_reels=self.shelf_reels)

        # Set batch start frame

        self.batch_group.start_frame = self.batch_start_frame

        # If creating batch group from selected clip add clip to batch group, add nodes, modify render nodes

        if self.selection:

            # Get index of reel clips will be copied to

            self.clip_reel_index = self.schematic_reels.index(self.clip_dest_reel)

            # Copy clips into batch group

            self.copy_clips(shot_name, all_clips, self.batch_group.reels[self.clip_reel_index])

            # Get background clip

            all_clips = flame.batch.nodes
            clip = flame.batch.nodes[0]

            # Set batch group duration

            self.batch_group.duration = clip.duration

            # Get clip timecode and frame rate

            imported_clip = self.batch_group.reels[self.clip_reel_index].clips[0]
            clip_timecode = imported_clip.start_time
            clip_frame_rate = imported_clip.frame_rate

            # Get clip tape name

            clip_tape_name = (((imported_clip.versions[0]).tracks[0]).segments[0]).tape_name

            # Force batch group name in case duplicate name already exists in desktop

            if self.batch_additional_naming:
                self.batch_group.name = str(shot_name + self.batch_additional_naming)
            else:
                self.batch_group.name = shot_name

            # If Apply Template is select load batch template otherwise use generic default node layout

            if self.apply_batch_template:

                # Append template batch setup to new batch

                self.batch_group.append_setup(self.batch_template_path)

                # Confirm template has plate_in Mux node - if not delete batch and give error message

                plate_in_mux_present = [node.name for node in self.batch_group.nodes if node.name == 'plate_in']

                if not plate_in_mux_present:
                    flame.delete(self.batch_group)
                    return FlameMessageWindow('Error', 'error', 'Batch Template should have Mux node named: plate_in')

                # Check for nodes with context set - Context does not carry over when batch setup is appended.
                # Nodes in template need to have note attached with desired context view: context 1, context 2...
                # Render nodes can not have context set through python

                for node in flame.batch.nodes:
                    if 'context' in str(node.note):
                        print (node.name)
                        context_view = str(node.note).rsplit(' ', 1)[1][:-1]
                        while not context_view.isnumeric():
                            context_view = context_view[:-1]
                        print (context_view)
                        node.set_context(int(context_view))

                # Reposition plate to left of plate_in Mux

                for node in self.batch_group.nodes:
                    if node.name == 'plate_in':
                        plate_in_mux = node

                clip.pos_x = plate_in_mux.pos_x - 300
                clip.pos_y = plate_in_mux.pos_y + 30
                clip_y_pos = clip.pos_y

                # Connect main plate to plate_in Mux

                flame.batch.connect_nodes(clip, 'Default', plate_in_mux, 'Default')

                # Remove main clip from clip list then reposition any additional clips under main plate in schematic

                all_clips.pop(0)

                for additional_clip in all_clips:
                    additional_clip.pos_x = clip.pos_x
                    additional_clip.pos_y = clip_y_pos - 150
                    clip_y_pos = additional_clip.pos_y

                # Apply clip settings to render node

                for node in self.batch_group.nodes:
                    if node.type == 'Render' or node.type == 'Write File':
                        set_render_node_values(node)

            else:

                # Create default node setup
                # Clip -> Mux -> Mux -> Render/Write Node

                # Create mux nodes

                plate_in_mux = self.batch_group.create_node('Mux')
                plate_in_mux.name = 'plate_in'
                plate_in_mux.set_context(1, 'Default')
                plate_in_mux.pos_x = 400
                plate_in_mux.pos_y = -30

                render_out_mux = self.batch_group.create_node('Mux')
                render_out_mux.name = 'render_out'
                render_out_mux.set_context(2, 'Default')
                render_out_mux.pos_x = plate_in_mux.pos_x + 1600
                render_out_mux.pos_y = plate_in_mux.pos_y - 30

                # Add Render or Write File node to batch group

                if self.add_render_node:

                    # Create render node

                    render_node = flame.batch.create_node('Render')

                    # Apply clip settings to render node

                    set_render_node_values(render_node)

                else:

                    # Create write node

                    image_format = self.write_file_image_format.split(' ', 1)[0]
                    bit_depth = self.write_file_image_format.split(' ', 1)[1]

                    render_node = flame.batch.create_node('Write File')
                    render_node.media_path = self.write_file_media_path
                    render_node.media_path_pattern = self.write_file_pattern
                    render_node.create_clip = self.write_file_create_open_clip
                    render_node.include_setup = self.write_file_include_setup
                    render_node.create_clip_path = self.write_file_create_open_clip_value
                    render_node.include_setup_path = self.write_file_include_setup_value
                    render_node.file_type = image_format
                    render_node.bit_depth = bit_depth

                    if self.write_file_compression:
                        render_node.compress = True
                        render_node.compress_mode = self.write_file_compression
                    if image_format == 'Jpeg':
                        render_node.quality = 100

                    render_node.frame_index_mode = self.write_file_frame_index
                    render_node.frame_padding = int(self.write_file_padding)
                    render_node.frame_rate = clip_frame_rate
                    render_node.range_end = clip.duration
                    render_node.source_timecode = clip_timecode
                    render_node.record_timecode = clip_timecode
                    render_node.shot_name = shot_name
                    render_node.range_start = self.batch_start_frame
                    render_node.range_end = self.batch_start_frame + self.batch_group.duration - 1
                    # render_node.name = '<batch iteration>'

                    if self.write_file_create_open_clip:
                        render_node.version_mode = 'Follow Iteration'
                        render_node.version_name = self.write_file_version_name
                        render_node.version_padding = int(self.write_file_iteration_padding)

                render_node.pos_x = render_out_mux.pos_x + 400
                render_node.pos_y = render_out_mux.pos_y -30

                # Connect nodes

                flame.batch.connect_nodes(clip, 'Default', plate_in_mux, 'Default')
                flame.batch.connect_nodes(plate_in_mux, 'Result', render_out_mux, 'Default')
                flame.batch.connect_nodes(render_out_mux, 'Result', render_node, 'Default')

        # Frame all nodes

        flame.go_to('Batch')
        flame.batch.frame_all()

        # Move batch group from desktop to destination

        if self.batch_group_dest == 'Library':
            flame.media_panel.move(self.batch_group, dest)

        print (f'    batch group created: {shot_name}')

    def create_desktop(self, shot_name, all_clips, dest):
        import flame

        def build_reel_group():

            # Create reel group

            reel_group = self.ws.desktop.create_reel_group(str(self.reel_group).split("'", 2)[1])

            # Create extra reels in group past four

            for x in range(len(self.reel_group) - 4):
                reel_group.create_reel('')

            for reel in reel_group.reels:
                if 'Sequences' not in str(reel.name):
                    reel.name = self.reel_group[reel_group.reels.index(reel)]

            reel_group.name = str(self.reel_group_dict.keys())[12:-3]

        self.create_batch_group(shot_name, all_clips, self.desktop)
        self.desktop.name = shot_name

        # Create reel group

        if self.add_reel_group:
            build_reel_group()

        #  Remove old batch group

        flame.delete(self.desktop.batch_groups[0])

        # Copy desktop to Destination

        flame.media_panel.copy(self.desktop, dest)

        self.clear_current_desktop()

        print (f'    desktop created: {shot_name}')

    def create_file_system_folders(self, root_folder_path, shot_name):
        import flame

        def folder_loop(value, shot_folder):
            for k, v in iter(value.items()):
                folder = os.path.join(shot_folder, k)
                os.makedirs(folder)
                folder_loop(v, folder)

        # Create shot folders

        for key, value, in iter(self.file_system_folder_dict.items()):
            shot_folder = os.path.join(root_folder_path, shot_name)
            if not os.path.isdir(shot_folder):
                try:
                    os.makedirs(shot_folder)
                    print (f'    file system shot folder created: {shot_name}')
                    folder_loop(value, shot_folder)
                except:
                    self.system_folder_creation_errors.append(shot_name)
            else:
                self.system_folder_creation_errors.append(shot_name)

        flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

    def create_timeline_shots(self, timelinefx):
        import flame

        # Create temp library

        self.temp_lib = self.ws.create_library('Create_Shot_Temp_Library')

        # Match out selected clips from timeline into temporary library

        for clip in self.selection:
            clip.match(self.temp_lib, include_timeline_fx = timelinefx)

        self.selection = self.temp_lib.clips

        self.clips_to_shots()

        flame.delete(self.temp_lib)

    # ------------------------------------- #
    # Export

    def init_exporter(self):

        import flame

        # Initialize Exporter

        self.exporter = flame.PyExporter()

        # Set export to foreground

        self.exporter.foreground = self.create_shot_fg_export
        print (f'            export in foreground: {self.create_shot_fg_export}')

    def export_plate(self, root_folder_path, shot_name, all_clips):

        print ('\n        exporting plates:')

        # Initialize Flame exporter

        self.init_exporter()

        # Get selected export preset

        preset_split = self.create_shot_export_plate_preset.split(' ', 1)
        preset_type = preset_split[0]
        preset_name = preset_split[1] + '.xml'

        if preset_type == 'Shared:':
            preset_path = '/opt/Autodesk/shared/export/presets'
        else:
            preset_path = os.path.join('/opt/Autodesk/project', self.project_name, 'export/presets/flame')
        print ('            preset_path:', preset_path)

        for root, dirs, files in os.walk(preset_path):
            for f in files:
                if f == preset_name:
                    full_preset_path = os.path.join(root, f)
                    print ('            full_preset_path:', full_preset_path)

        # Get shot export path

        shot_export_path = os.path.join(root_folder_path, shot_name, self.export_dest_folder.split('/', 1)[1])
        print ('            shot_export_path:', shot_export_path, '\n')

        # Export clips to shot folder(s)

        for clip in self.selection:
            if all_clips:
                self.exporter.export(clip, full_preset_path, shot_export_path)
            else:
                if shot_name in str(clip.versions[0].tracks[0].segments[0].shot_name) or shot_name in str(clip.name):
                    self.exporter.export(clip, full_preset_path, shot_export_path)

# ------------------------------------- #

def setup(selection):
    '''
    Loads setup UI where custom folder/batch group/desktop/system folder shot structures can be defined
    '''

    script = CreateShotFolders(selection)
    script.preset_selector()

def create_shot_folders(selection):
    '''
    Loads UI where custom empty shot folders/batch groups/desktops/system folders can be created from
    '''

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return
    script.create_shot_folder_window()

def create_custom_selected_shots(selection):
    '''
    Loads UI where custom empty shot folders/batch groups/desktops/system folders can be created from
    '''

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return
    script.custom_shot_from_selected_window()

def clip_shot_name_to_shot(selection):
    '''
    Create shots based off of shot names assigned to clips
    If no shot name is assigned to clip, shot name will be guessed at from clip name
    Clips with same shot name with be put into same shot folder/batch group/desktop
    '''

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return
    script.clips_to_shots()

def clip_shot_name_to_shot_all_clips(selection):
    '''
    Create shot based off of shot name assigned to first clip in selection.
    If no shot name is assigned to clip, shot name will be guessed at from clip name.
    All selected clips will go into the same shot folder/batch group/desktop.
    '''

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return

    script.all_clips_to_shot()

def import_shot_name_to_shot(selection):
    '''
    Import selected to clip to separate shots with shot name
    '''

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return
    script.import_clips_to_shots()

def import_shot_name_to_shot_all(selection):
    '''
    Import all selected clips to single shot with shot name
    Shot name comes from shot name of first selected clip
    '''

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return
    script.import_all_clips_to_shot()

def timeline_clips_to_shot(selection):
    '''
    Create shots from selected clips on timeline
    '''
    import flame

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return
    script.create_timeline_shots(False)

def timeline_clips_to_shot_timeline_fx(selection):
    '''
    Create shots from selected clips on timeline with timelinefx included
    '''

    script = CreateShotFolders(selection)
    preset_loaded = script.load_preset_values()
    if not preset_loaded:
        return
    script.create_timeline_shots(True)

#-------------------------------------#
# SCOPES

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            if not isinstance(item.parent, flame.PyReel):
                return True
    return False

def scope_segment(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PySegment):
            return True
    return False

def scope_file(selection):
    import re

    for item in selection:
        item_path = str(item.path)
        item_ext = re.search(r'\.\w{3}$', item_path, re.I)
        if item_ext != (None):
            return True
    return False

#-------------------------------------#

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Create Shot Setup',
                    'execute': setup,
                    'minimumVersion': '2022'
                }
            ]
        }

    ]

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Create Shot...',
            'actions': [
                {
                    'name': 'Folders',
                    'execute': create_shot_folders,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Import to Shot',
                    'isVisible': scope_file,
                    'execute': import_shot_name_to_shot,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Import to Shot - All Clips / One Shot',
                    'isVisible': scope_file,
                    'execute': import_shot_name_to_shot_all,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Create Shot...',
            'actions': [
                {
                    'name': 'Folders',
                    'execute': create_shot_folders,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Clips to Shot',
                    'isVisible': scope_clip,
                    'execute': clip_shot_name_to_shot,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Clips to Shot - All Clips / One Shot',
                    'isVisible': scope_clip,
                    'execute': clip_shot_name_to_shot_all_clips,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Custom Shots',
                    'isVisible': scope_clip,
                    'execute': create_custom_selected_shots,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_timeline_custom_ui_actions():

    return [
        {
            'name': 'Create Shot...',
            'actions': [
                {
                    'name': 'Clips to Shot',
                    'isVisible': scope_segment,
                    'execute': timeline_clips_to_shot,
                    'minimumVersion': '2023'
                },
                {
                    'name': 'Clips to Shot w/Timeline FX',
                    'isVisible': scope_segment,
                    'execute': timeline_clips_to_shot_timeline_fx,
                    'minimumVersion': '2023'
                },
                {
                    'name': 'Custom Shots',
                    'isVisible': scope_segment,
                    'execute': create_custom_selected_shots,
                    'minimumVersion': '2023'
                }
            ]
        }
    ]
