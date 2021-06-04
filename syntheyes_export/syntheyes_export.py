'''
Script Name: SynthEyes Export
Script Version: 2.0
Flame Version: 2020.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 10.27.19
Update Date: 06.01.21

Custom Action Type: Flame Main Menu

Description:

    Exports selected plate as jpg sequence, launches SynthEyes, then loads sequence into syntheyes for tracking

    SynthEyes will open behind the Flame window

    Right-click on clip in Media Panel -> SynthEyes... -> Export to SynthEyes

To install:

    Copy script into /opt/Autodesk/shared/python/syntheyes_export

    *** VERY IMPORTANT ***

    The SyPy python package that comes with SynthEyes needs to be installed for scipt to work.

    For Flame 2022 and later:

    Copy the SyPy3 folder from Applications/SynthEyes into /opt/Autodesk/python/FLAME_VERSION/lib/python3.7/site-packages

    For Flame 2021.2 and ealier

    Copy the SyPy folder from Applications/SynthEyes into /opt/Autodesk/python/FLAME_VERSION/lib/python2.7/site-packages

    Then unzip sylevel.zip into: /opt/Autodesk/python/FLAME_VERSION/lib/python2.7/site-packages/SyPy

    This will replace the existing sylevel.py file in that folder with a new one.

Updates:

v2.0 06.01.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.1 06.08.20

    Simplified clip exporting
'''

from __future__ import print_function
import os
from PySide2 import QtWidgets, QtCore

VERSION = 'v2.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/syntheyes_export'

class FlameToSynthEyes(object):

    def __init__(self, selection):

        print ('\n', '>' * 20, 'syntheyes export %s' % VERSION, '<' * 20, '\n')

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')

        self.clip = selection[0]

        self.config_file_check()

        # Get config values

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.last_export_path = values[2]

        get_config_values.close()

        # Set export path to / if last export path does not exist

        if not os.path.isdir(self.last_export_path):
            self.last_export_path = '/'

        # Init varaibles

        self.export_path = ''
        self.first_image_path = ''
        self.clip_ratio = ''
        self.sypy = ''

        self.check_flame_version()

        sypy_installed = self.check_sypy()

        if sypy_installed:
            self.syntheyes_export()

    def config_file_check(self):

        # Check for and load config file
        #-------------------------------

        if not os.path.isdir(self.config_path):
            try:
                os.makedirs(self.config_path)
            except:
                message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)
                print ('\n>>> Unable to create folder: %s Check folder permissions <<<\n')

        if not os.path.isfile(self.config_file):
            print ('>>> config file does not exist, creating new config file <<<')

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame Flame to SynthEyes script:')
            config_text.insert(1, 'Last Export Path:')
            config_text.insert(2, '/')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print (line, file=out_file)
            out_file.close()

    def check_flame_version(self):
        import flame

        # Check flame version

        flame_version = flame.get_version()

        if 'pr' in flame_version:
            flame_version = flame_version.rsplit('.pr', 1)[0]
        if  flame_version.count('.') > 1:
            flame_version = flame_version.rsplit('.', 1)[0]
        self.flame_version = float(flame_version)
        print ('flame_version:', self.flame_version)

    def check_sypy(self):
        '''
        Check if to see if SyPy is installed
        If using Flame 2022 or higher, SyPy3 should be installed
        If using Flame 2021.2 or lower, SyPy should be installed
        '''

        try:
            if self.flame_version >= 2022.0:
                import SyPy3
                self.sypy = 'SyPy3'
                print ('\n>>> SyPy Installed - Using SyPy3<<<\n')
                return True
            else:
                import SyPy
                self.sypy = 'SyPy'
                print ('\n>>> SyPy Installed - Using SyPy<<<\n')
                return True
        except:
            return message_box('SynthEyes SyPy Python Package not found!<br><br>'
                               'SyPy needs to be installed for script to work.<br>'
                               'SyPy can be found in Applications/Syntheyes<br><br>'
                               'If using Flame 2022 or later copy SyPy3 into:<br>'
                               '/opt/Autodesk/python/FLAME_VERSION/lib/python3.7/site-packages<br><br>'
                               'If using Flame 2021.2 or earlier copy SyPy into:<br>'
                               '/opt/Autodesk/python/FLAME_VERSION/lib/python2.7/site-packages<br>'
                               'Then unzip sylevel.zip into: '
                               '/opt/Autodesk/python/FLAME_VERSION/lib/python2.7/site-packages/SyPy')

    def syntheyes_export(self):
        import flame

        def export_browse():

            self.export_path = str(QtWidgets.QFileDialog.getExistingDirectory(QtWidgets.QWidget(), 'Select Directory', self.last_export_path, QtWidgets.QFileDialog.ShowDirsOnly))

        def save_settings():

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame Flame to SynthEyes script:')
            config_text.insert(1, 'Last Export Path:')
            config_text.insert(2, self.export_path)

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print (line, file=out_file)
            out_file.close()

            print ('\n>>> config file saved <<<\n')

        def get_clip_info():

            self.clip_name = str(self.clip.name)[1:-1]
            print ('clip_name:', self.clip_name)

            self.clip_framerate = str(self.clip.frame_rate)[:-4]
            self.clip_framerate = float(self.clip_framerate)
            print ('clip_framerate:', self.clip_framerate)

            self.clip_ratio = float(self.clip.ratio)
            print ('clip_ratio:', self.clip_ratio)

        def export_clip():

            # Path to export preset

            export_preset = os.path.join(SCRIPT_PATH, 'syntheyes_jpeg_export.xml')

            # Export jpeg_sequence to shot folder

            clip_exporter = flame.PyExporter()
            clip_exporter.foreground = True

            clip_exporter.export(sources = self.clip, preset_path = export_preset, output_directory = self.export_path)

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
            from random import randint

            # Create random port number

            random_port = randint(1000, 9999)
            print ('random_port:', random_port)

            # Set hlev
            # Try with SyPy3 for python 3, if using Python 2 use SyPy

            if self.sypy == 'SyPy3':
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

        export_browse()

        if not os.path.isdir(self.export_path):
            print ('\n>>> No folder selected <<<\n')
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

            print ('\ndone.\n')

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

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

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
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]
