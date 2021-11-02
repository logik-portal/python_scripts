'''
Script Name: Export Frame
Script Version: 1.3
Flame Version: 2021.2
Written by: Michael Vaglienty
Creation Date: 10.11.21
Update Date: 11.02.21

Custom Action Type: Media Panel/Player

Description:

    Export current frame or frames at markers from selected clips/sequences.
    Based in part from the Autodesk Export Current Frame example script.

    Frames can be exported from player view.

    One or more clips can be selected in the Media Panel to export frames from.

    When exporting multiple frames using markers, the export preset should use frame padding
    or timecode in the file name to avoid overwriting frames.

    The default export preset used is the default Autodesk Jpeg preset. To use custom presets,
    save them as shared presets and then select it in the script setup.

    Custom export paths using tokens can be set in the script setup.

    Openning the MediaHub or a Finder window after the export is completed can be set in the script setup.

    Menus:

        Flame Main Menu -> pyFlame -> Export Current Frame Setup

        Right-click on clip, sequence, or player view -> Export... -> Export Current Frame
        Right-click on clip, sequence, or player view -> Export... -> Export Marker Frames

To install:

    Copy script into /opt/Autodesk/shared/python/export_frame

Updates:

    v1.3 11.02.21

        Fixed shot name token compatibility to work with python 3.7

    v1.2 10.24.21

        Removed custom path menus. Custom export paths can be turned on in Setup.

        Known bug - right clicking on clip in schematic reel will cause flame to crash.

    v1.1 10.12.21

        Fixed SEQNAME token
'''

from __future__ import print_function
from PySide2 import QtWidgets, QtCore
from functools import partial
import xml.etree.ElementTree as ET
import re, os, ast, datetime, platform, subprocess

VERSION = 'v1.3'

SCRIPT_PATH = '/opt/Autodesk/shared/python/export_frame'

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget
    Options for normal, label with background color, and label with background color and outline
    """

    def __init__(self, label_name, parent, label_type='normal', *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent)
        self.setMinimumSize(150, 28)
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
            # self.setAlignment(QtCore.Qt.AlignLeft)
            self.setStyleSheet('QLabel {color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"}'
                               'QLabel:disabled {color: #6a6a6a}')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget
    """

    def __init__(self, button_name, connect, parent, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumSize(QtCore.QSize(150, 28))
        self.setMaximumSize(QtCore.QSize(150, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

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
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

class FlamePushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Widget

    To use:

    pushbutton = FlamePushButton(' Button Name', bool, window)
    """

    def __init__(self, button_name, button_checked, parent_window, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setCheckable(True)
        self.setChecked(button_checked)
        self.setMinimumSize(150, 28)
        self.setMaximumSize(150, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #424142, stop: .94 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #4f4f4f, stop: .94 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlamePushButtonMenu(QtWidgets.QPushButton):
    """
    Custom Qt Flame Menu Push Button Widget

    To use:

    push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
    menu_push_button = FlamePushButtonMenu('push_button_name', push_button_menu_options, window)

    or

    push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
    menu_push_button = FlamePushButtonMenu(push_button_menu_options[0], push_button_menu_options, window)
    """

    def __init__(self, button_name, menu_options, parent_window, *args, **kwargs):
        super(FlamePushButtonMenu, self).__init__(*args, **kwargs)
        from functools import partial

        self.setText(button_name)
        self.setParent(parent_window)
        self.setMinimumHeight(28)
        self.setMinimumWidth(150)
        # self.setMaximumWidth(150)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        def create_menu(option):
            self.setText(option)

        pushbutton_menu = QtWidgets.QMenu(parent_window)
        pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        pushbutton_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        for option in menu_options:
            pushbutton_menu.addAction(option, partial(create_menu, option))

        self.setMenu(pushbutton_menu)

class FlameTokenPushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Token Push Button Widget

    To use:

    token_dict = {'Token 1': '<Token1>', 'Token2': '<Token2>'}
    token_push_button = FlameTokenPushButton('Add Token', token_dict, token_dest, window)

    token_dict: Key in dictionary is what will show in button menu.
                Value in dictionary is what will be applied to the button destination
    token_dest: Where the Value of the item selected will be applied such as a LineEdit
    """

    def __init__(self, button_name, token_dict, token_dest, parent, *args, **kwargs):
        super(FlameTokenPushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setMinimumWidth(150)
        self.setMaximumWidth(150)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #6a6a6a}')

        def token_action_menu():
            from functools import partial

            def insert_token(token):
                for key, value in token_dict.items():
                    if key == token:
                        token_name = value
                        token_dest.insert(token_name)

            for key, value in token_dict.items():
                token_menu.addAction(key, partial(insert_token, key))

        token_menu = QtWidgets.QMenu(parent)
        token_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        token_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                 'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.setMenu(token_menu)

        token_action_menu()

#-------------------------------------#

class ExportFrame(object):

    def __init__(self, selection):
        import flame

        print ('''
 ______                       _      ______
|  ____|                     | |    |  ____|
| |__  __  ___ __   ___  _ __| |_   | |__ _ __ __ _ _ __ ___   ___
|  __| \ \/ / '_ \ / _ \| '__| __|  |  __| '__/ _` | '_ ` _ \ / _ \\
| |____ >  <| |_) | (_) | |  | |_   | |  | | | (_| | | | | | |  __/
|______/_/\_\ .__/ \___/|_|   \__|  |_|  |_|  \__,_|_| |_| |_|\___|
            | |
            |_|
        ''')

        print ('>' * 24, 'export frame %s' % VERSION, '<' * 24, '\n')

        self.selection = selection

        # Set paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Get list of export presets in shared export folder

        self.shared_presets_path = '/opt/Autodesk/shared/export/presets/file_sequence'
        self.shared_presets = ['Default Jpeg'] + [preset[:-4] for preset in os.listdir(self.shared_presets_path)]

        # Load config file

        self.config()

        print ('selected export preset:', self.export_preset, '\n')

        # Get current date/time for token conversion

        self.date = datetime.datetime.now()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('export_frame_settings'):
                self.saved_browse_path = setting.find('saved_browse_path').text
                self.custom_export_path = setting.find('custom_export_path').text
                self.export_preset = setting.find('export_preset').text
                self.reveal_in_finder = ast.literal_eval(setting.find('reveal_in_finder').text)
                self.reveal_in_mediahub = ast.literal_eval(setting.find('reveal_in_mediahub').text)
                self.export_destination = setting.find('export_destination').text

            print ('>>> config loaded <<<\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)

            if not os.path.isfile(self.config_xml):
                print ('>>> config file does not exist, creating new config file <<<')

                config = """
<settings>
    <export_frame_settings>
        <saved_browse_path>/</saved_browse_path>
        <custom_export_path>/</custom_export_path>
        <export_preset>Default Jpeg</export_preset>
        <reveal_in_finder>False</reveal_in_finder>
        <reveal_in_mediahub>False</reveal_in_mediahub>
        <export_destination>Browse to Path</export_destination>
    </export_frame_settings>
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

    def setup(self):

        def export_dest_toggle(dest):

            self.export_dest_menu_push_button.setText(dest)

            if dest == 'Browse to Path':
                self.custom_path_settings_label.setEnabled(False)
                self.custom_export_path_label.setEnabled(False)
                self.custom_export_path_lineedit.setEnabled(False)
                self.custom_token_push_btn.setEnabled(False)
                self.browse_btn.setEnabled(False)
            else:
                self.custom_path_settings_label.setEnabled(True)
                self.custom_export_path_label.setEnabled(True)
                self.custom_export_path_lineedit.setEnabled(True)
                self.custom_token_push_btn.setEnabled(True)
                self.browse_btn.setEnabled(True)

        def custom_path_browse():

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.setup_window, 'Select Directory', self.custom_export_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.custom_export_path_lineedit.setText(file_path)

        def save_config():

            if self.custom_export_path_lineedit.text() == '':
                self.custom_export_path_lineedit.setText('/')
            else:

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                custom_export_path = root.find('.//custom_export_path')
                custom_export_path.text = self.custom_export_path_lineedit.text()

                export_preset = root.find('.//export_preset')
                export_preset.text = self.export_preset_menu_push_button.text()

                reveal_in_finder = root.find('.//reveal_in_finder')
                reveal_in_finder.text = str(self.reveal_finder_push_button.isChecked())

                reveal_in_mediahub = root.find('.//reveal_in_mediahub')
                reveal_in_mediahub.text = str(self.reveal_mediahub_push_button.isChecked())

                export_destination = root.find('.//export_destination')
                export_destination.text = self.export_dest_menu_push_button.text()

                xml_tree.write(self.config_xml)

                print ('>>> Config saved <<<\n')

                self.setup_window.close()

                print ('Done.\n')

        self.setup_window = QtWidgets.QWidget()
        self.setup_window.setMinimumSize(QtCore.QSize(900, 420))
        self.setup_window.setMaximumSize(QtCore.QSize(900, 420))
        self.setup_window.setWindowTitle('Export Frame Setup %s' % VERSION)
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                               (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        # Labels

        self.export_settings_label = FlameLabel('Export Settings', self.setup_window, label_type='background')
        self.after_export_label = FlameLabel('After Export', self.setup_window, label_type='normal')
        self.export_dest_label = FlameLabel('Export Destination', self.setup_window, label_type='normal')
        self.custom_path_settings_label = FlameLabel('Custom Path Settings', self.setup_window, label_type='background')
        self.custom_export_path_label = FlameLabel('Custom Export Path', self.setup_window, label_type='normal')
        self.export_preset_label = FlameLabel('Export Preset', self.setup_window, label_type='normal')

        # LineEdits

        self.custom_export_path_lineedit = FlameLineEdit(self.custom_export_path, self.setup_window)

        # Batch Path Token Pushbutton Menu

        custom_token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>', 'Shot Name': '<ShotName>',
                             'Sequence Name': '<SeqName>', 'SEQUENCE NAME': '<SEQNAME>', 'Clip Name': '<ClipName>',
                             'User Name': '<UserName>', 'User Nickname': '<UserNickName>', 'Clip Resolution': '<Resolution>',
                             'Clip Height': '<ClipHeight>', 'Clip Width': '<ClipWidth>', 'Year (YYYY)': '<YYYY>',
                             'Year (YY)': '<YY>', 'Month': '<MM>', 'Day': '<DD>', 'Hour': '<Hour>', 'Minute': '<Minute>',
                             'AM/PM': '<AMPM>', 'am/pm': '<ampm>'}

        self.custom_token_push_btn = FlameTokenPushButton('Add Token', custom_token_dict, self.custom_export_path_lineedit, self.setup_window)

        # Menu Push Buttons

        self.export_preset_menu_push_button = FlamePushButtonMenu(self.export_preset, self.shared_presets, self.setup_window)

        # Export Destination Menu Push Button

        self.export_dest_menu = QtWidgets.QMenu(self.setup_window)
        self.export_dest_menu.addAction('Browse to Path', partial(export_dest_toggle, 'Browse to Path'))
        self.export_dest_menu.addAction('Use Custom Path', partial(export_dest_toggle, 'Use Custom Path'))
        self.export_dest_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                            'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.export_dest_menu_push_button = QtWidgets.QPushButton(self.export_destination, self.setup_window)
        self.export_dest_menu_push_button.setMenu(self.export_dest_menu)
        self.export_dest_menu_push_button.setMinimumSize(QtCore.QSize(150, 28))
        self.export_dest_menu_push_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.export_dest_menu_push_button.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                        'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        # Push buttons

        self.reveal_finder_push_button = FlamePushButton(' Reveal in Finder', self.reveal_in_finder, self.setup_window)
        self.reveal_mediahub_push_button = FlamePushButton(' Reveal in MediaHub', self.reveal_in_mediahub, self.setup_window)

        #  Buttons

        self.browse_btn = FlameButton('Browse', custom_path_browse, self.setup_window)
        self.save_btn = FlameButton('Save', save_config, self.setup_window)
        self.cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window)

        export_dest_toggle(self.export_destination)

        # Setup window layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setMargin(20)

        gridbox.setRowMinimumHeight(1, 30)
        gridbox.setRowMinimumHeight(4, 30)
        gridbox.setRowMinimumHeight(8, 30)
        gridbox.setRowMinimumHeight(11, 30)

        gridbox.setColumnMinimumWidth(2, 75)

        gridbox.addWidget(self.export_settings_label, 0 ,0, 1, 6)

        gridbox.addWidget(self.export_preset_label, 3 ,0)
        gridbox.addWidget(self.export_preset_menu_push_button, 3, 1, 1, 3)

        gridbox.addWidget(self.export_dest_label, 5 ,0)
        gridbox.addWidget(self.export_dest_menu_push_button, 5 ,1)

        gridbox.addWidget(self.after_export_label, 5 ,3)
        gridbox.addWidget(self.reveal_finder_push_button, 5 ,4)
        gridbox.addWidget(self.reveal_mediahub_push_button, 6 ,4)

        gridbox.addWidget(self.custom_path_settings_label, 9 ,0, 1, 6)

        gridbox.addWidget(self.custom_export_path_label, 10 ,0)
        gridbox.addWidget(self.custom_export_path_lineedit, 10 ,1, 1, 3)
        gridbox.addWidget(self.custom_token_push_btn, 10 ,4)
        gridbox.addWidget(self.browse_btn, 10 ,5)

        gridbox.addWidget(self.save_btn, 12, 5)
        gridbox.addWidget(self.cancel_btn, 13, 5)

        self.setup_window.setLayout(gridbox)

        self.setup_window.show()

        return self.setup_window

    def export_current_frame(self):
        # import flame

        marker = ''

        if self.export_destination == 'Browse to Path':

            export_path = self.folder_browser()

            # Export current frame from selected clips

            if os.path.isdir(export_path):
                for clip in self.selection:
                    self.export(export_path, marker, clip)
                print ('\n')
                self.post_export(export_path)
            else:
                print ('>>> Export cancelled <<<\n')

        else:
            # Check path in config file

            if self.custom_export_path == '/':
                return message_box('<center>Add custom path in script setup. <br><br>Flame Main Menu -> pyFlame -> <br>Export Frame Setup')

            # Export frames

            for clip in self.selection:

                # Translate custom path

                export_path = self.translate_path(clip)

                # Export

                self.export(export_path, marker, clip)

            print ('\n')

            self.post_export(export_path)

    def export_marker_frame(self):

        if self.export_destination == 'Browse to Path':

            export_path = self.folder_browser()

            # Export current frame from selected clips

            if os.path.isdir(export_path):
                for clip in self.selection:
                    for marker in clip.markers:
                        self.export(export_path, marker, clip)
                print ('\n')
                self.post_export(export_path)
            else:
                print ('>>> Export cancelled <<<\n')

        else:
            # Check saved settings

            if self.custom_export_path == '/':
                return message_box('<center>Add custom path in script setup. <br><br>Flame Main Menu -> pyFlame -> <br>Export Frame Setup')

            for clip in self.selection:
                for marker in clip.markers:

                    # Translate custom path

                    export_path = self.translate_path(clip)

                    # Export

                    self.export(export_path, marker, clip)

                    print ('\n')

            print ('\n')

            self.post_export(export_path)

#-------------------------------------#

    def export(self, export_path, marker, clip):
        import flame

        # Set exporter

        exporter = flame.PyExporter()
        exporter.foreground = True
        exporter.export_between_marks = True

        # Duplicate the clip to avoid modifying the original clip

        duplicate_clip = flame.duplicate(clip)

        # Set export preset path

        if self.export_preset == 'Default Jpeg':

            # Get default export preset path

            preset_dir = flame.PyExporter.get_presets_dir(
                flame.PyExporter.PresetVisibility.Autodesk,
                flame.PyExporter.PresetType.Image_Sequence)
            export_preset_path = os.path.join(preset_dir, "Jpeg", "Jpeg (8-bit).xml")

        else:
            export_preset_path = os.path.join(self.shared_presets_path, self.export_preset + '.xml')

        try:
            if marker:
                duplicate_clip.in_mark = marker.location.get_value()
                duplicate_clip.out_mark = marker.location.get_value() + 1
            else:
                duplicate_clip.in_mark = clip.current_time.get_value()
                duplicate_clip.out_mark = clip.current_time.get_value() + 1
            exporter.export(duplicate_clip, export_preset_path, export_path)
        finally:
            print ('    Exported:', str(clip.name)[1:-1], 'at %s' % duplicate_clip.in_mark)
            flame.delete(duplicate_clip)

#-------------------------------------#

    def folder_browser(self):

        def save_config():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            saved_browse_path = root.find('.//saved_browse_path')
            saved_browse_path.text = export_path

            xml_tree.write(self.config_xml)

            print ('>>> config saved <<<\n')

        # Select export folder

        message_box('Select still image export path')

        # Open folder browse window

        window = QtWidgets.QWidget()
        export_path = str(QtWidgets.QFileDialog.getExistingDirectory(window, 'Select Directory', self.saved_browse_path, QtWidgets.QFileDialog.ShowDirsOnly))

        # Save config if path is good

        if os.path.isdir(export_path):
            save_config()
            print ('Export path:', export_path, '\n')

        return export_path

    def translate_path(self, clip):
        import flame

        def get_shot_name(name):

            shot_name_split = re.split(r'(\d+)', name)

            if len(shot_name_split) > 1:
                if shot_name_split[1].isalnum():
                    shot_name = shot_name_split[0] + shot_name_split[1]
                else:
                    shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]
            else:
                shot_name = name

            return shot_name

        def get_seq_name(name):

            # Get sequence name abreviation from shot name

            seq_name = re.split('[^a-zA-Z]', name)[0]

            return seq_name

        clip_name = str(clip.name)[1:-1]

        # Get shot name

        try:
            if clip.versions[0].tracks[0].segments[0].shot_name != '':
                shot_name = str(clip.versions[0].tracks[0].segments[0].shot_name)[1:-1]
            else:
                shot_name = get_shot_name(clip_name)
        except:
            shot_name = ''

        # Get Seq Name

        seq_name = get_seq_name(shot_name)

        # Get time values for tokens

        yyyy = self.date.strftime('%Y')
        yy = self.date.strftime('%y')
        mm = self.date.strftime('%m')
        dd = self.date.strftime('%d')
        hour = self.date.strftime('%I')
        if hour.startswith('0'):
            hour = hour[1:]
        minute = self.date.strftime('%M')
        ampm_caps = self.date.strftime('%p')
        ampm = str(self.date.strftime('%p')).lower()

        # Replace tokens in path

        new_export_path = re.sub('<ProjectName>', flame.project.current_project.name, self.custom_export_path)
        new_export_path = re.sub('<ProjectNickName>', flame.project.current_project.nickname, new_export_path)
        new_export_path = re.sub('<ShotName>',shot_name, new_export_path)
        new_export_path = re.sub('<SEQNAME>', seq_name.upper(), new_export_path)
        new_export_path = re.sub('<SeqName>', seq_name, new_export_path)
        new_export_path = re.sub('<UserName>', flame.users.current_user.name, new_export_path)
        new_export_path = re.sub('<UserNickName>', flame.users.current_user.nickname, new_export_path)
        new_export_path = re.sub('<ClipName>', str(clip.name)[1:-1], new_export_path)
        new_export_path = re.sub('<Resolution>', str(clip.width) + 'x' + str(clip.height), new_export_path)
        new_export_path = re.sub('<ClipHeight>', str(clip.height), new_export_path)
        new_export_path = re.sub('<ClipWidth>', str(clip.width), new_export_path)
        new_export_path = re.sub('<YYYY>', yyyy, new_export_path)
        new_export_path = re.sub('<YY>', yy, new_export_path)
        new_export_path = re.sub('<MM>', mm, new_export_path)
        new_export_path = re.sub('<DD>', dd, new_export_path)
        new_export_path = re.sub('<Hour>', hour, new_export_path)
        new_export_path = re.sub('<Minute>', minute, new_export_path)
        new_export_path = re.sub('<AMPM>', ampm_caps, new_export_path)
        new_export_path = re.sub('<ampm>', ampm, new_export_path)

        # print ('custom_export_path:', self.custom_export_path)
        print ('    Export path:', new_export_path)

        if not os.path.isdir(new_export_path):
            os.makedirs(new_export_path)

        return new_export_path

    def post_export(self, export_path):

        if self.reveal_in_finder:
            self.open_finder(export_path)

        if self.reveal_in_mediahub:
            self.open_mediahub(export_path)

        message_box('Export done.')

    def open_mediahub(self, export_path):
        import flame

        flame.go_to('MediaHub')
        flame.mediahub.files.set_path(export_path)
        print ('>>> Media Hub opened <<<\n')

    def open_finder(self, export_path):

        if platform.system() == 'Darwin':
            subprocess.Popen(['open', export_path])
        else:
            subprocess.Popen(['xdg-open', export_path])

#-------------------------------------#

def export_select_path(selection):

    export = ExportFrame(selection)
    return export.export_current_frame()

def export_marker_select_path(selection):

    export = ExportFrame(selection)
    return export.export_marker_frame()

def script_setup(selection):

    open_setup = ExportFrame(selection)
    return open_setup.setup()

#-------------------------------------#

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

    message = message.replace('<br>', '')
    message = message.replace('<center>', '')

    print ('>>> %s\n' % message)

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PyClip, flame.PySequence)):
            # if item.parent.type == "Schematic":
            return True
    return False

def scope_markers(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PySequence, flame.PyClip)):
            if not isinstance(item.parent, flame.PyReel):
                if item.markers:
                    return True
    return False

#-------------------------------------#

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Export...',
            'actions': [
                {
                    'name': 'Export Current Frame',
                    'isVisible': scope_clip,
                    'execute': export_select_path,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Export Marker Frames',
                    'isVisible': scope_markers,
                    'execute': export_marker_select_path,
                    'minimumVersion': '2021.2'
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
                    'name': 'Export Frame Setup',
                    'execute': script_setup,
                    'minimumVersion': '2021.2'
                }
            ]
        }
    ]


























