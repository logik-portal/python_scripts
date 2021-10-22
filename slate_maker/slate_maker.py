# -*- coding: utf-8 -*-
'''
Script Name: Slate Maker
Script Version: 4.3
Flame Version: 2020.2
Written by: Michael Vaglienty
Creation Date: 12.29.18
Update Date: 10.18.21

Custom Action Type: Media Panel

Description:

    Create slates from CSV file

    *** DOES NOT WORK WITH FLARE ***

    Right-click on clip to be used as slate background -> Slates... -> Slate Maker

        Create slates of different aspect ratios from single CSV file

    Right-click on selection of clips to be used as slate backgrounds -> Slates... -> Slate Maker - Multi Ratio

        For Multi Ratio to properly work you must do the following:

            Slate clip names need to end with the aspect ratio. Such as: slate_bg_16x9

            Text node templates should all end with the aspect ratio. Such as: slate_template_16x9

            Text node templates for all the different aspect ratios should all be in one folder. The file browser
            for Multi Ratio selects a folder, not a csv file. Any number of aspect ratio templates can be in this
            folder. Only templates that correspond to selected background clip aspect ratios will be used. Although
            there should only be one template per aspect ratio.

            The aspect ratio should be somewhere in each line of the csv for each slate to be created.

            Create Ratio Folders button: When enabled this will create separate folders in the newly created slates
            library for each aspect ratio. When disabled all slates will be put together in the slates library.

To install:

    Copy script into /opt/Autodesk/shared/python/slate_maker

Updates:

    v4.3 10.18.21

        If path is typed into csv or template fields the browser will now open to those paths

        Scrpit now saves last path selected in browser

        Script now creates test clip to check for Protect from Editing. Gives warning if Protect from Editing is on.

    v4.2 10.12.21

        Added ability to create slates of different ratios from one CSV file.

        A new menu has been created for this: Slates... -> Slate Maker - Multi Ratio

        Added progress bar

        Updated config to xml

    v4.0 05.23.21

        Updated to be compatible with Flame 2022/Python 3.7

    v3.7 02.12.21

        Fixed bug causing script not to load when CSV or ttg files have been moved or deleted - Thanks John!

    v3.6 01.10.21

        Added ability to use tokens to name slate clip
        Added button to convert spaces to underscores in slate clip name

    v3.5 10.13.20

        More UI Updates

    v3.4 08.26.20

        Updated UI
        Added drop down menu to select CSV column for slate clip naming

    v3.3 04.03.20

        Fixed UI issues in Linux
        Main Window opens centered in linux

    v2.6 09.02.19

        Fixed bug - Script failed to convert multiple occurrences of token in slate template
        Fixed bug - Script failed when token not present in slate template for column in csv file
'''

from __future__ import print_function
from functools import partial
from random import randint
import os, re, ast, shutil, datetime
import xml.etree.ElementTree as ET
from PySide2 import QtWidgets, QtCore

VERSION = 'v4.3'

SCRIPT_PATH = '/opt/Autodesk/shared/python/slate_maker'

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
        self.setMinimumSize(125, 28)
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
        self.setMinimumSize(QtCore.QSize(150, 28))
        self.setMaximumSize(QtCore.QSize(150, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(do_when_pressed)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

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
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
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
        self.setMaximumWidth(150)
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

#-------------------------------------#

class CreateSlates(object):

    def __init__(self, selection):

        print ('''
     _____ _       _         __  __       _
    / ____| |     | |       |  \/  |     | |
   | (___ | | __ _| |_ ___  | \  / | __ _| | _____ _ __
    \___ \| |/ _` | __/ _ \ | |\/| |/ _` | |/ / _ \ '__|
    ____) | | (_| | ||  __/ | |  | | (_| |   <  __/ |
   |_____/|_|\__,_|\__\___| |_|  |_|\__,_|_|\_\___|_|
        \n''')

        print ('>' * 20, 'slate maker %s' % VERSION, '<' * 20, '\n')

        self.selection = selection

        # Set paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')
        self.temp_save_path = os.path.join(SCRIPT_PATH, 'temp_slate_folder')

        # Load config file

        self.config()

        # Create temp folder for text node files

        try:
            os.makedirs(self.temp_save_path)
        except:
            shutil.rmtree(self.temp_save_path)
            os.makedirs(self.temp_save_path)

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Slate Maker Settings

            for setting in root.iter('slate_maker_settings'):

                self.csv_file_path = setting.find('csv_file_path').text
                self.template_file_path = setting.find('template_file_path').text
                self.date_format = setting.find('date_format').text
                self.slate_clip_name = setting.find('slate_clip_name').text
                self.use_underscores = ast.literal_eval(setting.find('spaces_to_underscores').text)

                if not self.csv_file_path:
                    self.csv_file_path = ''
                if not self.template_file_path:
                    self.template_file_path = ''

            # Get Slate Maker Multi Ratio Settings

            for multi_ratio_setting in root.iter('slate_maker_multi_ratio_settings'):
                self.multi_ratio_csv_file_path = multi_ratio_setting.find('multi_ratio_csv_file_path').text
                self.multi_ratio_template_folder_path = multi_ratio_setting.find('multi_ratio_template_folder_path').text
                self.multi_ratio_date_format = multi_ratio_setting.find('multi_ratio_date_format').text
                self.multi_ratio_slate_clip_name = multi_ratio_setting.find('multi_ratio_slate_clip_name').text
                self.multi_ratio_use_underscores = ast.literal_eval(multi_ratio_setting.find('multi_ratio_spaces_to_underscores').text)
                self.multi_ratio_create_ratio_folders = ast.literal_eval(multi_ratio_setting.find('multi_ratio_create_ratio_folders').text)

                if not self.multi_ratio_csv_file_path:
                    self.multi_ratio_csv_file_path = ''
                if not self.multi_ratio_template_folder_path:
                    self.multi_ratio_template_folder_path = ''

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
    <slate_maker_settings>
        <csv_file_path></csv_file_path>
        <template_file_path></template_file_path>
        <date_format>mm/dd/yy</date_format>
        <slate_clip_name>&lt;ISCI&gt;</slate_clip_name>
        <spaces_to_underscores>True</spaces_to_underscores>
    </slate_maker_settings>
    <slate_maker_multi_ratio_settings>
        <multi_ratio_csv_file_path></multi_ratio_csv_file_path>
        <multi_ratio_template_folder_path></multi_ratio_template_folder_path>
        <multi_ratio_date_format>mm/dd/yy</multi_ratio_date_format>
        <multi_ratio_slate_clip_name>&lt;ISCI&gt;</multi_ratio_slate_clip_name>
        <multi_ratio_spaces_to_underscores>True</multi_ratio_spaces_to_underscores>
        <multi_ratio_create_ratio_folders>True</multi_ratio_create_ratio_folders>
    </slate_maker_multi_ratio_settings>
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

    def slate_maker(self):

        def save_config():

            if not self.csv_path_entry.text():
                message_box('Enter Path to CSV File')
                return False

            elif not os.path.isfile(self.csv_path_entry.text()):
                message_box('CSV file does not exist')
                return False

            elif not self.template_path_entry.text():

                message_box('Enter Path to Text Node Template')
                return False

            elif not os.path.isfile(self.template_path_entry.text()):
                message_box('Text node template file does not exist')
                return False

            elif not self.slate_clip_name_entry.text():
                message_box('Enter tokens for slate clip naming')
                return False

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            csv_file_path = root.find('.//csv_file_path')
            csv_file_path.text = self.csv_path_entry.text()
            template_file_path = root.find('.//template_file_path')
            template_file_path.text = self.template_path_entry.text()
            date_format = root.find('.//date_format')
            date_format.text = self.date_push_btn.text()
            slate_clip_name = root.find('.//slate_clip_name')
            slate_clip_name.text = self.slate_clip_name_entry.text()
            spaces_to_underscores = root.find('.//spaces_to_underscores')
            spaces_to_underscores.text = str(self.convert_spaces_btn.isChecked())

            xml_tree.write(self.config_xml)

            print ('>>> config saved <<<\n')

            self.multi_ratio = False

            self.template_path = self.template_path_entry.text()

            # self.window.close()

            self.create_slates()

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(1000, 250))
        self.window.setMaximumSize(QtCore.QSize(1000, 250))
        self.window.setWindowTitle('Slate Maker %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #313131')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.csv_label = FlameLabel('CSV', 'normal', self.window)
        self.template_label = FlameLabel('Template', 'normal', self.window)
        self.date_format_label = FlameLabel('Date Format', 'normal', self.window)
        self.slate_clip_name_label = FlameLabel('Slate Clip Name', 'normal', self.window)

        # Entry Boxes

        self.csv_path_entry = FlameLineEdit(self.csv_file_path, self.window)
        self.template_path_entry = FlameLineEdit(self.template_file_path, self.window)
        self.slate_clip_name_entry = FlameLineEdit(self.slate_clip_name, self.window)

        # Date Pushbutton Menu

        date_formats = ['yy/mm/dd', 'yyyy/mm/dd', 'mm/dd/yy', 'mm/dd/yyyy', 'dd/mm/yy', 'dd/mm/yyyy']
        self.date_push_btn = FlamePushButtonMenu(self.date_format, date_formats, self.window)

        # Clip Name Pushbutton Menu

        self.clip_name_menu = QtWidgets.QMenu(self.window)
        self.clip_name_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                          'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.clip_name_push_btn = QtWidgets.QPushButton('Add Token', self.window)
        self.clip_name_push_btn.setMenu(self.clip_name_menu)
        self.clip_name_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.clip_name_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                              'QPushButton:disabled {color: #6a6a6a}')

        # Spaces to Underscore Pushbutton

        self.convert_spaces_btn = FlamePushButton(' Convert Spaces', self.use_underscores, self.window)
        self.convert_spaces_btn.setToolTip('Enable to convert spaces in clip name to underscores')

        # Buttons

        self.csv_browse_btn = FlameButton('Browse', self.csv_browse, self.window)
        self.template_browse_btn = FlameButton('Browse', self.template_browse, self.window)
        self.cancel_btn = FlameButton('Cancel', self.window.close, self.window)
        self.create_slates_btn = FlameButton('Create Slates', save_config, self.window)

        # Get clip name tokens from csv

        if os.path.isfile(self.csv_path_entry.text()):
            self.get_csv_tokens()
            self.column_names = self.csv_token_line
            self.create_clip_name_menu()

        #------------------------------------#

        # Window Layout

        self.grid = QtWidgets.QGridLayout()
        self.grid.setVerticalSpacing(5)
        self.grid.setHorizontalSpacing(5)
        self.grid.setMargin(20)

        self.grid.setColumnMinimumWidth(3, 150)

        self.grid.addWidget(self.csv_label, 1, 0)
        self.grid.addWidget(self.csv_path_entry, 1, 1, 1, 3)
        self.grid.addWidget(self.csv_browse_btn, 1, 4)

        self.grid.addWidget(self.template_label, 2, 0)
        self.grid.addWidget(self.template_path_entry, 2, 1, 1, 3)
        self.grid.addWidget(self.template_browse_btn, 2, 4)

        self.grid.addWidget(self.slate_clip_name_label, 3, 0)
        self.grid.addWidget(self.slate_clip_name_entry, 3, 1)
        self.grid.addWidget(self.clip_name_push_btn, 3, 2)
        self.grid.addWidget(self.convert_spaces_btn, 3, 3)

        self.grid.addWidget(self.date_format_label, 4, 0)
        self.grid.addWidget(self.date_push_btn, 4, 1)

        self.grid.addWidget(self.create_slates_btn, 5, 4)
        self.grid.addWidget(self.cancel_btn, 6, 4)

        self.window.setLayout(self.grid)

        # ----------------------------------------------

        self.window.show()

        return self.window

    def slate_maker_multi_ratio(self):

        def save_config():

            if not self.csv_path_entry.text():
                message_box('Enter Path to CSV File')
                return False

            elif not os.path.isfile(self.csv_path_entry.text()):
                message_box('CSV file does not exist')
                return False

            elif not self.template_path_entry.text():
                message_box('Enter Path to Text Node Templates')
                return False

            elif not os.path.isdir(self.template_path_entry.text()):
                message_box('Text node template folder does not exist')
                return False

            elif not self.slate_clip_name_entry.text():
                message_box('Enter tokens for slate clip naming')
                return False

            # Check for missing templates for selected slate backgrounds

            self.slate_bgs = [str(clip.name)[1:-1].rsplit('_', 1)[1] for clip in self.selection]

            self.missing_templates = []

            for bg in self.slate_bgs:
                found = False
                for f in os.listdir(self.template_path_entry.text()):
                    if bg.lower() in f.lower():
                        found = True
                if not found:
                    self.missing_templates.append(bg)

            if self.missing_templates:
                missing = ', '.join([str(elem) for elem in self.missing_templates])
                return message_box('Text node templates not found for: %s' % missing)
            else:
                print ('>>> templates found for all slate backgrounds <<<\n')

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            multi_ratio_csv_file_path = root.find('.//multi_ratio_csv_file_path')
            multi_ratio_csv_file_path.text = self.csv_path_entry.text()
            multi_ratio_template_folder_path = root.find('.//multi_ratio_template_folder_path')
            multi_ratio_template_folder_path.text = self.template_path_entry.text()
            multi_ratio_date_format = root.find('.//multi_ratio_date_format')
            multi_ratio_date_format.text = self.date_push_btn.text()
            multi_ratio_slate_clip_name = root.find('.//multi_ratio_slate_clip_name')
            multi_ratio_slate_clip_name.text = self.slate_clip_name_entry.text()
            multi_ratio_spaces_to_underscores = root.find('.//multi_ratio_spaces_to_underscores')
            multi_ratio_spaces_to_underscores.text = str(self.convert_spaces_btn.isChecked())
            multi_ratio_create_ratio_folders = root.find('.//multi_ratio_create_ratio_folders')
            multi_ratio_create_ratio_folders.text = str(self.ratio_folders_btn.isChecked())

            xml_tree.write(self.config_xml)

            print ('>>> config saved <<<\n')

            self.multi_ratio = True

            self.create_slates()

        def get_slate_ratios():

            # Check selected slate backgrounds for proper name. Must end with ratio. Such as: slate_bg_16x9

            self.slate_bgs = [str(clip.name)[1:-1].rsplit('_', 1)[1] for clip in self.selection if 'x' in str(clip.name)[1:-1].rsplit('_', 1)[1].lower()]
            self.ratios = ', '.join([str(elem).lower() for elem in self.slate_bgs])

        get_slate_ratios()

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(1000, 250))
        self.window.setMaximumSize(QtCore.QSize(1000, 250))
        self.window.setWindowTitle('Slate Maker Multi Ratio %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #313131')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.selected_slate_ratio_label01 = FlameLabel('Selected Slate Ratios', 'normal', self.window)
        self.selected_slate_ratio_label02 = FlameLabel(self.ratios, 'outline', self.window)

        self.csv_label = FlameLabel('CSV', 'normal', self.window)
        self.template_label = FlameLabel('Template Folder', 'normal', self.window)
        self.date_format_label = FlameLabel('Date Format', 'normal', self.window)
        self.slate_clip_name_label = FlameLabel('Slate Clip Name', 'normal', self.window)

        # Entry Boxes

        self.csv_path_entry = FlameLineEdit(self.multi_ratio_csv_file_path, self.window)
        self.template_path_entry = FlameLineEdit(self.multi_ratio_template_folder_path, self.window)
        self.slate_clip_name_entry = FlameLineEdit(self.multi_ratio_slate_clip_name, self.window)

        # Date Pushbutton Menu

        date_formats = ['yy/mm/dd', 'yyyy/mm/dd', 'mm/dd/yy', 'mm/dd/yyyy', 'dd/mm/yy', 'dd/mm/yyyy']
        self.date_push_btn = FlamePushButtonMenu(self.multi_ratio_date_format, date_formats, self.window)

        # Clip Name Pushbutton Menu

        self.clip_name_menu = QtWidgets.QMenu(self.window)
        self.clip_name_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                          'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.clip_name_push_btn = QtWidgets.QPushButton('Add Token', self.window)
        self.clip_name_push_btn.setMenu(self.clip_name_menu)
        self.clip_name_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.clip_name_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                              'QPushButton:disabled {color: #6a6a6a}')

        # Spaces to Underscore Pushbutton

        self.convert_spaces_btn = FlamePushButton(' Convert Spaces', self.multi_ratio_use_underscores, self.window)
        self.convert_spaces_btn.setToolTip('Enable to convert spaces in clip name to underscores')

        self.ratio_folders_btn = FlamePushButton(' Create Ratio Folders', self.multi_ratio_create_ratio_folders, self.window)
        self.ratio_folders_btn.setToolTip('Create separate folders for each ratio')

        # Buttons

        self.csv_browse_btn = FlameButton('Browse', self.csv_browse, self.window)
        self.template_browse_btn = FlameButton('Browse', self.template_folder_browse, self.window)
        self.cancel_btn = FlameButton('Cancel', self.window.close, self.window)
        self.create_slates_btn = FlameButton('Create Slates', save_config, self.window)

        # Get clip name tokens from csv

        if os.path.isfile(self.csv_path_entry.text()):
            self.get_csv_tokens()
            self.column_names = self.csv_token_line
            self.create_clip_name_menu()

        #------------------------------------#

        # Window Layout

        self.grid = QtWidgets.QGridLayout()
        self.grid.setVerticalSpacing(5)
        self.grid.setHorizontalSpacing(5)

        self.grid.setColumnMinimumWidth(3, 150)

        self.grid.setRowMinimumHeight(0, 33)

        self.grid.addWidget(self.selected_slate_ratio_label01, 0, 0)
        self.grid.addWidget(self.selected_slate_ratio_label02, 0, 1, 1, 2)
        self.grid.addWidget(self.ratio_folders_btn, 0, 3)

        self.grid.addWidget(self.csv_label, 1, 0)
        self.grid.addWidget(self.csv_path_entry, 1, 1, 1, 3)
        self.grid.addWidget(self.csv_browse_btn, 1, 4)

        self.grid.addWidget(self.template_label, 2, 0)
        self.grid.addWidget(self.template_path_entry, 2, 1, 1, 3)
        self.grid.addWidget(self.template_browse_btn, 2, 4)

        self.grid.addWidget(self.date_format_label, 4, 0)
        self.grid.addWidget(self.date_push_btn, 4, 1)

        self.grid.addWidget(self.slate_clip_name_label, 3, 0)
        self.grid.addWidget(self.slate_clip_name_entry, 3, 1, 1, 1)
        self.grid.addWidget(self.clip_name_push_btn, 3, 2)
        self.grid.addWidget(self.convert_spaces_btn, 3, 3)

        self.grid.addWidget(self.create_slates_btn, 5, 4)
        self.grid.addWidget(self.cancel_btn, 6, 4)

        self.window.setLayout(self.grid)

        # ----------------------------------------------

        self.window.show()

        return self.window

    # ----------------------- #

    def save_path(self, path_type, path):

        # Save settings to config file

        xml_tree = ET.parse(self.config_xml)
        root = xml_tree.getroot()

        path_to_save = root.find('.//%s' % path_type)
        path_to_save.text = path

        xml_tree.write(self.config_xml)

        print ('>>> path saved <<<\n')

    def csv_browse(self):

        if os.path.isfile(self.csv_path_entry.text()):
            path = self.csv_path_entry.text().rsplit('/', 1)[0]
        else:
            path = self.csv_path_entry.text()

        csv_file_path = QtWidgets.QFileDialog.getOpenFileName(self.window, "Select Script or Folder", path, "CSV Files (*.csv)")[0]

        if csv_file_path:
            self.save_path('csv_file_path', csv_file_path)
            self.csv_path_entry.setText(csv_file_path)
            self.get_csv_tokens()
            self.column_names = self.csv_token_line
            self.create_clip_name_menu()

    def template_browse(self):

        if os.path.isfile(self.template_path_entry.text()):
            path = self.template_path_entry.text().rsplit('/', 1)[0]
        else:
            path = self.template_path_entry.text()
        print ('PATH:', path)
        template_file_path = QtWidgets.QFileDialog.getOpenFileName(self.window, "Select Script or Folder", path, "Text Node Setup Files (*.ttg)")[0]

        if template_file_path:
            self.save_path('template_file_path', template_file_path)
            self.template_path_entry.setText(template_file_path)

    def template_folder_browse(self):

        folder_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.window, 'Select Directory', self.template_path_entry.text(), QtWidgets.QFileDialog.ShowDirsOnly))

        if folder_path:
            self.save_path('multi_ratio_template_folder_path', folder_path)
            self.template_path_entry.setText(folder_path)

    # ----------------------- #

    def get_csv_tokens(self):

        # Get list of items in first line

        with open(self.csv_path_entry.text(), 'r') as csv_file:
            self.csv_token_line = csv_file.readline().strip()
        self.csv_token_line = self.csv_token_line.split(',')

    def create_clip_name_menu(self):

        # Create clip name menu from first line of csv file

        def create_menu(name):
            self.slate_clip_name_entry.insert('<' + name + '>')

        self.clip_name_menu.clear()

        # Create clip name menu from column name list

        for name in self.column_names:
            self.clip_name_menu.addAction(name, partial(create_menu, name))

    def create_slates(self):
        import flame

        def get_date(date_format):

            now = datetime.datetime.now()
            date_format = date_format.replace('yyyy', '20%y')
            date_format = date_format.replace('yy', '%y')
            date_format = date_format.replace('mm', '%m')
            date_format = date_format.replace('dd', '%d')
            current_date = now.strftime(date_format)
            return current_date

        def create_temp_text_file():

            # Get random number

            text_node_num = randint(1, 10000)

            temp_text_file = self.temp_save_path + '/Slate_Template_' + str(text_node_num) + '.ttg'

            shutil.copy(self.template_path, temp_text_file)

            return temp_text_file

        def ascii_convert(text_to_convert):

            # Convert fancy quotes to regular quotes

            text_to_convert = text_to_convert.replace('“', '"').replace('”', '"')

            # Create list for ascii codes

            ascii_list = []

            # Convert characters to ascii code then add to list

            for char in text_to_convert:
                ascii_num = ord(char)
                if ascii_num != 194:
                    ascii_list.append(ascii_num)

            ascii_code = ' '.join(str(a) for a in ascii_list)

            return ascii_code

        def modify_setup_line(token, token_value, temp_text_file):

            # Open text node file and get token and character length line number

            with open(temp_text_file, 'r') as text_node:
                for num, line in enumerate(text_node, 1):
                    if token in line:
                        token_line_num = num - 1
                        token_char_len_line_num = num - 2

                        # Replace token with token value in line

                        token_line_split = line.rsplit(token, 1)[0]
                        new_token_line = token_line_split + token_value + '\n'
                        new_token_chars = new_token_line.rsplit('Text ', 1)[1]
                        new_token_char_len_line = 'TextLength ' + str(len(new_token_chars.split(' '))) + '\n'

                        # Edit text node with new token and character lenth lines

                        edit_text_node = open(temp_text_file, 'r')
                        contents = edit_text_node.readlines()
                        edit_text_node.close()

                        contents[token_line_num] = '%s' % new_token_line
                        contents[token_char_len_line_num] = '%s' % new_token_char_len_line

                        edit_text_node = open(temp_text_file, 'w')
                        contents = ''.join(contents)
                        edit_text_node.write(contents)
                        edit_text_node.close()

        def create_text_node(line):

            def rename_text_file(clip_name, temp_text_file, temp_save_path):

                def name_clip(clip_num, num):

                    new_text_file = os.path.join(temp_save_path, clip_name) + clip_num + '.ttg'

                    if os.path.isfile(new_text_file):
                        if len(str(num)) == 1:
                            clip_num = '_0' + str(num)
                        else:
                            clip_num = '_' + str(num)
                        num += 1
                        return name_clip(clip_num, num)

                    return new_text_file

                clip_num = ''
                num = 1
                if clip_name != '':
                    clip_name = clip_name.replace('/', '')

                    self.text_node_path = name_clip(clip_num, num)
                    # print ('text_node_path:', self.text_node_path, '\n')
                    shutil.move(temp_text_file, self.text_node_path)

                    return

            clip_name = self.slate_clip_name_entry.text()

            temp_text_file = create_temp_text_file()

            line_list = line.split(',')

            # Merge column list with line list into dictionary

            line_dict = dict(zip(token_list, line_list))

            # for item in line_dict.iteritems():

            for item in iter(line_dict.items()):

                # Try to convert token in CSV
                # If token not in template, pass

                try:
                    token = item[0]
                    token_value = item[1]

                    if token == '<CURRENT_DATE>':
                        token_value = get_date(self.date_push_btn.text())

                    # Convert token to ascii code

                    token = ascii_convert(token)

                    # Convert token value to ascii code

                    token_value = ascii_convert(token_value)

                    # Update text node setup file

                    modify_setup_line(token, token_value, temp_text_file)

                except:
                    pass

            # Get clip name pushbutton text to name clips

            for item in iter(line_dict.items()):

                token = item[0]
                token_value = item[1]

                if token in clip_name:
                    clip_name = clip_name.replace(token, token_value)

                if '<CURRENT_DATE>' in clip_name:
                    date = get_date(self.date_push_btn.text())
                    clip_name = clip_name.replace('<CURRENT_DATE>', date)

            # Remove bad characters from clip name

            clip_name = re.sub(r'[\\/*?:"<>|]', ' ', clip_name)

            # If Use Underscores in checked, replace spaces with underscores

            if self.convert_spaces_btn.isChecked():
                clip_name = re.sub(r' ', '_', clip_name)

            # Rename temp text file selected clip name option

            rename_text_file(clip_name, temp_text_file, self.temp_save_path)

        def create_slate_clip(slate_background):
            import flame

            # Copy slate background to slate dest - either a slate library or ratio folders within the slate library

            new_bg_clip = flame.media_panel.copy(slate_background, self.slate_dest)

            # Rename clip to match name of text node

            for clip in new_bg_clip:
                clip.name = str(self.text_node_path.rsplit('/', 1)[1])[:-4]
                print ('   ', str(clip.name)[1:-1])

            # Add text effect and load text setup

            seg = clip.versions[0].tracks[0].segments[0]
            seg_name = str(seg.name)[1:-1]
            text_fx = seg.create_effect('Text')
            text_file_path = os.path.join(self.temp_save_path, seg_name) + '.ttg'
            text_fx.load_setup(text_file_path)

        # Create slate library and set as slate dest

        self.slate_library = flame.project.current_project.current_workspace.create_library('-Slates-')
        self.slate_library.expanded = True
        self.slate_dest = self.slate_library

        # Read token like from csv

        self.get_csv_tokens()

        # Add < and > to column names

        token_list = ['<' + item.upper() + '>' for item in self.csv_token_line]
        print ('token_list:', token_list, '\n')

        # Build list of lines from csv file - skip first row which should be token row

        with open(self.csv_path_entry.text(), 'r') as csv_file:
            csv_text = csv_file.read().splitlines()[1:]

        # --------------------

        # Create slates

        missing_slate_bgs = []

        if self.multi_ratio:
            for bg in self.slate_bgs:

                # Remove slate background from list if not found is csv file

                if not re.search(bg, str(csv_text), re.I):
                    missing_slate_bgs.append(bg)
                    self.slate_bgs.remove(bg)

            if self.slate_bgs:

                # Get number of slates to be created then load progress bar window

                self.num_of_slates = 0
                for bg in self.slate_bgs:
                    for line in csv_text:
                        if bg.lower() in line.lower():
                            self.num_of_slates += 1

                slates_created = 0
                self.progress_bar_window()

                # Iterate through selected slate backgrounds

                for bg in self.slate_bgs:
                    print ('\n>>> Creating %s Slates...\n' % bg)

                    # If Create Ratio Folders button is enabled create folder for ratio in slate library then set folder as slate dest

                    if self.ratio_folders_btn.isChecked():
                        ratio_folder = self.slate_library.create_folder(bg.lower())
                        self.slate_dest = ratio_folder

                    # Find csv lines that matches background ratio

                    for line in csv_text:
                        if bg.lower() in line.lower():

                            # Get slate background clip object to use as background

                            for clip in self.selection:
                                if bg in str(clip.name):
                                    slate_background = clip
                                    # print ('slate_background:', str(slate_background.name)[1:-1])

                            # Find text node template that matches background ratio

                            for (root, dirs, files) in os.walk(self.template_path_entry.text()):
                                for f in files:
                                    if bg.lower() in f.lower() and f.endswith('.ttg'):
                                        self.template_path = os.path.join(root, f)

                            create_text_node(line)
                            create_slate_clip(slate_background)

                            # Update progress window

                            slates_created = self.update_progress_bar('Creating Slate', self.num_of_slates, slates_created)

        else:
            # Create text nodes for single slate bg/template

            # Get number of slates to be created then load progress bar window

            self.num_of_slates = len(csv_text)
            slates_created = 0
            self.progress_bar_window()

            # Get slate background clip from selection

            slate_background = self.selection[0]
            self.template_path = self.template_path_entry.text()

            print ('\n>>> Creating slates...\n')

            # Create slates

            for line in csv_text:

                create_text_node(line)
                create_slate_clip(slate_background)

                # Update progress window

                slates_created = self.update_progress_bar('Creating Slate', self.num_of_slates, slates_created)

        if missing_slate_bgs:
            missing = ', '.join(missing_slate_bgs)
            message_box('No entries in csv for selected slate backgrounds: %s' % missing)

        # Delete temp folder

        shutil.rmtree(self.temp_save_path)

        print ('\ndone.\n')

    # ----------------------- #

    def update_progress_bar(self, task, num_to_do, num_done):
        num_done += 1
        self.progress_bar.setValue(num_done)
        self.creating_slates_label.setText('%s %s of %s' % (task, num_done, num_to_do))
        if num_done == num_to_do:
            self.progress_done_btn.setEnabled(True)
        return num_done

    def progress_bar_window(self):

        def close_windows():

            self.window.close()
            self.progress_window.close()

        self.progress_window = QtWidgets.QWidget()
        self.progress_window.setFixedSize(400, 160)
        self.progress_window.setWindowTitle('Slate Maker %s' % VERSION)
        self.progress_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.progress_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.progress_window.setStyleSheet('background-color: #313131')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.progress_window.move((resolution.width() / 2) - (self.progress_window.frameSize().width() / 2),
                                  (resolution.height() / 2) - (self.progress_window.frameSize().height() / 2))

        # Label

        self.creating_slates_label = FlameLabel('', 'normal', self.progress_window)
        self.creating_slates_label.setAlignment(QtCore.Qt.AlignCenter)

        # Buttons

        self.progress_done_btn = FlameButton('Done', close_windows, self.progress_window)
        self.progress_done_btn.setEnabled(False)
        self.progress_done_btn.setMinimumWidth(125)

        # Progress bar

        self.progress_bar = QtWidgets.QProgressBar(self.progress_window)
        self.progress_bar.setMaximum(self.num_of_slates)
        self.progress_bar.setStyleSheet('QProgressBar {color: #9a9a9a; font: 14px "Discreet"; text-align: center}'
                                        'QProgressBar:chunk {background-color: #373e47; border-top: 1px solid #242424; border-bottom: 1px solid #474747; border-left: 1px solid #242424; border-right: 1px solid #474747}')

        #------------------------------------#

        # Window Layout

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(self.creating_slates_label)

        self.grid = QtWidgets.QGridLayout()
        self.grid.setVerticalSpacing(5)
        self.grid.setHorizontalSpacing(5)

        self.grid.addWidget(self.progress_bar, 1, 0, 1, 3)
        self.grid.addWidget(self.progress_done_btn, 2, 1)

        self.grid.setColumnMinimumWidth(2, 125)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addLayout(self.grid)

        self.progress_window.setLayout(self.vbox)

        self.progress_window.show()

def message_box(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setMinimumSize(400, 100)
    msg_box.setText(message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14pt "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14pt "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>', '<center>']

    for code in code_list:
        message = message.replace(code, '')

    print ('>>> %s <<<\n' % message)

#-------------------------------------#

def text_fx_check(selection):

    # Make sure selected clips do not already contain timeline text fx

    for clip in selection:
        for version in clip.versions:
            for track in version.tracks:
                for seg in track.segments:
                    for fx in seg.effects:
                        if fx.type == 'Text':
                            message_box('<center>Slate background clip cannot have a timeline text fx applied. Remove and try again.')
                            return True
    return False

def protect_from_editing_check(selection):
    import flame

    # Check for protect from editing by duplicating selected clip

    try:
        for clip in selection:
            new_clip = flame.duplicate(clip)
            new_clip.name = 'protect_from_editing_test_clip'
            seg = new_clip.versions[0].tracks[0].segments[0]
            seg_name = str(seg.name)[1:-1]
            text_fx = seg.create_effect('Text')
            break
        flame.delete(new_clip)
        return False
    except:
        flame.delete(new_clip)
        message_box('<center>Turn off Protect from Editing:<br>Flame Preferences -> General.')
        return True

def slate_maker(selection):
    '''
    Create slates from csv
    '''

    text_fx = text_fx_check(selection)
    protect_from_editing = protect_from_editing_check(selection)

    if not text_fx and not protect_from_editing:
        script = CreateSlates(selection)
        script.slate_maker()

def slate_maker_multi_ratio(selection):
    '''
    Create slates of multiple ratios from one csv
    '''

    text_fx = text_fx_check(selection)
    protect_from_editing = protect_from_editing_check(selection)

    if not text_fx and not protect_from_editing:
        script = CreateSlates(selection)

        # Make sure all selected clips have a ratio at the end of their name

        try:
            slate_bgs = [str(clip.name)[1:-1].rsplit('_', 1)[1] for clip in selection if 'x' in str(clip.name)[1:-1].rsplit('_', 1)[1].lower()]
        except:
            return message_box('<center>All selected slate backgrounds must have ratio at end of file name. Such as: slate_bg_16x9')
        if not slate_bgs:
            return message_box('<center>All selected slate backgrounds must have ratio at end of file name. Such as: slate_bg_16x9')

        script.slate_maker_multi_ratio()

#-------------------------------------#

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

#-------------------------------------#

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Slates...',
            'actions': [
                {
                    'name': 'Slate Maker',
                    'isVisible': scope_clip,
                    'execute': slate_maker,
                    'minimumVersion': '2020.2'
                },
                {
                    'name': 'Slate Maker - Multi Ratio',
                    'isVisible': scope_clip,
                    'execute': slate_maker_multi_ratio,
                    'minimumVersion': '2020.2'
                }
            ]
        }
    ]
