'''
Script Name: Create Shot
Script Version: 4.0
Flame Version: 2021.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 06.09.18
Update Date: 06.03.21

Custom Action Type: Media Panel / Media Hub

Description:

    Create shot folders with/without shot batch groups
    Create shot batch groups only
    Create shot desktops with batch groups and reel groups
    Create file system shot folders in Media Hub - Flame 2021.2 and higher only

    In the Media Panel:

    Right-click in Media Panel -> Create Shot... -> Create Shot Folders
    Right-click in Media Panel -> Create Shot... -> Create Shot Batch Groups
    Right-click in Media Panel -> Create Shot... -> Create Shot Desktops

    In Media Hub Files:

    Right-click in the Media Hub -> Create Shot... -> Create File System Shot Folders

    Shot Folder Structure, Batch Groups, and Desktops can all be customized by going to Setup in the main window.

To install:

    Copy script into /opt/Autodesk/shared/python/create_shot

Updates:

v4.0 06.03.21

    Updated to be compatible with Flame 2022/Python 3.7

    UI Updates/Calculator fixes

    Fixed adding folders to in setup to file system folder structure

    Added ability to create shot desktops

v3.2 11.11.20

    Updates to paths and description for Logik Portal

v3.1 11.10.20

    Fixed bug when creating system shot folders that incorrectly used media hub folder template - thanks John!

v3.0 10.13.20

    Updated and simplified UI

    Added ability to create file system shot folders

    Code cleanup
'''

from __future__ import print_function
import os
import re
import ast
from functools import partial
from PySide2 import QtWidgets, QtCore

VERSION = 'v4.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/create_shot'

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
        self.setMinimumSize(155, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                               'QLabel:disabled {color: #6a6a6a}')
        elif label_type == 'background':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')
        elif label_type == 'outline':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"')

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

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget

    To use:

    button = FlameButton('Button Name', do_this_when_pressed, window)
    """

    def __init__(self, button_name, do_when_pressed, parent_window, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setMinimumSize(QtCore.QSize(155, 28))
        self.setMaximumSize(QtCore.QSize(155, 28))
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
        self.setMinimumSize(155, 28)
        self.setMaximumSize(155, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

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
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #6a6a6a}')

        def token_action_menu():

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
        self.setMinimumWidth(110)
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

# ------------------------------------- #

class CreateShotFolders(object):

    def __init__(self, selection, create_type):
        import flame

        print ('\n', '>' * 20, 'create shot folders %s' % VERSION, '<' * 20, '\n')

        self.selection = selection

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')

        self.check_config_file()

        # Read config file

        self.load_config_file()

        # Get flame variables

        self.ws = flame.projects.current_project.current_workspace
        self.desktop = self.ws.desktop
        self.current_flame_tab = flame.get_current_tab()

        # Get flame version

        self.flame_version = flame.get_version()

        if 'pr' in self.flame_version:
            self.flame_version = self.flame_version.rsplit('.pr', 1)[0]
        if self.flame_version.count('.') > 1:
            self.flame_version = self.flame_version.rsplit('.', 1)[0]
        self.flame_version = float(self.flame_version)
        print ('flame_version:', self.flame_version)

        self.reel_group_tree = ''
        self.create_type = create_type
        self.shot_folder_name = ''
        self.batch_group = ''
        self.lib = ''

    def check_config_file(self):

        # Check for and load config file
        #-------------------------------

        if not os.path.isdir(self.config_path):
            try:
                os.makedirs(self.config_path)
            except:
                message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)

        if not os.path.isfile(self.config_file):
            print ('>>> config file does not exist, creating new config file <<<')

            config_text = []

            config_text.insert(0, 'This text file saves setup values for Shot Folder Creator python script.')
            config_text.insert(1, 'Shot Naming:')
            config_text.insert(2, 'PYT_<ShotNum####>')
            config_text.insert(3, 'Number of Shots:')
            config_text.insert(4, '10')
            config_text.insert(5, 'Starting Shot:')
            config_text.insert(6, '10')
            config_text.insert(7, 'Shot Increments')
            config_text.insert(8, '10')
            config_text.insert(9, 'Create batch groups')
            config_text.insert(10, 'False')
            config_text.insert(11, 'Shot Folders:')
            config_text.insert(12, "{'Shot_Folder': {'Batch': {}, 'Elements': {}, 'Plates': {}, 'Ref': {}, 'Renders': {}}}")
            config_text.insert(13, 'File System Shot Folders:')
            config_text.insert(14, "{'Shot_Folder': {'Elements': {}, 'Plates': {}, 'Ref': {}, 'Renders': {}}}")
            config_text.insert(15, 'Schematic Reels:')
            config_text.insert(16, "{'Schematic Reels': {'Plates': {}, 'PreRenders': {}, 'Elements': {}, 'Ref': {}}}")
            config_text.insert(17, 'Shelf Reels:')
            config_text.insert(18, "{'Shelf Reels': {'Batch Renders': {}}}")
            config_text.insert(19, 'Add Render Node:')
            config_text.insert(20, 'True')
            config_text.insert(21, 'Add Write Node:')
            config_text.insert(22, 'False')
            config_text.insert(23, 'Write File Node Media Path:')
            config_text.insert(24, '/opt/Autodesk')
            config_text.insert(25, 'Write File Node Pattern:')
            config_text.insert(26, '<name>')
            config_text.insert(27, 'Write File Node Create Open Clip:')
            config_text.insert(28, 'True')
            config_text.insert(29, 'Write File Node Include Setup:')
            config_text.insert(30, 'True')
            config_text.insert(31, 'Write File Node Create Open Clip Entry:')
            config_text.insert(32, '<name>')
            config_text.insert(33, 'Write File Node Include Setup Entry:')
            config_text.insert(34, '<name>')
            config_text.insert(35, 'Write File Node File Type:')
            config_text.insert(36, 'Dpx 10-bit')
            config_text.insert(37, 'Write File Node Padding')
            config_text.insert(38, '4')
            config_text.insert(39, 'Write File Node Frame Index: ')
            config_text.insert(40, 'Use Start Frame')
            config_text.insert(41, 'Add Reel Group:')
            config_text.insert(42, 'True')
            config_text.insert(43, 'Reel Group Reels:')
            config_text.insert(44, "{'Reels': {'Reel 1': {}, 'Reel 2': {}, 'Reel 3': {}, 'Reel 4': {}}}")

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

    def load_config_file(self):

        # Read config file

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        # Assign values from config file

        self.shot_naming = values[2]
        self.num_of_shots = int(values[4])
        self.starting_shot = int(values[6])
        self.shot_increments = int(values[8])
        self.create_batch_groups = ast.literal_eval(values[10])
        self.folder_dict = ast.literal_eval(values[12])
        self.file_system_folder_dict = ast.literal_eval(values[14])
        self.schematic_reel_dict = ast.literal_eval(values[16])
        self.shelf_reel_dict = ast.literal_eval(values[18])
        self.add_render_node = ast.literal_eval(values[20])
        self.add_write_file_node = ast.literal_eval(values[22])
        self.write_file_media_path = values[24]
        self.write_file_pattern = values[26]
        self.write_file_create_open_clip = ast.literal_eval(values[28])
        self.write_file_include_setup = ast.literal_eval(values[30])
        self.write_file_create_open_clip_value = values[32]
        self.write_file_include_setup_value = values[34]
        self.write_file_image_format = values[36]
        self.write_file_padding = values[38]
        self.write_file_frame_index = values[40]
        self.add_reel_group = ast.literal_eval(values[42])
        self.reel_group_dict = ast.literal_eval(values[44])

        # Close config file

        get_config_values.close()

        # Convert dictionaries to lists

        self.schematic_reels = self.convert_reel_dict(self.schematic_reel_dict)
        self.shelf_reels = self.convert_reel_dict(self.shelf_reel_dict)
        self.reel_group = self.convert_reel_dict(self.reel_group_dict)

        print ('\n>>> settings loaded <<<\n')

    def convert_reel_dict(self, reel_dict):

        converted_list = []

        for key, value in sorted(iter(reel_dict.items())):
            for v in value:
                converted_list.append(v)

        converted_list.sort()

        print ('converted_list:', converted_list, '\n')

        return converted_list

    def main_window(self):

        class CustomSpinBox(QtWidgets.QLineEdit):
            from PySide2 import QtWidgets, QtCore, QtGui

            IntSpinBox = 0
            DoubleSpinBox = 1

            def __init__(self, spinbox_type, value, parent=None):
                from PySide2 import QtGui

                super(CustomSpinBox, self).__init__(parent)

                if spinbox_type == CustomSpinBox.IntSpinBox:
                    self.setValidator(QtGui.QIntValidator(parent=self))
                else:
                    self.setValidator(QtGui.QDoubleValidator(parent=self))

                self.spinbox_type = spinbox_type
                self.min = None
                self.max = None
                self.steps = 1
                self.value_at_press = None
                self.pos_at_press = None

                self.setValue(value)
                self.setReadOnly(True)
                self.textChanged.connect(self.value_changed)
                self.setFocusPolicy(QtCore.Qt.NoFocus)
                self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14pt "Discreet"')
                self.clearFocus()

            def calculator(self):
                from PySide2 import QtCore, QtWidgets, QtGui
                from functools import partial

                def clear():
                    calc_lineedit.setText('')

                def button_press(key):

                    if self.clean_line == True:
                        calc_lineedit.setText('')

                    calc_lineedit.insert(key)

                    self.clean_line = False

                def plus_minus():

                    # calc = int(calc_lineedit.text()) * -1
                    calc_lineedit.setText(str(int(calc_lineedit.text()) * -1))

                def add_sub(key):

                    if calc_lineedit.text() == '':
                        calc_lineedit.setText('0')

                    if '**' not in calc_lineedit.text():
                        try:
                            calc_num = eval(calc_lineedit.text().lstrip('0'))

                            calc_lineedit.setText(str(calc_num))

                            calc_num = int(calc_lineedit.text())

                            if calc_num == 0:
                                calc_num = 1
                            if key == 'add':
                                self.setValue(int(self.text()) + int(calc_num))
                            else:
                                self.setValue(int(self.text()) - int(calc_num))

                            self.clean_line = True
                        except:
                            pass

                def enter():

                    if self.clean_line == True:
                        return calc_window.close()

                    if calc_lineedit.text() != '':

                        new_value = calculate_entry()

                        self.setValue(int(new_value))

                    # calc_window.close()
                    close_calc()

                def equals():

                    if calc_lineedit.text() == '':
                        calc_lineedit.setText('0')

                    if calc_lineedit.text() != '0':

                        calc_line = calc_lineedit.text().lstrip('0')
                    else:
                        calc_line = calc_lineedit.text()

                    if '**' not in calc_lineedit.text():
                        try:
                            calc = eval(calc_line)
                        except:
                            calc = 0

                        calc_lineedit.setText(str(calc))
                    else:
                        calc_lineedit.setText('1')

                def calculate_entry():

                    calc_line = calc_lineedit.text().lstrip('0')

                    if '**' not in calc_lineedit.text():
                        try:
                            if calc_line.startswith('+'):
                                calc = int(self.text()) + eval(calc_line[-1:])
                            elif calc_line.startswith('-'):
                                calc = int(self.text()) - eval(calc_line[-1:])
                            elif calc_line.startswith('*'):
                                calc = int(self.text()) * eval(calc_line[-1:])
                            elif calc_line.startswith('/'):
                                calc = int(self.text()) / eval(calc_line[-1:])
                            else:
                                calc = eval(calc_line)
                        except:
                            calc = 0
                    else:
                        calc = 1

                    calc_lineedit.setText(str(int(calc)))

                    return calc

                def close_calc():
                    calc_window.close()
                    self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14pt "Discreet"')

                def revert_color():
                    self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14pt "Discreet"')

                calc_version = '1.0'
                self.clean_line = False

                calc_window = QtWidgets.QWidget()
                calc_window.setMinimumSize(QtCore.QSize(210, 280))
                calc_window.setMaximumSize(QtCore.QSize(210, 280))
                calc_window.setWindowTitle('pyFlame Calc %s' % calc_version)
                calc_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
                calc_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                calc_window.destroyed.connect(revert_color)
                calc_window.move(QtGui.QCursor.pos().x() - 110, QtGui.QCursor.pos().y() - 290)
                calc_window.setStyleSheet('background-color: #313131')

                # Labels

                calc_label = QtWidgets.QLabel('Calculator', calc_window)
                calc_label.setAlignment(QtCore.Qt.AlignCenter)
                calc_label.setMinimumHeight(28)
                calc_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"')

                #  LineEdit

                calc_lineedit = QtWidgets.QLineEdit('', calc_window)
                calc_lineedit.setMinimumHeight(28)
                calc_lineedit.setFocus()
                calc_lineedit.returnPressed.connect(enter)
                calc_lineedit.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14pt "Discreet"}')

                # Limit characters that can be entered into lineedit

                regex = QtCore.QRegExp('[0-9_,=,/,*,+,\-,.]+')
                validator = QtGui.QRegExpValidator(regex)
                calc_lineedit.setValidator(validator)

                # Buttons

                blank_btn = QtWidgets.QPushButton('', calc_window)
                blank_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                blank_btn.setMinimumSize(40, 28)
                blank_btn.setMaximumSize(40, 28)
                blank_btn.setDisabled(True)
                blank_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                        'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                plus_minus_btn = QtWidgets.QPushButton('+/-', calc_window)
                plus_minus_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                plus_minus_btn.setMinimumSize(40, 28)
                plus_minus_btn.setMaximumSize(40, 28)
                plus_minus_btn.clicked.connect(plus_minus)
                plus_minus_btn.setStyleSheet('color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"')

                add_btn = QtWidgets.QPushButton('Add', calc_window)
                add_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                add_btn.setMinimumSize(40, 28)
                add_btn.setMaximumSize(40, 28)
                add_btn.clicked.connect(partial(add_sub, 'add'))
                add_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                      'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                sub_btn = QtWidgets.QPushButton('Sub', calc_window)
                sub_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                sub_btn.setMinimumSize(40, 28)
                sub_btn.setMaximumSize(40, 28)
                sub_btn.clicked.connect(partial(add_sub, 'sub'))
                sub_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                      'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                clear_btn = QtWidgets.QPushButton('C', calc_window)
                clear_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                clear_btn.setMinimumSize(40, 28)
                clear_btn.setMaximumSize(40, 28)
                clear_btn.clicked.connect(clear)
                clear_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                        'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                equal_btn = QtWidgets.QPushButton('=', calc_window)
                equal_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                equal_btn.setMinimumSize(40, 28)
                equal_btn.setMaximumSize(40, 28)
                equal_btn.clicked.connect(equals)
                equal_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                        'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                div_btn = QtWidgets.QPushButton('/', calc_window)
                div_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                div_btn.setMinimumSize(40, 28)
                div_btn.setMaximumSize(40, 28)
                div_btn.clicked.connect(partial(button_press, '/'))
                div_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                      'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                mult_btn = QtWidgets.QPushButton('*', calc_window)
                mult_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                mult_btn.setMinimumSize(40, 28)
                mult_btn.setMaximumSize(40, 28)
                mult_btn.clicked.connect(partial(button_press, '*'))
                mult_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                       'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _7_btn = QtWidgets.QPushButton('7', calc_window)
                _7_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _7_btn.setMinimumSize(40, 28)
                _7_btn.setMaximumSize(40, 28)
                _7_btn.clicked.connect(partial(button_press, '7'))
                _7_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _8_btn = QtWidgets.QPushButton('8', calc_window)
                _8_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _8_btn.setMinimumSize(40, 28)
                _8_btn.setMaximumSize(40, 28)
                _8_btn.clicked.connect(partial(button_press, '8'))
                _8_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _9_btn = QtWidgets.QPushButton('9', calc_window)
                _9_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _9_btn.setMinimumSize(40, 28)
                _9_btn.setMaximumSize(40, 28)
                _9_btn.clicked.connect(partial(button_press, '9'))
                _9_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                minus_btn = QtWidgets.QPushButton('-', calc_window)
                minus_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                minus_btn.setMinimumSize(40, 28)
                minus_btn.setMaximumSize(40, 28)
                minus_btn.clicked.connect(partial(button_press, '-'))
                minus_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                        'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _4_btn = QtWidgets.QPushButton('4', calc_window)
                _4_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _4_btn.setMinimumSize(40, 28)
                _4_btn.setMaximumSize(40, 28)
                _4_btn.clicked.connect(partial(button_press, '4'))
                _4_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _5_btn = QtWidgets.QPushButton('5', calc_window)
                _5_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _5_btn.setMinimumSize(40, 28)
                _5_btn.setMaximumSize(40, 28)
                _5_btn.clicked.connect(partial(button_press, '5'))
                _5_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _6_btn = QtWidgets.QPushButton('6', calc_window)
                _6_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _6_btn.setMinimumSize(40, 28)
                _6_btn.setMaximumSize(40, 28)
                _6_btn.clicked.connect(partial(button_press, '6'))
                _6_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                plus_btn = QtWidgets.QPushButton('+', calc_window)
                plus_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                plus_btn.setMinimumSize(40, 28)
                plus_btn.setMaximumSize(40, 28)
                plus_btn.clicked.connect(partial(button_press, '+'))
                plus_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                       'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _1_btn = QtWidgets.QPushButton('1', calc_window)
                _1_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _1_btn.setMinimumSize(40, 28)
                _1_btn.setMaximumSize(40, 28)
                _1_btn.clicked.connect(partial(button_press, '1'))
                _1_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _2_btn = QtWidgets.QPushButton('2', calc_window)
                _2_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _2_btn.setMinimumSize(40, 28)
                _2_btn.setMaximumSize(40, 28)
                _2_btn.clicked.connect(partial(button_press, '2'))
                _2_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _3_btn = QtWidgets.QPushButton('3', calc_window)
                _3_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _3_btn.setMinimumSize(40, 28)
                _3_btn.setMaximumSize(40, 28)
                _3_btn.clicked.connect(partial(button_press, '3'))
                _3_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                enter_btn = QtWidgets.QPushButton('Enter', calc_window)
                enter_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                enter_btn.setMinimumSize(28, 61)
                enter_btn.clicked.connect(enter)
                enter_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                        'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _0_btn = QtWidgets.QPushButton('0', calc_window)
                _0_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _0_btn.setMinimumSize(80, 28)
                _0_btn.clicked.connect(partial(button_press, '0'))
                _0_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                point_btn = QtWidgets.QPushButton('.', calc_window)
                point_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                point_btn.setMinimumSize(40, 28)
                point_btn.setMaximumSize(40, 28)
                point_btn.clicked.connect(partial(button_press, '.'))
                point_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                        'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                gridbox = QtWidgets.QGridLayout()
                gridbox.setVerticalSpacing(5)
                gridbox.setHorizontalSpacing(5)

                gridbox.addWidget(calc_label, 0, 0, 1, 4)

                gridbox.addWidget(calc_lineedit, 1, 0, 1, 4)

                gridbox.addWidget(blank_btn, 2, 0)
                gridbox.addWidget(plus_minus_btn, 2, 1)
                gridbox.addWidget(add_btn, 2, 2)
                gridbox.addWidget(sub_btn, 2, 3)

                gridbox.addWidget(clear_btn, 3, 0)
                gridbox.addWidget(equal_btn, 3, 1)
                gridbox.addWidget(div_btn, 3, 2)
                gridbox.addWidget(mult_btn, 3, 3)

                gridbox.addWidget(_7_btn, 4, 0)
                gridbox.addWidget(_8_btn, 4, 1)
                gridbox.addWidget(_9_btn, 4, 2)
                gridbox.addWidget(minus_btn, 4, 3)

                gridbox.addWidget(_4_btn, 5, 0)
                gridbox.addWidget(_5_btn, 5, 1)
                gridbox.addWidget(_6_btn, 5, 2)
                gridbox.addWidget(plus_btn, 5, 3)

                gridbox.addWidget(_1_btn, 6, 0)
                gridbox.addWidget(_2_btn, 6, 1)
                gridbox.addWidget(_3_btn, 6, 2)
                gridbox.addWidget(enter_btn, 6, 3, 2, 1)

                gridbox.addWidget(_0_btn, 7, 0, 1, 2)
                gridbox.addWidget(point_btn, 7, 2)

                calc_window.setLayout(gridbox)

                calc_window.show()

            def value_changed(self):

                # If value is greater or less than min/max values set values to min/max

                if int(self.value()) < self.min:
                    self.setText(str(self.min))
                if int(self.value()) > self.max:
                    self.setText(str(self.max))

            def mousePressEvent(self, event):
                from PySide2 import QtGui

                if event.buttons() == QtCore.Qt.LeftButton:
                    self.value_at_press = self.value()
                    self.pos_at_press = event.pos()
                    self.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
                    self.setStyleSheet('color: #d9d9d9; background-color: #474e58; selection-color: #d9d9d9; selection-background-color: #474e58; font: 14pt "Discreet"')

            def mouseReleaseEvent(self, event):
                from PySide2 import QtGui

                if event.button() == QtCore.Qt.LeftButton:

                    # Open calculator if button is released within 10 pixels of button click

                    if event.pos().x() in range((self.pos_at_press.x() - 10), (self.pos_at_press.x() + 10)) and event.pos().y() in range((self.pos_at_press.y() - 10), (self.pos_at_press.y() + 10)):
                        self.calculator()
                    else:
                        self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14pt "Discreet"')

                    self.value_at_press = None
                    self.pos_at_press = None
                    self.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
                    return

                super(CustomSpinBox, self).mouseReleaseEvent(event)

            def mouseMoveEvent(self, event):

                if event.buttons() != QtCore.Qt.LeftButton:
                    return

                if self.pos_at_press is None:
                    return

                steps_mult = self.getStepsMultiplier(event)

                delta = event.pos().x() - self.pos_at_press.x()
                delta /= 20  # Make movement less sensitive.
                delta *= self.steps * steps_mult

                value = self.value_at_press + delta
                self.setValue(value)

                super(CustomSpinBox, self).mouseMoveEvent(event)

            def getStepsMultiplier(self, event):

                steps_mult = 1

                if event.modifiers() == QtCore.Qt.CTRL:
                    steps_mult = 10
                elif event.modifiers() == QtCore.Qt.SHIFT:
                    steps_mult = 0.10

                return steps_mult

            def setMinimum(self, value):

                self.min = value

            def setMaximum(self, value):

                self.max = value

            def setSteps(self, steps):

                if self.spinbox_type == CustomSpinBox.IntSpinBox:
                    self.steps = max(steps, 1)
                else:
                    self.steps = steps

            def value(self):

                if self.spinbox_type == CustomSpinBox.IntSpinBox:
                    return int(self.text())
                else:
                    return float(self.text())

            def setValue(self, value):

                if self.min is not None:
                    value = max(value, self.min)

                if self.max is not None:
                    value = min(value, self.max)

                if self.spinbox_type == CustomSpinBox.IntSpinBox:
                    self.setText(str(int(value)))
                else:
                    # Keep float values to two decimal places

                    value_string = str(float(value))

                    if len(value_string.rsplit('.', 1)[1]) < 2:
                        value_string = value_string + '0'

                    if len(value_string.rsplit('.', 1)[1]) > 2:
                        value_string = value_string[:-1]

                    self.setText(value_string)

        def setup():

            def setup_folder_tab():

                # Labels

                self.folders_label = FlameLabel('Folder Setup', 'background', self.setup_window.tab1)

                # Media Panel Shot Folder Tree

                self.folder_tree = QtWidgets.QTreeWidget(self.setup_window.tab1)
                self.folder_tree.setColumnCount(1)
                self.folder_tree.setHeaderLabel('Media Panel Shot Folder Template')
                self.folder_tree.itemsExpandable()
                self.folder_tree.setAlternatingRowColors(True)
                self.folder_tree.setFocusPolicy(QtCore.Qt.NoFocus)
                self.folder_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
                                               'QTreeWidget::item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                                               'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"}'
                                               'QTreeWidget::item:selected {selection-background-color: #111111}'
                                               'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                               'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                # File System Shot Folder Tree

                self.file_system_folder_tree = QtWidgets.QTreeWidget(self.setup_window.tab1)
                self.file_system_folder_tree.setColumnCount(1)
                self.file_system_folder_tree.setHeaderLabel('File System Shot Folder Template')
                self.file_system_folder_tree.itemsExpandable()
                self.file_system_folder_tree.setAlternatingRowColors(True)
                self.file_system_folder_tree.setFocusPolicy(QtCore.Qt.NoFocus)
                self.file_system_folder_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
                                                           'QTreeWidget:disabled {color: #747474; background-color: #353535; alternate-background-color: #353535}'
                                                           'QTreeWidget::item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                                                           'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"}'
                                                           'QTreeWidget::item:selected {selection-background-color: #111111}'
                                                           'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                # Fill tree

                fill_tree(self.folder_tree, self.folder_dict)
                fill_tree(self.file_system_folder_tree, self.file_system_folder_dict)

                # Set tree top level items

                folder_tree_top = self.folder_tree.topLevelItem(0)
                self.folder_tree.setCurrentItem(folder_tree_top)
                file_system_folder_tree_top = self.file_system_folder_tree.topLevelItem(0)

                # Buttons

                self.add_folder_btn = FlameButton('Add Folder', partial(add_tree_item, folder_tree_top, self.folder_tree), self.setup_window.tab1)
                self.delete_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, folder_tree_top, self.folder_tree), self.setup_window.tab1)

                self.add_file_system_folder_btn = FlameButton('Add Folder', partial(add_tree_item, file_system_folder_tree_top, self.file_system_folder_tree), self.setup_window.tab1)
                self.delete_file_system_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, file_system_folder_tree_top, self.file_system_folder_tree), self.setup_window.tab1)

                setup_save_btn = FlameButton('Save', save_setup_settings, self.setup_window.tab1)
                setup_cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window.tab1)

                # Media panel shot folder tree contextual right click menus

                action_add_folder = QtWidgets.QAction('Add Folder', self.setup_window.tab1)
                action_add_folder.triggered.connect(partial(add_tree_item, folder_tree_top, self.folder_tree))
                self.folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                self.folder_tree.addAction(action_add_folder)

                action_delete_folder = QtWidgets.QAction('Delete Folder', self.setup_window.tab1)
                action_delete_folder.triggered.connect(partial(del_tree_item, folder_tree_top, self.folder_tree))
                self.folder_tree.addAction(action_delete_folder)

                # File system shot folder tree contextual right click menus

                action_file_system_add_folder = QtWidgets.QAction('Add Folder', self.setup_window.tab1)
                action_file_system_add_folder.triggered.connect(partial(add_tree_item, file_system_folder_tree_top, self.file_system_folder_tree))
                self.file_system_folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                self.file_system_folder_tree.addAction(action_file_system_add_folder)

                action_file_system_delete_folder = QtWidgets.QAction('Delete Folder', self.setup_window.tab1)
                action_file_system_delete_folder.triggered.connect(partial(del_tree_item, file_system_folder_tree_top, self.file_system_folder_tree))
                self.file_system_folder_tree.addAction(action_file_system_delete_folder)

                # Tab layout

                vbox01 = QtWidgets.QVBoxLayout()
                vbox01.addWidget(self.add_folder_btn)
                vbox01.addWidget(self.delete_folder_btn)
                vbox01.addStretch(50)

                vbox02 = QtWidgets.QVBoxLayout()
                vbox02.addWidget(self.add_file_system_folder_btn)
                vbox02.addWidget(self.delete_file_system_folder_btn)
                vbox02.addStretch(50)

                self.setup_window.tab1.layout = QtWidgets.QGridLayout()
                self.setup_window.tab1.layout.setMargin(10)
                self.setup_window.tab1.layout.setVerticalSpacing(5)
                self.setup_window.tab1.layout.setHorizontalSpacing(5)

                self.setup_window.tab1.layout.addWidget(self.folders_label, 0, 0)
                self.setup_window.tab1.layout.addWidget(self.folder_tree, 1, 0)
                self.setup_window.tab1.layout.addWidget(self.file_system_folder_tree, 2, 0)
                self.setup_window.tab1.layout.addLayout(vbox01, 1, 1)
                self.setup_window.tab1.layout.addLayout(vbox02, 2, 1)

                self.setup_window.tab1.layout.addWidget(setup_save_btn, 4, 1)
                self.setup_window.tab1.layout.addWidget(setup_cancel_btn, 5, 1)

                self.setup_window.tab1.setLayout(self.setup_window.tab1.layout)

            def setup_batch_group_tab():

                # Labels

                self.batch_groups_label = FlameLabel('Batch Group Reel Setup', 'background', self.setup_window)

                # Schematic Reel Tree

                self.schematic_reel_tree = QtWidgets.QTreeWidget(self.setup_window.tab2)
                self.schematic_reel_tree.setColumnCount(1)
                self.schematic_reel_tree.setHeaderLabel('Schematic Reel Template')
                self.schematic_reel_tree.itemsExpandable()
                self.schematic_reel_tree.setDragEnabled(True)
                self.schematic_reel_tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
                self.schematic_reel_tree.setAlternatingRowColors(True)
                self.schematic_reel_tree.setFocusPolicy(QtCore.Qt.NoFocus)
                self.schematic_reel_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
                                                       'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                                                       'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"}'
                                                       'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                                       'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                # Shelf Reel Tree

                self.shelf_reel_tree = QtWidgets.QTreeWidget(self.setup_window)
                self.shelf_reel_tree.setColumnCount(1)
                self.shelf_reel_tree.setHeaderLabel('Shelf Reel Template')
                self.shelf_reel_tree.itemsExpandable()
                self.shelf_reel_tree.setAlternatingRowColors(True)
                self.shelf_reel_tree.setFocusPolicy(QtCore.Qt.NoFocus)
                self.shelf_reel_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
                                                   'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                                                   'QTreeWidget:item:selected:active {color: #999999}'
                                                   'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"}'
                                                   'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                                   'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                # Fill trees

                fill_tree(self.schematic_reel_tree, self.schematic_reel_dict)
                fill_tree(self.shelf_reel_tree, self.shelf_reel_dict)

                # Set tree top level items

                batch_group_schematic_tree_top = self.schematic_reel_tree.topLevelItem(0)
                batch_group_shelf_tree_top = self.shelf_reel_tree.topLevelItem(0)

                # ------------------------------------------------------------- #

                # Push Buttons

                self.add_render_node_btn = FlamePushButton(' Add Render Node', self.add_render_node, self.setup_window.tab2)
                self.add_render_node_btn.clicked.connect(render_button_toggle)

                self.add_write_file_node_btn = FlamePushButton(' Add Write File Node', self.add_write_file_node, self.setup_window.tab2)
                self.add_write_file_node_btn.clicked.connect(write_file_button_toggle)

                # Buttons

                self.add_schematic_reel_btn = FlameButton('Add Schematic Reel', partial(add_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree), self.setup_window.tab2)
                self.del_schematic_reel_btn = FlameButton('Delete Schematic Reel', partial(del_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree), self.setup_window.tab2)

                self.add_shelf_reel_btn = FlameButton('Add Shelf Reel', partial(add_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree), self.setup_window.tab2)
                self.del_shelf_reel_btn = FlameButton('Delete Shelf Reel', partial(del_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree), self.setup_window.tab2)

                self.write_file_setup_btn = FlameButton('Write File Setup', write_file_node_setup, self.setup_window.tab2)
                if self.add_render_node:
                    self.write_file_setup_btn.setEnabled(False)

                setup_save_btn = FlameButton('Save', save_setup_settings, self.setup_window.tab2)
                setup_cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window.tab2)

                # Schematic reel tree contextual right click menus

                action_add_schematic_reel = QtWidgets.QAction('Add Reel', self.setup_window.tab2)
                action_add_schematic_reel.triggered.connect(partial(add_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree))
                self.schematic_reel_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                self.schematic_reel_tree.addAction(action_add_schematic_reel)

                action_delete_schematic_reel = QtWidgets.QAction('Delete Reel', self.setup_window.tab2)
                action_delete_schematic_reel.triggered.connect(partial(del_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree))
                self.schematic_reel_tree.addAction(action_delete_schematic_reel)

                # Shelf reel contextual right click menus

                action_add_shelf_reel = QtWidgets.QAction('Add Reel', self.setup_window.tab2)
                action_add_shelf_reel.triggered.connect(partial(add_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))
                self.shelf_reel_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                self.shelf_reel_tree.addAction(action_add_shelf_reel)

                action_delete_shelf_reel = QtWidgets.QAction('Delete Reel', self.setup_window.tab2)
                action_delete_shelf_reel.triggered.connect(partial(del_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))
                self.shelf_reel_tree.addAction(action_delete_shelf_reel)

                # Tab layout

                vbox03 = QtWidgets.QVBoxLayout()
                vbox03.addWidget(self.add_schematic_reel_btn)
                vbox03.addWidget(self.del_schematic_reel_btn)
                vbox03.addStretch(50)

                vbox04 = QtWidgets.QVBoxLayout()
                vbox04.addWidget(self.add_shelf_reel_btn)
                vbox04.addWidget(self.del_shelf_reel_btn)
                vbox04.addStretch(50)
                vbox04.addWidget(self.add_render_node_btn)
                vbox04.addWidget(self.add_write_file_node_btn)
                vbox04.addWidget(self.write_file_setup_btn)

                self.setup_window.tab2.layout = QtWidgets.QGridLayout()
                self.setup_window.tab2.layout.setMargin(10)
                self.setup_window.tab2.layout.setVerticalSpacing(5)
                self.setup_window.tab2.layout.setHorizontalSpacing(5)

                self.setup_window.tab2.layout.addWidget(self.batch_groups_label, 0, 0)
                self.setup_window.tab2.layout.addWidget(self.schematic_reel_tree, 1, 0)
                self.setup_window.tab2.layout.addWidget(self.shelf_reel_tree, 2, 0)
                self.setup_window.tab2.layout.addLayout(vbox03, 1, 1)
                self.setup_window.tab2.layout.addLayout(vbox04, 2, 1)

                self.setup_window.tab2.layout.addWidget(setup_save_btn, 4, 1)
                self.setup_window.tab2.layout.addWidget(setup_cancel_btn, 5, 1)

                self.setup_window.tab2.setLayout(self.setup_window.tab2.layout)

            def setup_desktop_tab():

                def del_reel_item(tree_top, tree):
                    '''
                    Delete Reel Group reels if number of reels is greater than four
                    '''

                    # Create list of exiting reels

                    existing_reels = []

                    iterator = QtWidgets.QTreeWidgetItemIterator(tree)
                    while iterator.value():
                        item = iterator.value()
                        existing_reel = item.text(0)
                        existing_reels.append(existing_reel)
                        iterator += 1

                    # Count number of reels in list

                    reel_count = len(existing_reels)
                    print ('reel_count: ', reel_count)

                    # Don't allow to delete reels if only 4 reels are left

                    if reel_count > 5:
                        # Delete reels

                        for item in tree.selectedItems():
                            (item.parent() or tree_top).removeChild(item)

                # Labels

                self.reel_group_label = FlameLabel('Desktop Reel Group Setup', 'background', self.setup_window)

                # Reel Group Tree

                self.reel_group_tree = QtWidgets.QTreeWidget(self.setup_window.tab3)
                self.reel_group_tree.move(230, 170)
                self.reel_group_tree.resize(250, 140)
                self.reel_group_tree.setColumnCount(1)
                self.reel_group_tree.setHeaderLabel('Reel Group Template')
                self.reel_group_tree.itemsExpandable()
                self.reel_group_tree.setAlternatingRowColors(True)
                # self.reel_group_tree.setFocusPolicy(QtCore.Qt.NoFocus)
                # self.reel_group_tree.setDragEnabled(True)
                # self.reel_group_tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
                self.reel_group_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
                                                   'QTreeWidget:disabled {color: #656565; background-color: #2a2a2a}'
                                                   'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                                                   'QTreeWidget:item:selected:active {color: #999999}'
                                                   'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"}'
                                                   'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                                   'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                # Fill trees

                fill_tree(self.reel_group_tree, self.reel_group_dict)

                # Set tree top level items

                reel_tree_top = self.reel_group_tree.topLevelItem(0)

                # Push Button

                def add_reel_group_button():
                    if self.add_reel_group_btn.isChecked():
                        self.reel_group_tree.setEnabled(True)
                        self.add_reel_btn.setEnabled(True)
                        self.del_reel_btn.setEnabled(True)
                    else:
                        self.reel_group_tree.setEnabled(False)
                        self.add_reel_btn.setEnabled(False)
                        self.del_reel_btn.setEnabled(False)

                self.add_reel_group_btn = FlamePushButton(' Add Reel Group', self.add_reel_group, self.setup_window.tab3)
                self.add_reel_group_btn.clicked.connect(add_reel_group_button)

                # Buttons

                self.add_reel_btn = FlameButton('Add Reel', partial(add_tree_item, reel_tree_top, self.reel_group_tree), self.setup_window.tab3)
                self.del_reel_btn = FlameButton('Delete Reel', partial(del_reel_item, reel_tree_top, self.reel_group_tree), self.setup_window.tab3)

                setup_save_btn = FlameButton('Save', save_setup_settings, self.setup_window.tab3)
                setup_cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window.tab3)

                # Tab layout

                vbox03 = QtWidgets.QVBoxLayout()
                vbox03.addWidget(self.add_reel_btn)
                vbox03.addWidget(self.del_reel_btn)
                vbox03.addStretch(50)

                self.setup_window.tab3.layout = QtWidgets.QGridLayout()
                self.setup_window.tab3.layout.setMargin(10)
                self.setup_window.tab3.layout.setVerticalSpacing(5)
                self.setup_window.tab3.layout.setHorizontalSpacing(5)

                self.setup_window.tab3.layout.addWidget(self.reel_group_label, 0, 0)
                self.setup_window.tab3.layout.addWidget(self.add_reel_group_btn, 0, 1)
                self.setup_window.tab3.layout.addWidget(self.reel_group_tree, 1, 0)
                self.setup_window.tab3.layout.addLayout(vbox03, 1, 1)

                self.setup_window.tab3.layout.addWidget(setup_save_btn, 4, 1)
                self.setup_window.tab3.layout.addWidget(setup_cancel_btn, 5, 1)

                self.setup_window.tab3.setLayout(self.setup_window.tab3.layout)

            # ------------------------------------------------------------- #

            def flame_version_check():

                # Disable adding file system folder setup options in versions older than 2021.2

                if self.flame_version < 2021.2:
                    self.file_system_folder_tree.setDisabled(True)
                    self.add_file_system_folder_btn.setDisabled(True)
                    self.delete_file_system_folder_btn.setDisabled(True)

            def fill_tree(tree_widget, tree_dict):

                def fill_item(item, value):

                    # Set top level item so name can not be changed except for reel group tree

                    if tree_widget == self.reel_group_tree or str(item.parent()) != 'None':
                        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled)
                    else:
                        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled)

                    item.setExpanded(True)

                    if type(value) is dict:
                        for key, val in sorted(iter(value.items())):
                            child = QtWidgets.QTreeWidgetItem()
                            # child.setText(0, unicode(key))
                            child.setText(0, key)

                            item.addChild(child)

                            fill_item(child, val)

                def fill_widget(widget, value):

                    widget.clear()
                    fill_item(widget.invisibleRootItem(), value)

                # Fill tree widget with dictionary

                fill_widget(tree_widget, tree_dict)

            def del_tree_item(tree_top, tree):

                def count_items(tree):

                    count = 0
                    iterator = QtWidgets.QTreeWidgetItemIterator(tree) # pass your treewidget as arg
                    while iterator.value():
                        item = iterator.value()

                        if item.parent():
                            if item.parent().isExpanded():
                                count += 1
                        else:
                            count += 1
                        iterator += 1
                    return count

                root = tree_top

                # Last item in tree should not be deleted

                if count_items(tree) > 2:

                    # Delete any tree widget items other than root item

                    for item in tree.selectedItems():
                        (item.parent() or root).removeChild(item)
                else:
                    return message_box('Template must have at least one folder/reel')

            def add_tree_item(tree_top, tree, new_item_num=0):

                # Get list of exisiting schematic reels for new reel numbering

                existing_item_names = []

                iterator = QtWidgets.QTreeWidgetItemIterator(tree)
                while iterator.value():
                    item = iterator.value()
                    existing_item = item.text(0)
                    print ('existing_item:', existing_item)
                    existing_item_names.append(existing_item)
                    iterator += 1
                print ('existing_item_names:', existing_item_names)

                # Set New Item name

                if tree in (self.folder_tree, self.file_system_folder_tree):
                    new_item_name = 'New Folder'
                elif tree == self.schematic_reel_tree:
                    new_item_name = 'New Schematic Reel'
                elif tree == self.shelf_reel_tree:
                    new_item_name = 'New Shelf Reel'
                elif tree == self.reel_group_tree:
                    new_item_name = 'New Reel'

                new_item = new_item_name + ' ' + str(new_item_num)

                if new_item == '%s 0' % new_item_name:
                    new_item = '%s' % new_item_name

                # Check if new item name exists, if it does add one to file name

                if new_item not in existing_item_names:

                    if tree in (self.schematic_reel_tree, self.shelf_reel_tree, self.reel_group_tree):

                        # Select Tree Top Item

                        tree.setCurrentItem(tree_top)

                    # Create new tree item

                    parent = tree.currentItem()

                    if tree in (self.folder_tree, self.file_system_folder_tree):

                        # Expand folder

                        tree.expandItem(parent)

                    item = QtWidgets.QTreeWidgetItem(parent)
                    item.setText(0, new_item)
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled)

                else:
                    # Add 1 to item name and try again

                    new_item_num += 1
                    add_tree_item(tree_top, tree, new_item_num)

            def save_setup_settings():

                def create_dict(tree):
                    '''
                    Convert tree's into dictionaries to save to config
                    '''

                    def get_items_recursively():

                        # Create empty list for all folder paths

                        self.path_list = []

                        # Iterate through folders to get paths through get_tree_path

                        def search_child_item(item=None):
                            if not item:
                                return
                            for m in range(item.childCount()):
                                child_item = item.child(m)
                                get_tree_path(child_item)
                                if not child_item:
                                    continue
                                search_child_item(child_item)

                        for i in range(tree.topLevelItemCount()):
                            item = tree.topLevelItem(i)
                            if not item:
                                continue
                            search_child_item(item)

                    def get_tree_path(item):

                        # Get path of each child item

                        path = []

                        while item is not None:
                            path.append(str(item.text(0)))
                            item = item.parent()
                        item_path = '/'.join(reversed(path))
                        self.path_list.append(item_path)

                    get_items_recursively()

                    # Create empty dictionary for paths

                    path_dict = {}

                    # Convert path list to dictionary

                    for path in self.path_list:
                        p = path_dict
                        for x in path.split('/'):
                            p = p.setdefault(x, {})

                    return path_dict

                # Save settings to config file

                edit_config = open(self.config_file, 'r')
                contents = edit_config.readlines()
                edit_config.close

                contents[12] = str(create_dict(self.folder_tree)) + '\n'
                contents[14] = str(create_dict(self.file_system_folder_tree)) + '\n'
                contents[16] = str(create_dict(self.schematic_reel_tree)) + '\n'
                contents[18] = str(create_dict(self.shelf_reel_tree)) + '\n'
                contents[20] = str(self.add_render_node_btn.isChecked()) + '\n'
                contents[22] = str(self.add_write_file_node_btn.isChecked()) + '\n'
                contents[42] = str(self.add_reel_group_btn.isChecked()) + '\n'
                contents[44] = str(create_dict(self.reel_group_tree)) + '\n'

                edit_config = open(self.config_file, 'w')
                contents = ''.join(contents)
                edit_config.write(contents)
                edit_config.close()

                print ('\n>>> new settings saved <<<\n')

                # Close setup window and reload settings

                self.setup_window.close()
                self.window.close()

                self.load_config_file()

                self.main_window()

            def render_button_toggle():
                if self.add_render_node_btn.isChecked():
                    self.add_write_file_node_btn.setChecked(False)
                    self.write_file_setup_btn.setDisabled(True)
                else:
                    self.add_write_file_node_btn.setChecked(True)
                    self.write_file_setup_btn.setDisabled(False)

            def write_file_button_toggle():
                if self.add_write_file_node_btn.isChecked():
                    self.add_render_node_btn.setChecked(False)
                    self.write_file_setup_btn.setDisabled(False)
                else:
                    self.add_render_node_btn.setChecked(True)
                    self.write_file_setup_btn.setDisabled(True)

            self.setup_window = QtWidgets.QTabWidget()
            self.setup_window.setMinimumSize(QtCore.QSize(600, 520))
            self.setup_window.setMaximumSize(QtCore.QSize(600, 520))
            self.setup_window.setWindowTitle('Create Shot Folders Setup %s' % VERSION)
            self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.setup_window.setStyleSheet('background-color: #212121')

            # Center window in linux

            resolution = QtWidgets.QDesktopWidget().screenGeometry()
            self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                                   (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

            self.setup_window.tab1 = QtWidgets.QWidget()
            self.setup_window.tab2 = QtWidgets.QWidget()
            self.setup_window.tab3 = QtWidgets.QWidget()

            self.setup_window.setStyleSheet('QTabWidget {background-color: #212121; font: 14px "Discreet"}'
                                            'QTabWidget::tab-bar {alignment: center}'
                                            'QTabBar::tab {color: #9a9a9a; background-color: #212121; border: 1px solid #3a3a3a; border-bottom-color: #555555; min-width: 20ex; padding: 5px}'
                                            'QTabBar::tab:selected {color: #bababa; border: 1px solid #555555; border-bottom: 1px solid #212121}'
                                            'QTabWidget::pane {border-top: 1px solid #555555; top: -0.05em}')

            self.setup_window.addTab(self.setup_window.tab1, 'Folders')
            self.setup_window.addTab(self.setup_window.tab2, 'Batch Groups')
            self.setup_window.addTab(self.setup_window.tab3, 'Desktops')

            setup_folder_tab()
            setup_batch_group_tab()
            setup_desktop_tab()

            flame_version_check()

            # Window Layout

            vbox = QtWidgets.QVBoxLayout()
            vbox.setMargin(15)

            vbox.addLayout(self.setup_window.tab1.layout)
            vbox.addLayout(self.setup_window.tab2.layout)
            vbox.addLayout(self.setup_window.tab3.layout)

            self.setup_window.setLayout(vbox)

            self.setup_window.show()

            return self.setup_window

        def write_file_node_setup():

            def media_path_browse():

                file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.window, 'Select Directory', self.write_file_media_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

                if os.path.isdir(file_path):
                    self.write_file_media_path_lineedit.setText(file_path)

            def save_write_file_config():

                def save_config():

                    # Save settings to config file

                    edit_config = open(self.config_file, 'r')
                    contents = edit_config.readlines()
                    edit_config.close

                    contents[24] = self.write_file_media_path_lineedit.text() + '\n'
                    contents[26] = self.write_file_pattern_lineedit.text() + '\n'
                    contents[28] = str(self.write_file_create_open_clip_btn.isChecked()) + '\n'
                    contents[30] = str(self.write_file_include_setup_btn.isChecked()) + '\n'
                    contents[32] = self.write_file_create_open_clip_lineedit.text() + '\n'
                    contents[34] = self.write_file_include_setup_lineedit.text() + '\n'
                    contents[36] = self.write_file_image_format_push_btn.text() + '\n'
                    contents[38] = self.write_file_padding_lineedit.text() + '\n'
                    contents[40] = self.write_file_frame_index_push_btn.text() + '\n'

                    edit_config = open(self.config_file, 'w')
                    contents = ''.join(contents)
                    edit_config.write(contents)
                    edit_config.close()

                    print ('\n>>> new settings saved <<<\n')

                    # Close setup window and reload settings

                    self.write_file_setup_window.close()

                    self.load_config_file()

                if self.write_file_media_path_lineedit.text() == '':
                    message_box('Enter Media Path')
                elif not os.path.isdir(self.write_file_media_path_lineedit.text()):
                    message_box('Enter Valid Media Path')
                elif self.write_file_pattern_lineedit.text() == '':
                    message_box('Enter Pattern for image files')
                elif self.write_file_create_open_clip_lineedit.text() == '':
                    message_box('Enter Create Open Clip Naming')
                elif self.write_file_include_setup_lineedit.text() == '':
                    message_box('Enter Include Setup Naming')
                else:
                    save_config()

            self.write_file_setup_window = QtWidgets.QWidget()
            self.write_file_setup_window.setMinimumSize(QtCore.QSize(1000, 400))
            self.write_file_setup_window.setMaximumSize(QtCore.QSize(1000, 400))
            self.write_file_setup_window.setWindowTitle('Shot Folder Creator Write File Node Setup %s' % VERSION)
            self.write_file_setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.write_file_setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.write_file_setup_window.setStyleSheet('background-color: #313131')

            # Center window in linux

            resolution = QtWidgets.QDesktopWidget().screenGeometry()
            self.write_file_setup_window.move((resolution.width() / 2) - (self.write_file_setup_window.frameSize().width() / 2),
                                              (resolution.height() / 2) - (self.write_file_setup_window.frameSize().height() / 2))

            # Labels

            self.write_file_setup_label = FlameLabel('Write File Node Setup', 'background', self.write_file_setup_window)
            self.write_file_media_path_label = FlameLabel('Media Path', 'normal', self.write_file_setup_window)
            self.write_file_pattern_label = FlameLabel('Pattern', 'normal', self.write_file_setup_window)
            self.write_file_type_label = FlameLabel('File Type', 'normal', self.write_file_setup_window)
            self.write_file_frame_index_label = FlameLabel('Frame Index', 'normal', self.write_file_setup_window)
            self.write_file_padding_label = FlameLabel('Padding', 'normal', self.write_file_setup_window)

            # LineEdits

            self.write_file_media_path_lineedit = FlameLineEdit(self.write_file_media_path, self.write_file_setup_window)
            self.write_file_pattern_lineedit = FlameLineEdit(self.write_file_pattern, self.write_file_setup_window)
            self.write_file_create_open_clip_lineedit = FlameLineEdit(self.write_file_create_open_clip_value, self.write_file_setup_window)
            self.write_file_include_setup_lineedit = FlameLineEdit(self.write_file_include_setup_value, self.write_file_setup_window)

            # Padding Slider

            self.write_file_padding_min_value = 1
            self.write_file_padding_max_value = 20
            self.write_file_padding_start_value = int(self.write_file_padding)

            def padding_set_slider():
                self.write_file_padding_slider.setValue(int(self.write_file_padding_lineedit.text()))

            self.write_file_padding_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.write_file_setup_window)
            self.write_file_padding_slider.setMaximumHeight(3)
            self.write_file_padding_slider.setMaximumWidth(150)
            self.write_file_padding_slider.setMinimum(self.write_file_padding_min_value)
            self.write_file_padding_slider.setMaximum(self.write_file_padding_max_value)
            self.write_file_padding_slider.setValue(self.write_file_padding_start_value)
            self.write_file_padding_slider.setStyleSheet('QSlider {color: #111111}'
                                                         'QSlider::groove:horizontal {background-color: #111111}'
                                                         'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.write_file_padding_slider.setDisabled(True)

            self.write_file_padding_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.write_file_padding_start_value, parent=self.write_file_setup_window)
            self.write_file_padding_lineedit.setMinimum(self.write_file_padding_min_value)
            self.write_file_padding_lineedit.setMaximum(self.write_file_padding_max_value)
            self.write_file_padding_lineedit.setMinimumHeight(28)
            self.write_file_padding_lineedit.setMaximumWidth(150)
            self.write_file_padding_lineedit.textChanged.connect(padding_set_slider)
            self.write_file_padding_slider.raise_()

            # Image Pushbutton Menu

            image_formats = ['Dpx 8-bit', 'Dpx 10-bit', 'Dpx 12-bit', 'Dpx 16-bit', 'Jpeg 8-bit', 'OpenEXR 16-bit fp', 'OpenEXR 32-bit fp',
                             'Sgi 8-bit', 'Sgi 16-bit', 'Targa 8-bit', 'Tiff 8-bit', 'Tiff 16-bit']
            self.write_file_image_format_push_btn = FlamePushButtonMenu(self.write_file_image_format, image_formats, self.write_file_setup_window)

            # Frame Index Pushbutton Menu

            frame_index = ['Use Start Frame', 'Use Timecode']
            self.write_file_frame_index_push_btn = FlamePushButtonMenu(self.write_file_frame_index, frame_index, self.write_file_setup_window)

            # Token Push Buttons

            write_file_token_dict = {'Batch Name': '<batch name>', 'Batch Iteration': '<batch iteration>', 'Iteration': '<iteration>',
                                     'Project': '<project>', 'Shot Name': '<shot name>', 'Clip Height': '<height>',
                                     'Clip Width': '<width>', 'Clip Name': '<name>', }

            self.write_file_pattern_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_pattern_lineedit, self.write_file_setup_window)
            self.write_file_open_clip_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_create_open_clip_lineedit, self.write_file_setup_window)
            self.write_file_include_setup_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_include_setup_lineedit, self.write_file_setup_window)

            # Pushbuttons

            def write_file_create_open_clip_btn_check():
                if self.write_file_create_open_clip_btn.isChecked():
                    self.write_file_create_open_clip_lineedit.setDisabled(False)
                    self.write_file_open_clip_token_btn.setDisabled(False)
                else:
                    self.write_file_create_open_clip_lineedit.setDisabled(True)
                    self.write_file_open_clip_token_btn.setDisabled(True)

            self.write_file_create_open_clip_btn = FlamePushButton('  Create Open Clip', self.write_file_create_open_clip, self.write_file_setup_window)
            self.write_file_create_open_clip_btn.clicked.connect(write_file_create_open_clip_btn_check)
            write_file_create_open_clip_btn_check()

            def write_file_include_setup_btn_check():
                if self.write_file_include_setup_btn.isChecked():
                    self.write_file_include_setup_lineedit.setDisabled(False)
                    self.write_file_include_setup_token_btn.setDisabled(False)
                else:
                    self.write_file_include_setup_lineedit.setDisabled(True)
                    self.write_file_include_setup_token_btn.setDisabled(True)

            self.write_file_include_setup_btn = FlamePushButton('  Include Setup', self.write_file_include_setup, self.write_file_setup_window)
            self.write_file_include_setup_btn.clicked.connect(write_file_include_setup_btn_check)
            write_file_include_setup_btn_check()

            # Buttons

            self.write_file_browse_btn = FlameButton('Browse', media_path_browse, self.write_file_setup_window)
            self.write_file_save_btn = FlameButton('Save', save_write_file_config, self.write_file_setup_window)
            self.write_file_cancel_btn = FlameButton('Cancel', self.write_file_setup_window.close, self.write_file_setup_window)

            # ------------------------------------------------------------- #

            # Window layout

            gridbox = QtWidgets.QGridLayout()
            gridbox.setMargin(20)
            gridbox.setVerticalSpacing(5)
            gridbox.setHorizontalSpacing(5)
            gridbox.setRowStretch(3, 2)
            gridbox.setRowStretch(6, 2)
            gridbox.setRowStretch(9, 2)

            gridbox.addWidget(self.write_file_setup_label, 0, 0, 1, 6)

            gridbox.addWidget(self.write_file_media_path_label, 1, 0)
            gridbox.addWidget(self.write_file_media_path_lineedit, 1, 1, 1, 4)
            gridbox.addWidget(self.write_file_browse_btn, 1, 5)

            gridbox.addWidget(self.write_file_pattern_label, 2, 0)
            gridbox.addWidget(self.write_file_pattern_lineedit, 2, 1, 1, 4)
            gridbox.addWidget(self.write_file_pattern_token_btn, 2, 5)

            gridbox.addWidget(self.write_file_create_open_clip_btn, 4, 0)
            gridbox.addWidget(self.write_file_create_open_clip_lineedit, 4, 1, 1, 4)
            gridbox.addWidget(self.write_file_open_clip_token_btn, 4, 5)

            gridbox.addWidget(self.write_file_include_setup_btn, 5, 0)
            gridbox.addWidget(self.write_file_include_setup_lineedit, 5, 1, 1, 4)
            gridbox.addWidget(self.write_file_include_setup_token_btn, 5, 5)

            gridbox.addWidget(self.write_file_type_label, 7, 0)
            gridbox.addWidget(self.write_file_image_format_push_btn, 7, 1)
            gridbox.addWidget(self.write_file_padding_label, 8, 0)
            gridbox.addWidget(self.write_file_padding_slider, 8, 1, QtCore.Qt.AlignBottom)
            gridbox.addWidget(self.write_file_padding_lineedit, 8, 1)

            gridbox.addWidget(self.write_file_frame_index_label, 7, 3)
            gridbox.addWidget(self.write_file_frame_index_push_btn, 7, 4)

            gridbox.addWidget(self.write_file_save_btn, 10, 5)
            gridbox.addWidget(self.write_file_cancel_btn, 11, 5)

            self.write_file_setup_window.setLayout(gridbox)

            self.write_file_setup_window.show()

        def ui_setup():

            if self.create_type == 'Shot Batch Groups':
                self.create_batch_groups_btn.setChecked(True)
                self.create_batch_groups_btn.setDisabled(True)
                self.create_desktops_btn.setChecked(False)
                self.create_desktops_btn.setDisabled(True)

        def cancel():

            self.window.close()
            try:
                self.setup_window.close()
            except:
                pass

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(900, 200))
        self.window.setMaximumSize(QtCore.QSize(1000, 300))
        self.window.setWindowTitle('Create Shot Folders %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.window.setStyleSheet('background-color: #212121')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.create_label = FlameLabel('Create %s' % self.create_type, 'background', self.window)
        self.shot_name_label = FlameLabel('Shot Name', 'normal', self.window)
        self.num_shots_label = FlameLabel('Number of Shots', 'normal', self.window)
        self.start_shot_num_label = FlameLabel('Starting Shot', 'normal', self.window)
        self.shot_increment_label = FlameLabel('Shot Increments', 'normal', self.window)

        # LineEdits

        self.shot_name_entry = FlameLineEdit(self.shot_naming, self.window)
        self.shot_name_entry.setToolTip("Shot name must contain <ShotNum####> Token. Shot number padding can be changed by changing the number of #'s in the token")

        # Number of Shots Slider

        self.num_of_shots_min_value = 1
        self.num_of_shots_max_value = 1000
        self.num_of_shots_start_value = self.num_of_shots

        def scale_spinbox_move_slider():
            self.num_of_shots_slider.setValue(int(self.num_of_shots_lineedit.text()))

        self.num_of_shots_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.num_of_shots_slider.setMaximumHeight(3)
        self.num_of_shots_slider.setMaximumWidth(75)
        self.num_of_shots_slider.setMinimum(self.num_of_shots_min_value)
        self.num_of_shots_slider.setMaximum(self.num_of_shots_max_value)
        self.num_of_shots_slider.setValue(self.num_of_shots_start_value)
        self.num_of_shots_slider.setStyleSheet('QSlider {color: #111111}'
                                               'QSlider::groove:horizontal {background-color: #111111}'
                                               'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
        self.num_of_shots_slider.setDisabled(True)

        self.num_of_shots_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.num_of_shots_start_value, parent=self.window)
        self.num_of_shots_lineedit.setMinimum(self.num_of_shots_min_value)
        self.num_of_shots_lineedit.setMaximum(self.num_of_shots_max_value)
        self.num_of_shots_lineedit.setMinimumHeight(28)
        self.num_of_shots_lineedit.setMaximumWidth(75)
        self.num_of_shots_lineedit.textChanged.connect(scale_spinbox_move_slider)
        self.num_of_shots_slider.raise_()

        # Start Shot Number Slider

        self.start_shot_num_min_value = 1
        self.start_shot_num_max_value = 1000
        self.start_shot_num_start_value = self.starting_shot

        def scale_spinbox_move_slider():
            self.start_shot_num_slider.setValue(int(self.start_shot_num_lineedit.text()))

        self.start_shot_num_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.start_shot_num_slider.setMaximumHeight(3)
        self.start_shot_num_slider.setMaximumWidth(75)
        self.start_shot_num_slider.setMinimum(self.start_shot_num_min_value)
        self.start_shot_num_slider.setMaximum(self.start_shot_num_max_value)
        self.start_shot_num_slider.setValue(self.start_shot_num_start_value)
        self.start_shot_num_slider.setStyleSheet('QSlider {color: #111111}'
                                                 'QSlider::groove:horizontal {background-color: #111111}'
                                                 'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
        self.start_shot_num_slider.setDisabled(True)

        self.start_shot_num_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.start_shot_num_start_value, parent=self.window)
        self.start_shot_num_lineedit.setMinimum(self.start_shot_num_min_value)
        self.start_shot_num_lineedit.setMaximum(self.start_shot_num_max_value)
        self.start_shot_num_lineedit.setMinimumHeight(28)
        self.start_shot_num_lineedit.setMaximumWidth(75)
        self.start_shot_num_lineedit.textChanged.connect(scale_spinbox_move_slider)
        self.start_shot_num_slider.raise_()

        # Shot Increment Slider

        self.shot_increment_min_value = 1
        self.shot_increment_max_value = 100
        self.shot_increment_start_value = self.shot_increments

        def scale_spinbox_move_slider():
            self.shot_increment_slider.setValue(int(self.shot_increment_lineedit.text()))

        self.shot_increment_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.shot_increment_slider.setMaximumHeight(3)
        self.shot_increment_slider.setMaximumWidth(75)
        self.shot_increment_slider.setMinimum(self.shot_increment_min_value)
        self.shot_increment_slider.setMaximum(self.shot_increment_max_value)
        self.shot_increment_slider.setValue(self.shot_increment_start_value)
        self.shot_increment_slider.setStyleSheet('QSlider {color: #111111}'
                                                 'QSlider::groove:horizontal {background-color: #111111}'
                                                 'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
        self.shot_increment_slider.setDisabled(True)

        self.shot_increment_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.shot_increment_start_value, parent=self.window)
        self.shot_increment_lineedit.setMinimum(self.shot_increment_min_value)
        self.shot_increment_lineedit.setMaximum(self.shot_increment_max_value)
        self.shot_increment_lineedit.setMinimumHeight(28)
        self.shot_increment_lineedit.setMaximumWidth(75)
        self.shot_increment_lineedit.textChanged.connect(scale_spinbox_move_slider)
        self.shot_increment_slider.raise_()

        # Token PushButton

        shot_num_dict = {'Shot Number': '<ShotNum####>'}
        self.shot_name_token_btn = FlameTokenPushButton('Add Token', shot_num_dict, self.shot_name_entry, self.window)

        # Pushbutton

        def create_desktops_toggle():

            # Turn off create batch groups button if create desktops is selected
            # Batch groups get created with desktops by default

            if self.create_desktops_btn.isChecked():
                self.create_batch_groups_btn.setChecked(True)
                self.create_batch_groups_btn.setDisabled(True)
            else:
                self.create_batch_groups_btn.setChecked(False)
                self.create_batch_groups_btn.setDisabled(False)

        self.create_desktops_btn = FlamePushButton(' Create Desktops', self.create_batch_groups, self.window)
        self.create_desktops_btn.clicked.connect(create_desktops_toggle)

        self.create_batch_groups_btn = FlamePushButton(' Create Batch Groups', self.create_batch_groups, self.window)

        # Check create desktops button

        create_desktops_toggle()

        # If creating file system folder, disable create desktops and create batch group buttons

        if self.create_type in ('File System Shot Folders', 'Shot Desktops'):
            self.create_desktops_btn.setDisabled(True)
            self.create_batch_groups_btn.setDisabled(True)

        # Buttons

        self.setup_btn = FlameButton('Setup', setup, self.window)
        self.create_btn = FlameButton('Create', self.create_from_ui, self.window)
        self.cancel_btn = FlameButton('Cancel', cancel, self.window)

        # ------------------------------------------------------------- #

        # Window layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setVerticalSpacing(5)
        gridbox.setHorizontalSpacing(5)

        gridbox.addWidget(self.create_label, 0, 1, 1, 5)

        gridbox.addWidget(self.shot_name_label, 1, 1)
        gridbox.addWidget(self.shot_name_entry, 1, 2, 1, 3)
        gridbox.addWidget(self.shot_name_token_btn, 1, 5)

        gridbox.addWidget(self.num_shots_label, 2, 1)
        gridbox.addWidget(self.num_of_shots_slider, 2, 2, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.num_of_shots_lineedit, 2, 2)

        gridbox.addWidget(self.start_shot_num_label, 3, 1)
        gridbox.addWidget(self.start_shot_num_slider, 3, 2, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.start_shot_num_lineedit, 3, 2)

        gridbox.addWidget(self.shot_increment_label, 4, 1)
        gridbox.addWidget(self.shot_increment_slider, 4, 2, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.shot_increment_lineedit, 4, 2)

        gridbox.addWidget(self.setup_btn, 0, 7)
        gridbox.addWidget(self.create_desktops_btn, 1, 7)
        gridbox.addWidget(self.create_batch_groups_btn, 2, 7)

        gridbox.addWidget(self.cancel_btn, 5, 6)
        gridbox.addWidget(self.create_btn, 5, 7)

        self.window.setLayout(gridbox)

        self.window.show()

        ui_setup()

# ------------------------------------- #

    def create_from_ui(self):
        import flame

        # Folders

        def create_media_panel_folders():

            self.create_library()

            if self.create_desktops_btn.isChecked():

                # Create copy of current desktop in temp library then clear out desktop

                copy_current_desktop()
                clear_current_desktop()

            for x in range(starting_shot, num_folders, shot_increments):

                def folder_loop(value, shot_folder):
                    for k, v in iter(value.items()):
                        folder = shot_folder.create_folder(k)
                        folder_loop(v, folder)

                # Create shot folders

                for key1, value1 in iter(self.folder_dict.items()):
                    self.shot_folder_name = re.sub('<ShotNum#*>', str(x).zfill(int(shot_padding.group(0).count('#'))), shot_name)
                    shot_folder = self.lib.create_folder(self.shot_folder_name)
                    folder_loop(value1, shot_folder)

                    if self.create_desktops_btn.isChecked():
                        build_shot_desktop(shot_folder)
                        clear_current_desktop()

                    elif self.create_batch_groups_btn.isChecked():
                        build_batch_group(shot_folder)

            if self.create_desktops_btn.isChecked():

                # Replace desktop with desktop saved in temp folder

                replace_desktop()

        def create_file_system_folders():

            for x in range(starting_shot, num_folders, shot_increments):

                def folder_loop(value, shot_folder):
                    for k, v in iter(value.items()):
                        folder = os.path.join(shot_folder, k)
                        os.makedirs(folder)
                        folder_loop(v, folder)

                # Create shot folders

                for key1, value1, in iter(self.file_system_folder_dict.items()):
                    shot_folder_name = re.sub('<ShotNum#*>', str(x).zfill(int(shot_padding.group(0).count('#'))), shot_name)
                    shot_folder = os.path.join(flame.mediahub.files.get_path(), shot_folder_name)

                    if not os.path.isdir(shot_folder):
                        os.makedirs(shot_folder)
                        folder_loop(value1, shot_folder)
                    else:
                        return message_box('Cannot create Folder. Folder already exists.')

                print ('\n>>> %s shot folder created <<<\n' % shot_folder_name)

            flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

        # Batch groups

        def create_shot_batch_group():

            self.create_library()

            for x in range(starting_shot, num_folders, shot_increments):
                self.shot_folder_name = re.sub('<ShotNum#*>', str(x).zfill(int(shot_padding.group(0).count('#'))), shot_name)
                build_batch_group(self.lib)

        def build_batch_group(destination):

            # Create batch group

            self.batch_group = flame.batch.create_batch_group(self.shot_folder_name,
                                                              duration=100,
                                                              reels=self.schematic_reels,
                                                              shelf_reels=self.shelf_reels)

            # Force batch group name in case duplicate name already exists in desktop

            self.batch_group.name = self.shot_folder_name

            # Add Render or Write File node to batch group

            if self.add_render_node:
                flame.batch.create_node('Render')
            else:

                image_format = self.write_file_image_format.split(' ', 1)[0]
                bit_depth = self.write_file_image_format.split(' ', 1)[1]
                # print ('image_format:', image_format)
                # print ('bit_depth:', bit_depth)

                write_node = flame.batch.create_node('Write File')
                write_node.media_path = self.write_file_media_path
                write_node.media_path_pattern = self.write_file_media_path
                write_node.create_clip = self.write_file_create_open_clip
                write_node.include_setup = self.write_file_include_setup
                write_node.create_clip_path = self.write_file_create_open_clip_value
                write_node.include_setup_path = self.write_file_include_setup_value
                write_node.file_type = image_format
                write_node.bit_depth = bit_depth
                write_node.frame_index_mode = self.write_file_frame_index
                write_node.frame_padding = int(self.write_file_padding)

                if self.write_file_create_open_clip:
                    write_node.version_mode = 'Follow Iteration'
                    write_node.version_name = 'v<version>'
                    write_node.version_padding = 2

            # Move batch group from desktop to destination

            flame.media_panel.move(self.batch_group, destination)

        # Desktops

        def copy_current_desktop():

            # Copy current desktop to Temp Library

            self.temp_lib = self.ws.create_library('Temp__Desk__Lib')

            self.desktop_name = str(self.desktop.name)[1:-1]
            print (self.desktop_name)

            self.desktop_copy = flame.media_panel.copy(self.desktop, self.temp_lib)
            print (self.desktop_copy)

        def clear_current_desktop():

            # Clear out current desktop

            for b in self.desktop.batch_groups:
                flame.delete(b)
            for r in self.desktop.reel_groups:
                flame.delete(r)

        def replace_desktop():

            # When done creating shot desktops replace original desktop from Temp Library

            flame.media_panel.move(self.desktop_copy, self.ws.desktop)
            flame.delete(self.desktop.batch_groups[0])
            self.ws.desktop.name = self.desktop_name
            flame.delete(self.temp_lib)

        def build_shot_desktop(destination):

            def build_reel_group():

                # Create reel group

                reel_group = self.ws.desktop.create_reel_group(str(self.reel_group_dict).split("'", 2)[1])

                # Create extra reels in group past four

                for x in range(len(self.reel_group) - 4):
                    reel_group.create_reel('')

                for reel in reel_group.reels:
                    reel.name = self.reel_group[reel_group.reels.index(reel)]

            build_batch_group(self.desktop)
            self.desktop.name = self.shot_folder_name

            # Create reel group

            if self.add_reel_group:
                build_reel_group()

            #  Remove old batch group

            flame.delete(self.desktop.batch_groups[0])

            # Copy desktop to Destination

            flame.media_panel.copy(self.desktop, destination)

        def create_desktops():

            # Create new desktop library

            self.create_library()

            # Create copy of current desktop in temp library then clear out desktop

            copy_current_desktop()
            clear_current_desktop()

            for x in range(starting_shot, num_folders, shot_increments):

                # Create shot batch group in shot desktop

                self.shot_folder_name = re.sub('<ShotNum#*>', str(x).zfill(int(shot_padding.group(0).count('#'))), shot_name)

                build_shot_desktop(self.lib)
                clear_current_desktop()

            # Replace desktop with desktop saved in temp folder

            replace_desktop()

        # Save settings

        self.save_settings()

        # Warn if shot name field empty

        if self.shot_name_entry.text() == '':
            return message_box('Enter shot naming')

        # Get shot name value

        shot_name = str(self.shot_name_entry.text())

        # Warn if shot num token not found

        if re.search('<ShotNum#*>', shot_name) == None:
            return message_box('Shot naming must include Shot Number token')

        else:
            # Create folders

            # Get values from UI

            shot_padding = re.search('<ShotNum#*>', shot_name)
            num_of_shots = int(self.num_of_shots_lineedit.text())
            starting_shot = int(self.start_shot_num_lineedit.text())
            shot_increments = int(self.shot_increment_lineedit.text())
            num_folders = num_of_shots * shot_increments + starting_shot

            # Switch to batch tab if MediaHub tab is open. MediaPanel cannot be accessed from MediaHub tab

            if self.create_type != 'File System Shot Folders' and self.current_flame_tab == 'MediaHub':
                flame.set_current_tab('batch')

            # Create folders, batch groups, or desktops

            if self.create_type == 'Shot Folders':

                create_media_panel_folders()

                print ('\n>>> new shot folders created <<<\n')

            elif self.create_type == 'File System Shot Folders':

                try:
                    create_file_system_folders()
                except:
                    return message_box('Shot folders can not be created in selected destination')

            elif self.create_type == 'Shot Batch Groups':

                create_shot_batch_group()

                print ('\n>>> new shot folders created <<<\n')

            elif self.create_type == 'Shot Desktops':

                create_desktops()

                print ('\n>>> new shot desktops created <<<\n')

            print ('done.')

            # Close window

            self.window.close()

    def create_library(self):

        # Create new library

        self.lib = self.ws.create_library('New %s' % self.create_type)
        self.lib.expanded = True

    def save_settings(self):

        # Save settings to config file

        edit_config = open(self.config_file, 'r')
        contents = edit_config.readlines()
        edit_config.close

        contents[2] = self.shot_name_entry.text() + '\n'
        contents[4] = self.num_of_shots_lineedit.text() + '\n'
        contents[6] = self.start_shot_num_lineedit.text() + '\n'
        contents[8] = self.shot_increment_lineedit.text() + '\n'
        contents[10] = str(self.create_batch_groups_btn.isChecked()) + '\n'

        edit_config = open(self.config_file, 'w')
        contents = ''.join(contents)
        edit_config.write(contents)
        edit_config.close()

        print ('\n>>> settings saved <<<\n')

# ------------------------------------- #

def message_box(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setMinimumSize(400, 100)
    msg_box.setText(message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131}'
                          'QLabel {color: #9a9a9a; font: 14pt "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

#-------------------------------------#

def shot_folders(selection):

    script = CreateShotFolders(selection, 'Shot Folders')
    script.main_window()

def file_system_shot_folders(selection):

    script = CreateShotFolders(selection, 'File System Shot Folders')
    script.main_window()

def batch_groups(selection):

    script = CreateShotFolders(selection, 'Shot Batch Groups')
    script.main_window()

def desktops(selection):

    script = CreateShotFolders(selection, 'Shot Desktops')
    script.main_window()

#-------------------------------------#

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Create Shot Folders...',
            'actions': [
                {
                    'name': 'Create File System Shot Folders',
                    'execute': file_system_shot_folders,
                    'minimumVersion': '2021.2'
                }
            ]
        }
    ]

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Create Shot...',
            'actions': [
                {
                    'name': 'Create Shot Folders',
                    'execute': shot_folders,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Create Shot Batch Groups',
                    'execute': batch_groups,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Create Shot Desktops',
                    'execute': desktops,
                    'minimumVersion': '2021.1'
                }
            ]
        }
    ]
