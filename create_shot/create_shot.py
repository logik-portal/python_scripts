'''
Script Name: Create Shot
Script Version: 4.1
Flame Version: 2021.2
Written by: Michael Vaglienty
Creation Date: 06.09.18
Update Date: 08.28.21

Custom Action Type: Media Panel / Media Hub

Description:

    Create shot folders, batch groups, desktops, and system folders.

    Structures of the shot folders, batch groups, desktops, and system folders can all be customized
    in Create Shot Setup.

    Menus:

        Flame Main Menu

            Flame Main Menu -> pyFlame -> Create Shot Setup

        Media Panel:

            Right-click anywhere in Media Panel -> Create Shot... -> Folders
            Right-click on selected clips in Media Panel -> Create Shot... -> Custom Shots
            Right-click on selected clips in Media Panel -> Create Shot... -> Clips to Shot - Shot Name
            Right-click on selected clips in Media Panel -> Create Shot... -> Clips to Shot - Shot Name - All Clips / One Shot
            Right-click on selected clips in Media Panel -> Create Shot... -> Clips to Shot - Clip Name
            Right-click on selected clips in Media Panel -> Create Shot... -> Clips to Shot - Clip Name - All Clips / One Shot

        Media Hub Files:

            Right-click anywhere in Media Hub Files -> Create Shot... -> Folders
            Right-click on selected files in Media Hub Files -> Create Shot... -> Import to Shot - Shot Name
            Right-click on selected files in Media Hub Files -> Create Shot... -> Import to Shot - Shot Name - All Clips / One Batch
            Right-click on selected files in Media Hub Files -> Create Shot... -> Import to Shot - Clip Name
            Right-click on selected files in Media Hub Files -> Create Shot... -> Import to Shot - Clip Name - All Clips / One Batch

To install:

    Copy script into /opt/Autodesk/shared/python/create_shot

Updates:

    v4.1 08.19.21

        Major rewrite / Merged Shot Folder Creator script with Clip to Batch Group script.

        Config file now in xml format

        Added help button

        Added ability to create shots by selecting clips in Media Panel or Media Hub. Selected clips will be added to folders and
        batch groups.

        Settings are applied globally through settings in Setup. Custom settings can be applied through Custom Shots menu when
        right clicking on clips

        Shots can now be created by selecting clips in Media Panel or Media Hub file view.

        Batch templates can be applied when creating shot batch groups

        Added compression options to write node format option in the write node setup window

        Shot name is now added to render/write node

        Destination for newly created batch groups can now be set when only creating batch groups. Destination can be current
        desktop or a new library

        Folders, Schematic/Shelf/Reel Group reels will not automatically sort when being created. A button has been added to the setup
        menu to manually apply sorting.

        Destination folders and schematic reels can be set for clips in the Setup window using either the Set Clip Dest button or by
        right-clicking on a folder or schematic reel.

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
import os, re, ast, webbrowser
from functools import partial
import xml.etree.ElementTree as ET
from PySide2 import QtWidgets, QtCore, QtGui

VERSION = 'v4.1'

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

class FlameLineEditFileBrowse(QtWidgets.QLineEdit):
    """
    Custom Qt Flame Clickable Line Edit Widget with File Browser

    To use:

    lineedit = FlameLineEditFileBrowse('some_path', 'Python (*.py)', window)

    file_path: Path browser will open to. If set to root folder (/), browser will open to user home directory
    filter_type: Type of file browser will filter_type for. If set to 'dir', browser will select directory
    """

    clicked = QtCore.Signal()

    def __init__(self, file_path, filter_type, parent, *args, **kwargs):
        super(FlameLineEditFileBrowse, self).__init__(*args, **kwargs)

        self.filter_type = filter_type
        self.file_path = file_path

        self.setText(file_path)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setReadOnly(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(self.file_browse)
        self.setStyleSheet('QLineEdit {color: #898989; background-color: #373e47; font: 14px "Discreet"}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.setStyleSheet('QLineEdit {color: #bbbbbb; background-color: #474e58; font: 14px "Discreet"}'
                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
            self.clicked.emit()
            self.setStyleSheet('QLineEdit {color: #898989; background-color: #373e47; font: 14px "Discreet"}'
                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
        else:
            super().mousePressEvent(event)

    def file_browse(self):
        from PySide2 import QtWidgets

        file_browser = QtWidgets.QFileDialog()

        # If no path go to user home directory

        if self.file_path == '/':
            self.file_path = os.path.expanduser("~")
        if os.path.isfile(self.file_path):
            self.file_path = self.file_path.rsplit('/', 1)[0]

        file_browser.setDirectory(self.file_path)

        # If filter_type set to dir, open Directory Browser, if anything else, open File Browser

        if self.filter_type == 'dir':
            file_browser.setFileMode(QtWidgets.QFileDialog.Directory)
            if file_browser.exec_():
                self.setText(file_browser.selectedFiles()[0])
        else:
            file_browser.setFileMode(QtWidgets.QFileDialog.ExistingFile) # Change to ExistingFiles to capture many files
            file_browser.setNameFilter(self.filter_type)
            if file_browser.exec_():
                self.setText(file_browser.selectedFiles()[0])

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

class CustomSpinBox(QtWidgets.QLineEdit):

    IntSpinBox = 0
    DoubleSpinBox = 1

    def __init__(self, spinbox_type, value, parent=None):

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
        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')
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

            if calc_lineedit.text():
                calc_lineedit.setText(str(float(calc_lineedit.text()) * -1))

        def add_sub(key):

            if calc_lineedit.text() == '':
                calc_lineedit.setText('0')

            if '**' not in calc_lineedit.text():
                try:
                    calc_num = eval(calc_lineedit.text().lstrip('0'))

                    calc_lineedit.setText(str(calc_num))

                    calc_num = float(calc_lineedit.text())

                    if calc_num == 0:
                        calc_num = 1
                    if key == 'add':
                        self.setValue(float(self.text()) + float(calc_num))
                    else:
                        self.setValue(float(self.text()) - float(calc_num))

                    self.clean_line = True
                except:
                    pass

        def enter():

            if self.clean_line == True:
                return calc_window.close()

            if calc_lineedit.text():
                try:

                    # If only single number set slider value to that number

                    self.setValue(float(calc_lineedit.text()))
                except:

                    # Do math

                    new_value = calculate_entry()
                    self.setValue(float(new_value))

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
                        calc = float(self.text()) + eval(calc_line[-1:])
                    elif calc_line.startswith('-'):
                        calc = float(self.text()) - eval(calc_line[-1:])
                    elif calc_line.startswith('*'):
                        calc = float(self.text()) * eval(calc_line[-1:])
                    elif calc_line.startswith('/'):
                        calc = float(self.text()) / eval(calc_line[-1:])
                    else:
                        calc = eval(calc_line)
                except:
                    calc = 0
            else:
                calc = 1

            calc_lineedit.setText(str(float(calc)))

            return calc

        def close_calc():
            calc_window.close()
            self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"')

        def revert_color():
            self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"')

        calc_version = '1.1'
        self.clean_line = False

        calc_window = QtWidgets.QWidget()
        calc_window.setMinimumSize(QtCore.QSize(210, 280))
        calc_window.setMaximumSize(QtCore.QSize(210, 280))
        calc_window.setWindowTitle('pyFlame Calc %s' % calc_version)
        calc_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
        calc_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        calc_window.destroyed.connect(revert_color)
        calc_window.move(QtGui.QCursor.pos().x() - 110, QtGui.QCursor.pos().y() - 290)
        calc_window.setStyleSheet('background-color: #282828')

        # Labels

        calc_label = QtWidgets.QLabel('Calculator', calc_window)
        calc_label.setAlignment(QtCore.Qt.AlignCenter)
        calc_label.setMinimumHeight(28)
        calc_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')

        #  LineEdit

        calc_lineedit = QtWidgets.QLineEdit('', calc_window)
        calc_lineedit.setMinimumHeight(28)
        calc_lineedit.setFocus()
        calc_lineedit.returnPressed.connect(enter)
        calc_lineedit.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}')

        # Limit characters that can be entered into lineedit

        regex = QtCore.QRegExp('[0-9_,=,/,*,+,\-,.]+')
        validator = QtGui.QRegExpValidator(regex)
        calc_lineedit.setValidator(validator)

        # Buttons

        def calc_null():
            # For blank button - this does nothing
            pass

        class FlameButton(QtWidgets.QPushButton):
            """
            Custom Qt Flame Button Widget
            """

            def __init__(self, button_name, size_x, size_y, connect, parent, *args, **kwargs):
                super(FlameButton, self).__init__(*args, **kwargs)

                self.setText(button_name)
                self.setParent(parent)
                self.setMinimumSize(size_x, size_y)
                self.setMaximumSize(size_x, size_y)
                self.setFocusPolicy(QtCore.Qt.NoFocus)
                self.clicked.connect(connect)
                self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                   'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                                   'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        blank_btn = FlameButton('', 40, 28, calc_null, calc_window)
        blank_btn.setDisabled(True)
        plus_minus_btn = FlameButton('+/-', 40, 28, plus_minus, calc_window)
        plus_minus_btn.setStyleSheet('color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"')
        add_btn = FlameButton('Add', 40, 28, (partial(add_sub, 'add')), calc_window)
        sub_btn = FlameButton('Sub', 40, 28, (partial(add_sub, 'sub')), calc_window)

        #  --------------------------------------- #

        clear_btn = FlameButton('C', 40, 28, clear, calc_window)
        equal_btn = FlameButton('=', 40, 28, equals, calc_window)
        div_btn = FlameButton('/', 40, 28, (partial(button_press, '/')), calc_window)
        mult_btn = FlameButton('/', 40, 28, (partial(button_press, '*')), calc_window)

        #  --------------------------------------- #

        _7_btn = FlameButton('7', 40, 28, (partial(button_press, '7')), calc_window)
        _8_btn = FlameButton('8', 40, 28, (partial(button_press, '8')), calc_window)
        _9_btn = FlameButton('9', 40, 28, (partial(button_press, '9')), calc_window)
        minus_btn = FlameButton('-', 40, 28, (partial(button_press, '-')), calc_window)

        #  --------------------------------------- #

        _4_btn = FlameButton('4', 40, 28, (partial(button_press, '4')), calc_window)
        _5_btn = FlameButton('5', 40, 28, (partial(button_press, '5')), calc_window)
        _6_btn = FlameButton('6', 40, 28, (partial(button_press, '6')), calc_window)
        plus_btn = FlameButton('+', 40, 28, (partial(button_press, '+')), calc_window)

        #  --------------------------------------- #

        _1_btn = FlameButton('1', 40, 28, (partial(button_press, '1')), calc_window)
        _2_btn = FlameButton('2', 40, 28, (partial(button_press, '2')), calc_window)
        _3_btn = FlameButton('3', 40, 28, (partial(button_press, '3')), calc_window)
        enter_btn = FlameButton('Enter', 40, 61, enter, calc_window)

        #  --------------------------------------- #

        _0_btn = FlameButton('0', 80, 28, (partial(button_press, '0')), calc_window)
        point_btn = FlameButton('.', 40, 28, (partial(button_press, '.')), calc_window)

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

# ------------------------------------- #

class CreateShotFolders(object):

    def __init__(self, selection):
        import flame

        print ('''
   _____                _          _____ _           _
  / ____|              | |        / ____| |         | |
 | |     _ __ ___  __ _| |_ ___  | (___ | |__   ___ | |_
 | |    | '__/ _ \/ _` | __/ _ \  \___ \| '_ \ / _ \| __|
 | |____| | |  __/ (_| | ||  __/  ____) | | | | (_) | |_
  \_____|_|  \___|\__,_|\__\___| |_____/|_| |_|\___/ \__|
 ''')

        print ('>' * 20, 'create shot %s' % VERSION, '<' * 20, '\n')

        self.selection = selection

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Load config file

        self.config()

        # Get flame variables

        self.ws = flame.projects.current_project.current_workspace
        self.desktop = self.ws.desktop
        self.current_flame_tab = flame.get_current_tab()

        self.project_name = flame.projects.current_project.name
        self.project_nick_name = flame.projects.current_project.nickname

        # Get flame version

        self.flame_version = flame.get_version()

        if 'pr' in self.flame_version:
            self.flame_version = self.flame_version.rsplit('.pr', 1)[0]
        if self.flame_version.count('.') > 1:
            self.flame_version = self.flame_version.rsplit('.', 1)[0]
        self.flame_version = float(self.flame_version)
        print ('flame_version:', self.flame_version, '\n')

        self.reel_group_tree = ''
        self.shot_folder_name = ''
        self.batch_group = ''
        self.lib = ''

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get UI settings

            for setting in root.iter('create_shot_ui_settings'):

                self.shot_naming = setting.find('shot_naming').text
                self.num_of_shots = int(setting.find('number_of_shots').text)
                self.starting_shot = int(setting.find('starting_shot').text)
                self.shot_increments = int(setting.find('shot_increments').text)
                self.create_custom_folders = ast.literal_eval(setting.find('create_folders').text)
                self.create_custom_batch_groups = ast.literal_eval(setting.find('create_batch_groups').text)
                self.create_custom_desktops = ast.literal_eval(setting.find('create_desktops').text)
                self.create_custom_system_folders = ast.literal_eval(setting.find('create_system_folders').text)

            # Get Setup settings

            for setup_setting in root.iter('setup'):
                self.folder_dict = ast.literal_eval(setup_setting.find('shot_folders').text)
                self.file_system_folder_dict = ast.literal_eval(setup_setting.find('file_system_folders').text)
                self.schematic_reel_dict = ast.literal_eval(setup_setting.find('schematic_reels').text)
                self.shelf_reel_dict = ast.literal_eval(setup_setting.find('shelf_reels').text)
                self.reel_group_dict = ast.literal_eval(setup_setting.find('reel_group_reels').text)

                self.add_reel_group = ast.literal_eval(setup_setting.find('add_reel_group').text)
                self.add_render_node = ast.literal_eval(setup_setting.find('add_render_node').text)
                self.add_write_file_node = ast.literal_eval(setup_setting.find('add_write_node').text)

                self.write_file_media_path = setup_setting.find('write_file_media_path').text
                self.write_file_pattern = setup_setting.find('write_file_pattern').text
                self.write_file_create_open_clip = ast.literal_eval(setup_setting.find('write_file_create_open_clip').text)
                self.write_file_include_setup = ast.literal_eval(setup_setting.find('write_file_include_setup').text)
                self.write_file_create_open_clip_value = setup_setting.find('write_file_create_open_clip_value').text
                self.write_file_include_setup_value = setup_setting.find('write_file_include_setup_value').text
                self.write_file_image_format = setup_setting.find('write_file_image_format').text
                self.write_file_compression = setup_setting.find('write_file_compression').text
                self.write_file_padding = setup_setting.find('write_file_padding').text
                self.write_file_frame_index = setup_setting.find('write_file_frame_index').text

                self.create_shot_type_folders = ast.literal_eval(setup_setting.find('create_shot_type_folders').text)
                self.create_shot_type_batch_group = ast.literal_eval(setup_setting.find('create_shot_type_batch_group').text)
                self.create_shot_type_desktop = ast.literal_eval(setup_setting.find('create_shot_type_desktop').text)
                self.create_shot_type_system_folders = ast.literal_eval(setup_setting.find('create_shot_type_system_folders').text)
                self.system_shot_folders_path = setup_setting.find('system_shot_folders_path').text
                self.clip_dest_folder = setup_setting.find('clip_destination_folder').text
                self.clip_dest_reel = setup_setting.find('clip_destination_reel').text
                self.apply_batch_template = ast.literal_eval(setup_setting.find('setup_batch_template').text)
                self.batch_template_path = setup_setting.find('setup_batch_template_path').text
                self.batch_group_dest = setup_setting.find('setup_batch_group_dest').text
                self.batch_start_frame = int(setup_setting.find('setup_batch_start_frame').text)
                self.batch_additional_naming = setup_setting.find('setup_batch_additional_naming').text

            # Settings for Custom Shot from Selected clips UI

            for setup_setting in root.iter('custom_ui'):
                self.all_clips = ast.literal_eval(setup_setting.find('all_clips').text)
                self.shot_name = ast.literal_eval(setup_setting.find('shot_name').text)
                self.clip_name = ast.literal_eval(setup_setting.find('clip_name').text)
                self.custom_folders = ast.literal_eval(setup_setting.find('custom_folders').text)
                self.custom_batch_group = ast.literal_eval(setup_setting.find('custom_batch_group').text)
                self.custom_desktop = ast.literal_eval(setup_setting.find('custom_desktop').text)
                self.custom_system_folders = ast.literal_eval(setup_setting.find('custom_system_folders').text)
                self.custom_system_folders_path = setup_setting.find('custom_system_folders_path').text
                self.custom_apply_batch_template = ast.literal_eval(setup_setting.find('custom_apply_batch_template').text)
                self.custom_batch_template_path = setup_setting.find('custom_batch_template_path').text
                self.custom_batch_group_dest = setup_setting.find('custom_batch_group_dest').text
                self.custom_batch_start_frame = int(setup_setting.find('custom_batch_start_frame').text)
                self.custom_batch_additional_naming = setup_setting.find('custom_batch_additional_naming').text

            # Convert reel dictionaries to lists

            self.schematic_reels = self.convert_reel_dict(self.schematic_reel_dict)
            self.shelf_reels = self.convert_reel_dict(self.shelf_reel_dict)
            self.reel_group = self.convert_reel_dict(self.reel_group_dict)

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
    <create_shot_ui_settings>
        <shot_naming>PYT_&lt;ShotNum####&gt;</shot_naming>
        <number_of_shots>10</number_of_shots>
        <starting_shot>10</starting_shot>
        <shot_increments>10</shot_increments>
        <create_folders>True</create_folders>
        <create_batch_groups>False</create_batch_groups>
        <create_desktops>False</create_desktops>
        <create_system_folders>False</create_system_folders>
    </create_shot_ui_settings>
    <setup>
        <shot_folders>{'Shot_Folder': {'Elements': {}, 'Plates': {}, 'Ref': {}, 'Renders': {}}}</shot_folders>
        <file_system_folders>{'Shot_Folder': {'Elements': {}, 'Plates': {}, 'Ref': {}, 'Renders': {}}}</file_system_folders>
        <schematic_reels>{'Schematic Reels': {'Plates': {}, 'PreRenders': {}, 'Elements': {}, 'Ref': {}}}</schematic_reels>
        <shelf_reels>{'Shelf Reels': {'Batch Renders': {}}}</shelf_reels>
        <reel_group_reels>{'Reels': {'Reel 1': {}, 'Reel 2': {}, 'Reel 3': {}, 'Reel 4': {}}}</reel_group_reels>
        <add_reel_group>True</add_reel_group>
        <add_render_node>True</add_render_node>
        <add_write_node>False</add_write_node>
        <write_file_media_path>/opt/Autodesk</write_file_media_path>
        <write_file_pattern>&lt;name&gt;</write_file_pattern>
        <write_file_create_open_clip>True</write_file_create_open_clip>
        <write_file_include_setup>True</write_file_include_setup>
        <write_file_create_open_clip_value>&lt;name&gt;</write_file_create_open_clip_value>
        <write_file_include_setup_value>&lt;name&gt;</write_file_include_setup_value>
        <write_file_image_format>Dpx 10-bit</write_file_image_format>
        <write_file_compression>Uncompressed</write_file_compression>
        <write_file_padding>4</write_file_padding>
        <write_file_frame_index>Use Start Frame</write_file_frame_index>
        <create_shot_type_folders>True</create_shot_type_folders>
        <create_shot_type_batch_group>False</create_shot_type_batch_group>
        <create_shot_type_desktop>False</create_shot_type_desktop>
        <create_shot_type_system_folders>False</create_shot_type_system_folders>
        <system_shot_folders_path>/opt/Autodesk</system_shot_folders_path>
        <clip_destination_folder>Plates</clip_destination_folder>
        <clip_destination_reel>Plates</clip_destination_reel>
        <setup_batch_template>False</setup_batch_template>
        <setup_batch_template_path>/opt/Autodesk</setup_batch_template_path>
        <setup_batch_group_dest>Desktop</setup_batch_group_dest>
        <setup_batch_start_frame>1</setup_batch_start_frame>
        <setup_batch_additional_naming>_comp</setup_batch_additional_naming>
    </setup>
    <custom_ui>
        <all_clips>False</all_clips>
        <shot_name>True</shot_name>
        <clip_name>False</clip_name>
        <custom_folders>True</custom_folders>
        <custom_batch_group>False</custom_batch_group>
        <custom_desktop>False</custom_desktop>
        <custom_system_folders>False</custom_system_folders>
        <custom_system_folders_path>/opt/Autodesk</custom_system_folders_path>
        <custom_apply_batch_template>False</custom_apply_batch_template>
        <custom_batch_template_path>/opt/Autodesk</custom_batch_template_path>
        <custom_batch_start_frame>1</custom_batch_start_frame>
        <custom_batch_additional_naming>_comp</custom_batch_additional_naming>
        <custom_batch_group_dest>Desktop</custom_batch_group_dest>
    </custom_ui>
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

    # ------------------------------------- #
    # Windows

    def create_shot_folder_window(self):

        def create_shot_list():

            def save_settings():

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                shot_naming = root.find('.//shot_naming')
                shot_naming.text = self.shot_name_entry.text()
                num_of_shots = root.find('.//number_of_shots')
                num_of_shots.text = self.num_of_shots_lineedit.text()
                starting_shot = root.find('.//starting_shot')
                starting_shot.text = self.start_shot_num_lineedit.text()
                shot_increments = root.find('.//shot_increments')
                shot_increments.text = self.shot_increment_lineedit.text()
                create_folders = root.find('.//create_folders')
                create_folders.text = str(self.create_folders_btn.isChecked())
                create_system_folders = root.find('.//create_system_folders')
                create_system_folders.text = str(self.create_system_folders_btn.isChecked())

                xml_tree.write(self.config_xml)

                print ('>>> settings saved <<<\n')

            # Check that at least on shot creation type is selection

            if not any ([self.create_folders_btn.isChecked(), self.create_system_folders_btn.isChecked()]):
                return message_box('Select shot type to create')

            # Clear selection

            self.selection = ''

            # Save settings

            save_settings()

            # Warn if shot name field empty

            if self.shot_name_entry.text() == '':
                return message_box('Enter shot naming')

            # Get values from UI

            shot_name_string = str(self.shot_name_entry.text())
            shot_padding = re.search('<ShotNum#*>', shot_name_string)
            num_of_shots = int(self.num_of_shots_lineedit.text())
            starting_shot = int(self.start_shot_num_lineedit.text())
            shot_increments = int(self.shot_increment_lineedit.text())
            num_folders = num_of_shots * shot_increments + starting_shot

            # Create list of shot names

            shot_seq_text = ['<ShotNum', '[', ']']
            shot_seq = [ele for ele in shot_seq_text if(ele in shot_name_string)]

            try:
                if re.search('<ShotNum#*>', shot_name_string):

                    # Create shot list using options and token

                    shot_name_list = []

                    for x in range(starting_shot, num_folders, shot_increments):
                        shot_name = re.sub('<ShotNum#*>', str(x).zfill(int(shot_padding.group(0).count('#'))), shot_name_string)
                        shot_name_list.append(shot_name)

                elif not shot_seq:

                    # Create single shot shot_name_list if token or list not present in shot_name_entry

                    shot_name_list = [shot_name_string]

                else:

                    # Create shot list using shot numbers and shot range
                    # [0010, 0020, 0050-0090]

                    shot_name_prefix = shot_name_string.split('[', 1)[0]
                    shot_name_string = shot_name_string.split('[', 1)[1]
                    shot_name_string = shot_name_string.rsplit(']', 1)[0]
                    shot_name_string = shot_name_string.replace(' ', '')
                    shots = shot_name_string.split(',')

                    shot_name_list = [shot_name_prefix + shot for shot in shots if '-' not in shot]

                    for num in shots:
                        if '-' in num:
                            print (num)

                            # Remove number range from list
                            # shot_name_list.pop(shot_name_list.index(num))

                            num_range = num.split('-')
                            print (num_range)

                            padding = len(num_range[0])
                            print (padding)

                            stripped_numbers = []
                            for n in num_range:
                                n = n.lstrip('0')
                                stripped_numbers.append(int(n))
                            print (stripped_numbers)

                            for n in range(stripped_numbers[0], stripped_numbers[1] + shot_increments, shot_increments):
                                num_len = padding - len(str(n))
                                shot_name = shot_name_prefix + '0'*num_len + str(n)
                                shot_name_list.append(shot_name)

                    print (shot_name_list)

            except:
                return message_box('Enter valid shot naming. PYT_<ShotNum####> or PYT[0010, 0020, 0050-0090] for shot lists or PYT_0010 for single shot.')

            # print ('shot_name_list:', shot_name_list)
            # print ('selection:', self.selection)

            # Get button settings

            self.create_shot_type_folders = self.create_folders_btn.isChecked()
            self.create_shot_type_desktop = False
            self.create_shot_type_batch_group = False
            self.create_shot_type_system_folders = self.create_system_folders_btn.isChecked()

            self.batch_group_dest = 'Library'

            # Create shots from list

            self.create_shots(shot_name_list)

            self.window.close()

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(1100, 200))
        self.window.setMaximumSize(QtCore.QSize(1100, 300))
        self.window.setWindowTitle('Create Shot Folders %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.shot_naming_label = FlameLabel('Shot Folder Settings', 'background', self.window)
        self.create_label = FlameLabel('Create', 'background', self.window)
        self.shot_name_label = FlameLabel('Shot Name', 'normal', self.window)
        self.num_shots_label = FlameLabel('Number of Shots', 'normal', self.window)
        self.start_shot_num_label = FlameLabel('Starting Shot', 'normal', self.window)
        self.shot_increment_label = FlameLabel('Shot Increments', 'normal', self.window)

        self.system_folder_path_label = FlameLabel('System Folder Path', 'normal', self.window)
        system_folder_path = self.translate_system_shot_folder_path('PYT_0100')
        self.system_folder_path_label2 = FlameLabel(system_folder_path, 'outline', self.window)

        # LineEdits

        def check_shot_name_entry():

            if re.search('<ShotNum#*>', self.shot_name_entry.text()):
                self.num_of_shots_lineedit.setEnabled(True)
                self.num_shots_label.setEnabled(True)
                self.start_shot_num_lineedit.setEnabled(True)
                self.start_shot_num_label.setEnabled(True)
                self.shot_increment_label.setEnabled(True)
                self.shot_increment_lineedit.setEnabled(True)

            elif '[' in self.shot_name_entry.text() and ']' in self.shot_name_entry.text() and re.search('\d-\d', self.shot_name_entry.text()):
                self.num_of_shots_lineedit.setEnabled(False)
                self.num_shots_label.setEnabled(False)
                self.start_shot_num_lineedit.setEnabled(False)
                self.start_shot_num_label.setEnabled(False)
                self.shot_increment_label.setEnabled(True)
                self.shot_increment_lineedit.setEnabled(True)

            else:
                self.num_of_shots_lineedit.setEnabled(False)
                self.num_shots_label.setEnabled(False)
                self.start_shot_num_lineedit.setEnabled(False)
                self.start_shot_num_label.setEnabled(False)
                self.shot_increment_label.setEnabled(False)
                self.shot_increment_lineedit.setEnabled(False)

        self.shot_name_entry = FlameLineEdit(self.shot_naming, self.window)
        self.shot_name_entry.textChanged.connect(check_shot_name_entry)
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
                                               'QSlider::disabled {color: #6a6a6a; background-color: #373737}'
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
        self.start_shot_num_max_value = 10000
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
                                                 'QSlider::disabled {color: #6a6a6a; background-color: #373737}'
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
                                                 'QSlider::disabled {color: #6a6a6a; background-color: #373737}'
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

        # Pushbuttons

        self.create_folders_btn = FlamePushButton(' Folders', self.create_custom_folders, self.window)

        self.create_system_folders_btn = FlamePushButton(' System Folders', self.create_custom_system_folders, self.window)

        # Buttons

        help_btn = FlameButton('Help', self.help, self.window)
        create_btn = FlameButton('Create', create_shot_list, self.window)
        cancel_btn = FlameButton('Cancel', self.window.close, self.window)

        check_shot_name_entry()

        # ------------------------------------------------------------- #

        # Window layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setVerticalSpacing(5)
        gridbox.setHorizontalSpacing(5)

        gridbox.addWidget(self.shot_naming_label, 0, 1, 1, 6)

        gridbox.addWidget(self.shot_name_label, 1, 1)
        gridbox.addWidget(self.shot_name_entry, 1, 2, 1, 4)
        gridbox.addWidget(self.shot_name_token_btn, 1, 6)

        gridbox.addWidget(self.shot_increment_label, 2, 1)
        gridbox.addWidget(self.shot_increment_slider, 2, 2, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.shot_increment_lineedit, 2, 2)

        gridbox.addWidget(self.num_shots_label, 3, 1)
        gridbox.addWidget(self.num_of_shots_slider, 3, 2, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.num_of_shots_lineedit, 3, 2)

        gridbox.addWidget(self.start_shot_num_label, 4, 1)
        gridbox.addWidget(self.start_shot_num_slider, 4, 2, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.start_shot_num_lineedit, 4, 2)

        gridbox.addWidget(self.create_label, 0, 8)
        gridbox.addWidget(self.create_folders_btn, 1, 8)
        gridbox.addWidget(self.create_system_folders_btn, 2, 8)


        gridbox.addWidget(self.system_folder_path_label, 5, 1)
        gridbox.addWidget(self.system_folder_path_label2, 5, 2, 1, 5)

        gridbox.setRowMinimumHeight(6, 30)

        gridbox.addWidget(help_btn, 7, 1)
        gridbox.addWidget(cancel_btn, 7, 7)
        gridbox.addWidget(create_btn, 7, 8)

        self.window.setLayout(gridbox)

        self.window.show()

    def setup(self):

        def setup_folder_tab():

            # Labels

            self.setup_folder_clip_dest_label = FlameLabel('Clip Dest Folder', 'background', self.setup_window.tab1)
            self.setup_folder_clip_dest_label_02 = FlameLabel(self.clip_dest_folder, 'outline', self.setup_window.tab1)
            self.folders_label = FlameLabel('Folder Setup', 'background', self.setup_window.tab1)

            # Media Panel Shot Folder Tree

            self.folder_tree = QtWidgets.QTreeWidget(self.setup_window.tab1)
            self.folder_tree.setColumnCount(1)
            self.folder_tree.setHeaderLabel('Media Panel Shot Folder Template')
            self.folder_tree.itemsExpandable()
            self.folder_tree.setAlternatingRowColors(True)
            self.folder_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.folder_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #222222; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
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
            self.file_system_folder_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #222222; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
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

            self.folder_sort_btn = FlameButton('Sort Folders', partial(self.sort_tree_items, self.folder_tree), self.setup_window.tab1)
            self.system_folder_sort_btn = FlameButton('Sort Folders', partial(self.sort_tree_items, self.file_system_folder_tree), self.setup_window.tab1)

            self.add_folder_btn = FlameButton('Add Folder', partial(add_tree_item, folder_tree_top, self.folder_tree), self.setup_window.tab1)
            self.delete_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, folder_tree_top, self.folder_tree), self.setup_window.tab1)
            self.set_clip_dest_folder_btn = FlameButton('Set Clip Dest Folder', partial(set_as_destination, self.setup_folder_clip_dest_label_02, folder_tree_top, self.folder_tree), self.setup_window.tab1)

            self.add_file_system_folder_btn = FlameButton('Add Folder', partial(add_tree_item, file_system_folder_tree_top, self.file_system_folder_tree), self.setup_window.tab1)
            self.delete_file_system_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, file_system_folder_tree_top, self.file_system_folder_tree), self.setup_window.tab1)

            setup_help_btn = FlameButton('Help', self.help, self.setup_window.tab1)
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

            action_set_dest_folder = QtWidgets.QAction('Set Clip Dest Folder', self.setup_window.tab1)
            action_set_dest_folder.triggered.connect(partial(set_as_destination, self.setup_folder_clip_dest_label_02, folder_tree_top, self.folder_tree))
            self.folder_tree.addAction(action_set_dest_folder)

            # File system shot folder tree contextual right click menus

            action_file_system_add_folder = QtWidgets.QAction('Add Folder', self.setup_window.tab1)
            action_file_system_add_folder.triggered.connect(partial(add_tree_item, file_system_folder_tree_top, self.file_system_folder_tree))
            self.file_system_folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            self.file_system_folder_tree.addAction(action_file_system_add_folder)

            action_file_system_delete_folder = QtWidgets.QAction('Delete Folder', self.setup_window.tab1)
            action_file_system_delete_folder.triggered.connect(partial(del_tree_item, file_system_folder_tree_top, self.file_system_folder_tree))
            self.file_system_folder_tree.addAction(action_file_system_delete_folder)

            # Tab layout

            self.setup_window.tab1.layout = QtWidgets.QGridLayout()
            self.setup_window.tab1.layout.setMargin(10)
            self.setup_window.tab1.layout.setVerticalSpacing(5)
            self.setup_window.tab1.layout.setHorizontalSpacing(5)

            self.setup_window.tab1.layout.addWidget(self.setup_folder_clip_dest_label, 1, 0)
            self.setup_window.tab1.layout.addWidget(self.setup_folder_clip_dest_label_02, 2, 0)

            self.setup_window.tab1.layout.addWidget(self.folders_label, 0, 1)
            self.setup_window.tab1.layout.addWidget(self.folder_tree, 1, 1, 6, 1)
            self.setup_window.tab1.layout.addWidget(self.file_system_folder_tree, 7, 1, 6, 1)

            self.setup_window.tab1.layout.addWidget(self.add_folder_btn, 1, 2)
            self.setup_window.tab1.layout.addWidget(self.delete_folder_btn, 2, 2)
            self.setup_window.tab1.layout.addWidget(self.folder_sort_btn, 3, 2)
            self.setup_window.tab1.layout.addWidget(self.set_clip_dest_folder_btn, 4, 2)

            self.setup_window.tab1.layout.addWidget(self.add_file_system_folder_btn, 7, 2)
            self.setup_window.tab1.layout.addWidget(self.delete_file_system_folder_btn, 8, 2)
            self.setup_window.tab1.layout.addWidget(self.system_folder_sort_btn, 9, 2)

            self.setup_window.tab1.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab1.layout.addWidget(setup_save_btn, 13, 2)
            self.setup_window.tab1.layout.addWidget(setup_cancel_btn, 14, 2)

            self.setup_window.tab1.setLayout(self.setup_window.tab1.layout)

        def setup_batch_group_tab():

            # Labels

            self.batch_groups_label = FlameLabel('Batch Group Reel Setup', 'background', self.setup_window.tab2)
            self.setup_batch_clip_dest_reel_label = FlameLabel('Clip Dest Reel', 'background', self.setup_window.tab2)
            self.setup_batch_clip_dest_reel_label_02 = FlameLabel(self.clip_dest_reel, 'outline', self.setup_window.tab2)
            self.setup_batch_start_frame_label = FlameLabel('Batch Start Frame', 'background', self.setup_window.tab2)
            self.setup_batch_additional_naming_label = FlameLabel('Additional Batch Naming', 'background', self.setup_window.tab2)

            # LineEdits

            self.setup_batch_additional_naming_lineedit = FlameLineEdit(self.batch_additional_naming, self.setup_window.tab2)
            self.setup_batch_additional_naming_lineedit.setMaximumWidth(150)

            # Schematic Reel Tree

            self.schematic_reel_tree = QtWidgets.QTreeWidget(self.setup_window.tab2)
            self.schematic_reel_tree.setColumnCount(1)
            self.schematic_reel_tree.setHeaderLabel('Schematic Reel Template')
            self.schematic_reel_tree.itemsExpandable()
            self.schematic_reel_tree.setDragEnabled(True)
            self.schematic_reel_tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
            self.schematic_reel_tree.setAlternatingRowColors(True)
            self.schematic_reel_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.schematic_reel_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #222222; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
                                                   'QTreeWidget:item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                                                   'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14pt "Discreet"}'
                                                   'QMenu {color: #9a9a9a; background-color: #24303d; font: 14pt "Discreet"}'
                                                   'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            # Shelf Reel Tree

            self.shelf_reel_tree = QtWidgets.QTreeWidget(self.setup_window.tab2)
            self.shelf_reel_tree.setColumnCount(1)
            self.shelf_reel_tree.setHeaderLabel('Shelf Reel Template')
            self.shelf_reel_tree.itemsExpandable()
            self.shelf_reel_tree.setAlternatingRowColors(True)
            self.shelf_reel_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            self.shelf_reel_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #222222; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
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

            # Batch Start Frame Slider

            self.setup_batch_start_frame_min_value = 1
            self.setup_batch_start_frame_max_value = 10000
            self.setup_batch_start_frame_start_value = self.batch_start_frame

            def setup_batch_start_frame_spinbox_move_slider():
                self.setup_batch_start_frame_slider.setValue(int(self.setup_batch_start_frame_lineedit.text()))

            self.setup_batch_start_frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.setup_window.tab2)
            self.setup_batch_start_frame_slider.setMaximumHeight(3)
            self.setup_batch_start_frame_slider.setMaximumWidth(75)
            self.setup_batch_start_frame_slider.setMinimum(self.setup_batch_start_frame_min_value)
            self.setup_batch_start_frame_slider.setMaximum(self.setup_batch_start_frame_max_value)
            self.setup_batch_start_frame_slider.setValue(self.setup_batch_start_frame_start_value)
            self.setup_batch_start_frame_slider.setStyleSheet('QSlider {color: #111111}'
                                                              'QSlider::disabled {color: #6a6a6a; background-color: #373737}'
                                                              'QSlider::groove:horizontal {background-color: #111111}'
                                                              'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.setup_batch_start_frame_slider.setDisabled(True)

            self.setup_batch_start_frame_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.setup_batch_start_frame_start_value, parent=self.setup_window.tab2)
            self.setup_batch_start_frame_lineedit.setMinimum(self.setup_batch_start_frame_min_value)
            self.setup_batch_start_frame_lineedit.setMaximum(self.setup_batch_start_frame_max_value)
            self.setup_batch_start_frame_lineedit.setMinimumHeight(28)
            self.setup_batch_start_frame_lineedit.setMaximumWidth(75)
            self.setup_batch_start_frame_lineedit.textChanged.connect(setup_batch_start_frame_spinbox_move_slider)
            self.setup_batch_start_frame_slider.raise_()

            # Push Buttons

            self.add_render_node_btn = FlamePushButton(' Add Render Node', self.add_render_node, self.setup_window.tab2)
            self.add_render_node_btn.clicked.connect(render_button_toggle)

            self.add_write_file_node_btn = FlamePushButton(' Add Write File Node', self.add_write_file_node, self.setup_window.tab2)
            self.add_write_file_node_btn.clicked.connect(write_file_button_toggle)

            # Buttons

            self.schematic_reels_sort_btn = FlameButton('Sort Schematic Reels', partial(self.sort_tree_items, self.schematic_reel_tree), self.setup_window.tab2)
            self.shelf_reels_sort_btn = FlameButton('Sort Shelf Reels', partial(self.sort_tree_items, self.shelf_reel_tree), self.setup_window.tab2)

            self.add_schematic_reel_btn = FlameButton('Add Schematic Reel', partial(add_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree), self.setup_window.tab2)
            self.del_schematic_reel_btn = FlameButton('Delete Schematic Reel', partial(del_tree_item, batch_group_schematic_tree_top, self.schematic_reel_tree), self.setup_window.tab2)
            self.set_clip_dest_reel_btn = FlameButton('Set Clip Dest Reel', partial(set_as_destination, self.setup_batch_clip_dest_reel_label_02, batch_group_schematic_tree_top, self.schematic_reel_tree), self.setup_window.tab2)

            self.add_shelf_reel_btn = FlameButton('Add Shelf Reel', partial(add_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree), self.setup_window.tab2)
            self.del_shelf_reel_btn = FlameButton('Delete Shelf Reel', partial(del_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree), self.setup_window.tab2)

            self.write_file_setup_btn = FlameButton('Write File Setup', self.write_file_node_setup, self.setup_window.tab2)
            if self.add_render_node:
                self.write_file_setup_btn.setEnabled(False)

            setup_help_btn = FlameButton('Help', self.help, self.setup_window.tab2)
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

            action_set_dest_reel = QtWidgets.QAction('Set Clip Dest Reel', self.setup_window.tab2)
            action_set_dest_reel.triggered.connect(partial(set_as_destination, self.setup_batch_clip_dest_reel_label_02, batch_group_schematic_tree_top, self.schematic_reel_tree))
            self.schematic_reel_tree.addAction(action_set_dest_reel)

            # Shelf reel contextual right click menus

            action_add_shelf_reel = QtWidgets.QAction('Add Reel', self.setup_window.tab2)
            action_add_shelf_reel.triggered.connect(partial(add_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))
            self.shelf_reel_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            self.shelf_reel_tree.addAction(action_add_shelf_reel)

            action_delete_shelf_reel = QtWidgets.QAction('Delete Reel', self.setup_window.tab2)
            action_delete_shelf_reel.triggered.connect(partial(del_tree_item, batch_group_shelf_tree_top, self.shelf_reel_tree))
            self.shelf_reel_tree.addAction(action_delete_shelf_reel)

            # Tab layout

            self.setup_window.tab2.layout = QtWidgets.QGridLayout()
            self.setup_window.tab2.layout.setMargin(10)
            self.setup_window.tab2.layout.setVerticalSpacing(5)
            self.setup_window.tab2.layout.setHorizontalSpacing(5)

            self.setup_window.tab2.layout.addWidget(self.batch_groups_label, 0, 1)

            self.setup_window.tab2.layout.addWidget(self.setup_batch_clip_dest_reel_label, 1, 0)
            self.setup_window.tab2.layout.addWidget(self.setup_batch_clip_dest_reel_label_02, 2, 0)

            self.setup_window.tab2.layout.addWidget(self.setup_batch_start_frame_label, 4, 0)
            self.setup_window.tab2.layout.addWidget(self.setup_batch_start_frame_slider, 5, 0, QtCore.Qt.AlignBottom)
            self.setup_window.tab2.layout.addWidget(self.setup_batch_start_frame_lineedit, 5, 0)

            self.setup_window.tab2.layout.addWidget(self.setup_batch_additional_naming_label, 7, 0)
            self.setup_window.tab2.layout.addWidget(self.setup_batch_additional_naming_lineedit, 8, 0)

            self.setup_window.tab2.layout.addWidget(self.schematic_reel_tree, 1, 1, 6, 1)
            self.setup_window.tab2.layout.addWidget(self.shelf_reel_tree, 7, 1, 6, 1)

            self.setup_window.tab2.layout.addWidget(self.add_schematic_reel_btn, 1, 2)
            self.setup_window.tab2.layout.addWidget(self.del_schematic_reel_btn, 2, 2)
            self.setup_window.tab2.layout.addWidget(self.schematic_reels_sort_btn, 3, 2)
            self.setup_window.tab2.layout.addWidget(self.set_clip_dest_reel_btn, 4, 2)

            self.setup_window.tab2.layout.addWidget(self.add_shelf_reel_btn, 7, 2)
            self.setup_window.tab2.layout.addWidget(self.del_shelf_reel_btn, 8, 2)
            self.setup_window.tab2.layout.addWidget(self.shelf_reels_sort_btn, 9, 2)

            self.setup_window.tab2.layout.addWidget(self.add_render_node_btn, 10, 0)
            self.setup_window.tab2.layout.addWidget(self.add_write_file_node_btn, 11, 0)
            self.setup_window.tab2.layout.addWidget(self.write_file_setup_btn, 12, 0)

            self.setup_window.tab2.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab2.layout.addWidget(setup_save_btn, 13, 2)
            self.setup_window.tab2.layout.addWidget(setup_cancel_btn, 14, 2)

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
                else:
                    message_box('Reel Group must have at least 4 reels')

            # Labels

            self.reel_group_label = FlameLabel('Desktop Reel Group Setup', 'background', self.setup_window.tab3)

            # Reel Group Tree

            self.reel_group_tree = QtWidgets.QTreeWidget(self.setup_window.tab3)
            self.reel_group_tree.move(230, 170)
            self.reel_group_tree.resize(250, 140)
            self.reel_group_tree.setColumnCount(1)
            self.reel_group_tree.setHeaderLabel('Reel Group Template')
            self.reel_group_tree.setAlternatingRowColors(True)
            self.reel_group_tree.setFocusPolicy(QtCore.Qt.NoFocus)
            # self.reel_group_tree.setAcceptDrops(True)
            # self.reel_group_tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            # self.reel_group_tree.setDragEnabled(True)
            # self.reel_group_tree.setDropIndicatorShown(True)
            # self.reel_group_tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
            # self.reel_group_tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            self.reel_group_tree.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #222222; alternate-background-color: #2d2d2d; border: none; font: 14pt "Discreet"}'
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
                    self.reel_group_sort_btn.setEnabled(True)

                else:
                    self.reel_group_tree.setEnabled(False)
                    self.add_reel_btn.setEnabled(False)
                    self.del_reel_btn.setEnabled(False)
                    self.reel_group_sort_btn.setEnabled(False)


            self.add_reel_group_btn = FlamePushButton(' Add Reel Group', self.add_reel_group, self.setup_window.tab3)
            self.add_reel_group_btn.clicked.connect(add_reel_group_button)

            # Buttons

            self.reel_group_sort_btn = FlameButton('Sort Reels', partial(self.sort_tree_items, self.reel_group_tree), self.setup_window.tab3)

            self.add_reel_btn = FlameButton('Add Reel', partial(add_tree_item, reel_tree_top, self.reel_group_tree), self.setup_window.tab3)
            self.del_reel_btn = FlameButton('Delete Reel', partial(del_reel_item, reel_tree_top, self.reel_group_tree), self.setup_window.tab3)

            setup_help_btn = FlameButton('Help', self.help, self.setup_window.tab3)
            setup_save_btn = FlameButton('Save', save_setup_settings, self.setup_window.tab3)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window.tab3)

            # Tab layout

            self.setup_window.tab3.layout = QtWidgets.QGridLayout()
            self.setup_window.tab3.layout.setMargin(10)
            self.setup_window.tab3.layout.setVerticalSpacing(5)
            self.setup_window.tab3.layout.setHorizontalSpacing(5)

            self.setup_window.tab3.layout.addWidget(self.add_reel_group_btn, 1, 0)

            self.setup_window.tab3.layout.addWidget(self.reel_group_label, 0, 1)
            self.setup_window.tab3.layout.addWidget(self.add_reel_btn, 1, 2)
            self.setup_window.tab3.layout.addWidget(self.del_reel_btn, 2, 2)
            self.setup_window.tab3.layout.addWidget(self.reel_group_sort_btn, 3, 2)

            self.setup_window.tab3.layout.addWidget(self.reel_group_tree, 1, 1, 6, 1)

            self.setup_window.tab3.layout.addWidget(setup_help_btn, 14, 0)
            self.setup_window.tab3.layout.addWidget(setup_save_btn, 13, 2)
            self.setup_window.tab3.layout.addWidget(setup_cancel_btn, 14, 2)

            self.setup_window.tab3.setLayout(self.setup_window.tab3.layout)

        def setup_clips_tab():

            def update_system_folder_path():

                shot_name = 'pyt_0010'
                self.system_shot_folders_path = self.setup_system_shot_folders_path_lineedit.text()
                self.setup_system_folder_path_translated_label.setText(self.translate_system_shot_folder_path(shot_name))

            def folders_button_toggle():

                if self.setup_folders_pushbutton.isChecked():
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)
                else:
                    if self.setup_batch_group_pushbutton.isChecked():
                        if not self.setup_desktop_pushbutton.isChecked():
                            self.setup_batch_group_dest_label.setEnabled(True)
                            self.setup_batch_group_dest_btn.setEnabled(True)

            def batch_group_button_toggle():

                # When batch group button is selected enable batch group reel destination lineedit

                if self.setup_batch_group_pushbutton.isChecked():
                    self.setup_batch_template_pushbutton.setEnabled(True)

                    if self.setup_folders_pushbutton.isChecked():
                        self.setup_batch_group_dest_label.setEnabled(False)
                        self.setup_batch_group_dest_btn.setEnabled(False)
                    else:
                        self.setup_batch_group_dest_label.setEnabled(True)
                        self.setup_batch_group_dest_btn.setEnabled(True)

                    if self.setup_batch_template_pushbutton.isChecked():
                        self.setup_batch_template_path_label.setEnabled(True)
                        self.setup_batch_template_path_lineedit.setEnabled(True)
                        self.setup_batch_template_path_browse_button.setEnabled(True)
                    else:
                        self.setup_batch_template_path_label.setEnabled(False)
                        self.setup_batch_template_path_lineedit.setEnabled(False)
                        self.setup_batch_template_path_browse_button.setEnabled(False)


                elif self.setup_desktop_pushbutton.isChecked():
                    self.setup_batch_group_pushbutton.setChecked(True)
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)
                else:
                    self.setup_batch_template_pushbutton.setEnabled(False)
                    self.setup_batch_template_path_label.setEnabled(False)
                    self.setup_batch_template_path_lineedit.setEnabled(False)
                    self.setup_batch_template_path_browse_button.setEnabled(False)
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)

            def desktop_button_toggle():

                # When desktop button is selected enable batch group button

                if self.setup_desktop_pushbutton.isChecked():
                    self.setup_batch_group_pushbutton.setChecked(True)
                    self.setup_batch_group_dest_label.setEnabled(False)
                    self.setup_batch_group_dest_btn.setEnabled(False)
                    self.setup_batch_template_pushbutton.setEnabled(True)
                    if self.setup_batch_template_pushbutton.isChecked():
                        self.setup_batch_template_path_label.setEnabled(True)
                        self.setup_batch_template_path_lineedit.setEnabled(True)
                        self.setup_batch_template_path_browse_button.setEnabled(True)
                else:
                    self.setup_batch_group_pushbutton.setEnabled(True)
                    if self.setup_batch_group_pushbutton.isChecked():
                        if not self.setup_folders_pushbutton.isChecked():
                            self.setup_batch_group_dest_label.setEnabled(True)
                            self.setup_batch_group_dest_btn.setEnabled(True)

            def batch_template_toggle():

                if self.setup_batch_template_pushbutton.isChecked():
                    self.setup_batch_template_path_label.setEnabled(True)
                    self.setup_batch_template_path_lineedit.setEnabled(True)
                    self.setup_batch_template_path_browse_button.setEnabled(True)
                else:
                    self.setup_batch_template_path_label.setEnabled(False)
                    self.setup_batch_template_path_lineedit.setEnabled(False)
                    self.setup_batch_template_path_browse_button.setEnabled(False)

            # Labels

            self.setup_create_shot_type_label = FlameLabel('Create', 'background', self.setup_window.tab4)
            self.setup_settings_label = FlameLabel('Settings', 'background', self.setup_window.tab4)
            self.setup_batch_group_options_label = FlameLabel('Batch Group Options', 'background', self.setup_window.tab4)
            self.setup_batch_template_path_label = FlameLabel('Template Path', 'normal', self.setup_window.tab4)
            self.setup_batch_group_dest_label = FlameLabel('Batch Group Dest', 'normal', self.setup_window.tab4)
            self.setup_system_folder_path_label = FlameLabel('File System Folders Path', 'background', self.setup_window.tab4)
            self.setup_system_folder_path_translated_label = FlameLabel('', 'outline', self.setup_window.tab4)

            # LineEdits

            self.setup_batch_template_path_lineedit = FlameLineEdit(self.batch_template_path, self.setup_window.tab4)

            self.setup_system_shot_folders_path_lineedit = FlameLineEdit(self.system_shot_folders_path, self.setup_window.tab4)
            self.setup_system_shot_folders_path_lineedit.textChanged.connect(update_system_folder_path)
            update_system_folder_path()

            # Push Buttons

            self.setup_folders_pushbutton = FlamePushButton('  Folders', self.create_shot_type_folders, self.setup_window.tab4)
            self.setup_folders_pushbutton.clicked.connect(folders_button_toggle)

            self.setup_batch_group_pushbutton = FlamePushButton('  Batch Group', self.create_shot_type_batch_group, self.setup_window.tab4)
            self.setup_batch_group_pushbutton.clicked.connect(batch_group_button_toggle)

            self.setup_desktop_pushbutton = FlamePushButton('  Desktop', self.create_shot_type_desktop, self.setup_window.tab4)
            self.setup_desktop_pushbutton.clicked.connect(desktop_button_toggle)

            self.setup_system_folders_pushbutton = FlamePushButton('  System Folders', self.create_shot_type_system_folders, self.setup_window.tab4)

            self.setup_batch_template_pushbutton = FlamePushButton('  Batch Template', self.apply_batch_template, self.setup_window.tab4)
            self.setup_batch_template_pushbutton.clicked.connect(batch_template_toggle)

            # Push Button Menu

            batch_group_dest_options = ['Desktop', 'Library']
            self.setup_batch_group_dest_btn = FlamePushButtonMenu(self.batch_group_dest, batch_group_dest_options, self.setup_window.tab4)

            system_path_token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>', 'SEQUENCE NAME': '<SEQNAME>', 'Sequence Name': '<SeqName>'}
            self.system_path_token_push_button = FlameTokenPushButton('Add Token', system_path_token_dict, self.setup_system_shot_folders_path_lineedit, self.setup_window.tab4)

            # Buttons

            self.setup_system_folder_path_browse_button = FlameButton('Browse', partial(self.system_folder_browse, self.setup_system_shot_folders_path_lineedit, self.setup_window.tab4), self.setup_window.tab4)
            self.setup_batch_template_path_browse_button = FlameButton('Browse', partial(self.batch_template_browse, self.setup_batch_template_path_lineedit, self.setup_window.tab4), self.setup_window.tab4)

            setup_help_btn = FlameButton('Help', self.help, self.setup_window.tab4)
            setup_save_btn = FlameButton('Save', save_setup_settings, self.setup_window.tab4)
            setup_cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window.tab4)

            # ----- #

            # Check button states

            batch_group_button_toggle()
            desktop_button_toggle()
            batch_template_toggle()
            folders_button_toggle()

            # Tab layout

            self.setup_window.tab4.layout = QtWidgets.QGridLayout()
            self.setup_window.tab4.layout.setMargin(10)
            self.setup_window.tab4.layout.setVerticalSpacing(5)
            self.setup_window.tab4.layout.setHorizontalSpacing(5)

            self.setup_window.tab4.layout.addWidget(self.setup_create_shot_type_label, 0, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_folders_pushbutton, 1, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_pushbutton, 2, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_desktop_pushbutton, 3, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_system_folders_pushbutton, 4, 0)

            self.setup_window.tab4.layout.addWidget(self.setup_settings_label, 0, 1)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_pushbutton, 1, 1)

            self.setup_window.tab4.layout.setRowMinimumHeight(8, 28)

            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_options_label, 9, 0, 1, 5)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_path_label, 10, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_path_lineedit, 10, 1, 1, 3)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_template_path_browse_button, 10, 4)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_dest_label, 11, 0)
            self.setup_window.tab4.layout.addWidget(self.setup_batch_group_dest_btn, 11, 1)

            self.setup_window.tab4.layout.addWidget(self.setup_system_folder_path_label, 13, 0, 1, 5)
            self.setup_window.tab4.layout.addWidget(self.setup_system_folder_path_translated_label, 14, 0, 1, 5)
            self.setup_window.tab4.layout.addWidget(self.setup_system_shot_folders_path_lineedit, 15, 0, 1, 3)
            self.setup_window.tab4.layout.addWidget(self.setup_system_folder_path_browse_button, 15, 3)
            self.setup_window.tab4.layout.addWidget(self.system_path_token_push_button, 15, 4)

            self.setup_window.tab4.layout.setRowMinimumHeight(12, 30)

            self.setup_window.tab4.layout.setRowMinimumHeight(17, 100)

            self.setup_window.tab4.layout.addWidget(setup_help_btn, 19, 0)
            self.setup_window.tab4.layout.addWidget(setup_save_btn, 18, 4)
            self.setup_window.tab4.layout.addWidget(setup_cancel_btn, 19, 4)

            self.setup_window.tab4.setLayout(self.setup_window.tab4.layout)

        # ------------------------------------------------------------- #

        def flame_version_check():

            # Disable adding file system folder setup options in versions older than 2021.2

            if self.flame_version < 2021.2:
                self.file_system_folder_tree.setDisabled(True)
                self.add_file_system_folder_btn.setDisabled(True)
                self.delete_file_system_folder_btn.setDisabled(True)

        def set_as_destination(label, tree_top, tree):
            '''Set selected item in tree as clip folder or reel destination'''

            for item in tree.selectedItems():
                if item != tree_top:
                    label.setText(item.text(0))

        def fill_tree(tree_widget, tree_dict):

            def fill_item(item, value):

                # Set top level item so name can not be changed except for reel group tree

                if tree_widget == self.reel_group_tree or str(item.parent()) != 'None':
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled)
                else:
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled)

                item.setExpanded(True)

                if type(value) is dict:
                    for key, val in iter(value.items()):
                    # for key, val in sorted(iter(value.items())):
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
                iterator = QtWidgets.QTreeWidgetItemIterator(tree)  # pass your treewidget as arg
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

            def clip_dest(lineedit, tree_dict):

                # Make sure entry destination exists in current folder/reel tree

                for key, value in iter(tree_dict.items()):
                    # print (value)
                    for v in value:
                        # print (v)
                        if v == str(lineedit.text()):
                            return True
                return False

            folder_dict = create_dict(self.folder_tree)
            reel_dict = create_dict(self.schematic_reel_tree)

            if not clip_dest(self.setup_folder_clip_dest_label_02, folder_dict):
                return message_box('Clip destination folder must exist in Shot Folder Template')

            if not clip_dest(self.setup_batch_clip_dest_reel_label_02, reel_dict):
                return message_box('Clip destination reel must exist in Batch Group Template')

            if not any([self.setup_folders_pushbutton.isChecked(), self.setup_batch_group_pushbutton.isChecked(), self.setup_desktop_pushbutton.isChecked(), self.setup_system_folders_pushbutton.isChecked()]):
                return message_box('At least one Create Shot Type must be selected ')

            if self.setup_batch_template_pushbutton.isChecked():
                if not self.setup_batch_template_path_lineedit.text():
                    return message_box('Select batch setup to use as batch template')

                elif not os.path.isfile(self.setup_batch_template_path_lineedit.text()):
                    return message_box('Select valid batch setup')

                elif not self.setup_batch_template_path_lineedit.text().endswith('.batch'):
                    return message_box('Selected file should be batch setup')

            batch_group_dest = self.setup_batch_group_dest_btn.text()

            if self.setup_folders_pushbutton.isChecked() or self.setup_desktop_pushbutton.isChecked():
                batch_group_dest = 'Library'

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            shot_folders = root.find('.//shot_folders')
            shot_folders.text = str(create_dict(self.folder_tree))
            file_system_folders = root.find('.//file_system_folders')
            file_system_folders.text = str(create_dict(self.file_system_folder_tree))
            schematic_reels = root.find('.//schematic_reels')
            schematic_reels.text = str(create_dict(self.schematic_reel_tree))
            shelf_reels = root.find('.//shelf_reels')
            shelf_reels.text = str(create_dict(self.shelf_reel_tree))
            reel_group_reels = root.find('.//reel_group_reels')
            reel_group_reels.text = str(create_dict(self.reel_group_tree))
            add_reel_group = root.find('.//add_reel_group')
            add_reel_group.text = str(self.add_reel_group_btn.isChecked())
            add_render_node = root.find('.//add_render_node')
            add_render_node.text = str(self.add_render_node_btn.isChecked())
            add_write_node = root.find('.//add_write_node')
            add_write_node.text = str(self.add_write_file_node_btn.isChecked())
            create_shot_type_folders = root.find('.//create_shot_type_folders')
            create_shot_type_folders.text = str(self.setup_folders_pushbutton.isChecked())
            create_shot_type_batch_group = root.find('.//create_shot_type_batch_group')
            create_shot_type_batch_group.text = str(self.setup_batch_group_pushbutton.isChecked())
            create_shot_type_desktop = root.find('.//create_shot_type_desktop')
            create_shot_type_desktop.text = str(self.setup_desktop_pushbutton.isChecked())
            create_shot_type_system_folders = root.find('.//create_shot_type_system_folders')
            create_shot_type_system_folders.text = str(self.setup_system_folders_pushbutton.isChecked())
            system_shot_folders_path = root.find('.//system_shot_folders_path')
            system_shot_folders_path.text = self.setup_system_shot_folders_path_lineedit.text()
            clip_destination_folder = root.find('.//clip_destination_folder')
            clip_destination_folder.text = str(self.setup_folder_clip_dest_label_02.text())
            clip_destination_reel = root.find('.//clip_destination_reel')
            clip_destination_reel.text = str(self.setup_batch_clip_dest_reel_label_02.text())
            setup_batch_template = root.find('.//setup_batch_template')
            setup_batch_template.text = str(self.setup_batch_template_pushbutton.isChecked())
            setup_batch_template_path = root.find('.//setup_batch_template_path')
            setup_batch_template_path.text = self.setup_batch_template_path_lineedit.text()
            setup_batch_group_dest = root.find('.//setup_batch_group_dest')
            setup_batch_group_dest.text = batch_group_dest

            setup_batch_start_frame = root.find('.//setup_batch_start_frame')
            setup_batch_start_frame.text = self.setup_batch_start_frame_lineedit.text()
            setup_batch_additional_naming = root.find('.//setup_batch_additional_naming')
            setup_batch_additional_naming.text = self.setup_batch_additional_naming_lineedit.text()

            xml_tree.write(self.config_xml)

            print ('\n>>> settings saved <<<\n')

            # Close setup window and reload settings

            self.setup_window.close()

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
        self.setup_window.setMinimumSize(QtCore.QSize(800, 560))
        self.setup_window.setMaximumSize(QtCore.QSize(800, 560))
        self.setup_window.setWindowTitle('Create Shot Setup %s' % VERSION)
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                               (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        self.setup_window.tab1 = QtWidgets.QWidget()
        self.setup_window.tab2 = QtWidgets.QWidget()
        self.setup_window.tab3 = QtWidgets.QWidget()
        self.setup_window.tab4 = QtWidgets.QWidget()

        self.setup_window.setStyleSheet('QTabWidget {background-color: #272727; font: 14px "Discreet"}'
                                        'QTabWidget::tab-bar {alignment: center}'
                                        'QTabBar::tab {color: #9a9a9a; background-color: #272727; border: 1px solid #3a3a3a; border-bottom-color: #555555; min-width: 20ex; padding: 5px}'
                                        'QTabBar::tab:selected {color: #bababa; border: 1px solid #555555; border-bottom: 1px solid #272727}'
                                        'QTabWidget::pane {border-top: 1px solid #555555; top: -0.05em}')

        self.setup_window.addTab(self.setup_window.tab1, 'Folders')
        self.setup_window.addTab(self.setup_window.tab2, 'Batch Groups')
        self.setup_window.addTab(self.setup_window.tab3, 'Desktops')
        self.setup_window.addTab(self.setup_window.tab4, 'Clip/File to Shot')

        setup_folder_tab()
        setup_batch_group_tab()
        setup_desktop_tab()
        setup_clips_tab()

        flame_version_check()

        # Window Layout

        vbox = QtWidgets.QVBoxLayout()
        vbox.setMargin(15)

        vbox.addLayout(self.setup_window.tab1.layout)
        vbox.addLayout(self.setup_window.tab2.layout)
        vbox.addLayout(self.setup_window.tab3.layout)
        vbox.addLayout(self.setup_window.tab4.layout)

        self.setup_window.setLayout(vbox)

        self.setup_window.show()

        return self.setup_window

    def write_file_node_setup(self):

        def media_path_browse():

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.write_file_setup_window, 'Select Directory', self.write_file_media_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.write_file_media_path_lineedit.setText(file_path)

        def save_write_file_config():

            def save_config():

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                write_file_media_path = root.find('.//write_file_media_path')
                write_file_media_path.text = self.write_file_media_path_lineedit.text()
                write_file_pattern = root.find('.//write_file_pattern')
                write_file_pattern.text = self.write_file_pattern_lineedit.text()
                write_file_create_open_clip = root.find('.//write_file_create_open_clip')
                write_file_create_open_clip.text = str(self.write_file_create_open_clip_btn.isChecked())
                write_file_include_setup = root.find('.//write_file_include_setup')
                write_file_include_setup.text = str(self.write_file_include_setup_btn.isChecked())
                write_file_create_open_clip_value = root.find('.//write_file_create_open_clip_value')
                write_file_create_open_clip_value.text = self.write_file_create_open_clip_lineedit.text()
                write_file_include_setup_value = root.find('.//write_file_include_setup_value')
                write_file_include_setup_value.text = self.write_file_include_setup_lineedit.text()
                write_file_image_format = root.find('.//write_file_image_format')
                write_file_image_format.text = self.write_file_image_format_push_btn.text()
                write_file_image_format = root.find('.//write_file_compression')
                write_file_image_format.text = self.write_file_compression_push_btn.text()
                write_file_padding = root.find('.//write_file_padding')
                write_file_padding.text = self.write_file_padding_lineedit.text()
                write_file_frame_index = root.find('.//write_file_frame_index')
                write_file_frame_index.text = self.write_file_frame_index_push_btn.text()

                xml_tree.write(self.config_xml)

                print ('\n>>> settings saved <<<\n')

                # Close setup window and reload settings

                self.write_file_setup_window.close()

                self.config()

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
        self.write_file_setup_window.setMinimumSize(QtCore.QSize(1000, 500))
        self.write_file_setup_window.setMaximumSize(QtCore.QSize(1000, 500))
        self.write_file_setup_window.setWindowTitle('Shot Folder Creator Write File Node Setup %s' % VERSION)
        self.write_file_setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.write_file_setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.write_file_setup_window.setStyleSheet('background-color: #272727')

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
        self.write_file_compression_label = FlameLabel('Compression', 'normal', self.write_file_setup_window)
        self.write_file_settings_label = FlameLabel('Settings', 'background', self.write_file_setup_window)

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



        image_format_menu = QtWidgets.QMenu(self.write_file_setup_window)
        image_format_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                               'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.write_file_image_format_push_btn = QtWidgets.QPushButton(self.write_file_image_format, self.write_file_setup_window)
        self.write_file_image_format_push_btn.setMenu(image_format_menu)
        self.write_file_image_format_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.write_file_image_format_push_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.write_file_image_format_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.write_file_image_format_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                            'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        # -------------------------------------------------------------

        def compression(file_format):

            def create_menu(option):
                self.write_file_compression_push_btn.setText(option)

            compression_menu.clear()
            # compression_list = []

            self.write_file_image_format_push_btn.setText(file_format)

            if 'Dpx' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'Pixspan', 'Packed']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Jpeg' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'OpenEXR' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'Scanline', 'Multi_Scanline', 'RLE', 'PXR24', 'PIZ', 'DWAB', 'DWAA', 'B44A', 'B44']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Png' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'Sgi' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'RLE']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Targa' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'Tiff' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'RLE', 'LZW']
                self.write_file_compression_push_btn.setEnabled(True)

            for option in compression_list:
                compression_menu.addAction(option, partial(create_menu, option))

        image_format_menu.addAction('Dpx 8-bit', partial(compression, 'Dpx 8-bit'))
        image_format_menu.addAction('Dpx 10-bit', partial(compression, 'Dpx 10-bit'))
        image_format_menu.addAction('Dpx 12-bit', partial(compression, 'Dpx 12-bit'))
        image_format_menu.addAction('Dpx 16-bit', partial(compression, 'Dpx 16-bit'))
        image_format_menu.addAction('Jpeg 8-bit', partial(compression, 'Jpeg 8-bit'))
        image_format_menu.addAction('OpenEXR 16-bit fp', partial(compression, 'OpenEXR 16-bit fp'))
        image_format_menu.addAction('OpenEXR 32-bit fp', partial(compression, 'OpenEXR 32-bit fp'))
        image_format_menu.addAction('Png 8-bit', partial(compression, 'Png 8-bit'))
        image_format_menu.addAction('Png 16-bit', partial(compression, 'Png 16-bit'))
        image_format_menu.addAction('Sgi 8-bit', partial(compression, 'Sgi 8-bit'))
        image_format_menu.addAction('Sgi 16-bit', partial(compression, 'Sgi 16-bit'))
        image_format_menu.addAction('Targa 8-bit', partial(compression, 'Targa 8-bit'))
        image_format_menu.addAction('Tiff 8-bit', partial(compression, 'Tiff 8-bit'))
        image_format_menu.addAction('Tiff 16-bit', partial(compression, 'Tiff 16-bit'))

        compression_menu = QtWidgets.QMenu(self.write_file_setup_window)
        compression_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                       'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.write_file_compression_push_btn = QtWidgets.QPushButton(self.write_file_compression, self.write_file_setup_window)
        self.write_file_compression_push_btn.setMenu(compression_menu)
        self.write_file_compression_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.write_file_compression_push_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.write_file_compression_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.write_file_compression_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')


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
        compression(self.write_file_image_format_push_btn.text())

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

        gridbox.setRowMinimumHeight(6, 28)

        gridbox.addWidget(self.write_file_settings_label, 7, 0, 1, 2)
        gridbox.addWidget(self.write_file_frame_index_label, 8, 0)
        gridbox.addWidget(self.write_file_frame_index_push_btn, 8, 1)
        gridbox.addWidget(self.write_file_type_label, 9, 0)
        gridbox.addWidget(self.write_file_image_format_push_btn, 9, 1)
        gridbox.addWidget(self.write_file_padding_label, 10, 0)
        gridbox.addWidget(self.write_file_padding_slider, 10, 1, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.write_file_padding_lineedit, 10, 1)
        gridbox.addWidget(self.write_file_compression_label, 11, 0)
        gridbox.addWidget(self.write_file_compression_push_btn, 11, 1)

        gridbox.addWidget(self.write_file_save_btn, 12, 5)
        gridbox.addWidget(self.write_file_cancel_btn, 13, 5)

        self.write_file_setup_window.setLayout(gridbox)

        self.write_file_setup_window.show()

    def custom_shot_from_selected_window(self):

        def create_shots():

            def save_settings():

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                all_clips = root.find('.//all_clips')
                all_clips.text = str(self.custom_all_clips_btn.isChecked())
                shot_name = root.find('.//shot_name')
                shot_name.text = str(self.custom_shot_name_btn.isChecked())
                clip_name = root.find('.//clip_name')
                clip_name.text = str(self.custom_clip_name_btn.isChecked())
                custom_folders = root.find('.//custom_folders')
                custom_folders.text = str(self.custom_folders_btn.isChecked())
                custom_batch_group = root.find('.//custom_batch_group')
                custom_batch_group.text = str(self.custom_batch_group_btn.isChecked())
                custom_desktop = root.find('.//custom_desktop')
                custom_desktop.text = str(self.custom_desktop_btn.isChecked())
                custom_system_folders = root.find('.//custom_system_folders')
                custom_system_folders.text = str(self.custom_system_folders_btn.isChecked())
                custom_system_folders_path = root.find('.//custom_system_folders_path')
                custom_system_folders_path.text = self.custom_system_folders_path_lineedit.text()
                custom_apply_batch_template = root.find('.//custom_apply_batch_template')
                custom_apply_batch_template.text = str(self.custom_batch_template_btn.isChecked())
                custom_batch_template_path = root.find('.//custom_batch_template_path')
                custom_batch_template_path.text = self.custom_batch_template_lineedit.text()
                custom_batch_group_dest = root.find('.//custom_batch_group_dest')
                custom_batch_group_dest.text = self.custom_batch_group_dest_btn.text()
                custom_batch_start_frame = root.find('.//custom_batch_start_frame')
                custom_batch_start_frame.text = self.custom_batch_start_frame_lineedit.text()
                custom_batch_additional_naming = root.find('.//custom_batch_additional_naming')
                custom_batch_additional_naming.text = self.custom_batch_additional_naming_lineedit.text()

                xml_tree.write(self.config_xml)

                print ('\n>>> settings saved <<<\n')

            # Check that at least on shot creation type is selection

            if not any ([self.custom_folders_btn.isChecked(), self.custom_desktop_btn.isChecked(), self.custom_batch_group_btn.isChecked(), self.custom_system_folders_btn.isChecked()]):
                return message_box('Select shot type to create')

            # If apply batch template is enabled, check batch path is valid

            if self.custom_batch_template_btn.isChecked():
                if not os.path.isfile(self.custom_batch_template_lineedit.text()):
                    return message_box('Select valid batch setup to use as shot template')

            # Save settings

            save_settings()

            # Create list of shot names

            shot_name_list = []

            # print ('shot_name_list:', shot_name_list)
            # print ('selection:', self.selection)

            # Apply button settings to global settings

            self.create_shot_type_folders = self.custom_folders_btn.isChecked()
            self.create_shot_type_desktop = self.custom_desktop_btn.isChecked()
            self.create_shot_type_batch_group = self.custom_batch_group_btn.isChecked()
            self.create_shot_type_system_folders = self.custom_system_folders_btn.isChecked()
            self.apply_batch_template = self.custom_batch_template_btn.isChecked()
            self.batch_template_path = str(self.custom_batch_template_lineedit.text())
            self.batch_group_dest = self.custom_batch_group_dest_btn.text()
            if self.custom_folders_btn.isChecked() or self.custom_desktop_btn.isChecked():
                self.batch_group_dest = 'Library'
            self.system_shot_folders_path = self.custom_system_folders_path_lineedit.text()

            self.batch_start_frame = int(self.custom_batch_start_frame_lineedit.text())
            self.batch_additional_naming = self.custom_batch_additional_naming_lineedit.text()

            # Create shots

            if self.custom_all_clips_btn.isChecked() and self.custom_shot_name_btn.isChecked():
                self.create_shot_name_shots_all_clips()
            elif self.custom_all_clips_btn.isChecked() and self.custom_clip_name_btn.isChecked():
                self.create_clip_name_shots_all_clips()
            elif not self.custom_all_clips_btn.isChecked() and self.custom_shot_name_btn.isChecked():
                self.create_shot_name_shots()
            elif not self.custom_all_clips_btn.isChecked() and self.custom_clip_name_btn.isChecked():
                self.create_clip_name_shots()

            self.custom_selected_window.close()

        def update_system_folder_path():

            shot_name = self.selection[0]
            shot_name = str(shot_name.name)[1:-1]
            self.system_shot_folders_path = self.custom_system_folders_path_lineedit.text()
            self.custom_system_folders_path_translated_label.setText(self.translate_system_shot_folder_path(shot_name))

        def batch_group_button_toggle():

            if self.custom_desktop_btn.isChecked():
                self.custom_batch_group_btn.setChecked(True)
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)

            if self.custom_batch_group_btn.isChecked():
                self.custom_batch_template_btn.setEnabled(True)
                self.custom_batch_group_dest_label.setEnabled(True)
                self.custom_batch_group_dest_btn.setEnabled(True)
                if self.custom_batch_template_btn.isChecked():
                    self.custom_batch_group_template_path_label.setEnabled(True)
                    self.custom_batch_template_lineedit.setEnabled(True)
                    self.custom_batch_template_browse_btn.setEnabled(True)
                if self.custom_desktop_btn.isChecked() or self.custom_folders_btn.isChecked():
                    self.custom_batch_group_dest_label.setEnabled(False)
                    self.custom_batch_group_dest_btn.setEnabled(False)
            else:
                self.custom_batch_template_btn.setEnabled(False)
                self.custom_batch_group_template_path_label.setEnabled(False)
                self.custom_batch_template_lineedit.setEnabled(False)
                self.custom_batch_template_browse_btn.setEnabled(False)
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)

        def folder_toggle():

            if self.custom_folders_btn.isChecked():
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)
            else:
                if self.custom_batch_group_btn.isChecked() and not self.custom_desktop_btn.isChecked():
                    self.custom_batch_group_dest_label.setEnabled(True)
                    self.custom_batch_group_dest_btn.setEnabled(True)

        def desktop_toggle():

            # When desktop button is selected enable batch group button

            if self.custom_desktop_btn.isChecked():
                self.custom_batch_group_btn.setChecked(True)
                self.custom_batch_group_dest_label.setEnabled(False)
                self.custom_batch_group_dest_btn.setEnabled(False)
                self.custom_batch_template_btn.setEnabled(True)
                if self.custom_batch_template_btn.isChecked():
                    self.custom_batch_group_template_path_label.setEnabled(True)
                    self.custom_batch_template_lineedit.setEnabled(True)
                    self.custom_batch_template_browse_btn.setEnabled(True)
            else:
                self.custom_batch_group_btn.setEnabled(True)
                if self.custom_batch_group_btn.isChecked():
                    self.custom_batch_group_dest_label.setEnabled(True)
                    self.custom_batch_group_dest_btn.setEnabled(True)

        def shot_name_toggle():

            self.custom_shot_name_btn.setChecked(True)
            self.custom_clip_name_btn.setChecked(False)

        def clip_name_toggle():

            self.custom_clip_name_btn.setChecked(True)
            self.custom_shot_name_btn.setChecked(False)

        def batch_template_toggle():

            if self.custom_batch_template_btn.isChecked():
                self.custom_batch_group_template_path_label.setEnabled(True)
                self.custom_batch_template_lineedit.setEnabled(True)
                self.custom_batch_template_browse_btn.setEnabled(True)
            else:
                self.custom_batch_group_template_path_label.setEnabled(False)
                self.custom_batch_template_lineedit.setEnabled(False)
                self.custom_batch_template_browse_btn.setEnabled(False)

        def system_folder_toggle():

            if self.custom_system_folders_btn.isChecked():
                self.custom_system_folders_path_translated_label.setEnabled(True)
                self.custom_system_folders_path_lineedit.setEnabled(True)
                self.custom_system_folders_browse_btn.setEnabled(True)
                self.custom_system_path_token_push_button.setEnabled(True)
            else:
                self.custom_system_folders_path_translated_label.setEnabled(False)
                self.custom_system_folders_path_lineedit.setEnabled(False)
                self.custom_system_folders_browse_btn.setEnabled(False)
                self.custom_system_path_token_push_button.setEnabled(False)

        self.custom_selected_window = QtWidgets.QWidget()
        self.custom_selected_window.setMinimumSize(QtCore.QSize(1200, 360))
        self.custom_selected_window.setMaximumSize(QtCore.QSize(1200, 360))
        self.custom_selected_window.setWindowTitle('Create Shots for Selected Clips %s' % VERSION)
        self.custom_selected_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.custom_selected_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.custom_selected_window.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.custom_selected_window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.custom_selected_window.move((resolution.width() / 2) - (self.custom_selected_window.frameSize().width() / 2),
                                         (resolution.height() / 2) - (self.custom_selected_window.frameSize().height() / 2))

        # Labels

        self.custom_batch_options_label = FlameLabel('Batch Group Options', 'background', self.custom_selected_window)
        self.custom_batch_group_template_path_label = FlameLabel('Template Path', 'normal', self.custom_selected_window)
        self.custom_batch_group_dest_label = FlameLabel('Batch Group Dest', 'normal', self.custom_selected_window)
        self.custom_batch_group_start_frame_label = FlameLabel('Batch Start Frame', 'normal', self.custom_selected_window)
        self.custom_batch_group_additional_naming_label = FlameLabel('Additional Batch Naming', 'normal', self.custom_selected_window)

        self.custom_system_folders_path_label = FlameLabel('File System Shot Folders Path', 'background', self.custom_selected_window)
        self.custom_system_folders_path_translated_label = FlameLabel('', 'outline', self.custom_selected_window)

        self.custom_settings_label = FlameLabel('Settings', 'background', self.custom_selected_window)
        self.custom_shot_naming_label = FlameLabel('Shot Naming', 'background', self.custom_selected_window)
        self.custom_create_label = FlameLabel('Create', 'background', self.custom_selected_window)

        # LineEdits

        self.custom_batch_template_lineedit = FlameLineEdit(self.custom_batch_template_path, self.custom_selected_window)
        self.custom_batch_additional_naming_lineedit = FlameLineEdit(self.custom_batch_additional_naming, self.custom_selected_window)
        self.custom_system_folders_path_lineedit = FlameLineEdit(self.custom_system_folders_path, self.custom_selected_window)
        self.custom_system_folders_path_lineedit.textChanged.connect(update_system_folder_path)
        update_system_folder_path()

        # Batch Start Frame Slider

        self.custom_batch_start_frame_min_value = 1
        self.custom_batch_start_frame_max_value = 10000
        self.custom_batch_start_frame_start_value = self.custom_batch_start_frame

        def custom_batch_start_frame_spinbox_move_slider():
            self.custom_batch_start_frame_slider.setValue(int(self.custom_batch_start_frame_lineedit.text()))

        self.custom_batch_start_frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.custom_selected_window)
        self.custom_batch_start_frame_slider.setMaximumHeight(3)
        self.custom_batch_start_frame_slider.setMaximumWidth(75)
        self.custom_batch_start_frame_slider.setMinimum(self.custom_batch_start_frame_min_value)
        self.custom_batch_start_frame_slider.setMaximum(self.custom_batch_start_frame_max_value)
        self.custom_batch_start_frame_slider.setValue(self.custom_batch_start_frame_start_value)
        self.custom_batch_start_frame_slider.setStyleSheet('QSlider {color: #111111}'
                                                           'QSlider::disabled {color: #6a6a6a; background-color: #373737}'
                                                           'QSlider::groove:horizontal {background-color: #111111}'
                                                           'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
        self.custom_batch_start_frame_slider.setDisabled(True)

        self.custom_batch_start_frame_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.custom_batch_start_frame_start_value, parent=self.custom_selected_window)
        self.custom_batch_start_frame_lineedit.setMinimum(self.custom_batch_start_frame_min_value)
        self.custom_batch_start_frame_lineedit.setMaximum(self.custom_batch_start_frame_max_value)
        self.custom_batch_start_frame_lineedit.setMinimumHeight(28)
        self.custom_batch_start_frame_lineedit.setMaximumWidth(75)
        self.custom_batch_start_frame_lineedit.textChanged.connect(custom_batch_start_frame_spinbox_move_slider)
        self.custom_batch_start_frame_slider.raise_()

        # Push Button Menus

        batch_group_dest_options = ['Desktop', 'Library']
        self.custom_batch_group_dest_btn = FlamePushButtonMenu(self.custom_batch_group_dest, batch_group_dest_options, self.custom_selected_window)
        self.custom_batch_group_dest_btn.setMinimumWidth(150)

        system_path_token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>', 'SEQUENCE NAME': '<SEQNAME>', 'Sequence Name': '<SeqName>'}
        self.custom_system_path_token_push_button = FlameTokenPushButton('Add Token', system_path_token_dict, self.custom_system_folders_path_lineedit, self.custom_selected_window)

        # Pushbuttons

        self.custom_batch_template_btn = FlamePushButton(' Batch Template', self.custom_apply_batch_template, self.custom_selected_window)
        self.custom_batch_template_btn.clicked.connect(batch_template_toggle)

        self.custom_all_clips_btn = FlamePushButton(' All Clips/One Shot', self.all_clips, self.custom_selected_window)

        self.custom_shot_name_btn = FlamePushButton(' Shot Name', self.shot_name, self.custom_selected_window)
        self.custom_shot_name_btn.clicked.connect(shot_name_toggle)

        self.custom_clip_name_btn = FlamePushButton(' Clip Name', self.clip_name, self.custom_selected_window)
        self.custom_clip_name_btn.clicked.connect(clip_name_toggle)

        self.custom_folders_btn = FlamePushButton(' Folders', self.custom_folders, self.custom_selected_window)
        self.custom_folders_btn.clicked.connect(folder_toggle)

        self.custom_batch_group_btn = FlamePushButton(' Batch Groups', self.custom_batch_group, self.custom_selected_window)
        self.custom_batch_group_btn.clicked.connect(batch_group_button_toggle)

        self.custom_desktop_btn = FlamePushButton(' Desktops', self.custom_desktop, self.custom_selected_window)
        self.custom_desktop_btn.clicked.connect(desktop_toggle)

        self.custom_system_folders_btn = FlamePushButton(' System Folders', self.custom_system_folders, self.custom_selected_window)
        self.custom_system_folders_btn.clicked.connect(system_folder_toggle)

        # Buttons

        self.custom_batch_template_browse_btn = FlameButton('Browse', partial(self.batch_template_browse, self.custom_batch_template_lineedit, self.custom_selected_window), self.custom_selected_window)
        self.custom_system_folders_browse_btn = FlameButton('Browse', partial(self.system_folder_browse, self.custom_system_folders_path_lineedit, self.custom_selected_window), self.custom_selected_window)

        help_btn = FlameButton('Help', self.help, self.custom_selected_window)
        create_btn = FlameButton('Create', create_shots, self.custom_selected_window)
        cancel_btn = FlameButton('Cancel', self.custom_selected_window.close, self.custom_selected_window)

        # Check button states

        desktop_toggle()
        batch_group_button_toggle()
        batch_template_toggle()
        system_folder_toggle()

        # ------------------------------------------------------------- #

        # Window layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setVerticalSpacing(5)
        gridbox.setHorizontalSpacing(5)

        gridbox.setColumnMinimumWidth(2, 30)

        gridbox.addWidget(self.custom_create_label, 0, 0)
        gridbox.addWidget(self.custom_folders_btn, 1, 0)
        gridbox.addWidget(self.custom_batch_group_btn, 2, 0)
        gridbox.addWidget(self.custom_desktop_btn, 3, 0)
        gridbox.addWidget(self.custom_system_folders_btn, 4, 0)

        gridbox.addWidget(self.custom_settings_label, 0, 1)
        gridbox.addWidget(self.custom_all_clips_btn, 1, 1)
        gridbox.addWidget(self.custom_batch_template_btn, 2, 1)

        gridbox.addWidget(self.custom_shot_naming_label, 3, 1)
        gridbox.addWidget(self.custom_shot_name_btn, 4, 1)
        gridbox.addWidget(self.custom_clip_name_btn, 5, 1)

        gridbox.addWidget(self.custom_batch_options_label, 0, 4, 1, 5)
        gridbox.addWidget(self.custom_batch_group_template_path_label, 1, 4)
        gridbox.addWidget(self.custom_batch_template_lineedit, 1, 5, 1, 3)
        gridbox.addWidget(self.custom_batch_template_browse_btn, 1, 8)

        gridbox.addWidget(self.custom_batch_group_dest_label, 3, 4)
        gridbox.addWidget(self.custom_batch_group_dest_btn, 3, 5)

        gridbox.addWidget(self.custom_batch_group_start_frame_label, 2, 4)
        gridbox.addWidget(self.custom_batch_start_frame_slider, 2, 5, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.custom_batch_start_frame_lineedit, 2, 5)

        gridbox.addWidget(self.custom_batch_group_additional_naming_label, 2, 6)
        gridbox.addWidget(self.custom_batch_additional_naming_lineedit, 2, 7, 1, 2)

        gridbox.addWidget(self.custom_system_folders_path_label, 5, 4, 1, 5)
        gridbox.addWidget(self.custom_system_folders_path_translated_label, 6, 4, 1, 5)
        gridbox.addWidget(self.custom_system_folders_path_lineedit, 7, 4, 1, 3)
        gridbox.addWidget(self.custom_system_folders_browse_btn, 7, 7)
        gridbox.addWidget(self.custom_system_path_token_push_button, 7, 8)

        gridbox.setRowMinimumHeight(8, 30)

        gridbox.addWidget(help_btn, 9, 0)
        gridbox.addWidget(cancel_btn, 9, 7)
        gridbox.addWidget(create_btn, 9, 8)

        self.custom_selected_window.setLayout(gridbox)

        self.custom_selected_window.show()

    # ------------------------------------- #

    def create_shots(self, shot_name_list):
        '''
        Create shots from selected clips in media panel or media hub using shot name as shot name
        If shot names are not assigned to clips, shot name will be guessed
        '''

        import flame

        # Check for system folder path if creating system folders

        if self.create_shot_type_system_folders and not self.system_shot_folders_path:
                return message_box('<center>Enter path for creating system folders in Setup<br>Flame Main Menu -> pyFlame -> Create Shot Setup')

        # All clips are not going to single shot so all_clips is false

        all_clips = False

        if shot_name_list == []:
            return message_box('No Shots Found')
        print ('selection:', self.selection)
        shot_name_list.sort()
        print ('shot_name_list:', shot_name_list, '\n')

        # If creating folders, batch groups, or desktops, switch to batch so get access to MediaPanel

        if self.current_flame_tab == 'MediaHub':
            flame.set_current_tab('batch')

        # If creating desktops is selected, backup and clear current desktop

        if self.create_shot_type_desktop:
            self.copy_current_desktop()
            self.clear_current_desktop()

        # Create shot type based on saved settings

        print ('>>> creating shots...\n')

        if self.create_shot_type_folders:
            self.create_library('Folders')
            for shot_name in shot_name_list:
                self.create_media_panel_folders(shot_name, all_clips)

        elif self.create_shot_type_desktop:
            self.create_library('Desktops')
            for shot_name in shot_name_list:
                self.create_desktop(shot_name, all_clips, self.lib)

        elif self.create_shot_type_batch_group:
            self.create_library('Batch Groups')
            for shot_name in shot_name_list:
                self.create_batch_group(shot_name, all_clips, self.lib)

        # Create system folders if selected in settings

        self.system_folder_creation_errors = []

        if self.create_shot_type_system_folders:
            print ('\n')
            for shot_name in shot_name_list:
                root_folder_path = self.translate_system_shot_folder_path(shot_name)
                self.create_file_system_folders(root_folder_path, shot_name)

        if self.system_folder_creation_errors:
            problem_shots = ''
            for shot in self.system_folder_creation_errors:
                problem_shots = problem_shots + shot + ', '
            return message_box('Could not create folders for %s. Folders may already exists.' % problem_shots[:-2])

        # If desktops were created restore original desktop

        if self.create_shot_type_desktop:
            self.replace_desktop()

        print ('\ndone.\n')

    def create_shots_all_clips(self, shot_name):
        '''
        Create one shot from all selected clips in media panel or media hub.
        Uses shot name from first clip selected as shot name.
        '''

        import flame

        # Check for system folder path if creating system folders

        if self.create_shot_type_system_folders and not self.system_shot_folders_path:
                return message_box('<center>Enter path for creating system folders in Setup<br>Flame Main Menu -> pyFlame -> Create Shot Setup')

        all_clips = True

        if not shot_name:
            return message_box('No Shot Found')

        # If creating folders, batch groups, or desktops, switch to batch so get access to MediaPanel

        if self.current_flame_tab == 'MediaHub':
            flame.set_current_tab('batch')

        # If creating desktops is selected, backup and clear current desktop

        if self.create_shot_type_desktop:
            self.copy_current_desktop()
            self.clear_current_desktop()

        # Create shot type based on saved settings

        print ('>>> creating shot...')

        if self.create_shot_type_folders:
            self.create_library('Folders')
            self.create_media_panel_folders(shot_name, all_clips)

        elif self.create_shot_type_desktop:
            self.create_library('Desktops')
            self.create_desktop(shot_name, all_clips, self.lib)

        elif self.create_shot_type_batch_group:
            self.create_library('Batch Groups')
            self.create_batch_group(shot_name, all_clips, self.lib)

        # Create system folders if selected in settings

        self.system_folder_creation_errors = []

        if self.create_shot_type_system_folders:
            print ('\n')
            root_folder_path = self.translate_system_shot_folder_path(shot_name)
            self.create_file_system_folders(root_folder_path, shot_name)

        if self.system_folder_creation_errors:
            return message_box('Could not create folders for %s. Folders may already exists.' % shot_name)

        # If desktops were created restore original desktop

        if self.create_shot_type_desktop:
            self.replace_desktop()

        print ('\ndone.\n')

    # -------- #

    def create_shot_name_shots(self):
        '''
        Create shots for each shot name found in selected shots. One shot is created for each shot name found.
        All clips with the same shot name will be put into the same shot.
        Uses shot names assigned to clips. If shot names are not assigned, shot name will be guessed at from clip name.
        '''

        # Build list of shot names from selected clips

        shot_name_list = []

        for clip in self.selection:

            # Get shot name from assigned clip shot name

            if clip.versions[0].tracks[0].segments[0].shot_name != '':
                if clip.versions[0].tracks[0].segments[0].shot_name not in shot_name_list:
                    shot_name_list.append(str(clip.versions[0].tracks[0].segments[0].shot_name)[1:-1])
            else:
                # If shot name not assigned to clip, guess at shot name from clip name

                new_shot_name = self.get_shot_name_from_clip_name(clip)

                if new_shot_name not in shot_name_list:
                    shot_name_list.append(new_shot_name)

        # Create shots from shot name list

        self.create_shots(shot_name_list)

    def create_shot_name_shots_all_clips(self):
        '''
        Create shots for each shot name found in selected shots. One shot is created for each shot name found.
        All clips with the same shot name will be put into the same shot.
        Uses shot names assigned to clips. If shot names are not assigned, shot name will be guessed at from clip name.
        '''

        # Get first clip from selection

        clip = self.selection[0]

        # Get shot name from assigned clip shot name

        if clip.versions[0].tracks[0].segments[0].shot_name != '':
            shot_name = str(clip.versions[0].tracks[0].segments[0].shot_name)[1:-1]
        else:
            # If shot name not assigned to clip, guess at shot name from clip name

            shot_name = self.get_shot_name_from_clip_name(clip)

        print ('shot_name:', shot_name, '\n')

        # Create shots from shot name list

        self.create_shots_all_clips(shot_name)

    def create_clip_name_shots(self):
        '''
        Creates shots for each clip selected. Each shot will be named the same as the selected clip.
        '''

        # Build list of clip names to create shots from

        shot_name_list = [str(clip.name)[1:-1] for clip in self.selection]

        print ('shot_name_list:', shot_name_list, '\n')

        # Create shots from shot name list

        self.create_shots(shot_name_list)

    def create_clip_name_shots_all_clips(self):
        '''
        All selected clips to shot named after the clip name of the first clip selected
        '''

        # Build list of clip names to create shots from

        shot_name = [str(clip.name)[1:-1] for clip in self.selection][0]
        print ('shot_name:', shot_name, '\n')

        # Create shots from shot name list

        self.create_shots_all_clips(shot_name)

    def import_shot_name_shots(self):
        import flame

        # Create temp library

        self.temp_lib = self.ws.create_library('-- Temp Shot Library --')
        self.temp_lib.expanded = True

        # Import selected clips to library

        for clip in self.selection:
            clip_path = str(clip.path)
            print ('clip_path:', clip_path)

            # Import clip to temp library

            flame.import_clips(clip_path, self.temp_lib)

        # Replace selection with clip in temp library

        self.selection = [clip for clip in self.temp_lib.clips]

        # Create shots from all clips in temp library

        shot_name_list = []

        for clip in self.temp_lib.clips:
            new_shot_name = self.get_shot_name_from_clip_name(clip)

            if new_shot_name not in shot_name_list:
                shot_name_list.append(new_shot_name)

        print ('shot_name_list:', shot_name_list, '\n')

        self.create_shots(shot_name_list)

        # Remove temp library

        flame.delete(self.temp_lib)

    def import_shot_name_all_clips(self):
        import flame

        # Create temp library

        self.temp_lib = self.ws.create_library('-- Temp Shot Library --')
        self.temp_lib.expanded = True

        # Import selected clips to library

        for clip in self.selection:
            clip_path = str(clip.path)
            print ('clip_path:', clip_path)

            # Import clip to batchgroup

            flame.import_clips(clip_path, self.temp_lib)

        # Replace selection with clip in temp library

        self.selection = [clip for clip in self.temp_lib.clips]

        # Create shot from clips in temp library

        clip = self.temp_lib.clips[0]
        shot_name = self.get_shot_name_from_clip_name(clip)

        print ('shot_name:', shot_name, '\n')

        self.create_shots_all_clips(shot_name)

        # Remove temp library

        flame.delete(self.temp_lib)

    def import_clip_name_shots(self):
        import flame

        # Create temp library

        self.temp_lib = self.ws.create_library('-- Temp Shot Library --')
        self.temp_lib.expanded = True

        # Import selected clips to library

        for clip in self.selection:
            clip_path = str(clip.path)
            print ('clip_path:', clip_path)

            # Import clip to temp library

            flame.import_clips(clip_path, self.temp_lib)

        # Replace selection with clip in temp library

        self.selection = [clip for clip in self.temp_lib.clips]

        # Get list of clip names

        shot_name_list = [str(clip.name)[1:-1] for clip in self.selection]
        print ('shot_name_list:', shot_name_list, '\n')

        # Create shots from all clips in temp library

        self.create_shots(shot_name_list)

        # Remove temp library

        flame.delete(self.temp_lib)

    def import_clip_name_shots_all_clips(self):
        import flame

        # Create temp library

        self.temp_lib = self.ws.create_library('-- Temp Shot Library --')
        self.temp_lib.expanded = True

        # Import selected clips to library

        for clip in self.selection:
            clip_path = str(clip.path)
            print ('clip_path:', clip_path)

            # Import clip to temp library

            flame.import_clips(clip_path, self.temp_lib)

        # Replace selection with clip in temp library

        self.selection = [clip for clip in self.temp_lib.clips]

        # Get list of clip names

        shot_name = [str(clip.name)[1:-1] for clip in self.selection][0]
        print ('shot_name:', shot_name, '\n')

        # Create shots from all clips in temp library

        self.create_shots_all_clips(shot_name)

        # Remove temp library

        flame.delete(self.temp_lib)

    # -------- #

    def help(self):

        webbrowser.open('https://www.pyflame.com/create-shot')
        print ('openning www.pyflame.com/create-shot...\n')

    def sort_tree_items(self, tree):
        tree.sortItems(0, QtGui.Qt.AscendingOrder)

    def convert_reel_dict(self, reel_dict):

        converted_list = []

        for key, value in iter(reel_dict.items()):
            for v in value:
                converted_list.append(v)

        # print ('converted_list:', converted_list, '\n')

        return converted_list

    def get_shot_name_from_clip_name(self, clip):

        clip_name = str(clip.name)[1:-1]
        # print ('clip_name:', clip_name)

        # Split clip name into list by numbers in clip name

        shot_name_split = re.split(r'(\d+)', clip_name)
        shot_name_split = [s for s in shot_name_split if s != '']
        # print ('shot_name_split:', shot_name_split)

        # Recombine shot name split list into new batch group name
        # Else statement is used if clip name starts with number

        if shot_name_split[1].isalnum():
            new_shot_name = shot_name_split[0] + shot_name_split[1]
        else:
            new_shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]

        return new_shot_name

    def translate_system_shot_folder_path(self, shot_name):
        import flame

        # print ('path to translate:', self.system_shot_folders_path)

        seq_name = ''
        seq_name_caps = ''

        if '<SeqName>' in self.system_shot_folders_path or '<SEQNAME>' in self.system_shot_folders_path:
            seq_name = re.split('[^a-zA-Z]', shot_name)[0]
            if '<SEQNAME>' in self.system_shot_folders_path:
                seq_name_caps = seq_name.upper()

        # Replace any tokens in system shot folder path

        root_folder_path = re.sub('<ProjectName>', flame.project.current_project.name, self.system_shot_folders_path)
        root_folder_path = re.sub('<ProjectNickName>', flame.project.current_project.nickname, root_folder_path)
        root_folder_path = re.sub('<SeqName>', seq_name, root_folder_path)
        root_folder_path = re.sub('<SEQNAME>', seq_name_caps, root_folder_path)

        # print ('translated root_folder_path:', root_folder_path)

        return root_folder_path

    def copy_current_desktop(self):
        import flame

        # Copy current desktop to Temp Library

        self.temp_lib = self.ws.create_library('Temp__Desk__Lib')

        self.desktop_name = str(self.desktop.name)[1:-1]

        self.desktop_copy = flame.media_panel.copy(self.desktop, self.temp_lib)

    def clear_current_desktop(self):
        import flame

        # Clear out current desktop

        for b in self.desktop.batch_groups:
            flame.delete(b)
        for r in self.desktop.reel_groups:
            flame.delete(r)

    def replace_desktop(self):
        import flame

        # When done creating shot desktops replace original desktop from Temp Library

        flame.media_panel.move(self.desktop_copy, self.ws.desktop)
        flame.delete(self.desktop.batch_groups[0])
        self.ws.desktop.name = self.desktop_name
        flame.delete(self.temp_lib)

    def copy_clips(self, shot_name, all_clips, dest):
        import flame

        # Copy selected clips into media panel destination

        for clip in self.selection:
            if all_clips:
                flame.media_panel.copy(clip, dest)
            else:
                if shot_name in str(clip.versions[0].tracks[0].segments[0].shot_name) or shot_name in str(clip.name):
                    flame.media_panel.copy(clip, dest)

    def batch_template_browse(self, lineedit, parent_window):

        batch_path = QtWidgets.QFileDialog.getOpenFileName(parent_window, 'Select .batch File', lineedit.text(), 'Batch Files (*.batch)')[0]
        lineedit.setText(batch_path)

    def system_folder_browse(self, lineedit, parent_window):

        dir_path = str(QtWidgets.QFileDialog.getExistingDirectory(parent_window, 'Select Directory', lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))
        if os.path.isdir(dir_path):
            lineedit.setText(dir_path)

    # -------- #
    # Create

    def create_library(self, create_type):

        # Create new library if destination is Library

        if self.batch_group_dest == 'Library' or create_type == 'Folders':
            new_lib_name = 'New Shot %s' % create_type
            self.lib = self.ws.create_library(new_lib_name)
            self.lib.expanded = True

            print ('    library created: %s\n' % new_lib_name)

    def create_media_panel_folders(self, shot_name, all_clips):
        '''
        Create Shot Folders and copy clips into shot folder
        '''

        def folder_loop(value, shot_folder):
            for k, v in iter(value.items()):
                folder = shot_folder.create_folder(k)
                if self.clip_dest_folder == k:
                    self.copy_clips(shot_name, all_clips, folder)
                folder_loop(v, folder)

        # Create shot folders

        for key1, value1 in iter(self.folder_dict.items()):
            shot_folder = self.lib.create_folder(shot_name)
            print ('    shot folder created: %s' % shot_name)

            # Check if main folder is clip dest

            if self.clip_dest_folder == shot_name:
                self.copy_clips(shot_name, all_clips, shot_folder)

            # Check if creating desktop

            if self.create_shot_type_desktop:
                self.create_desktop(shot_name, all_clips, shot_folder)

            # Check if creating batch group

            elif self.create_shot_type_batch_group:
                self.create_batch_group(shot_name, all_clips, shot_folder)

            # Create sub-folders

            folder_loop(value1, shot_folder)

    def create_batch_group(self, shot_name, all_clips, dest):
        import flame

        def set_render_node_values(render_node):

            # Apply values to render node from clip

            render_node.frame_rate = clip_frame_rate
            render_node.range_end = clip.duration
            render_node.source_timecode = clip_timecode
            render_node.record_timecode = clip_timecode
            render_node.shot_name = shot_name

        # Create batch group

        self.batch_group = flame.batch.create_batch_group(shot_name, duration=100, reels=self.schematic_reels, shelf_reels=self.shelf_reels)

        # If creating batch group from selected clip add clip to batch group, add nodes, modify render nodes

        if self.selection:

            # Get index of reel clips will be copied to

            self.clip_reel_index = self.schematic_reels.index(self.clip_dest_reel)

            # Copy clips into batch group

            self.copy_clips(shot_name, all_clips, self.batch_group.reels[self.clip_reel_index])

            # Get background clip

            all_clips = flame.batch.nodes
            clip = flame.batch.nodes[0]

            # Set batch group duration

            self.batch_group.duration = clip.duration

            self.batch_group.start_frame = self.batch_start_frame

            # Get clip timecode and frame rate

            imported_clip = self.batch_group.reels[self.clip_reel_index].clips[0]
            clip_timecode = imported_clip.start_time
            clip_frame_rate = imported_clip.frame_rate
            # print ('clip_timecode:', clip_timecode)
            # print ('clip_frame_rate:', clip_frame_rate, '\n')

            # Force batch group name in case duplicate name already exists in desktop

            if self.batch_additional_naming:
                self.batch_group.name = shot_name + self.batch_additional_naming
            else:
                self.batch_group.name = shot_name

            # If Apply Template is select load batch template otherwise use generic default node layout

            if self.apply_batch_template:

                # Append template batch setup to new batch

                self.batch_group.append_setup(self.batch_template_path)

                # Confirm template has plate_in Mux node - if not delete batch and give error message

                plate_in_mux_present = [node.name for node in self.batch_group.nodes if node.name == 'plate_in']

                if not plate_in_mux_present:
                    flame.delete(self.batch_group)
                    return message_box('Batch Template should have Mux node named: plate_in')

                # Check for nodes with context set - Context does not carry over when batch setup is appended.
                # Nodes in template need to have note attached with desired context view: context 1, context 2...
                # Render nodes can not have context set through python

                for node in flame.batch.nodes:
                    if 'context' in str(node.note):
                        print (node.name)
                        context_view = str(node.note).rsplit(' ', 1)[1][:-1]
                        while not context_view.isnumeric():
                            context_view = context_view[:-1]
                        print (context_view)
                        node.set_context(int(context_view))

                # Reposition plate to left of plate_in Mux

                for node in self.batch_group.nodes:
                    if node.name == 'plate_in':
                        plate_in_mux = node

                clip.pos_x = plate_in_mux.pos_x - 300
                clip.pos_y = plate_in_mux.pos_y + 30
                clip_y_pos = clip.pos_y

                # Connect main plate to plate_in Mux

                flame.batch.connect_nodes(clip, 'Default', plate_in_mux, 'Default')

                # Remove main clip from clip list then reposition any additional clips under main plate in schematic

                all_clips.pop(0)

                for additional_clip in all_clips:
                    additional_clip.pos_x = clip.pos_x
                    additional_clip.pos_y = clip_y_pos - 150
                    clip_y_pos = additional_clip.pos_y

                # Apply clip settings to render node

                for node in self.batch_group.nodes:
                    if node.type == 'Render':
                        set_render_node_values(node)

            else:

                # Create default node setup
                # Clip -> Mux -> Mux -> Render/Write Node

                # Create mux nodes

                plate_in_mux = self.batch_group.create_node('Mux')
                plate_in_mux.name = 'plate_in'
                plate_in_mux.set_context(1, 'Default')
                plate_in_mux.pos_x = 400
                plate_in_mux.pos_y = -30

                render_out_mux = self.batch_group.create_node('Mux')
                render_out_mux.name = 'render_out'
                render_out_mux.set_context(2, 'Default')
                render_out_mux.pos_x = plate_in_mux.pos_x + 1600
                render_out_mux.pos_y = plate_in_mux.pos_y - 30

                # Add Render or Write File node to batch group

                if self.add_render_node:

                    # Create render node

                    render_node = flame.batch.create_node('Render')

                    # Apply clip settings to render node

                    set_render_node_values(render_node)

                else:

                    # Create write node

                    image_format = self.write_file_image_format.split(' ', 1)[0]
                    bit_depth = self.write_file_image_format.split(' ', 1)[1]
                    print ('image_format:', image_format)
                    print ('bit_depth:', bit_depth)

                    render_node = flame.batch.create_node('Write File')
                    render_node.media_path = self.write_file_media_path
                    render_node.media_path_pattern = self.write_file_pattern
                    render_node.create_clip = self.write_file_create_open_clip
                    render_node.include_setup = self.write_file_include_setup
                    render_node.create_clip_path = self.write_file_create_open_clip_value
                    render_node.include_setup_path = self.write_file_include_setup_value
                    render_node.file_type = image_format
                    render_node.bit_depth = bit_depth

                    if self.write_file_compression:
                        render_node.compress = True
                        render_node.compress_mode = self.write_file_compression
                    if image_format == 'Jpeg':
                        render_node.quality = 100

                    render_node.frame_index_mode = self.write_file_frame_index
                    render_node.frame_padding = int(self.write_file_padding)
                    render_node.frame_rate = clip_frame_rate
                    render_node.range_end = clip.duration
                    render_node.source_timecode = clip_timecode
                    render_node.record_timecode = clip_timecode
                    render_node.shot_name = shot_name

                    # render_node.name = '<batch iteration>'

                    if self.write_file_create_open_clip:
                        render_node.version_mode = 'Follow Iteration'
                        render_node.version_name = 'v<version>'
                        render_node.version_padding = 2

                render_node.pos_x = render_out_mux.pos_x + 400
                render_node.pos_y = render_out_mux.pos_y -30

                # Connect nodes

                flame.batch.connect_nodes(clip, 'Default', plate_in_mux, 'Default')
                flame.batch.connect_nodes(plate_in_mux, 'Result', render_out_mux, 'Default')
                flame.batch.connect_nodes(render_out_mux, 'Result', render_node, 'Default')

        # Frame all nodes

        flame.go_to('Batch')
        flame.batch.frame_all()

        # Move batch group from desktop to destination

        if self.batch_group_dest == 'Library':
            flame.media_panel.move(self.batch_group, dest)

        print ('    batch group created: %s' % shot_name)

    def create_desktop(self, shot_name, all_clips, dest):
        import flame

        def build_reel_group():

            # Create reel group

            reel_group = self.ws.desktop.create_reel_group(str(self.reel_group).split("'", 2)[1])

            # Create extra reels in group past four

            for x in range(len(self.reel_group) - 4):
                reel_group.create_reel('')

            for reel in reel_group.reels:
                if 'Sequences' not in str(reel.name):
                    reel.name = self.reel_group[reel_group.reels.index(reel)]

            reel_group.name = str(self.reel_group_dict.keys())[12:-3]

        self.create_batch_group(shot_name, all_clips, self.desktop)
        self.desktop.name = shot_name

        # Create reel group

        if self.add_reel_group:
            build_reel_group()

        #  Remove old batch group

        flame.delete(self.desktop.batch_groups[0])

        # Copy desktop to Destination

        flame.media_panel.copy(self.desktop, dest)

        self.clear_current_desktop()

        print ('    desktop created: %s' % shot_name)

    def create_file_system_folders(self, root_folder_path, shot_name):
        import flame

        def folder_loop(value, shot_folder):
            for k, v in iter(value.items()):
                folder = os.path.join(shot_folder, k)
                os.makedirs(folder)
                folder_loop(v, folder)

        # Create shot folders

        # print ('>>> creating file system shot folders <<<\n')

        for key, value, in iter(self.file_system_folder_dict.items()):
            shot_folder = os.path.join(root_folder_path, shot_name)
            if not os.path.isdir(shot_folder):
                os.makedirs(shot_folder)
                print ('    file system shot folder created: %s' % shot_name)
                folder_loop(value, shot_folder)
            else:
                self.system_folder_creation_errors.append(shot_name)

        flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

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

def setup(selection):
    '''
    Loads setup UI where custom folder/batch group/desktop/system folder shot structures can be defined
    '''

    script = CreateShotFolders(selection)
    script.setup()

def create_shot_folders(selection):
    '''
    Loads UI where custom empty shot folders/batch groups/desktops/system folders can be created from
    '''

    script = CreateShotFolders(selection)
    script.create_shot_folder_window()

def create_custom_selected_shots(selection):
    '''
    Loads UI where custom empty shot folders/batch groups/desktops/system folders can be created from
    '''

    script = CreateShotFolders(selection)
    script.custom_shot_from_selected_window()

def clip_shot_name_to_shot(selection):
    '''
    Create shots based off of shot names assigned to clips
    If no shot name is assigned to clip, shot name will be guessed at from clip name
    Clips with same shot name with be put into same shot folder/batch group/desktop
    '''

    script = CreateShotFolders(selection)
    script.create_shot_name_shots()

def clip_shot_name_to_shot_all_clips(selection):
    '''
    Create shot based off of shot name assigned to first clip in selection.
    If no shot name is assigned to clip, shot name will be guessed at from clip name.
    All selected clips will go into the same shot folder/batch group/desktop.
    '''

    script = CreateShotFolders(selection)
    script.create_shot_name_shots_all_clips()

def clip_name_to_shot(selection):
    '''
    Create shots based on name of clip
    One batch will be created for each clip
    '''

    script = CreateShotFolders(selection)
    script.create_clip_name_shots()

def clip_name_to_shot_all_clips(selection):
    '''
    Create shots based on name of clip
    All selected clips will go into the same shot folder/batch group/desktop.
    '''

    script = CreateShotFolders(selection)
    script.create_clip_name_shots_all_clips()

def import_shot_name_to_shot(selection):
    '''
    Import selected to clip to separate shots with shot name
    '''

    script = CreateShotFolders(selection)
    script.import_shot_name_shots()

def import_shot_name_to_shot_all(selection):
    '''
    Import all selected clips to single shot with shot name
    Shot name comes from shot name of first selected clip
    '''

    script = CreateShotFolders(selection)
    script.import_shot_name_all_clips()

def import_clip_name_to_shot(selection):
    '''
    Import selected to clip to separate shots with clip name
    '''

    script = CreateShotFolders(selection)
    script.import_clip_name_shots()

def import_clip_name_to_shot_all_clips(selection):
    '''
    Import all selected clips to single shot with clip name
    Shot name comes from clip name of first selected clip
    '''

    script = CreateShotFolders(selection)
    script.import_clip_name_shots_all_clips()

#-------------------------------------#
# SCOPES

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            if not isinstance(item.parent, flame.PyReel):
                return True
    return False

def scope_file(selection):
    import re

    for item in selection:
        item_path = str(item.path)
        item_ext = re.search(r'\.\w{3}$', item_path, re.I)
        if item_ext != (None):
            return True
    return False

#-------------------------------------#

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Create Shot Setup',
                    'execute': setup,
                    'minimumVersion': '2021.2'
                }
            ]
        }

    ]

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Create Shot...',
            'actions': [
                {
                    'name': 'Folders',
                    'execute': create_shot_folders,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Import to Shot - Shot Name',
                    'isVisible': scope_file,
                    'execute': import_shot_name_to_shot,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Import to Shot - Shot Name - All Clips / One Shot',
                    'isVisible': scope_file,
                    'execute': import_shot_name_to_shot_all,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Import to Shot - Clip Name',
                    'isVisible': scope_file,
                    'execute': import_clip_name_to_shot,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Import to Shot - Clip Name - All Clips / One Shot',
                    'isVisible': scope_file,
                    'execute': import_clip_name_to_shot_all_clips,
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
                    'name': 'Folders',
                    'execute': create_shot_folders,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Custom Shots',
                    'isVisible': scope_clip,
                    'execute': create_custom_selected_shots,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Clips to Shot - Shot Name',
                    'isVisible': scope_clip,
                    'execute': clip_shot_name_to_shot,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Clips to Shot - Shot Name - All Clips / One Shot',
                    'isVisible': scope_clip,
                    'execute': clip_shot_name_to_shot_all_clips,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Clips to Shot - Clip Name',
                    'isVisible': scope_clip,
                    'execute': clip_name_to_shot,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Clips to Shot - Clip Name - All Clips / One shot',
                    'isVisible': scope_clip,
                    'execute': clip_name_to_shot_all_clips,
                    'minimumVersion': '2021.2'
                }
            ]
        }
    ]
