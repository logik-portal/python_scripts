'''
Script Name: Uber Save
Script Version: 4.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 07.28.19
Update Date: 03.18.22

Custom Action Type: Batch / Media Panel

Description:

    Save/Save Iterate batch group iteration and batch setup file to custom path in one click

    Before using for the first time at least one preset must be created.

    One preset can be assigned as the Global Default which will then be applied to all Flame projects.

    Global Default Preset:

        The preset that is set as the Global Default will be used by all Flame projects.

        Setting a preset as the Global Default can be done when creating a preset or editing an existing preset.

        The Global Default preset can be overridden for individual projects by selecting a different preset in the Preset Selector Window.

        The preset set as the Global Default will have an asterisk at the end of the name in the Preset Selector window.

    Menus:

        Flame Main Menu -> Uber Save Setup

        Right-click selected batchgroups in desktop -> Uber Save... -> Save Selected Batchgroups
        Right-click selected batchgroups in desktop -> Uber Save... -> Iterate and Save Selected Batchgroups

        Right-click on desktop in media panel -> Uber Save... -> Save All Batchgroups

        Right-click in batch -> Uber Save... -> Save Current Batchgroup
        Right-click in batch -> Uber Save... -> Iterate and Save Current Batchgroup

    Uber Save Setup:

        Preset Selector Window:

            Presets can be created, edited, and set for the current project from this window.

            New/Edit:

                Preset Name:

                    Name of preset that will be used in the Preset Selector window dropdown menu.

                Global Default:

                    Enable this button to set a preset as the default. The first preset created will have this enabled by default.

                Root Save Path menu:

                    Default Project Path:

                        Uses the project default batch folder to save shots. Usually: /opt/Autodesk/project/FLAME_PROJECT/batch/flame

                    Custom Path:

                        Enables: Custom Root Save Path entry. Select this to assign an alternate location to save batch files to.

                    Custom Root Path:

                        Enter/browse to a path to be used as an alternate to the default Flame batch save location. Tokens for Project Name and Project Nickname can be used here.

                        Example:

                            /Jobs/<ProjectNickName>/<ProjectName>

                    Batch Path:

                        Use this to define the folder structure that batch setups will be saved in. They will be sub folders of the path defined by the Root Save Path.
                        This works in a way similar to defining where renders go with the write node.

                        Tokens:

                            <ProjectName> - Adds name of current Flame project to path
                            <ProjectNickName> - Adds Flame project nicknick to path
                            <DesktopName> - Adds name of current desktop to path
                            <SeqName> - Will try to guess shot seqeunce name from the batch group name - for example: PYT_0100_comp will give a sequence name of: pyt
                            <SEQNAME> - Will do the same as above but give the sequence name in all caps - for example: PYT_0100_comp will give a sequence name of: PYT
                            <ShotName> - Will try to guess shot name from the batch group name - for example: PYT_0100_comp will give a shot name of PYT_0100

                        Example:

                            shots/<ShotName>/batch

                    Shot Name From:

                        ShotName: Use when naming shots similar to this: PYT_0100, PYT_100, PYT100
                        BatchGroup: Use when the full name of the batch ground should be used as the shot name

To install:

    Copy script into either /opt/Autodesk/shared/python/uber_save

Updates:

    v4.2 03.18.22

        Moved UI widgets to external file

    v4.1 03.06.22

        Updated UI for Flame 2023

    v4.0 12.28.21

        Added ability to save presets so different settings can be used with different Flame projects.

    v3.2 10.11.21

        Removed JobName token - not needed with new project nick name token

        Removed Desktop Name token

        Shot name token improvements

    v3.1 07.10.21

        Fixed problem when trying to save on a flare. Added check for flame and flare batch folders.

        ProjectName token now uses exact flame project name. No longer tries to guess name of project on server. If flame
        project name is different than server project name, set flame project nickname and use ProjectNickName token

        Fixed sequence token when using batch group name as save type

    v3.0 06.08.21

        Updated to be compatible with Flame 2022/Python 3.7

        Improvements to shot name detection

        Speed improvements when saving

    v2.0 10.08.20:

        Updated UI

        Improved iteration handling

        Added SEQNAME token to add sequence name in caps to path

    v1.91 05.13.20:

        Fixed iterating: When previous iterations were not in batchgroup, new itereations would reset to 1.

        Iterations now continue from current iteration number.

    v1.9 03.10.20:

        Fixed Setup UI for Linux

    v1.7 12.29.19:

        Menu now appears as Uber Save in right-click menu
'''

from PySide2 import QtWidgets
import xml.etree.ElementTree as ET
import os, re, shutil
from flame_widgets_uber_save import FlameButton, FlameLabel, FlameLineEdit, FlamePushButton, FlamePushButtonMenu, FlameTokenPushButton, FlameMessageWindow, FlameWindow

VERSION = 'v4.2'

SCRIPT_PATH = '/opt/Autodesk/shared/python/uber_save'

class UberSave(object):

    def __init__(self, selection):
        import flame

        print ('''
       _    _ _               _____
      | |  | | |             / ____|
      | |  | | |__   ___ _ _| (___   __ ___   _____
      | |  | | '_ \ / _ \ '__\___ \ / _` \ \ / / _ \\
      | |__| | |_) |  __/ |  ____) | (_| |\ V /  __/
       \____/|_.__/ \___|_| |_____/ \__,_| \_/ \___|
       ''')

        print ('>' * 20, f'uber save {VERSION}', '<' * 20, '\n')

        self.selection = selection
        self.iterate = ''
        self.selected_batch = ''
        self.save_path = ''
        self.project_match = ''
        self.job_folder = ''
        self.batch_token_dict = ''

        # Get flame variables

        self.flame_prj_name = flame.project.current_project.project_name
        print ('flame_prj_name:', self.flame_prj_name)

        self.flame_prj_nickname = flame.projects.current_project.nickname
        print ('flame_prj_nickname:', self.flame_prj_nickname)

        self.current_project_path = self.get_current_project_path()
        print ('current_project_path:', self.current_project_path, '\n')

        # Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')
        self.preset_path = os.path.join(self.config_path, 'preset')
        self.project_config_path = os.path.join(self.config_path, 'project')

        # Load config file

        self.config()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('uber_save_settings'):
                self.global_default = setting.find('global_default').text

            print ('global_default:', self.global_default, '\n')

            print ('--> config loaded\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.preset_path)
                    os.makedirs(self.project_config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder:<br>{self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file\n')

                config = """
<settings>
    <uber_save_settings>
        <global_default></global_default>
    </uber_save_settings>
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

    #-------------------------------------#

    def load_preset(self, preset_path):

        print ('Loading preset:\n')

        print ('    preset_path:', preset_path, '\n')

        # Load settings from preset file

        xml_tree = ET.parse(preset_path)
        root = xml_tree.getroot()

        # Assign values from preset file to variables

        for setting in root.iter('uber_save_settings'):
            self.preset_name = setting.find('preset_name').text
            self.root_path = setting.find('root_path').text
            self.custom_path = setting.find('custom_path').text
            self.batch_path = setting.find('batch_path').text
            self.shot_name_type = setting.find('shot_name_type').text

        print ('    preset_name:', self.preset_name)
        print ('    root_path:', self.root_path)
        print ('    custom_path:', self.custom_path)
        print ('    batch_path:', self.batch_path)
        print ('    shot_name_type:', self.shot_name_type, '\n')

        print (f'    preset loaded: {self.preset_name}\n')

    def load_project_preset(self, project_preset_path):

        # Load settings from project file

        xml_tree = ET.parse(project_preset_path)
        root = xml_tree.getroot()

        # Assign values from config file to variables

        for setting in root.iter('uber_save_settings'):
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

            for setting in root.iter('uber_save_settings'):
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

            print ('--> config loaded\n')

        def new_preset():

            # Assign default settings

            self.preset_name = ''
            self.root_path = 'Default Project Path'
            self.custom_path = ''
            self.batch_path = ''
            self.shot_name_type = 'Shot Name'

            self.preset()

        def edit_preset():

            preset_name_text = self.current_preset_push_btn.text()
            if preset_name_text.endswith('*'):
                preset_name_text = preset_name_text[:-1]

            if self.current_preset_push_btn.text():

                preset_path = os.path.join(self.preset_path, preset_name_text + '.xml')

                self.load_preset(preset_path)

                self.preset()
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

                print (f'Preset duplicate created: {new_preset_name}', '\n')

                self.preset_selector()

                self.current_preset_push_btn.setText(new_preset_name)

        def delete_preset():

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
                        os.remove(preset_path)
                    else:
                        return
                else:
                    # If preset is not found in any projects, delete. Confirm first.

                    if FlameMessageWindow('Confirm Operation', 'warning', f'Delete: {preset_name}'):
                        os.remove(preset_path)
                    else:
                        return

                    # If preset is not found in any projects, delete. Confirm first.
            else:
                # If no project configs exist, delete preset. Confirm first.

                if FlameMessageWindow('Confirm Operation', 'warning', f'Delete: {preset_name}'):
                    os.remove(preset_path)
                else:
                    return

            self.selector_window.close()

            print (f'--> Preset deleted: {preset_name}\n')

            self.preset_selector()

        def save():

            preset_name_text = self.current_preset_push_btn.text()
            if preset_name_text.endswith('*'):
                preset_name_text = preset_name_text[:-1]

            if not preset_name_text:
                return FlameMessageWindow('Error', 'error', 'Uber Save Preset must be created to save.')

            preset_path = os.path.join(self.project_config_path, self.flame_prj_name + '.xml')

            if preset_name_text != self.global_default:

                if os.path.isfile(preset_path):
                    os.remove(preset_path)

                # Create project preset

                preset = """
<settings>
    <uber_save_settings>
        <preset_name></preset_name>
    </uber_save_settings>
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

                print ('--> custom project uber save preset saved\n')
            else:
                try:
                    os.remove(preset_path)
                except:
                    pass

            self.selector_window.close()

        gridbox = QtWidgets.QGridLayout()
        self.selector_window = FlameWindow(f'Uber Save <small>{VERSION}', gridbox, 600, 260)

        # Labels

        self.preset_label = FlameLabel('Uber Save Current Project Preset', label_type='underline')

        # Shot Name Type Pushbutton Menu

        preset_list = build_preset_list()
        self.current_preset_push_btn = FlamePushButtonMenu('', preset_list)

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

        self.selector_window.show()

        return self.selector_window

    #-------------------------------------#

    def get_current_project_path(self):

        # Get default save path from project.db file

        with open('/opt/Autodesk/project/project.db', 'r') as project_db:
            for line in project_db:
                if ':' + self.flame_prj_name + '=' in line:
                    current_project_path = re.search('SetupDir="(.*)",Partition', line)
                    current_project_path = current_project_path.group(1)

                    # If default project is on local drive add autodesk project folder to path

                    if not current_project_path.startswith('/'):
                        current_project_path = os.path.join('/opt/Autodesk/project', current_project_path)
                    return current_project_path

    def translate_path(self):
        import flame

        def load_preset_values():

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

        load_preset_values()

        print ('Translating path:\n')

        # If Use Custom button is selected use custom path provided
        # Otherwise use project default batch folder

        flame_batch_folder = os.path.join(self.current_project_path, 'batch/flame')
        flare_batch_folder = os.path.join(self.current_project_path, 'batch/flare')

        if self.root_path == 'Custom Path':
            self.save_path = os.path.join(self.custom_path, self.batch_path)
        else:
            if os.path.isdir(flame_batch_folder):
                batch_folder = flame_batch_folder
            elif os.path.isdir(flare_batch_folder):
                    batch_folder = flare_batch_folder
            else:
                os.makedirs(flame_batch_folder)
                batch_folder = flame_batch_folder
            self.save_path = os.path.join(batch_folder, self.batch_path)
        print ('    save_path:', self.save_path, '\n')

        #-------------------------------------#

        batch_name = str(self.selected_batch.name)[1:-1]
        print ('    batch_name:', batch_name)

        try:
            if self.shot_name_type == 'Shot Name':
                shot_name_split = re.split(r'(\d+)', batch_name)
                shot_name_split = [s for s in shot_name_split if s != '']
                # print ('shot_name_split:', shot_name_split)

                if len(shot_name_split) > 1:
                    if shot_name_split[1].isalnum():
                        shot_name = shot_name_split[0] + shot_name_split[1]
                    else:
                        shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]
                else:
                    shot_name = batch_name

                # Get sequence name from first split

                seq_name = shot_name_split[0]
                if seq_name.endswith('_'):
                    seq_name = seq_name[:-1]

            else:
                seq_name_split = re.split(r'(\d+)', shot_name)
                seq_name = seq_name_split[0]
                if seq_name.endswith('_'):
                    seq_name = seq_name[:-1]
        except:
            shot_name = batch_name
            seq_name_split = re.split(r'_', shot_name)
            seq_name = seq_name_split[0]
            if seq_name.endswith('_'):
                seq_name = seq_name[:-1]

        print ('    shot_name:', shot_name)
        print ('    seq_name:', seq_name, '\n')

        #-------------------------------------#

        print ('    path_to_translate:', self.save_path)

        # Translate tokens in path

        if '<ProjectName>' in self.save_path:
            self.save_path = re.sub('<ProjectName>', self.flame_prj_name, self.save_path)

        if '<ProjectNickName>' in self.save_path:
            self.save_path = re.sub('<ProjectNickName>', self.flame_prj_nickname, self.save_path)

        if '<SeqName>' in self.save_path:
            self.save_path = re.sub('<SeqName>', seq_name, self.save_path)

        if '<SEQNAME>' in self.save_path:
            self.save_path = re.sub('<SEQNAME>', seq_name.upper(), self.save_path)

        if '<ShotName>' in self.save_path:
            self.save_path = re.sub('<ShotName>', shot_name, self.save_path)

        print ('    translated save_path:', self.save_path, '\n')

    def preset_check(self):

        # Check for presets in config/preset folder

        if not os.listdir(self.preset_path):
            return FlameMessageWindow('Setup Script', 'message','No Uber Save presets exists.<br>Run Uber Save setup.<br>Flame Main Menu -> pyFlame -> Uber Save Setup' )
        return True

    #-------------------------------------#

    def batchgroup_save_all(self):
        import flame

        preset = self.preset_check()

        if preset:
            self.iterate = False
            batch_groups = flame.project.current_project.current_workspace.desktop.batch_groups

            for self.selected_batch in batch_groups:
                self.translate_path()
                self.save_batchgroup()

            print ('done.\n')

    def batchgroup_save_selected(self):
        import flame

        preset = self.preset_check()

        if preset:
            self.iterate = False

            for self.selected_batch in self.selection:
                self.translate_path()
                self.save_batchgroup()

            print ('done.\n')

    def batchgroup_save_selected_iterate(self):
        import flame

        preset = self.preset_check()

        if preset:
            self.iterate = True

            for self.selected_batch in self.selection:
                self.translate_path()
                self.save_batchgroup()

            print ('done.\n')

    def batchgroup_save(self):
        import flame

        preset = self.preset_check()

        if preset:
            self.iterate = False
            self.selected_batch = flame.batch
            self.translate_path()
            self.save_batchgroup()

            print ('done.\n')

    def batchgroup_save_iterate(self):
        import flame

        preset = self.preset_check()

        if preset:
            self.iterate = True
            self.selected_batch = flame.batch
            self.translate_path()
            self.save_batchgroup()

            print ('done.\n')

    #-------------------------------------#

    def preset(self):

        def global_default_pressed():

            if not os.listdir(self.preset_path):
                self.global_default_pushbutton.setChecked(True)

            if self.preset_name_lineedit.text() == self.global_default:
                self.global_default_pushbutton.setChecked(True)

        def global_default_state():

            # Set global default button state

            if not os.listdir(self.preset_path):
                self.global_default_pushbutton.setChecked(True)
            if self.preset_name_lineedit.text() == self.global_default:
                self.global_default_pushbutton.setChecked(True)

        def custom_path_browse():

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.preset_window, 'Select Directory', self.custom_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.custom_path_lineedit.setText(file_path)

        def save_preset():

            if not self.preset_name_lineedit.text():
                return FlameMessageWindow('Error', 'error', 'Enter name for preset.')
            if not self.root_path_push_btn.text() == 'Default Project Path':
                if not self.custom_path_lineedit.text():
                    return FlameMessageWindow('Error', 'error', 'Enter custom root path.')
            if not self.batch_path_lineedit.text():
                return FlameMessageWindow('Error', 'error', 'Enter batch path')

            preset_name_text = self.preset_name_lineedit.text()

            # Check if preset already exists with current name. Give option to delete.

            if [f for f in os.listdir(self.preset_path) if f[:-4] == preset_name_text]:
                if FlameMessageWindow('Confirm Operation', 'warning', 'Preset with this name already exists. Overwrite?'):
                    os.remove(os.path.join(self.preset_path, preset_name_text + '.xml'))
                else:
                    return

            # Save empty preset file

            preset_path = os.path.join(self.preset_path, preset_name_text + '.xml')

            preset = """
<settings>
    <uber_save_settings>
        <preset_name></preset_name>
        <root_path></root_path>
        <custom_path></custom_path>
        <batch_path></batch_path>
        <shot_name_type></shot_name_type>
    </uber_save_settings>
</settings>"""

            with open(preset_path, 'a') as xml_file:
                xml_file.write(preset)
                xml_file.close()

            # Save settings to preset file

            xml_tree = ET.parse(preset_path)
            root = xml_tree.getroot()

            preset_name = root.find('.//preset_name')
            preset_name.text = preset_name_text

            root_path = root.find('.//root_path')
            root_path.text = self.root_path_push_btn.text()

            custom_path = root.find('.//custom_path')
            custom_path.text = self.custom_path_lineedit.text()

            batch_path = root.find('.//batch_path')
            batch_path.text = self.batch_path_lineedit.text()

            shot_name_type = root.find('.//shot_name_type')
            shot_name_type.text = self.shot_name_type_push_btn.text()

            xml_tree.write(preset_path)

            # Remove old preset if preset name is changed.

            if self.preset_name and preset_name_text != self.preset_name:
                os.remove(os.path.join(self.preset_path, self.preset_name + '.xml'))

            # Update config

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            if self.global_default_pushbutton.isChecked():
                global_default = root.find('.//global_default')
                global_default.text = preset_name_text
                preset_name_text = preset_name_text + '*'

                xml_tree.write(self.config_xml)

            # Close preset window and reload settings

            self.preset_window.close()

            print ('--> preset saved\n')

            self.selector_window.close()

            self.preset_selector()

            self.current_preset_push_btn.setText(preset_name_text)

        gridbox = QtWidgets.QGridLayout()
        self.preset_window = FlameWindow(f'Uber Save Preset Setup <small>{VERSION}', gridbox, 1000, 370)

        # Labels

        self.preset_name_label = FlameLabel('Preset Name', 'normal')
        self.custom_path_label = FlameLabel('Custom Root Save Path', 'normal')
        self.batch_path_label = FlameLabel('Batch Path', 'normal')
        self.shot_name_label = FlameLabel('Shot Name From', 'normal')
        self.root_path_label = FlameLabel('Root Save Path', 'normal')

        # LineEdits

        self.preset_name_lineedit = FlameLineEdit(self.preset_name)
        self.custom_path_lineedit = FlameLineEdit(self.custom_path)
        self.batch_path_lineedit = FlameLineEdit(self.batch_path)

        # Pushbutton

        self.global_default_pushbutton = FlamePushButton('Global Default', False)
        self.global_default_pushbutton.clicked.connect(global_default_pressed)
        global_default_state()

        # Shot Name Type Pushbutton Menu

        shot_name_options = ['Shot Name', 'Batch Group Name']
        self.shot_name_type_push_btn = FlamePushButtonMenu(self.shot_name_type, shot_name_options, max_menu_width=150)

        # Custom Path Token Pushbutton Menu

        custom_token_dict = {'Project Name': '<ProjectName>', 'Project Nick Name': '<ProjectNickName>'}
        self.custom_token_push_btn = FlameTokenPushButton('Add Token', custom_token_dict, self.custom_path_lineedit)

        # Batch Path Token Pushbutton Menu

        batch_token_dict = {'Project Name': '<ProjectName>', 'Project Nick Name': '<ProjectNickName>', 'Sequence Name': '<SeqName>', 'SEQUENCE NAME': '<SEQNAME>', 'Shot Name': '<ShotName>'}
        self.batch_token_push_btn = FlameTokenPushButton('Add Token', batch_token_dict, self.batch_path_lineedit)

        #  Buttons

        self.browse_btn = FlameButton('Browse', custom_path_browse)
        self.save_btn = FlameButton('Save', save_preset)
        self.cancel_btn = FlameButton('Cancel', self.preset_window.close)

        # Batch Root Path Pushbutton Menu

        def root_path_toggle():
            if self.root_path_push_btn.text() == 'Default Project Path':
                self.root_path_push_btn.setText('Default Project Path')
                self.custom_path_label.setEnabled(False)
                self.custom_path_lineedit.setEnabled(False)
                self.custom_token_push_btn.setEnabled(False)
                self.browse_btn.setEnabled(False)
            else:
                self.root_path_push_btn.setText('Custom Path')
                self.custom_path_label.setEnabled(True)
                self.custom_path_lineedit.setEnabled(True)
                self.custom_token_push_btn.setEnabled(True)
                self.browse_btn.setEnabled(True)

        root_path_menu_options = ['Default Project Path', 'Custom Path']
        self.root_path_push_btn =  FlamePushButtonMenu(self.root_path, root_path_menu_options, max_menu_width=150, menu_action=root_path_toggle)

        root_path_toggle()

        # Setup window layout

        gridbox.setMargin(20)

        gridbox.addWidget(self.preset_name_label, 0, 0)
        gridbox.addWidget(self.preset_name_lineedit, 0, 1)
        gridbox.addWidget(self.global_default_pushbutton, 0, 4)

        gridbox.setRowMinimumHeight(1, 30)

        gridbox.addWidget(self.root_path_label, 2, 0)
        gridbox.addWidget(self.root_path_push_btn, 2, 1)

        gridbox.addWidget(self.custom_path_label, 3, 0)
        gridbox.addWidget(self.custom_path_lineedit, 3, 1, 1, 2)
        gridbox.addWidget(self.custom_token_push_btn, 3, 3)
        gridbox.addWidget(self.browse_btn, 3, 4)

        gridbox.addWidget(self.batch_path_label, 4, 0)
        gridbox.addWidget(self.batch_path_lineedit, 4, 1, 1, 2)
        gridbox.addWidget(self.batch_token_push_btn, 4, 3)

        gridbox.addWidget(self.shot_name_label, 5, 0)
        gridbox.addWidget(self.shot_name_type_push_btn, 5, 1)

        gridbox.addWidget(self.save_btn, 7, 4)
        gridbox.addWidget(self.cancel_btn, 8, 4)

        self.preset_window.show()

        return self.preset_window

    #-------------------------------------#

    def save_batchgroup(self):
        import flame

        print ('Saving batch group:\n')

        selected_batch_name = str(self.selected_batch.name)[1:-1]
        print ('    selected_batch_name:', selected_batch_name)

        # Open batch if closed

        self.selected_batch.open()

        # Get current iteration

        iteration_split = (re.split(r'(\d+)', str(self.selected_batch.current_iteration.name)[1:-1]))[1:-1]
        current_iteration = int(iteration_split[-1])
        print ('    current_iteration:', current_iteration)

        # Get latest iteration if iterations are saved

        if not self.selected_batch.batch_iterations == []:
            latest_iteration = int(((re.split(r'(\d+)', str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1]))[1:-1])[-1])
        else:
            latest_iteration = current_iteration
        print ('    latest_iteration:', latest_iteration)

        # If first save of batch group, create first iteration

        if self.selected_batch.batch_iterations == [] and current_iteration == 1:
            self.iterate = True

        # Iterate up if iterate up menu selected

        print ('    iterate:', self.iterate, '\n')

        if self.iterate:
            if current_iteration == 1:
                self.selected_batch.iterate()
            elif current_iteration < latest_iteration:
                self.selected_batch.iterate(index = (latest_iteration + 1))
            else:
                self.selected_batch.iterate(index = (current_iteration + 1))
            print ('    --> iterating up\n')
        else:
            self.selected_batch.iterate(index=current_iteration)
            print ('    --> overwriting existing iteration\n')

        # Get current iteration

        current_iteration = str(self.selected_batch.current_iteration.name)[1:-1]
        current_iteration_no_spaces = current_iteration.replace(' ', '_')
        print ('    new current_iteration:', current_iteration)

        # Set batch save path

        shot_save_path = os.path.join(self.save_path, current_iteration)
        print ('    shot_save_path:', shot_save_path)

        try:
            # Create shot save folder

            if not os.path.isdir(self.save_path):
                os.makedirs(self.save_path)

            # Hard save current batch iteration

            self.selected_batch.save_setup(shot_save_path)

            # edit_batch()

            print ('\n', f'--> {selected_batch_name} uber saved', '\n')

        except:
            FlameMessageWindow('Error', 'error', 'Batch not saved. Check path in setup')
#-------------------------------------#

def uber_save_setup(selection):

    # Opens Uber Save Setup window

    uber_save = UberSave(selection)
    uber_save.preset_selector()

def uber_batchgroup_save(selection):

    # Saves current batch from batch

    uber_save = UberSave(selection)
    uber_save.batchgroup_save()

def uber_batchgroup_iterate_save(selection):

    # Iterates and saves current batch from batch

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_iterate()

def uber_batchgroup_save_all(selection):

    # Saves all batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_all()

def uber_batchgroup_save_selected(selection):

    # Saves selected batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_selected()

def uber_batchgroup_iterate_save_selected(selection):

    # Saves selected batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_selected_iterate()

# Scopes
#-------------------------------------#

def scope_batch(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyBatch):
            return True
    return False

def scope_desktop(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyDesktop):
            return True
    return False

# Menus
#-------------------------------------#

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Uber Save',
            'actions': [
                {
                    'name': 'Save All Batch Groups',
                    'isVisible': scope_desktop,
                    'execute': uber_batchgroup_save_all,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Save Selected Batch Groups',
                    'isVisible': scope_batch,
                    'execute': uber_batchgroup_save_selected,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Iterate and Save Selected Batch Groups',
                    'isVisible': scope_batch,
                    'execute': uber_batchgroup_iterate_save_selected,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Uber Save',
            'actions': [
                {
                    'name': 'Save Current Batch Group',
                    'execute': uber_batchgroup_save,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Iterate and Save Current Batch Group',
                    'execute': uber_batchgroup_iterate_save,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Uber Save Setup',
                    'execute': uber_save_setup,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
