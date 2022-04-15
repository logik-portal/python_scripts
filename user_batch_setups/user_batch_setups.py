'''
Script Name: User Batch Setups
Script Version: 1.0
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 03.29.22
Update Date: 04.13.22

Custom Action Type: Batch

Description:

    Create menus for batch setups saved to a specified folder.

    Menu's for setups will only be visible in versions of Flame that setups are compatible with.

    After saving or deleting batch setups to the chosen folder, use the Refresh Menus menu option to regenerate setup menus.

    Setup menus are automatically regenerated each time flame starts up.

Menus:

    Setup:

        Flame Main Menu -> pyFlame -> User Batch Setups - Setup

    To refresh menus

        Flame Main Menu -> pyFlame -> User Batch Setups - Refresh Menus

     To access batch setup menus:

        Right-click in batch -> User Batch Setups -> Setup Name

To install:

    Copy script into /opt/Autodesk/shared/python/user_batch_setups

'''

import xml.etree.ElementTree as ET
from PySide2 import QtWidgets
from flame_widgets_user_setups import FlameMessageWindow, FlameWindow, FlameLabel, FlameClickableLineEdit, FlameButton
import os, re, shutil

VERSION = 'v1.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/user_batch_setups'

class UserSetups(object):

    def __init__(self, selection):
        import flame

        print ('''

 ''')
        print ('>' * 18, f'user batch setups {VERSION}', '<' * 18, '\n')

        self.selection = selection

        # Config paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.config()

        # Create menus folder if it doesn't already exist

        self.menu_path = os.path.join(SCRIPT_PATH, 'menus')
        if not os.path.isdir(self.menu_path):
            os.makedirs(self.menu_path)

        self.template_path = os.path.join(SCRIPT_PATH, 'batch_menu_template')

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('user_setup_settings'):
                self.setup_path = setting.find('setup_path').text

            print ('--> config loaded\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder: {self.config_path}<br><br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file')

                config = """
<settings>
    <user_setup_settings>
        <setup_path>/</setup_path>
    </user_setup_settings>
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

    def get_flame_version(self):
        import flame

        # Get version of flame and convert to float

        self.flame_version = flame.get_version()

        if 'pr' in self.flame_version:
            self.flame_version = self.flame_version.rsplit('.pr', 1)[0]

        if len(self.flame_version) > 6:
            self.flame_version = self.flame_version[:6]
        self.flame_version = float(self.flame_version)
        print ('flame version:', self.flame_version)

        self.flame_min_max_version = flame.get_version_major()
        if self.flame_min_max_version == '2021':
            self.flame_min_max_version = '2021.2'
        print ('flame_min_max_version:', self.flame_min_max_version, '\n')

    def setup_main_window(self):

        def browse_dir():

            file_browser = QtWidgets.QFileDialog()
            file_browser.setDirectory(self.setup_path_entry.text())
            file_browser.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if file_browser.exec_():
                self.setup_path_entry.setText(str(file_browser.selectedFiles()[0]))

        def save_config():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            setup_path = root.find('.//setup_path')
            setup_path.text = self.setup_path_entry.text()

            xml_tree.write(self.config_xml)

            print ('--> config saved\n')

            self.setup_window.close()

            self.refresh_menus_folder()

        vbox = QtWidgets.QVBoxLayout()
        self.setup_window = FlameWindow(f'User Setups <small>{VERSION}', vbox, 600, 200)

        # Labels

        self.setup_path_label = FlameLabel('Path to Batch Setups')

        # LineEdits

        self.setup_path_entry = FlameClickableLineEdit(self.setup_path, browse_dir)

        # Buttons

        self.save_button = FlameButton('Save', save_config)
        self.cancel_button = FlameButton('Cancel', self.setup_window.close)

        # UI Widget Layout

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(20)

        grid.addWidget(self.setup_path_label, 0, 0)
        grid.addWidget(self.setup_path_entry, 0, 1, 1, 2)

        # HBox

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(5)
        hbox.addWidget(self.cancel_button)
        hbox.addStretch(5)
        hbox.addWidget(self.save_button)
        hbox.addStretch(5)

        # Main VBox

        vbox.setMargin(15)
        vbox.addLayout(grid)
        vbox.addStretch(5)
        vbox.addLayout(hbox)
        vbox.addStretch(5)

        self.setup_window.show()

    def refresh_menus_folder(self, startup_refresh=False):
        import flame

        # Reload config

        self.config()

        # Check batch setup path - if path not found give error

        if not os.path.isdir(self.setup_path):
            return FlameMessageWindow('User Batch Setups - Error', 'error', 'Batch setup path not found.<br><br>Check path in script setup.<br><br>Flame Main Menu -> pyFlame -> User Setups Setup')


        if not os.listdir(self.setup_path):
            return FlameMessageWindow('User Batch Setups', 'message', 'No batch setups found.<br><br>No menus to create/update.')

        # Delete existing menus and recreate menus folder

        shutil.rmtree(self.menu_path)
        os.makedirs(self.menu_path)

        print ('--> menus folder cleared\n')

        # Create new menus for all batch setups found in batch setup path

        print ('--> generating batch menus:\n')

        for f in os.listdir(self.setup_path):
            if f.endswith('.batch'):
                self.create_menu(os.path.join(self.setup_path, f), f.split('.', 1)[0])

        print ('\n')

        # Refresh python hooks

        flame.execute_shortcut('Rescan Python Hooks')

        # Give user message that setup menus have been updated

        if not startup_refresh:
            FlameMessageWindow('User Batch Setups - Operation Complete', 'message', 'User batch menus have been created/updated.')

        print ('done.\n')

    def create_menu(self, batch_path, batch_name):

        print (f'    {batch_name}')

        # Read flame version from batch setup file

        xml_tree = ET.parse(batch_path)
        root = xml_tree.getroot()

        xml_version = root.find('.//Version')
        batch_version = xml_version.text

        if 'pr' in batch_version:
            batch_version = batch_version.rsplit('.pr', 1)[0]

        # Create menu for batch with menu minimum version set to flame version

        # Read menu template file

        template = open(self.template_path, 'r')
        template_lines = template.read().splitlines()

        # Replace tokens in template

        token_dict = {}

        token_dict['<BatchName>'] = batch_name
        token_dict['<ScriptVersion>'] = VERSION[1:]
        token_dict['<SetupPath>'] = batch_path
        token_dict['<MinFlameVersion>'] = batch_version

        # Replace tokens in menu template

        for key, value in token_dict.items():
            for line in template_lines:
                if key in line:
                    line_index = template_lines.index(line)
                    new_line = re.sub(key, value, line)
                    template_lines[line_index] = new_line

        # Write out menu for batch setup

        new_batch_script_path = os.path.join(self.menu_path, batch_name + '.py')

        out_file = open(new_batch_script_path, 'w')
        for line in template_lines:
            print(line, file=out_file)
        out_file.close()

def setup(selection):

    script = UserSetups(selection)
    script.setup_main_window()

def refresh(selection):

    script = UserSetups(selection)
    script.refresh_menus_folder()

def startup_refresh(selection):

    script = UserSetups(selection)
    script.refresh_menus_folder(startup_refresh=True)

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'User Batch Setups - Setup',
                    'execute': setup,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'User Batch Setups - Refresh Menus',
                    'execute': refresh,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def app_initialized(project_name):
    startup_refresh(project_name)
