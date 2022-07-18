'''
Script Name: SynthEyes Export
Script Version: 2.6
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 10.27.19
Update Date: 06.22.22

Custom Action Type: Flame Main Menu

Description:

    Exports selected plate as jpg sequence, launches SynthEyes, then loads sequence into syntheyes for tracking

    SynthEyes will open behind the Flame window

    Tokenized export path can be set in the setup window to avoid browsing to an export path for each export. Browser opens by default when doing an export.

Menus:

    Setup:

        Flame Main Menu -> PyFlame -> SynthEyes Export Setup

    Export:

        Right-click on clip in Media Panel -> SynthEyes... -> Export to SynthEyes

To install:

    Copy script into /opt/Autodesk/shared/python/syntheyes_export

Updates:

    v2.6 06.22.22

       Added setup window to allow for the setup of export paths with tokens. This avoids the need to browse for export paths.
       Setup menu can be found here: Flame Main Menu -> pyFlame -> SynthEyes Export Setup

    v2.5 05.30.22

        Messages print to Flame message window - Flame 2023.1 and later

        Updated directory browser for Flame 2023.1 and later

    v2.4 03.21.22

        Updated SyPy install path for Flame 2023/Python 3.9

        Updated UI for Flame 2023

        Updated jpeg export for Flame 2023

        UI widgets moved to separate file

    v2.3 03.15.22

        Added path to install sypy on linux systems

    v2.2 10.11.21

        Improved Flame version detection

    v2.1 09.05.21

        Script will now copy SyPy/SyPy3 into current Flame python folder if not already there first time script is run with new version of Flame.
        For Flame 2022 and newer SyPy3 will be copied. For earlier versions SyPy will be copied along with a fix for sylevel.py which is contained
        in sylevel.tar.

        Version number in jpeg export preset is updated to match flame version. Prevents export preset version warning.

        Updated config to xml

    v2.0 06.01.21

        Updated to be compatible with Flame 2022/Python 3.7

    v1.1 06.08.20

        Simplified clip exporting
'''

from PySide2 import QtWidgets
from random import randint
from subprocess import Popen, PIPE
import xml.etree.ElementTree as ET
import os, platform
from pyflame_lib_syntheyes_export import FlameWindow, FlameLabel, FlameLineEdit, FlameTokenPushButton, FlameButton, FlamePushButtonMenu,FlameMessageWindow, FlamePasswordWindow, pyflame_get_flame_version, pyflame_print, pyflame_file_browser, pyflame_resolve_path_tokens

SCRIPT_NAME = 'SynthEyes Export'
SCRIPT_PATH = '/opt/Autodesk/shared/python/syntheyes_export'
VERSION = 'v2.6'

class FlameToSynthEyes(object):

    def __init__(self, selection):

        print ('\n')
        print ('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

        self.clip = selection[0]

        # Load config

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.config()

        # Check for sylevel file

        self.sylevel_check()

        # Match export preset version with version of flame

        self.flame_version = pyflame_get_flame_version()

        if self.flame_version >= 2024.0:
            return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Newer version of script required for this version of Flame')

        self.export_preset = os.path.join(SCRIPT_PATH, 'syntheyes_jpeg_export.xml')
        self.update_export_preset()

        # Set export path to / if last export path does not exist

        if not os.path.isdir(self.last_export_path):
            self.last_export_path = '/'

        # Init varaibles

        self.first_image_path = ''
        self.clip_ratio = ''

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get settings

            for setting in root.iter('config'):
                self.last_export_path = setting.find('last_export_path').text
                self.export_path_menu = setting.find('export_path').text
                self.custom_export_path = setting.find('custom_export_path').text

            pyflame_print(SCRIPT_NAME, 'Config loaded.')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', f'Unable to create folder: {self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                pyflame_print(SCRIPT_NAME, 'Config file does not exist. Creating new config file.')

                config = """
<settings>
    <config>
        <last_export_path>/opt/Autodesk</last_export_path>
        <export_path>Browse To Path</export_path>
        <custom_export_path>/opt/Autodesk</custom_export_path>
    </config>
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

    def sylevel_check(self):

        # Make sure sylevel.py file doesn't exist in script folder from interupted install

        if 'sylevel.py' in os.listdir(SCRIPT_PATH):
            os.remove(os.path.join(SCRIPT_PATH, 'sylevel.py'))
            print ('--> sylevel file removed\n')

    def syntheyes_check(self):
        '''
        Check /opt/Autodesk/python/FLAME_VERSION/lib/python3.7/site-packages for SyPy3.
        If not found copy from /Applications/SynthEyes/SyPy3 folder.
        Linux users will have to manually copy.
        '''

        if not os.path.isdir('/Applications/SynthEyes'):
            return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'SynthEyes not found. Install SynthEyes before using this script.')

        version = int(str(self.flame_version)[:4])

        try:
            if version >= 2022:
                import SyPy3
                print ('--> SyPy3 Found!\n')
                return True
            else:
                import SyPy
                print ('--> SyPy Found!\n')
                return True
        except:
            print ('--> SyPy not found\n')
            if platform.system() == 'Darwin':
                syntheyes_path = '/Applications/SynthEyes'
                self.copy_sypy(syntheyes_path)
            else:
                syntheyes_path = '/opt/SynthEyes'
                self.copy_sypy(syntheyes_path)

    def copy_sypy(self, syntheyes_path):
        import flame

        system_password = str(FlamePasswordWindow(f'{SCRIPT_NAME}: Enter System Password', 'System password needed to install SynthEyes SyPY into Flame python folder.'))

        if system_password:
            version = int(str(self.flame_version)[:4])
            if version == 2023:

                # Copy SyPy3 from SynthEyes folder to Flame python folder

                sypy_folder = os.path.join(syntheyes_path, 'SyPy3')
                flame_sypy_folder = f'/opt/Autodesk/python/{flame.get_version()}/lib/python3.9/site-packages'

                p = Popen(['sudo', '-S', 'cp', '-r', sypy_folder, flame_sypy_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                p.communicate(system_password + '\n')[1]

                FlameMessageWindow('message', f'{SCRIPT_NAME}: Install complete', 'SynthEyes SyPy3 copied to Flame python folder.')

            elif version == 2022:

                # Copy SyPy3 from SynthEyes folder to Flame python folder

                sypy_folder = os.path.join(syntheyes_path, 'SyPy3')
                flame_sypy_folder = f'/opt/Autodesk/python/{flame.get_version()}/lib/python3.7/site-packages'

                p = Popen(['sudo', '-S', 'cp', '-r', sypy_folder, flame_sypy_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                p.communicate(system_password + '\n')[1]

                FlameMessageWindow('message', f'{SCRIPT_NAME}: Install complete', 'SynthEyes SyPy3 copied to Flame python folder.')

            self.syntheyes_export()

        system_password = ''

    def update_export_preset(self):
        '''
        Update jpeg export preset file version to match current version of flame being used.
        Flame 2021 is version 10. Every new full version of Flame adds one. 2022 is 11.
        '''

        export_preset_xml_tree = ET.parse(self.export_preset)
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

        if current_export_version != export_version:
            for element in root.iter('preset'):
                element.set('version', export_version)

            export_preset_xml_tree.write(self.export_preset)

            pyflame_print(SCRIPT_NAME, 'Export preset updated to match current Flame version.')

    # ------------------------ #

    def syntheyes_export(self):
        import flame

        def save_settings():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            last_export_path = root.find('.//last_export_path')
            last_export_path.text = export_path

            xml_tree.write(self.config_xml)

            pyflame_print(SCRIPT_NAME, 'Config saved.')

        def get_clip_info():

            print ('--> exporting clip:')

            self.clip_name = str(self.clip.name)[1:-1]
            print ('    clip name:', self.clip_name)

            self.clip_framerate = str(self.clip.frame_rate).split(' ')[0]
            print ('    clip framerate:', self.clip_framerate)

            self.clip_ratio = float(self.clip.ratio)
            print ('    clip ratio:', self.clip_ratio, '\n')

        def export_clip():

            # Export jpeg_sequence to shot folder

            clip_exporter = flame.PyExporter()
            clip_exporter.foreground = True

            clip_exporter.export(sources = self.clip, preset_path = self.export_preset, output_directory = export_path)

        def get_image_name():

            image_seq_path = os.path.join(export_path, self.clip_name)

            file_list = []

            for file in os.listdir(image_seq_path):
                if file.endswith('.jpg'):
                    file_list.append(file)
            file_list.sort()

            first_image_file = file_list[0]

            self.first_image_path = os.path.join(image_seq_path, first_image_file)

        def open_syntheyes():

            # Create random port number

            random_port = randint(1000, 9999)

            # Import SyPy and set hlev
            # If using Flame 2022 or later, use SyPy3 otherwise use SyPy

            if self.flame_version >= 2022.0:
                import SyPy3
                hlev = SyPy3.SyLevel()
            else:
                import SyPy
                hlev = SyPy.SyLevel()

            # Open Syntheyes

            hlev.OpenSynthEyes(port=random_port, pin='696969696969')

            # Load image sequence and set aspect ratio

            hlev.NewSceneAndShot(self.first_image_path, asp = self.clip_ratio)

            # Set scene to z-up mode

            hlev.SetSzlAxisMode(0)

            # Set scene frame rate

            cam = hlev.FindObjByName('Camera01')
            sht = cam.Get('shot')
            hlev.BeginShotChanges(sht)
            sht.Set('rate', self.clip_framerate)
            hlev.AcceptShotChanges(sht, 'Set up shot')

        # Make sure sypy/sypy3 is installed

        sypy_installed = self.syntheyes_check()

        # If sypy/sypy3 is installed, export

        if sypy_installed:

            if self.export_path_menu == 'Browse To Path':

                # Select export folder

                FlameMessageWindow('message', f'{SCRIPT_NAME}: Select Path', 'Select path to export plate for tracking in Syntheyes.')

                export_path = pyflame_file_browser('Select Export Directory', [''], self.last_export_path, select_directory=True)

            else:

                # Translate path from setup

                export_path = pyflame_resolve_path_tokens(self.custom_export_path, self.clip)
                print('export_path:', export_path)

            if export_path:

                # Check if export path exists, if not create it

                if not os.path.exists(export_path):
                    try:
                        os.makedirs(export_path)
                    except:
                        return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Could not create export folder.')

                # Save export path

                save_settings()

                # Get clip info for export

                get_clip_info()

                # Export clip

                export_clip()

                # Get name of first image exported to load into Syntheyes

                get_image_name()

                # Open Syntheyes

                open_syntheyes()

                FlameMessageWindow('message', f'{SCRIPT_NAME}: Export Complete', 'SynthEyes open behind Flame window.')
            else:
                pyflame_print(SCRIPT_NAME, 'Export Cancelled - No folder selected.')

    # ------------------------ #

    def setup(self):
        '''
        Setup window to create tokenized SynthEyes jpeg export path.
        '''

        def toggle_custom_path():

            if self.export_push_button.text() == 'Browse To Path':
                self.custom_export_path_label.setEnabled(False)
                self.custom_export_path_entry.setEnabled(False)
                self.custom_export_path_token_button.setEnabled(False)
                self.browse_button.setEnabled(False)
            else:
                self.custom_export_path_label.setEnabled(True)
                self.custom_export_path_entry.setEnabled(True)
                self.custom_export_path_token_button.setEnabled(True)
                self.browse_button.setEnabled(True)

        def browse():

            browse_path = pyflame_file_browser('Select Directory', [''], self.custom_export_path_entry.text(), select_directory=True, window_to_hide=[self.setup_window])

            if browse_path:
                self.custom_export_path_entry.setText(browse_path)

        def save():

            if self.export_push_button.text() == 'Use Custom Path' and not self.custom_export_path_entry.text():
                return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Custom Export Path: Enter path before saving.')

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            export_path = root.find('.//export_path')
            export_path.text = self.export_push_button.text()

            custom_export_path = root.find('.//custom_export_path')
            custom_export_path.text = self.custom_export_path_entry.text()

            xml_tree.write(self.config_xml)

            pyflame_print(SCRIPT_NAME, 'Config saved.')

            self.setup_window.close()

        def cancel():

            self.setup_window.close()

        gridbox = QtWidgets.QGridLayout()
        self.setup_window = FlameWindow(f'{SCRIPT_NAME}: Setup <small>{VERSION}', gridbox, 900, 300)

        # Labels

        self.export_path_label = FlameLabel('Export Path')
        self.custom_export_path_label = FlameLabel('Custom Export Path')

        # Entry

        self.custom_export_path_entry = FlameLineEdit(self.custom_export_path)

        # Token Push Button

        export_token_dict = {'Project Name': '<ProjectName>', 'Project Nick Name': '<ProjectNickName>', 'Sequence Name': '<SeqName>', 'SEQUENCE NAME': '<SEQNAME>', 'Shot Name': '<ShotName>'}
        self.custom_export_path_token_button = FlameTokenPushButton('Add Token', export_token_dict, self.custom_export_path_entry)

        # Menu Push Button

        export_options = ['Browse To Path', 'Use Custom Path']
        self.export_push_button = FlamePushButtonMenu(self.export_path_menu, export_options, menu_action=toggle_custom_path)

        # Buttons

        self.browse_button = FlameButton('Browse', browse)
        self.save_button = FlameButton('Save', save)
        self.cancel_button = FlameButton('Cancel', cancel)

        # Toggle UI

        toggle_custom_path()

        # Window Layout

        gridbox.setMargin(20)

        gridbox.addWidget(self.export_path_label, 0, 0)
        gridbox.addWidget(self.export_push_button, 0, 1)

        gridbox.addWidget(self.custom_export_path_label, 1, 0)
        gridbox.addWidget(self.custom_export_path_entry, 1, 1, 1, 5)
        gridbox.addWidget(self.custom_export_path_token_button, 1, 7)
        gridbox.addWidget(self.browse_button, 1, 8)

        gridbox.addWidget(self.save_button, 2, 7)
        gridbox.addWidget(self.cancel_button, 2, 8)

        self.setup_window.show()
        return

def export(selection):
    '''
    Export selected clip to Syntheyes.
    '''

    script = FlameToSynthEyes(selection)
    script.syntheyes_export()

def setup(selection):
    '''
    Open setup window.
    '''

    script = FlameToSynthEyes(selection)
    script.setup()

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'SynthEyes Export Setup',
                    'execute': setup,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'SynthEyes...',
            'actions': [
                {
                    'name': 'Export to SynthEyes',
                    'isVisible': scope_clip,
                    'execute': export,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
