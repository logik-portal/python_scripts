# -*- coding: utf-8 -*-
'''
Script Name: Slate Maker
Script Version: 4.0
Flame Version: 2020.2
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 12.29.18
Update Date: 05.23.21

Custom Action Type: Media Panel

Description:

    Creates slates from CSV files

    Right-click on clip to be used as slate background -> Slates... -> Slate Maker

    Does not work with Flare

To install:

    Copy script into /opt/Autodesk/shared/python/slate_maker

Updates:

v4.0 05.23.21

    Updated to be compatible with Flame 2022/Python 3.7

v3.7 02.12.21

    Fixed bug causing script not to load when csv or ttg files have been moved or deleted - Thanks John!

v3.6 01.10.21

    Added ability to use tokens to name slate clip
    Added button to convert spaces to underscores in slate clip name

v3.5 10.13.20

    More UI Updates

v3.4 08.26.20

    Updated UI
    Added drop down menu to select csv column for slate clip naming

v3.3 04.03.20

    Fixed UI issues in Linux
    Main Window is now resizable
    Main Window opens centered in linux

v2.6 09.02.19

    Fixed bug - Script failed to convert multiple occurrences of token in slate template
    Fixed bug - Script failed when token not present in slate template for column in csv file
'''

from __future__ import print_function
from functools import partial
import os
from PySide2 import QtWidgets, QtCore

VERSION = 'v4.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/slate_maker'

#-------------------------------------#

class CreateSlates(object):

    def __init__(self, selection):
        import ast
        import shutil

        print ('\n', '>' * 20, 'slate maker %s' % VERSION, '<' * 20, '\n')

        self.selection = selection

        # Set paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')

        self.temp_save_path = os.path.join(SCRIPT_PATH, 'temp_slate_folder')

        # Create temp folder for text node files

        try:
            os.makedirs(self.temp_save_path)
        except:
            shutil.rmtree(self.temp_save_path)
            os.makedirs(self.temp_save_path)

        # Check for config file

        self.check_config_file()

        # Get config variables

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.csv_file_path = values[2]
        self.template_file_path = values[4]
        self.date_format = values[6]
        self.slate_clip_name = values[8]
        self.use_underscores = ast.literal_eval(values[10])

        get_config_values.close()

        if not os.path.isfile(self.csv_file_path):
            self.csv_file_path = ''
        if not os.path.isfile(self.template_file_path):
            self.template_file_path = ''

        # Get selected clip info

        for bg_clip in self.selection:
            self.bg_clip = bg_clip
            self.bg_clip_name = str(bg_clip.name)[1:-1]
            self.bg_clip_timecode = str(bg_clip.duration)[1:-1]
            self.bg_clip_timecode = self.bg_clip_timecode.replace('+', ':')
            self.bg_clip_frame_rate = float(str(bg_clip.frame_rate)[:-4])
            self.slate_duration = str(self.convert_timecode_to_frames())
            break

        print ('bg_clip_name:', self.bg_clip_name)
        print ('bg_clip_timecode:', self.bg_clip_timecode)
        print ('bg_clip_frame_rate:', self.bg_clip_frame_rate)
        print ('slate_duration:', self.slate_duration, '\n')

        self.main_window()

    def check_config_file(self):

        # Check for existing config file

        if not os.path.isdir(self.config_path):
            try:
                os.makedirs(self.config_path)
            except:
                message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)

        if not os.path.isfile(self.config_file):
            print ('>>> config file does not exist, creating new config file <<<')

            config_text = []

            config_text.insert(0, 'Setup values for Slate Maker python script.')
            config_text.insert(1, 'CSV File Path:')
            config_text.insert(2, '')
            config_text.insert(3, 'Text node template path:')
            config_text.insert(4, '')
            config_text.insert(5, 'Date Format:')
            config_text.insert(6, 'mm/dd/yy')
            config_text.insert(7, 'Slate Clip Name:')
            config_text.insert(8, '<ISCI>')
            config_text.insert(9, 'Convert spaces to underscores:')
            config_text.insert(10, 'True')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

    def main_window(self):

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(1000, 300))
        self.window.setMaximumSize(QtCore.QSize(1000, 300))
        self.window.setWindowTitle('pyFlame Slate Maker %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #313131')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                            (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.csv_label = QtWidgets.QLabel('CSV', self.window)
        self.csv_label.setMaximumSize(QtCore.QSize(110, 28))
        self.csv_label.setMinimumWidth(125)
        self.csv_label.setMaximumWidth(125)
        self.csv_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')

        self.template_label = QtWidgets.QLabel('Template', self.window)
        self.template_label.setMinimumWidth(125)
        self.template_label.setMaximumWidth(125)
        self.template_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')

        self.date_format_label = QtWidgets.QLabel('Date Format', self.window)
        self.date_format_label.setMinimumWidth(125)
        self.date_format_label.setMaximumWidth(125)
        self.date_format_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')

        self.slate_clip_name_label = QtWidgets.QLabel('Slate Clip Name', self.window)
        self.slate_clip_name_label.setMinimumWidth(125)
        self.slate_clip_name_label.setMaximumWidth(125)
        self.slate_clip_name_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')

        self.slate_bg_label = QtWidgets.QLabel('    Slate Background: %s    ' % self.bg_clip_name, self.window)
        self.slate_bg_label.setAlignment(QtCore.Qt.AlignCenter)
        self.slate_bg_label.setMinimumHeight(30)
        self.slate_bg_label.setMaximumHeight(30)
        self.slate_bg_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"')

        self.slate_dur_label = QtWidgets.QLabel('    Slate Duration: %s Frames    ' % self.slate_duration, self.window)
        self.slate_dur_label.setAlignment(QtCore.Qt.AlignCenter)
        self.slate_dur_label.setMinimumHeight(30)
        self.slate_dur_label.setMaximumHeight(30)
        self.slate_dur_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"')

        # Entry Boxes

        self.csv_path_entry = QtWidgets.QLineEdit(self.csv_file_path, self.window)
        self.csv_path_entry.setMinimumWidth(450)
        self.csv_path_entry.setMinimumHeight(28)
        self.csv_path_entry.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14pt "Discreet"')

        self.template_path_entry = QtWidgets.QLineEdit(self.template_file_path, self.window)
        self.template_path_entry.setMinimumWidth(450)
        self.template_path_entry.setMinimumHeight(28)
        self.template_path_entry.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14pt "Discreet"')

        self.slate_clip_name_entry = QtWidgets.QLineEdit(self.slate_clip_name, self.window)
        self.slate_clip_name_entry.setMinimumWidth(200)
        self.slate_clip_name_entry.setMinimumHeight(28)
        self.slate_clip_name_entry.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14pt "Discreet"}'
                                                 'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

        # Date Pushbutton Menu

        self.date_formats = ['yy/mm/dd', 'yyyy/mm/dd', 'mm/dd/yy', 'mm/dd/yyyy', 'dd/mm/yy', 'dd/mm/yyyy']

        def create_date_menu(date):
            self.date_push_btn.setText(date)

        self.date_menu = QtWidgets.QMenu(self.window)
        self.date_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        for date in self.date_formats:
            self.date_menu.addAction(date, partial(create_date_menu, date))

        self.date_push_btn = QtWidgets.QPushButton(self.window)
        self.date_push_btn.setMenu(self.date_menu)
        self.date_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.date_push_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.date_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.date_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                         'QPushButton:disabled {color: #6a6a6a}')
        self.date_push_btn.setText(self.date_format)

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

        self.convert_spaces_btn = QtWidgets.QPushButton(' Convert Spaces', self.window)
        self.convert_spaces_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.convert_spaces_btn.setMinimumSize(150, 28)
        self.convert_spaces_btn.setMaximumSize(150, 28)
        self.convert_spaces_btn.setCheckable(True)
        self.convert_spaces_btn.setChecked(self.use_underscores)
        self.convert_spaces_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #424142, stop: .91 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                              'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #4f4f4f, stop: .91 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                              'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                                              'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')
        self.convert_spaces_btn.setToolTip('Enable to convert spaces in clip name to underscores')

        # Buttons

        self.csv_browse_btn = QtWidgets.QPushButton('Browse', self.window)
        self.csv_browse_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.csv_browse_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.csv_browse_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.csv_browse_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
        self.csv_browse_btn.clicked.connect(self.csv_browse)

        self.template_browse_btn = QtWidgets.QPushButton('Browse', self.window)
        self.template_browse_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.template_browse_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.template_browse_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.template_browse_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                               'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
        self.template_browse_btn.clicked.connect(self.template_browse)

        self.cancel_btn = QtWidgets.QPushButton('Cancel', self.window)
        self.cancel_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                      'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
        self.cancel_btn.clicked.connect(self.close_window)

        self.create_slates_btn = QtWidgets.QPushButton('Create Slates', self.window)
        self.create_slates_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.create_slates_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.create_slates_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                             'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
        self.create_slates_btn.clicked.connect(self.create_slates)

        # Disable UI elements if no csv is provided

        if not self.csv_path_entry.text():
            self.date_push_btn.setEnabled(False)
            self.slate_clip_name_entry.setEnabled(False)
            self.clip_name_push_btn.setEnabled(False)

        # Get clip name tokens from csv

        if os.path.isfile(self.csv_path_entry.text()):
            self.read_csv()
            self.column_names = self.first_line
            self.create_clip_name_menu()

        #------------------------------------#

        # Window Layout

        self.hbox01 = QtWidgets.QHBoxLayout()
        self.hbox01.addStretch(10)
        self.hbox01.addWidget(self.slate_bg_label)
        self.hbox01.addStretch(10)
        self.hbox01.addWidget(self.slate_dur_label)
        self.hbox01.addStretch(10)

        self.grid = QtWidgets.QGridLayout()
        self.grid.setVerticalSpacing(5)
        self.grid.setHorizontalSpacing(5)

        self.grid.setColumnMinimumWidth(3, 150)

        self.grid.setRowMinimumHeight(0, 33)

        self.grid.addWidget(self.csv_label, 1, 0)
        self.grid.addWidget(self.csv_path_entry, 1, 1, 1, 3)
        self.grid.addWidget(self.csv_browse_btn, 1, 4)

        self.grid.addWidget(self.template_label, 2, 0)
        self.grid.addWidget(self.template_path_entry, 2, 1, 1, 3)
        self.grid.addWidget(self.template_browse_btn, 2, 4)

        self.grid.addWidget(self.date_format_label, 3, 0)
        self.grid.addWidget(self.date_push_btn, 3, 1)

        self.grid.addWidget(self.slate_clip_name_label, 4, 0)
        self.grid.addWidget(self.slate_clip_name_entry, 4, 1)
        self.grid.addWidget(self.clip_name_push_btn, 4, 2)
        self.grid.addWidget(self.convert_spaces_btn, 4, 3)

        self.grid.setRowMinimumHeight(5, 33)

        self.grid.addWidget(self.create_slates_btn, 6, 4)
        self.grid.addWidget(self.cancel_btn, 7, 4)

        # Main VBox

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setMargin(15)
        self.vbox.addLayout(self.hbox01)
        self.vbox.addLayout(self.grid)
        self.window.setLayout(self.vbox)

        # ----------------------------------------------

        self.window.show()

        return self.window

    def close_window(self):

        self.window.close()

    def convert_timecode_to_frames(self):

        def _seconds(value):
            if isinstance(value, str):
                _zip_ft = zip((3600, 60, 1, 1/self.bg_clip_frame_rate), value.split(':'))
                return sum(f * float(t) for f,t in _zip_ft)
            elif isinstance(value, (int, float)):
                return value / self.bg_clip_frame_rate
            else:
                return 0

        def _frames(seconds):
            return seconds * self.bg_clip_frame_rate

        def timecode_to_frames(timecode, start=None):
            return _frames(_seconds(timecode) - _seconds(start))

        frames = int(round(timecode_to_frames(self.bg_clip_timecode, start='00:00:00:00')))

        return frames

    def csv_browse(self):
        from PySide2 import QtWidgets

        if os.path.isfile(self.csv_path_entry.text()):
            path = self.csv_path_entry.text().rsplit('/', 1)[0]
        else:
            path = '/'

        csv_file_path = QtWidgets.QFileDialog.getOpenFileName(self.window, "Select Script or Folder", path, "CSV Files (*.csv)")[0]

        if csv_file_path:
            self.csv_path_entry.setText(csv_file_path)
            self.read_csv()
            self.column_names = self.first_line
            self.slate_clip_name_entry.setEnabled(True)
            self.clip_name_push_btn.setEnabled(True)
            self.date_push_btn.setEnabled(True)
            self.create_clip_name_menu()

    def template_browse(self):
        from PySide2 import QtWidgets

        if os.path.isfile(self.template_path_entry.text()):
            path = self.template_path_entry.text().rsplit('/', 1)[0]
        else:
            path = '/'

        template_file_path = QtWidgets.QFileDialog.getOpenFileName(self.window, "Select Script or Folder", path, "Text Node Setup Files (*.ttg)")[0]

        if template_file_path != '':
            self.template_path_entry.setText(template_file_path)

    def read_csv(self):

        # Get list of items in first line

        with open(self.csv_path_entry.text(), 'r') as csv_file:
            self.first_line = csv_file.readline().strip()
        self.first_line = self.first_line.split(',')
        print ('first_line: ', self.first_line, '\n')

    def create_clip_name_menu(self):
        from functools import partial

        # Create clip name menu from first line of csv file

        def create_menu(name):
            self.slate_clip_name_entry.insert('<' + name + '>')

        self.clip_name_menu.clear()

        # Create clip name menu from column name list

        for name in self.column_names:
            self.clip_name_menu.addAction(name, partial(create_menu, name))

    def create_slates(self):
        import shutil
        import flame

        # Save setup file

        config_saved = self.save_config_file()

        if config_saved:

            # Create slates

            self.close_window()

            text_files_created = self.create_text_node_files()

            if text_files_created:

                # Create slate library

                slate_library = flame.project.current_project.current_workspace.create_library('-Slates-')
                slate_library.expanded = True

                for text_setup in os.listdir(self.temp_save_path):
                    # print 'text_setup:', text_setup

                    new_bg_clip = flame.media_panel.copy(self.bg_clip, slate_library)
                    for clip in new_bg_clip:
                        clip.name = text_setup[:-4]

                    # Add text effect and load text setup
                    # Warn if Protect from Editing is on
                    # Either turn off or create slate from desktop

                    try:
                        seg = clip.versions[0].tracks[0].segments[0]
                        seg_name = str(seg.name)[1:-1]
                        text_fx = seg.create_effect('Text')
                        text_file_path = os.path.join(self.temp_save_path, seg_name) + '.ttg'
                        text_fx.load_setup(text_file_path)
                    except:
                        flame.delete(slate_library)

                        message_box("Turn off 'Protect From Editing' in preferences or create slates from desktop")
                        return

                # Delete temp text node files

                shutil.rmtree(self.temp_save_path)

                message_box('Slates Created')

    def create_text_node_files(self):
        import re

        def get_date(date_format):
            import datetime

            now = datetime.datetime.now()

            date_format = date_format.replace('yyyy', '20%y')
            date_format = date_format.replace('yy', '%y')
            date_format = date_format.replace('mm', '%m')
            date_format = date_format.replace('dd', '%d')

            # print 'date_format:', date_format

            current_date = now.strftime(date_format)

            # print 'current_date: ', current_date

            return current_date

        def create_temp_text_file():
            from random import randint
            import shutil

            # Get random number

            text_node_num = randint(1, 10000)

            temp_text_file = self.temp_save_path + '/Slate_Template_' + str(text_node_num) + '.ttg'
            # print 'temp_text_file: ', temp_text_file

            shutil.copy(self.template_path_entry.text(), temp_text_file)

            print ('\n>>> created temp text node setup <<<\n')

            return temp_text_file

        def ascii_convert(text_to_convert):

            # Convert fancy quotes to regular quotes

            text_to_convert = text_to_convert.replace('“', '"').replace('”', '"')
            # print 'text_to_convert:', text_to_convert

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
                        # print 'token_line_num:', token_line_num
                        # print 'token_char_len_line_num:', token_char_len_line_num, '\n'

                        # Replace token with token value in line

                        token_line_split = line.rsplit(token, 1)[0]
                        new_token_line = token_line_split + token_value + '\n'
                        new_token_chars = new_token_line.rsplit('Text ', 1)[1]
                        new_token_char_len_line = 'TextLength ' + str(len(new_token_chars.split(' '))) + '\n'
                        # print 'new_token_line:', new_token_line, '\n'
                        # print 'new_token_char_len_line:', new_token_char_len_line

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

        def rename_text_file(clip_name, temp_text_file, temp_save_path):
            import shutil

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

                new_text_file = name_clip(clip_num, num)

                shutil.move(temp_text_file, new_text_file)

                return

        self.read_csv()

        # Add < and > to column names

        column_list = []

        for item in self.first_line:
            new_item = '<' + item.upper() + '>'
            column_list.append(new_item)

        print ('column_list:', column_list)

        # Go through rows of csv file and create slates

        with open(self.csv_path_entry.text(), 'r') as csv_file:

            # Read csv lines, skip first line

            csv_text = csv_file.read().splitlines()[1:]

        # --------------------

        # Create text files

        for line in csv_text:

            clip_name = self.slate_clip_name_entry.text()
            print ('clip_name:', clip_name)

            temp_text_file = create_temp_text_file()

            line_list = line.split(',')

            # Merge column list with line list into dictionary

            line_dict = dict(zip(column_list, line_list))

            # print 'line_dict:', line_dict

            # for item in line_dict.iteritems():

            for item in iter(line_dict.items()):

                # Try to convert token in CSV
                # If token not in template, pass

                try:
                    token = item[0]
                    token_value = item[1]

                    if token == '<CURRENT_DATE>':
                        token_value = get_date(self.date_push_btn.text())

                    # print 'token: ', token
                    # print 'token_value: ', token_value

                    # Convert token to ascii code

                    token = ascii_convert(token)
                    # print 'converted token: ', token

                    # Convert token value to ascii code

                    token_value = ascii_convert(token_value)
                    # print 'converted token_value: ', token_value

                    # Update text node setup file

                    modify_setup_line(token, token_value, temp_text_file)

                except:
                    pass

            # Get clip name pushbutton text to name clips

            # for item in line_dict.iteritems():
            for item in iter(line_dict.items()):

                token = item[0]
                token_value = item[1]

                print ('token:', token)
                print ('token_value:', token_value)

                if token in clip_name:
                    clip_name = clip_name.replace(token, token_value)

                if '<CURRENT_DATE>' in clip_name:
                    date = get_date(self.date_push_btn.text())
                    clip_name = clip_name.replace('<CURRENT_DATE>', date)

            # Remove bad characters from clip name

            clip_name = re.sub(r'[\\/*?:"<>|]', ' ', clip_name)
            print ('\nclip_name:', clip_name, '\n')

            # If Use Underscores in checked, replace spaces with underscores

            if self.convert_spaces_btn.isChecked():
                clip_name = re.sub(r' ', '_', clip_name)

            # Rename temp text file selected clip name option

            rename_text_file(clip_name, temp_text_file, self.temp_save_path)

        print ('\n', '>' * 10, 'text node files created', '<' * 10, '\n')

        return True

    def save_config_file(self):

        csv_path = self.csv_path_entry.text()
        template_path = self.template_path_entry.text()

        if not csv_path:
            message_box('Enter Path to CSV File')
            return False

        elif not os.path.isfile(csv_path):
            message_box('CSV file does not exist')
            return False

        elif not template_path:
            message_box('Enter Path to Text Node Template')
            return False

        elif not os.path.isfile(template_path):
            message_box('Text node template file does not exist')
            return False

        elif not self.slate_clip_name_entry.text():
            message_box('Enter tokens for slate clip naming')
            return False

        else:
            config_text = []

            config_text.insert(0, 'Setup values for Slate Maker python script.')
            config_text.insert(1, 'CSV File Path:')
            config_text.insert(2, csv_path)
            config_text.insert(3, 'Text node template path:')
            config_text.insert(4, template_path)
            config_text.insert(5, 'Date Format:')
            config_text.insert(6, self.date_push_btn.text())
            config_text.insert(7, 'Slate Clip Name:')
            config_text.insert(8, self.slate_clip_name_entry.text())
            config_text.insert(9, 'Convert spaces to underscores:')
            config_text.insert(10, self.convert_spaces_btn.isChecked())

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

            print ('\n', '>>> slate maker config saved <<<', '\n')

            return True

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

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

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
                    'execute': CreateSlates,
                    'minimumVersion': '2020.2'
                }
            ]
        }
    ]
