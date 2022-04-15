# -*- coding: utf-8 -*-
'''
Script Name: Slate Maker
Script Version: 4.6
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 12.29.18
Update Date: 03.18.22

Custom Action Type: Media Panel

Description:

    Create slates from CSV file

    *** DOES NOT WORK WITH FLARE ***

    Detailed instructions to use this script can be found on pyflame.com

    Example CSV and Text Node Template files can be found in /opt/autodesk/shared/python/slate_maker/example_files

Menus:

    Right-click on clip to be used as slate background -> Slates... -> Slate Maker

    Right-click on selection of clips to be used as slate backgrounds -> Slates... -> Slate Maker - Multi Ratio

To install:

    Copy script into /opt/Autodesk/shared/python/slate_maker

Updates:

    v4.6 03.18.22

        Moved UI widgets to external file

    v4.5 03.06.22

        Updated UI for Flame 2023

    v4.4 11.16.21

        Improved parsing of csv file

        If current tab is MediaHub, switch to Timeline tab. Slates cannot be created in MediaHub tab.

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

from functools import partial
from random import randint
import os, re, ast, csv, shutil, datetime
import xml.etree.ElementTree as ET
from PySide2 import QtWidgets, QtCore
from flame_widgets_slate_maker import FlameLabel, FlameLineEdit, FlameButton, FlamePushButton, FlamePushButtonMenu, FlameMessageWindow, FlameWindow, FlameProgressWindow

VERSION = 'v4.6'

SCRIPT_PATH = '/opt/Autodesk/shared/python/slate_maker'

#-------------------------------------#

class CreateSlates(object):

    def __init__(self, selection):
        import flame

        print ('''
     _____ _       _         __  __       _
    / ____| |     | |       |  \/  |     | |
   | (___ | | __ _| |_ ___  | \  / | __ _| | _____ _ __
    \___ \| |/ _` | __/ _ \ | |\/| |/ _` | |/ / _ \ '__|
    ____) | | (_| | ||  __/ | |  | | (_| |   <  __/ |
   |_____/|_|\__,_|\__\___| |_|  |_|\__,_|_|\_\___|_|
        \n''')

        print ('>' * 20, f'slate maker {VERSION}', '<' * 20, '\n')

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

        # Switch tab to Timeline if current tab is MediaHub
        # Slates cannot be created in the MediaHub tab

        if flame.get_current_tab() == 'MediaHub':
            flame.go_to('Timeline')

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
                FlameMessageWindow('Error', 'error', 'Enter Path to CSV File')
                return False

            elif not os.path.isfile(self.csv_path_entry.text()):
                FlameMessageWindow('Error', 'error', 'CSV file does not exist')
                return False

            elif not self.template_path_entry.text():
                FlameMessageWindow('Error', 'error', 'Enter Path to Text Node Template')
                return False

            elif not os.path.isfile(self.template_path_entry.text()):
                FlameMessageWindow('Error', 'error', 'Text node template file does not exist')
                return False

            elif not self.slate_clip_name_entry.text():
                FlameMessageWindow('Error', 'error', 'Enter tokens for slate clip naming')
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

            print ('--> config saved\n')

            self.multi_ratio = False

            self.template_path = self.template_path_entry.text()

            self.create_slates()

        grid = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'Slate Maker <small>{VERSION}', grid, 1000, 300)

        # Labels

        self.csv_label = FlameLabel('CSV', 'normal')
        self.template_label = FlameLabel('Template', 'normal')
        self.date_format_label = FlameLabel('Date Format', 'normal')
        self.slate_clip_name_label = FlameLabel('Slate Clip Name', 'normal')

        # Entry Boxes

        self.csv_path_entry = FlameLineEdit(self.csv_file_path)
        self.template_path_entry = FlameLineEdit(self.template_file_path)
        self.slate_clip_name_entry = FlameLineEdit(self.slate_clip_name)

        # Date Pushbutton Menu

        date_formats = ['yy/mm/dd', 'yyyy/mm/dd', 'mm/dd/yy', 'mm/dd/yyyy', 'dd/mm/yy', 'dd/mm/yyyy']
        self.date_push_btn = FlamePushButtonMenu(self.date_format, date_formats, max_menu_width=150)

        # Clip Name Pushbutton Menu

        self.clip_name_menu = QtWidgets.QMenu()
        self.clip_name_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_menu.setStyleSheet('QMenu {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                                          'QMenu::item:selected {color: rgb(217, 217, 217); background-color: rgb(58, 69, 81)}')

        self.clip_name_push_btn = QtWidgets.QPushButton('Add Token')
        self.clip_name_push_btn.setMenu(self.clip_name_menu)
        self.clip_name_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.clip_name_push_btn.setStyleSheet('QPushButton {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                                              'QPushButton:disabled {color: rgb(116, 116, 116); background-color: rgb(45, 55, 68); border: none}'
                                              'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                                              'QPushButton::menu-indicator {image: none}')

        #self.clip_name_push_btn = FlamePushButtonMenu(self.clip_name_menu, [])

        # Spaces to Underscore Pushbutton

        self.convert_spaces_btn = FlamePushButton('Convert Spaces', self.use_underscores)
        self.convert_spaces_btn.setToolTip('Enable to convert spaces in clip name to underscores')

        # Buttons

        self.csv_browse_btn = FlameButton('Browse', self.csv_browse)
        self.template_browse_btn = FlameButton('Browse', self.template_browse)
        self.cancel_btn = FlameButton('Cancel', self.window.close)
        self.create_slates_btn = FlameButton('Create Slates', save_config)

        # Get clip name tokens from csv

        try:
            self.get_csv_tokens()
        except:
            pass

        #------------------------------------#

        # Window Layout

        grid.setVerticalSpacing(5)
        grid.setHorizontalSpacing(5)
        grid.setMargin(20)

        grid.setColumnMinimumWidth(3, 150)

        grid.addWidget(self.csv_label, 1, 0)
        grid.addWidget(self.csv_path_entry, 1, 1, 1, 3)
        grid.addWidget(self.csv_browse_btn, 1, 4)

        grid.addWidget(self.template_label, 2, 0)
        grid.addWidget(self.template_path_entry, 2, 1, 1, 3)
        grid.addWidget(self.template_browse_btn, 2, 4)

        grid.addWidget(self.slate_clip_name_label, 3, 0)
        grid.addWidget(self.slate_clip_name_entry, 3, 1)
        grid.addWidget(self.clip_name_push_btn, 3, 2)
        grid.addWidget(self.convert_spaces_btn, 3, 3)

        grid.addWidget(self.date_format_label, 4, 0)
        grid.addWidget(self.date_push_btn, 4, 1)

        grid.addWidget(self.create_slates_btn, 5, 4)
        grid.addWidget(self.cancel_btn, 6, 4)

        self.window.show()

        return self.window

    def slate_maker_multi_ratio(self):

        def save_config():

            if not self.csv_path_entry.text():
                FlameMessageWindow('Error', 'error', 'Enter Path to CSV File')
                return False

            elif not os.path.isfile(self.csv_path_entry.text()):
                FlameMessageWindow('Error', 'error', 'CSV file does not exist')
                return False

            elif not self.template_path_entry.text():
                FlameMessageWindow('Error', 'error', 'Enter Path to Text Node Templates')
                return False

            elif not os.path.isdir(self.template_path_entry.text()):
                FlameMessageWindow('Error', 'error', 'Text node template folder does not exist')
                return False

            elif not self.slate_clip_name_entry.text():
                FlameMessageWindow('Error', 'error', 'Enter tokens for slate clip naming')
                return False

            # Check for missing templates for selected slate backgrounds

            self.slate_bgs = [str(clip.name)[1:-1].rsplit('_', 1)[1] for clip in self.selection]
            print ('slate_bgs:', self.slate_bgs)

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
                return FlameMessageWindow('Error', 'error', f'Text node templates not found for: {missing}')
            else:
                print ('--> templates found for all slate backgrounds\n')

            # CSV file should contain RATIO in first line - check for this

            with open(self.csv_path_entry.text(), 'r') as csv_file:
                csv_token_line = csv_file.readline().strip()
            csv_token_line = csv_token_line.split(',')
            if 'RATIO' not in csv_token_line:
                return FlameMessageWindow('Error', 'error', 'CSV missing column called RATIO. <br><br>The RATIO field should contain the ratio of the slate to be created')

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

            print ('--> config saved\n')

            self.multi_ratio = True

            self.create_slates()

        def get_slate_ratios():

            # Check selected slate backgrounds for proper name. Must end with ratio. Such as: slate_bg_16x9

            self.slate_bgs = [str(clip.name)[1:-1].rsplit('_', 1)[1] for clip in self.selection if 'x' in str(clip.name)[1:-1].rsplit('_', 1)[1].lower()]
            self.ratios = ', '.join([str(elem).lower() for elem in self.slate_bgs])

        get_slate_ratios()

        grid = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'Slate Maker - MultiRatio <small>{VERSION}', grid, 1000, 300)

        # Labels

        self.selected_slate_ratio_label01 = FlameLabel('Selected Slate Ratios', 'normal')
        self.selected_slate_ratio_label02 = FlameLabel(self.ratios, 'background')

        self.csv_label = FlameLabel('CSV', 'normal')
        self.template_label = FlameLabel('Template Folder', 'normal')
        self.date_format_label = FlameLabel('Date Format', 'normal')
        self.slate_clip_name_label = FlameLabel('Slate Clip Name', 'normal')

        # Entry Boxes

        self.csv_path_entry = FlameLineEdit(self.multi_ratio_csv_file_path)
        self.template_path_entry = FlameLineEdit(self.multi_ratio_template_folder_path)
        self.slate_clip_name_entry = FlameLineEdit(self.multi_ratio_slate_clip_name)

        # Date Pushbutton Menu

        date_formats = ['yy/mm/dd', 'yyyy/mm/dd', 'mm/dd/yy', 'mm/dd/yyyy', 'dd/mm/yy', 'dd/mm/yyyy']
        self.date_push_btn = FlamePushButtonMenu(self.multi_ratio_date_format, date_formats, max_menu_width=150)

        # Clip Name Pushbutton Menu

        self.clip_name_menu = QtWidgets.QMenu()
        self.clip_name_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_menu.setStyleSheet('QMenu {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                                          'QMenu::item:selected {color: rgb(217, 217, 217); background-color: rgb(58, 69, 81)}')

        self.clip_name_push_btn = QtWidgets.QPushButton('Add Token')
        self.clip_name_push_btn.setMenu(self.clip_name_menu)
        self.clip_name_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clip_name_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.clip_name_push_btn.setStyleSheet('QPushButton {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                                              'QPushButton:disabled {color: rgb(116, 116, 116); background-color: rgb(45, 55, 68); border: none}'
                                              'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                                              'QPushButton::menu-indicator {image: none}')

        # Spaces to Underscore Pushbutton

        self.convert_spaces_btn = FlamePushButton(' Convert Spaces', self.multi_ratio_use_underscores)
        self.convert_spaces_btn.setToolTip('Enable to convert spaces in clip name to underscores')

        self.ratio_folders_btn = FlamePushButton(' Create Ratio Folders', self.multi_ratio_create_ratio_folders)
        self.ratio_folders_btn.setToolTip('Create separate folders for each ratio')

        # Buttons

        self.csv_browse_btn = FlameButton('Browse', self.csv_browse)
        self.template_browse_btn = FlameButton('Browse', self.template_folder_browse)
        self.cancel_btn = FlameButton('Cancel', self.window.close)
        self.create_slates_btn = FlameButton('Create Slates', save_config)

        # Get clip name tokens from csv

        try:
            self.get_csv_tokens()
        except:
            pass

        #------------------------------------#

        # Window Layout

        grid.setVerticalSpacing(5)
        grid.setHorizontalSpacing(5)

        grid.setColumnMinimumWidth(3, 150)

        grid.setRowMinimumHeight(0, 33)

        grid.addWidget(self.selected_slate_ratio_label01, 0, 0)
        grid.addWidget(self.selected_slate_ratio_label02, 0, 1, 1, 2)
        grid.addWidget(self.ratio_folders_btn, 0, 3)

        grid.addWidget(self.csv_label, 1, 0)
        grid.addWidget(self.csv_path_entry, 1, 1, 1, 3)
        grid.addWidget(self.csv_browse_btn, 1, 4)

        grid.addWidget(self.template_label, 2, 0)
        grid.addWidget(self.template_path_entry, 2, 1, 1, 3)
        grid.addWidget(self.template_browse_btn, 2, 4)

        grid.addWidget(self.date_format_label, 4, 0)
        grid.addWidget(self.date_push_btn, 4, 1)

        grid.addWidget(self.slate_clip_name_label, 3, 0)
        grid.addWidget(self.slate_clip_name_entry, 3, 1, 1, 1)
        grid.addWidget(self.clip_name_push_btn, 3, 2)
        grid.addWidget(self.convert_spaces_btn, 3, 3)

        grid.addWidget(self.create_slates_btn, 5, 4)
        grid.addWidget(self.cancel_btn, 6, 4)

        self.window.show()

        return self.window

    # ----------------------- #

    def save_path(self, path_type, path):

        # Save settings to config file

        xml_tree = ET.parse(self.config_xml)
        root = xml_tree.getroot()

        path_to_save = root.find(f'.//{path_type}')
        path_to_save.text = path

        xml_tree.write(self.config_xml)

        print ('--> path saved\n')

    def csv_browse(self):

        if os.path.isfile(self.csv_path_entry.text()):
            path = self.csv_path_entry.text().rsplit('/', 1)[0]
        else:
            path = self.csv_path_entry.text()

        csv_file_path = QtWidgets.QFileDialog.getOpenFileName(self.window, "Select Script or Folder", path, "CSV Files (*.csv)")[0]

        if csv_file_path:
            self.save_path('csv_file_path', csv_file_path)
            self.csv_path_entry.setText(csv_file_path)
            self.get_csv_tokens

    def template_browse(self):

        if os.path.isfile(self.template_path_entry.text()):
            path = self.template_path_entry.text().rsplit('/', 1)[0]
        else:
            path = self.template_path_entry.text()
        #print ('PATH:', path)
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

        self.column_names = self.csv_token_line
        self.create_clip_name_menu()

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

                        contents[token_line_num] = f'{new_token_line}'
                        contents[token_char_len_line_num] = f'{new_token_char_len_line}'

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

            for item in iter(line.items()):

                # Try to convert token in CSV
                # If token not in template, pass

                try:
                    token = '<' + item[0] + '>'
                    token_value = item[1]
                    # print ('token:', token)
                    # print ('token_value:', token_value)

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

            for item in iter(line.items()):

                token = '<' + item[0] + '>'
                token_value = item[1]
                # print ('token:', token)

                if token in clip_name:
                    clip_name = clip_name.replace(token, token_value)

                if '<CURRENT_DATE>' in clip_name:
                    date = get_date(self.date_push_btn.text())
                    clip_name = clip_name.replace('<CURRENT_DATE>', date)

            # Remove bad characters from clip name

            clip_name = re.sub(r'[\\/*?:"<>|]', ' ', clip_name)
            # print ('clip_name:', clip_name)

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

        self.window.hide()

        # Create slate library and set as slate dest

        self.slate_library = flame.project.current_project.current_workspace.create_library('- Slates -')
        self.slate_library.expanded = True
        self.slate_dest = self.slate_library

        # Read token like from csv

        self.get_csv_tokens()

        # Add < and > to column names

        token_list = ['<' + item.upper() + '>' for item in self.csv_token_line]
        print ('token_list:', token_list, '\n')

        # --------------------

        # Create slates

        missing_slate_bgs = []

        if self.multi_ratio:

            # Get list of all ratios from csv file

            csv_ratios = []

            with open(self.csv_path_entry.text(), 'r') as csv_file:
                csv_text = csv.DictReader(csv_file)
                for line in csv_text:
                    for key, value in line.items():
                        if key == 'RATIO':
                            if value not in csv_ratios:
                                csv_ratios.append(value)

            print ('csv_ratios:', csv_ratios)

            for bg in self.slate_bgs:

                # Remove slate background from list if not found is csv file

                slate_bg_missing = True

                for r in csv_ratios:
                    if re.search(bg, r, re.I):
                        slate_bg_missing = False

                if slate_bg_missing:
                    missing_slate_bgs.append(bg)
                    self.slate_bgs.remove(bg)

            print ('missing_slate_bgs:', missing_slate_bgs)

            if self.slate_bgs:

                # Get number of slates to be created then load progress bar window

                num_of_slates = 0

                with open(self.csv_path_entry.text(), 'r') as csv_file:
                    csv_text = csv.DictReader(csv_file)
                    for line in csv_text:
                        for bg in self.slate_bgs:
                            if bg.lower() in str(line).lower():
                                num_of_slates += 1

                print ('num_of_slates:', num_of_slates)

                slates_created = 1

                self.progress_window = FlameProgressWindow('Creating Slates:', num_of_slates)
                self.progress_window.enable_done_button(False)

                # Iterate through selected slate backgrounds

                for bg in self.slate_bgs:
                    #print (f'\n--> Creating {bg} Slates...\n')

                    # If Create Ratio Folders button is enabled create folder for ratio in slate library then set folder as slate dest

                    if self.ratio_folders_btn.isChecked():
                        ratio_folder = self.slate_library.create_folder(bg.lower())
                        self.slate_dest = ratio_folder

                    # Find csv lines that matches background ratio

                    with open(self.csv_path_entry.text(), 'r') as csv_file:
                        csv_text = csv.DictReader(csv_file)
                        for line in csv_text:
                            if bg.lower() in str(line).lower():

                                # Get slate background clip object to use as background

                                for clip in self.selection:
                                    if bg in str(clip.name):
                                        slate_background = clip
                                        print ('slate_background:', str(slate_background.name)[1:-1])

                                # Find text node template that matches background ratio

                                for (root, dirs, files) in os.walk(self.template_path_entry.text()):
                                    for f in files:
                                        if bg.lower() in f.lower() and f.endswith('.ttg'):
                                            self.template_path = os.path.join(root, f)

                                create_text_node(line)
                                create_slate_clip(slate_background)

                                # Update progress window

                                self.progress_window.set_progress_value(slates_created)
                                self.progress_window.set_text(f'Processing Slate: {str(slates_created)} of {str(num_of_slates)}')
                                slates_created += 1

        else:
            # Create text nodes for single slate bg/template

            # Get number of slates to be created then load progress bar window

            with open(self.csv_path_entry.text(), 'r') as csv_file:
                csv_text = csv.DictReader(csv_file)
                num_of_slates = len([c for c in enumerate(csv_text)])

            slates_created = 1

            self.progress_window = FlameProgressWindow('Creating Slates:', num_of_slates)
            self.progress_window.enable_done_button(False)

            # Get slate background clip from selection

            slate_background = self.selection[0]
            self.template_path = self.template_path_entry.text()

            #print ('\n--> Creating slates...\n')

            # Create slates

            with open(self.csv_path_entry.text(), 'r') as csv_file:
                csv_text = csv.DictReader(csv_file)
                for line in csv_text:
                    create_text_node(line)
                    create_slate_clip(slate_background)

                    # Update progress window

                    self.progress_window.set_progress_value(slates_created)
                    self.progress_window.set_text(f'Processing Slate: {str(slates_created)} of {str(num_of_slates)}')
                    slates_created += 1

        if missing_slate_bgs:
            missing = ', '.join(missing_slate_bgs)
            FlameMessageWindow('Error', 'error', f'No entries in csv for selected slate backgrounds: {missing}')

        # Delete temp folder

        shutil.rmtree(self.temp_save_path)

        self.progress_window.enable_done_button(True)

        self.window.close()

        print ('\ndone.\n')

#-------------------------------------#

def text_fx_check(selection):

    # Make sure selected clips do not already contain timeline text fx

    for clip in selection:
        for version in clip.versions:
            for track in version.tracks:
                for seg in track.segments:
                    for fx in seg.effects:
                        if fx.type == 'Text':
                            FlameMessageWindow('Error', 'error', 'Slate background clip cannot have a timeline text fx applied. Remove and try again.')
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
        FlameMessageWindow('Error', 'error', 'Turn off Protect from Editing: Flame Preferences -> General.')
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
            return FlameMessageWindow('Error', 'error', '<center>All selected slate backgrounds must have ratio at end of file name. Such as: slate_bg_16x9')
        if not slate_bgs:
            return FlameMessageWindow('Error', 'error', '<center>All selected slate backgrounds must have ratio at end of file name. Such as: slate_bg_16x9')

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
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Slate Maker - Multi Ratio',
                    'isVisible': scope_clip,
                    'execute': slate_maker_multi_ratio,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
