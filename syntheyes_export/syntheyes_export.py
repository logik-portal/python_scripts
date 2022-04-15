'''
Script Name: SynthEyes Export
Script Version: 2.4
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 10.27.19
Update Date: 03.21.22

Custom Action Type: Flame Main Menu

Description:

    Exports selected plate as jpg sequence, launches SynthEyes, then loads sequence into syntheyes for tracking

    SynthEyes will open behind the Flame window

Menu:

    Right-click on clip in Media Panel -> SynthEyes... -> Export to SynthEyes

To install:

    Copy script into /opt/Autodesk/shared/python/syntheyes_export

Updates:

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

from random import randint
from subprocess import Popen, PIPE
import xml.etree.ElementTree as ET
import os, platform
from PySide2 import QtWidgets
from flame_widgets_syntheyes_export import FlameMessageWindow, FlamePasswordWindow

VERSION = 'v2.4'

SCRIPT_PATH = '/opt/Autodesk/shared/python/syntheyes_export'

# --------------------- #

class FlameToSynthEyes(object):

    def __init__(self, selection):
        print ('''
       _____             _   _     ______
      / ____|           | | | |   |  ____|
     | (___  _   _ _ __ | |_| |__ | |__  _   _  ___  ___
      \___ \| | | | '_ \| __| '_ \|  __|| | | |/ _ \/ __|
      ____) | |_| | | | | |_| | | | |___| |_| |  __/\__ \\
     |_____/ \__, |_| |_|\__|_| |_|______\__, |\___||___/
              __/ |                       __/ |
             |___/                       |___/
                ______                       _
               |  ____|                     | |
               | |__  __  ___ __   ___  _ __| |_
               |  __| \ \/ / '_ \ / _ \| '__| __|
               | |____ >  <| |_) | (_) | |  | |_
               |______/_/\_\ .__/ \___/|_|   \__|
                           | |
                           |_|
 ''')
        print ('>' * 20, f'syntheyes export {VERSION}', '<' * 20, '\n')

        self.clip = selection[0]

        # Load config

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.config()

        # Check for sylevel file

        self.sylevel_check()

        # Match export preset version with version of flame

        self.check_flame_version()

        self.export_preset = os.path.join(SCRIPT_PATH, 'syntheyes_jpeg_export.xml')
        self.update_export_preset()

        # Set export path to / if last export path does not exist

        if not os.path.isdir(self.last_export_path):
            self.last_export_path = '/'

        # Init varaibles

        self.export_path = ''
        self.first_image_path = ''
        self.clip_ratio = ''

        # Make sure sypy/sypy3 is installed

        sypy_installed = self.syntheyes_check()

        # If sypy/sypy3 is installed run script

        if sypy_installed:
            self.syntheyes_export()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get settings

            for setting in root.iter('config'):
                self.last_export_path = setting.find('last_export_path').text

            print ('--> config loaded\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder:<br>{self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file\n')

                config = """
<settings>
    <config>
        <last_export_path>/opt/Autodesk</last_export_path>
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

    def check_flame_version(self):
        import flame

        # Get version of flame and convert to float

        self.flame_version = flame.get_version()

        if 'pr' in self.flame_version:
            self.flame_version = self.flame_version.rsplit('.pr', 1)[0]

        if len(self.flame_version) > 6:
            self.flame_version = self.flame_version[:6]
        self.flame_version = float(self.flame_version)
        print ('flame version:', self.flame_version, '\n')

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
            return FlameMessageWindow('Error', 'error', 'SynthEyes not found. Install SynthEyes before using this script.')

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

        system_password = str(FlamePasswordWindow('SynthEyes Export - Enter System Password', 'System password needed to install SynthEyes SyPY into Flame python folder.'))

        if system_password:
            version = int(str(self.flame_version)[:4])
            if version == 2023:

                # Copy SyPy3 from SynthEyes folder to Flame python folder

                sypy_folder = os.path.join(syntheyes_path, 'SyPy3')
                flame_sypy_folder = f'/opt/Autodesk/python/{flame.get_version()}/lib/python3.9/site-packages'
                # print ('flame_sypy_folder:', flame_sypy_folder, '\n')

                p = Popen(['sudo', '-S', 'cp', '-r', sypy_folder, flame_sypy_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                p.communicate(system_password + '\n')[1]

                print ('--> SyPy3 copied to Flame python folder\n')

            elif version == 2022:

                # Copy SyPy3 from SynthEyes folder to Flame python folder

                sypy_folder = os.path.join(syntheyes_path, 'SyPy3')
                flame_sypy_folder = f'/opt/Autodesk/python/{flame.get_version()}/lib/python3.7/site-packages'
                # print ('flame_sypy_folder:', flame_sypy_folder, '\n')

                p = Popen(['sudo', '-S', 'cp', '-r', sypy_folder, flame_sypy_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                p.communicate(system_password + '\n')[1]

                print ('--> SyPy3 copied to Flame python folder\n')

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
        elif flame_version >= '2024':
            FlameMessageWindow('Error', 'error', 'Newer version of script required for this version of Flame')
            shit

        # If preset version if different than current export version then update xml

        if current_export_version != export_version:
            for element in root.iter('preset'):
                element.set('version', export_version)

            export_preset_xml_tree.write(self.export_preset)

            print ('--> export preset version updated')

    def syntheyes_export(self):
        import flame

        def export_browse():

            self.export_path = str(QtWidgets.QFileDialog.getExistingDirectory(QtWidgets.QWidget(), 'Select Directory', self.last_export_path, QtWidgets.QFileDialog.ShowDirsOnly))

        def save_settings():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            last_export_path = root.find('.//last_export_path')
            last_export_path.text = self.export_path

            xml_tree.write(self.config_xml)

            print ('--> config file saved\n')

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

            clip_exporter.export(sources = self.clip, preset_path = self.export_preset, output_directory = self.export_path)

        def get_image_name():

            image_seq_path = os.path.join(self.export_path, self.clip_name)

            file_list = []

            for file in os.listdir(image_seq_path):
                if file.endswith('.jpg'):
                    file_list.append(file)
            file_list.sort()
            # print 'file_list:', file_list

            first_image_file = file_list[0]
            # print 'first_image_file:', first_image_file

            self.first_image_path = os.path.join(image_seq_path, first_image_file)

        def open_syntheyes():

            # Create random port number

            random_port = randint(1000, 9999)
            # print ('random_port:', random_port)

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

        # Select export folder

        FlameMessageWindow('Select Path', 'message', 'Select path to export plate for tracking in Syntheyes.')

        export_browse()

        if not os.path.isdir(self.export_path):
            print ('--> Export Cancelled - No folder selected\n')
            print ('done.')
        else:
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

            FlameMessageWindow('Export Complete', 'message', 'SynthEyes open behind Flame window.')

            print ('done.\n')

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'SynthEyes...',
            'actions': [
                {
                    'name': 'Export to SynthEyes',
                    'isVisible': scope_clip,
                    'execute': FlameToSynthEyes,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
