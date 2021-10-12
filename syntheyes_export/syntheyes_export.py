'''
Script Name: SynthEyes Export
Script Version: 2.2
Flame Version: 2021.1
Written by: Michael Vaglienty
Creation Date: 10.27.19
Update Date: 10.11.21

Custom Action Type: Flame Main Menu

Description:

    Exports selected plate as jpg sequence, launches SynthEyes, then loads sequence into syntheyes for tracking

    SynthEyes will open behind the Flame window

    Right-click on clip in Media Panel -> SynthEyes... -> Export to SynthEyes

To install:

    Copy script into /opt/Autodesk/shared/python/syntheyes_export

Updates:

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

from __future__ import print_function
from random import randint
from subprocess import Popen, PIPE
import xml.etree.ElementTree as ET
import os, shutil, platform
from PySide2 import QtWidgets, QtCore

VERSION = 'v2.2'

SCRIPT_PATH = '/opt/Autodesk/shared/python/syntheyes_export'

# UI Classes

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget

    For different label looks set label_type as: 'normal', 'background', or 'outline'

    To use:

    label = FlameLabel('Label Name', 'normal', window)
    """

    def __init__(self, label_name, label_type, parent_window, *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent_window)
        self.setMinimumSize(110, 28)
        self.setMaximumSize(110, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                               'QLabel:disabled {color: #6a6a6a}')
        elif label_type == 'background':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('QLabel {color: #9a9a9a; background-color: #393939; font: 14px "Discreet"}'
                               'QLabel:disabled {color: #6a6a6a}')
        elif label_type == 'outline':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('QLabel {color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"}'
                               'QLabel:disabled {color: #6a6a6a}')

class FlameLineEdit(QtWidgets.QLineEdit):
    """
    Custom Qt Flame Line Edit Widget

    Main window should include this: window.setFocusPolicy(QtCore.Qt.StrongFocus)

    To use:

    line_edit = FlameLineEdit('Some text here', window)
    """

    def __init__(self, text, parent_window, *args, **kwargs):
        super(FlameLineEdit, self).__init__(*args, **kwargs)

        self.setText(text)
        self.setParent(parent_window)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        # self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                           'QLineEdit:focus {background-color: #474e58}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget

    To use:

    button = FlameButton('Button Name', do_when_pressed, window)
    """

    def __init__(self, button_name, do_when_pressed, parent_window, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setMinimumSize(QtCore.QSize(110, 28))
        self.setMaximumSize(QtCore.QSize(110, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(do_when_pressed)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

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
        print ('>' * 20, 'syntheyes export %s' % VERSION, '<' * 20, '\n')

        self.clip = selection[0]

        # Load config

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.config()

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

            print ('>>> config loaded <<<\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)

            if not os.path.isfile(self.config_xml):
                print ('>>> config file does not exist, creating new config file <<<\n')

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

        if len(self.flame_version) > 6:
            self.flame_version = self.flame_version[:6]
        self.flame_version = float(self.flame_version)
        print ('flame version:', self.flame_version, '\n')

    def syntheyes_check(self):
        '''
        Check /opt/Autodesk/python/FLAME_VERSION/lib/python3.7/site-packages for SyPy3.
        If not found copy from /Applications/SynthEyes/SyPy3 folder.
        Linux users will have to manually copy.
        '''

        if not os.path.isdir('/Applications/SynthEyes'):
            return message_box('SynthEyes not found. Install SynthEyes before using this script.')

        try:
            if self.flame_version >= 2022.0:
                import SyPy3
                print ('>>> SyPy3 Found! <<<\n')
                return True
            else:
                import SyPy
                print ('>>> SyPy Found! <<<\n')
                return True
        except:
            if platform.system() == 'Darwin':
                print ('>>> SyPy not found <<<\n')
                self.copy_sypy()
            else:
                if self.flame_version >= 2022.0:
                    message_box('Linux users must copy SynthEyes SyPy3 folder into:<br>/opt/Autodesk/python/FLAME_VERSION/lib/python3.7/site-packages')
                else:
                    message_box('Linux users must copy SynthEyes SyPy folder into:<br>/opt/Autodesk/python/FLAME_VERSION/lib/python2.7/site-packages')

    def copy_sypy(self):

        def ok():
            import flame

            temp_folder = '/opt/Autodesk/password_test_folder'

            self.sudo_password = self.password_lineedit.text()

            p = Popen(['sudo', '-S', 'mkdir', temp_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
            p.communicate(self.sudo_password + '\n')[1]

            if os.path.isdir(temp_folder):

                # Remove temp folder

                p = Popen(['sudo', '-S', 'rmdir', temp_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                p.communicate(self.sudo_password + '\n')[1]

                self.password_window.close()

                # For versions of Flame 2022 and higher, copy SyPy3 to current Flame python folder.
                # For earlier versions, copy SyPy to current Flame folder, then untar and move sylevel.py fix file

                if self.flame_version >= 2022.0:

                    # Copy SyPy3 from SynthEyes folder to Flame python folder

                    sypy_folder = '/Applications/SynthEyes/SyPy3'
                    flame_sypy_folder = '/opt/Autodesk/python/%s/lib/python3.7/site-packages' % flame.get_version()
                    # print ('flame_sypy_folder:', flame_sypy_folder, '\n')

                    p = Popen(['sudo', '-S', 'cp', '-r', sypy_folder, flame_sypy_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                    p.communicate(self.sudo_password + '\n')[1]

                    print ('>>> SyPy3 copied to Flame python folder <<<\n')

                else:

                    # Copy SyPy from SynthEyes folder to Flame python folder

                    sypy_folder = '/Applications/SynthEyes/SyPy'
                    flame_sypy_folder = '/opt/Autodesk/python/%s/lib/python2.7/site-packages' % flame.get_version()
                    # print ('flame_sypy_folder:', flame_sypy_folder, '\n')

                    p = Popen(['sudo', '-S', 'cp', '-r', sypy_folder, flame_sypy_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                    p.communicate(self.sudo_password + '\n')[1]

                    # Uncompress sylevel tar file

                    untar_command = 'tar -xf %s -C %s' % (os.path.join(SCRIPT_PATH, 'sylevel.tar'), SCRIPT_PATH)
                    # print ('untar command:', untar_command)

                    os.system(untar_command)

                    # Replace sylevel.py in new Flame SyPy folder

                    sylevel_source_path = os.path.join(SCRIPT_PATH, 'sylevel.py')
                    sylevel_dest_path = os.path.join(flame_sypy_folder, 'SyPy', 'sylevel.py')

                    p = Popen(['sudo', '-S', 'mv', sylevel_source_path, sylevel_dest_path], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                    p.communicate(self.sudo_password + '\n')[1]

                    print ('>>> SyPy copied to Flame python folder <<<\n')

                # Continue to export selected clip to SynthEyes

                self.syntheyes_export()

            else:
                message_box('System Password Incorrect')
                return

        def cancel():

            self.password_window.close()

            print ('SyPy3 copy cancelled.\n')

        self.password_window = QtWidgets.QWidget()
        self.password_window.setMinimumSize(QtCore.QSize(300, 120))
        self.password_window.setMaximumSize(QtCore.QSize(300, 120))
        self.password_window.setWindowTitle('Enter System Password')
        self.password_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.password_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.password_window.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.password_window.setStyleSheet('background-color: #272727')
        self.password_window.setWindowModality(QtCore.Qt.WindowModal)

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.password_window.move((resolution.width() / 2) - (self.password_window.frameSize().width() / 2),
                                  (resolution.height() / 2) - (self.password_window.frameSize().height() / 2))

        #  Labels

        self.password_label = FlameLabel('System Password', 'normal', self.password_window)
        self.password_label.setMinimumWidth(150)

        # LineEdits

        self.password_lineedit = FlameLineEdit('', self.password_window)
        self.password_lineedit.setMaximumWidth(150)
        self.password_lineedit.setEchoMode(QtWidgets.QLineEdit.Password)

        #  Buttons

        self.password_ok_btn = FlameButton('Ok', ok, self.password_window)
        self.password_cancel_btn = FlameButton('Cancel', cancel, self.password_window)

        #------------------------------------#

        #  Window Layout

        hbox = QtWidgets.QHBoxLayout()

        hbox.addWidget(self.password_cancel_btn)
        hbox.addWidget(self.password_ok_btn)

        gridbox = QtWidgets.QGridLayout()
        gridbox.setVerticalSpacing(20)
        gridbox.setHorizontalSpacing(20)

        gridbox.addWidget(self.password_label, 1, 0)
        gridbox.addWidget(self.password_lineedit, 1, 1)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(gridbox)
        vbox.addLayout(hbox)

        self.password_window.setLayout(vbox)

        self.password_window.show()

        if self.flame_version >= 2022.0:
            message_box('<center>System password needed to copy SyPy3 from SynthEyes folder to Flame python folder')
        else:
            message_box('<center>System password needed to copy SyPy from SynthEyes folder to Flame python folder')

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

        # Get export version for verion of flame being used. 2021 is version 10.

        export_version = str(int(flame_version) - 2021 + 10)

        # If preset version if different than current export version then update xml

        if current_export_version != export_version:
            for element in root.iter('preset'):
                element.set('version', export_version)

            export_preset_xml_tree.write(self.export_preset)

            print ('>>> export preset version updated <<<')

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

            print ('>>> config file saved <<<\n')

        def get_clip_info():

            print ('>>> exporting clip:')

            self.clip_name = str(self.clip.name)[1:-1]
            print ('    clip name:', self.clip_name)

            self.clip_framerate = str(self.clip.frame_rate)[:-4]
            self.clip_framerate = float(self.clip_framerate)
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

        message_box('Select path to export plate for tracking')

        export_browse()

        if not os.path.isdir(self.export_path):
            print ('>>> Export Cancelled - No folder selected <<<\n')
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

            message_box('Shot exported - SynthEyes open behind Flame window')

            print ('done.\n')

def message_box(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setMinimumSize(400, 100)
    msg_box.setText(message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14px "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14px "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>', '<center>']

    for code in code_list:
        message = message.replace(code, '')

    print ('>>> %s <<<\n' % message)

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
                    'minimumVersion': '2021.1'
                }
            ]
        }
    ]
