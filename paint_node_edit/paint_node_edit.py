'''
Script Name: Paint Node Edit
Script Version: 3.0
Flame Version: 2021.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 02.01.20
Update Date: 05.22.21

Custom Action Type: Batch Paint Node

Description:

    Edit paint stroke durations in paint node.

    Right-click on paint node -> Paint -> Delete Paint Strokes
    Right-click on paint node -> Paint -> Paint Strokes to Sequence: All
    Right-click on paint node -> Paint -> Paint Strokes to Range: All
    Right-click on paint node -> Paint -> Paint Strokes to Current: All
    Right-click on paint node -> Paint -> Paint Strokes to Sequence: Stroke Range
    Right-click on paint node -> Paint -> Paint Strokes to Range: Stroke Range
    Right-click on paint node -> Paint -> Paint Strokes to Current: Stroke Range

To install:

    Copy script into /opt/Autodesk/shared/python/paint_node_edit

Updates:

v3.0 05.22.21

    Updated to be compatible with Flame 2022/Python 3.7

v2.2 01.24.21

    Updated/Improved UI

v2.1 01.21.21:

    Speed improvements - script no longer needs to save and reload batch setup

    Removed paint stroke tracking - paint stroke limitations made tracking useless

v1.4 02.07.20:

    Fixed bug that caused Delete Paint Stokes not to work if last stroke in stack was deleted

v1.3 02.04.20:

    Four new menu options have been added:

        Delete Paint Strokes - Select a range of strokes to delete

        Paint Strokes to Sequence: Range - Select a range of strokes to change to sequence

        Paint Strokes to Range: Range - Select a range of strokes last over a range of frames

        Paint Strokes to Current Frame: Range - Select a range of strokes to be set to current frame

    The old menu options remain but have been named to:

        Paint Strokes to Sequence: All

        Paint Strokes to Range: All

        Paint Strokes to Current Frame: All

v1.1 02.01.20:

    There will be three options to choose from:

        Paint Strokes to Sequence

        Paint Strokes to Range

        Paint Strokes to Current Frame

    Changes will be applied to ALL strokes in selected paint node.
'''

from __future__ import print_function
import os

VERSION = 'v3.0'

class EditPaint(object):

    def __init__(self, selection, lifespanstart, lifespanend, range_type, menu_size):
        import flame
        import re

        print ('\n', '>' * 20, 'paint node edit - %s %s' % (range_type, VERSION), '<' * 20, '\n')

        self.range_type = range_type

        self.menu_size = menu_size

        self.paint_node = [n for n in selection][0]

        self.paint_node_name = str(self.paint_node.name)[1:-1]
        print ('paint_node:', self.paint_node_name)

        self.lifespanstart = lifespanstart
        self.lifespanend = lifespanend

        # Get batchgroup name

        self.batchgroup_name = str(flame.batch.name)[1:-1]
        print ('batchgroup_name:', self.batchgroup_name)

        # Get batch start frame

        self.batch_start_frame = int(str(flame.batch.start_frame))
        print ('batch_start_frame:', self.batch_start_frame)

        # Get batch duration

        self.batch_duration = int(str(flame.batch.duration))
        print ('batch_duration:', self.batch_duration)

        # Batch end frame

        self.batch_end_frame = (self.batch_start_frame + self.batch_duration) - 1

        # Create temp paint folder

        self.temp_paint_path = '/opt/Autodesk/shared/python/paint_node_edit/temp_paint/'
        if not os.path.isdir(self.temp_paint_path):
            os.makedirs(self.temp_paint_path)

        # Path to save paint node

        self.paint_node_path = os.path.join(self.temp_paint_path, self.paint_node_name + '.paint_node')

        # Save paint node

        self.paint_node.save_node_setup(self.paint_node_path)

        # Load saved paint node

        get_paint_node = open(self.paint_node_path, 'r')
        values = get_paint_node.read().splitlines()

        self.paint_node_code = values[0]

        get_paint_node.close()

        # ------------------------ #

        # Misc Variables

        self.stroke = ''
        self.stroke_x_pos = ''
        self.stroke_y_pos = ''
        self.x_shift = ''
        self.y_shift = ''
        self.rotation = ''
        self.x_scaling = ''
        self.y_scaling = ''

        # Get last stroke number

        try:
            self.last_stroke = int(re.findall('<stroke(.*?)>', self.paint_node_code)[-1])
            print ('last_stroke:', self.last_stroke, '\n')
        except:
            self.last_stroke = ''

        # If no strokes put up message window

        if self.last_stroke != '':
            if self.range_type == 'sequence all':
                self.editpaint_node_all()
            elif self.range_type == 'current frame all':
                self.editpaint_node_all()
            else:
                self.main_window()
        else:
            message_box('No strokes to edit - Paint something!')

    def main_window(self):
        from PySide2 import QtWidgets, QtCore
        import flame

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
                self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"')
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
                    self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"')

                def revert_color():
                    self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"')

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

                blank_btn = QtWidgets.QPushButton('', calc_window)
                blank_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                blank_btn.setMinimumSize(40, 28)
                blank_btn.setMaximumSize(40, 28)
                blank_btn.setDisabled(True)
                blank_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                plus_minus_btn = QtWidgets.QPushButton('+/-', calc_window)
                plus_minus_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                plus_minus_btn.setMinimumSize(40, 28)
                plus_minus_btn.setMaximumSize(40, 28)
                plus_minus_btn.clicked.connect(plus_minus)
                plus_minus_btn.setStyleSheet('color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"')

                add_btn = QtWidgets.QPushButton('Add', calc_window)
                add_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                add_btn.setMinimumSize(40, 28)
                add_btn.setMaximumSize(40, 28)
                add_btn.clicked.connect(partial(add_sub, 'add'))
                add_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                sub_btn = QtWidgets.QPushButton('Sub', calc_window)
                sub_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                sub_btn.setMinimumSize(40, 28)
                sub_btn.setMaximumSize(40, 28)
                sub_btn.clicked.connect(partial(add_sub, 'sub'))
                sub_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                clear_btn = QtWidgets.QPushButton('C', calc_window)
                clear_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                clear_btn.setMinimumSize(40, 28)
                clear_btn.setMaximumSize(40, 28)
                clear_btn.clicked.connect(clear)
                clear_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                equal_btn = QtWidgets.QPushButton('=', calc_window)
                equal_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                equal_btn.setMinimumSize(40, 28)
                equal_btn.setMaximumSize(40, 28)
                equal_btn.clicked.connect(equals)
                equal_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                div_btn = QtWidgets.QPushButton('/', calc_window)
                div_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                div_btn.setMinimumSize(40, 28)
                div_btn.setMaximumSize(40, 28)
                div_btn.clicked.connect(partial(button_press, '/'))
                div_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                mult_btn = QtWidgets.QPushButton('*', calc_window)
                mult_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                mult_btn.setMinimumSize(40, 28)
                mult_btn.setMaximumSize(40, 28)
                mult_btn.clicked.connect(partial(button_press, '*'))
                mult_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _7_btn = QtWidgets.QPushButton('7', calc_window)
                _7_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _7_btn.setMinimumSize(40, 28)
                _7_btn.setMaximumSize(40, 28)
                _7_btn.clicked.connect(partial(button_press, '7'))
                _7_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _8_btn = QtWidgets.QPushButton('8', calc_window)
                _8_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _8_btn.setMinimumSize(40, 28)
                _8_btn.setMaximumSize(40, 28)
                _8_btn.clicked.connect(partial(button_press, '8'))
                _8_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _9_btn = QtWidgets.QPushButton('9', calc_window)
                _9_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _9_btn.setMinimumSize(40, 28)
                _9_btn.setMaximumSize(40, 28)
                _9_btn.clicked.connect(partial(button_press, '9'))
                _9_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                minus_btn = QtWidgets.QPushButton('-', calc_window)
                minus_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                minus_btn.setMinimumSize(40, 28)
                minus_btn.setMaximumSize(40, 28)
                minus_btn.clicked.connect(partial(button_press, '-'))
                minus_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _4_btn = QtWidgets.QPushButton('4', calc_window)
                _4_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _4_btn.setMinimumSize(40, 28)
                _4_btn.setMaximumSize(40, 28)
                _4_btn.clicked.connect(partial(button_press, '4'))
                _4_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _5_btn = QtWidgets.QPushButton('5', calc_window)
                _5_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _5_btn.setMinimumSize(40, 28)
                _5_btn.setMaximumSize(40, 28)
                _5_btn.clicked.connect(partial(button_press, '5'))
                _5_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _6_btn = QtWidgets.QPushButton('6', calc_window)
                _6_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _6_btn.setMinimumSize(40, 28)
                _6_btn.setMaximumSize(40, 28)
                _6_btn.clicked.connect(partial(button_press, '6'))
                _6_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                plus_btn = QtWidgets.QPushButton('+', calc_window)
                plus_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                plus_btn.setMinimumSize(40, 28)
                plus_btn.setMaximumSize(40, 28)
                plus_btn.clicked.connect(partial(button_press, '+'))
                plus_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _1_btn = QtWidgets.QPushButton('1', calc_window)
                _1_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _1_btn.setMinimumSize(40, 28)
                _1_btn.setMaximumSize(40, 28)
                _1_btn.clicked.connect(partial(button_press, '1'))
                _1_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _2_btn = QtWidgets.QPushButton('2', calc_window)
                _2_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _2_btn.setMinimumSize(40, 28)
                _2_btn.setMaximumSize(40, 28)
                _2_btn.clicked.connect(partial(button_press, '2'))
                _2_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                _3_btn = QtWidgets.QPushButton('3', calc_window)
                _3_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _3_btn.setMinimumSize(40, 28)
                _3_btn.setMaximumSize(40, 28)
                _3_btn.clicked.connect(partial(button_press, '3'))
                _3_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                enter_btn = QtWidgets.QPushButton('Enter', calc_window)
                enter_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                enter_btn.setMinimumSize(28, 61)
                enter_btn.clicked.connect(enter)
                enter_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                #  --------------------------------------- #

                _0_btn = QtWidgets.QPushButton('0', calc_window)
                _0_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                _0_btn.setMinimumSize(80, 28)
                _0_btn.clicked.connect(partial(button_press, '0'))
                _0_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

                point_btn = QtWidgets.QPushButton('.', calc_window)
                point_btn.setFocusPolicy(QtCore.Qt.NoFocus)
                point_btn.setMinimumSize(40, 28)
                point_btn.setMaximumSize(40, 28)
                point_btn.clicked.connect(partial(button_press, '.'))
                point_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
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
                    self.setStyleSheet('color: #d9d9d9; background-color: #474e58; selection-color: #d9d9d9; selection-background-color: #474e58; font: 14px "Discreet"')

            def mouseReleaseEvent(self, event):
                from PySide2 import QtGui

                if event.button() == QtCore.Qt.LeftButton:

                    # Open calculator if button is released within 10 pixels of button click

                    if event.pos().x() in range((self.pos_at_press.x() - 10), (self.pos_at_press.x() + 10)) and event.pos().y() in range((self.pos_at_press.y() - 10), (self.pos_at_press.y() + 10)):
                        self.calculator()
                    else:
                        self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"')

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

        def all_strokes_to_range(self):

            self.window.setWindowTitle('Edit Paint Node %s - All Paint Strokes to Frame Range' % VERSION)

            # Labels

            self.range1_label = QtWidgets.QLabel('Frame Range', self.window)
            self.range1_label.setAlignment(QtCore.Qt.AlignCenter)
            self.range1_label.setMinimumSize(QtCore.QSize(260, 28))
            self.range1_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')

            self.range2_label = QtWidgets.QLabel('Start', self.window)
            self.range2_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range2_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            self.range3_label = QtWidgets.QLabel('End', self.window)
            self.range3_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range3_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            # End Frame lineedit init - for slider compare

            self.end_frame_lineedit = ''

            # Start Frame Slider

            self.start_frame_min_value = 1
            self.start_frame_max_value = (int(str(flame.batch.duration)))
            self.start_frame_start_value = 1

            def start_set_slider():
                self.start_frame_slider.setValue(int(self.start_frame_lineedit.text()))

                # Check value against other slider

                if int(self.start_frame_lineedit.text()) > int(self.end_frame_lineedit.text()):
                    self.end_frame_lineedit.setText(self.start_frame_lineedit.text())

            self.start_frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.start_frame_slider.setMaximumHeight(3)
            self.start_frame_slider.setMaximumWidth(100)
            self.start_frame_slider.setMinimum(self.start_frame_min_value)
            self.start_frame_slider.setMaximum(self.start_frame_max_value)
            self.start_frame_slider.setValue(self.start_frame_start_value)
            self.start_frame_slider.setStyleSheet('QSlider {color: #111111}'
                                                  'QSlider::groove:horizontal {background-color: #111111}'
                                                  'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.start_frame_slider.setDisabled(True)

            self.start_frame_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.start_frame_start_value, parent=self.window)
            self.start_frame_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.start_frame_lineedit.setMinimum(self.start_frame_min_value)
            self.start_frame_lineedit.setMaximum(self.start_frame_max_value)
            self.start_frame_lineedit.setMinimumHeight(28)
            self.start_frame_lineedit.setMaximumWidth(100)
            self.start_frame_lineedit.textChanged.connect(start_set_slider)
            self.start_frame_slider.raise_()

            # End Frame Slider

            self.end_frame_min_value = 1
            self.end_frame_max_value = (int(str(flame.batch.duration)))
            self.end_frame_start_value = (int(str(flame.batch.duration)))

            def end_set_slider():
                self.end_frame_slider.setValue(int(self.end_frame_lineedit.text()))

                # Check value against other slider

                if int(self.end_frame_lineedit.text()) < int(self.start_frame_lineedit.text()):
                    self.start_frame_lineedit.setText(self.end_frame_lineedit.text())

            self.end_frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.end_frame_slider.setMaximumHeight(3)
            self.end_frame_slider.setMaximumWidth(100)
            self.end_frame_slider.setMinimum(self.end_frame_min_value)
            self.end_frame_slider.setMaximum(self.end_frame_max_value)
            self.end_frame_slider.setValue(self.end_frame_start_value)
            self.end_frame_slider.setStyleSheet('QSlider {color: #111111}'
                                                'QSlider::groove:horizontal {background-color: #111111}'
                                                'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.end_frame_slider.setDisabled(True)

            self.end_frame_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.end_frame_start_value, parent=self.window)
            self.end_frame_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.end_frame_lineedit.setMinimum(self.end_frame_min_value)
            self.end_frame_lineedit.setMaximum(self.end_frame_max_value)
            self.end_frame_lineedit.setMinimumHeight(28)
            self.end_frame_lineedit.setMaximumWidth(100)
            self.end_frame_lineedit.textChanged.connect(end_set_slider)
            self.end_frame_slider.raise_()

            # Buttons

            self.apply_btn.clicked.connect(self.editpaint_node_range_all)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_frame_slider, 2, 1, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.start_frame_lineedit, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_frame_slider, 2, 4, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.end_frame_lineedit, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

        def delete_strokes_window(self):

            self.window.setWindowTitle('Edit Paint Node %s - Delete Paint Strokes: Stroke Range' % VERSION)

            # Labels

            self.range1_label = QtWidgets.QLabel('Stroke Range', self.window)
            self.range1_label.setAlignment(QtCore.Qt.AlignCenter)
            self.range1_label.setMinimumSize(QtCore.QSize(260, 28))
            self.range1_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')

            self.range2_label = QtWidgets.QLabel('Start', self.window)
            self.range2_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range2_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            self.range3_label = QtWidgets.QLabel('End', self.window)
            self.range3_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range3_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            # End Stroke lineedit init - for slider compare

            self.end_stroke_lineedit = ''

            # Start Stroke Slider

            self.start_stroke_min_value = 0
            self.start_stroke_max_value = self.last_stroke
            self.start_stroke_start_value = 0

            def start_set_slider():
                self.start_stroke_slider.setValue(int(self.start_stroke_lineedit.text()))

                # Check value against other slider

                if int(self.start_stroke_lineedit.text()) > int(self.end_stroke_lineedit.text()):
                    self.end_stroke_lineedit.setText(self.start_stroke_lineedit.text())

            self.start_stroke_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.start_stroke_slider.setMaximumHeight(3)
            self.start_stroke_slider.setMaximumWidth(100)
            self.start_stroke_slider.setMinimum(self.start_stroke_min_value)
            self.start_stroke_slider.setMaximum(self.start_stroke_max_value)
            self.start_stroke_slider.setValue(self.start_stroke_start_value)
            self.start_stroke_slider.setStyleSheet('QSlider {color: #111111}'
                                                   'QSlider::groove:horizontal {background-color: #111111}'
                                                   'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.start_stroke_slider.setDisabled(True)

            self.start_stroke_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.start_stroke_start_value, parent=self.window)
            self.start_stroke_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.start_stroke_lineedit.setMinimum(self.start_stroke_min_value)
            self.start_stroke_lineedit.setMaximum(self.start_stroke_max_value)
            self.start_stroke_lineedit.setMinimumHeight(28)
            self.start_stroke_lineedit.setMaximumWidth(100)
            self.start_stroke_lineedit.textChanged.connect(start_set_slider)
            self.start_stroke_slider.raise_()

            # End Stroke Slider

            self.end_stroke_min_value = 0
            self.end_stroke_max_value = self.last_stroke
            self.end_stroke_start_value = self.last_stroke

            def end_set_slider():
                self.end_stroke_slider.setValue(int(self.end_stroke_lineedit.text()))

                # Check value against other slider

                if int(self.end_stroke_lineedit.text()) < int(self.start_stroke_lineedit.text()):
                    self.start_stroke_lineedit.setText(self.end_stroke_lineedit.text())

            self.end_stroke_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.end_stroke_slider.setMaximumHeight(3)
            self.end_stroke_slider.setMaximumWidth(100)
            self.end_stroke_slider.setMinimum(self.end_stroke_min_value)
            self.end_stroke_slider.setMaximum(self.end_stroke_max_value)
            self.end_stroke_slider.setValue(self.end_stroke_start_value)
            self.end_stroke_slider.setStyleSheet('QSlider {color: #111111}'
                                                 'QSlider::groove:horizontal {background-color: #111111}'
                                                 'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.end_stroke_slider.setDisabled(True)

            self.end_stroke_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.end_stroke_start_value, parent=self.window)
            self.end_stroke_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.end_stroke_lineedit.setMinimum(self.end_stroke_min_value)
            self.end_stroke_lineedit.setMaximum(self.end_stroke_max_value)
            self.end_stroke_lineedit.setMinimumHeight(28)
            self.end_stroke_lineedit.setMaximumWidth(100)
            self.end_stroke_lineedit.textChanged.connect(end_set_slider)
            self.end_stroke_slider.raise_()

            # Buttons

            self.apply_btn.clicked.connect(self.delete_paint_strokes)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_stroke_slider, 2, 1, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.start_stroke_lineedit, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_stroke_slider, 2, 4, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.end_stroke_lineedit, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

        def range_window(self):

            self.window.setWindowTitle('Edit Paint Node %s - Paint Stroke Range to Frame Range' % VERSION)

            # Labels

            self.range1_label = QtWidgets.QLabel('Stroke Range', self.window)
            self.range1_label.setAlignment(QtCore.Qt.AlignCenter)
            self.range1_label.setMinimumSize(QtCore.QSize(260, 28))
            self.range1_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')

            self.range2_label = QtWidgets.QLabel('Start', self.window)
            self.range2_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range2_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            self.range3_label = QtWidgets.QLabel('End', self.window)
            self.range3_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range3_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            self.range4_label = QtWidgets.QLabel('Frame Range', self.window)
            self.range4_label.setAlignment(QtCore.Qt.AlignCenter)
            self.range4_label.setMinimumSize(QtCore.QSize(260, 28))
            self.range4_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')

            self.range5_label = QtWidgets.QLabel('Start', self.window)
            self.range5_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range5_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            self.range6_label = QtWidgets.QLabel('End', self.window)
            self.range6_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range6_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            # End Frame lineedit init - for slider compare

            self.end_frame_lineedit = ''

            # Start Frame Slider

            self.start_frame_min_value = 1
            self.start_frame_max_value = (int(str(flame.batch.duration)))
            self.start_frame_start_value = 1

            def start_set_slider():
                self.start_frame_slider.setValue(int(self.start_frame_lineedit.text()))

                # Check value against other slider

                if int(self.start_frame_lineedit.text()) > int(self.end_frame_lineedit.text()):
                    self.end_frame_lineedit.setText(self.start_frame_lineedit.text())

            self.start_frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.start_frame_slider.setMaximumHeight(3)
            self.start_frame_slider.setMaximumWidth(100)
            self.start_frame_slider.setMinimum(self.start_frame_min_value)
            self.start_frame_slider.setMaximum(self.start_frame_max_value)
            self.start_frame_slider.setValue(self.start_frame_start_value)
            self.start_frame_slider.setStyleSheet('QSlider {color: #111111}'
                                                          'QSlider::groove:horizontal {background-color: #111111}'
                                                          'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.start_frame_slider.setDisabled(True)

            self.start_frame_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.start_frame_start_value, parent=self.window)
            self.start_frame_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.start_frame_lineedit.setMinimum(self.start_frame_min_value)
            self.start_frame_lineedit.setMaximum(self.start_frame_max_value)
            self.start_frame_lineedit.setMinimumHeight(28)
            self.start_frame_lineedit.setMaximumWidth(100)
            self.start_frame_lineedit.textChanged.connect(start_set_slider)
            self.start_frame_slider.raise_()

            # End Frame Slider

            self.end_frame_min_value = 1
            self.end_frame_max_value = (int(str(flame.batch.duration)))
            self.end_frame_start_value = (int(str(flame.batch.duration)))

            def end_set_slider():
                self.end_frame_slider.setValue(int(self.end_frame_lineedit.text()))

                # Check value against other slider

                if int(self.end_frame_lineedit.text()) < int(self.start_frame_lineedit.text()):
                    self.start_frame_lineedit.setText(self.end_frame_lineedit.text())

            self.end_frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.end_frame_slider.setMaximumHeight(3)
            self.end_frame_slider.setMaximumWidth(100)
            self.end_frame_slider.setMinimum(self.end_frame_min_value)
            self.end_frame_slider.setMaximum(self.end_frame_max_value)
            self.end_frame_slider.setValue(self.end_frame_start_value)
            self.end_frame_slider.setStyleSheet('QSlider {color: #111111}'
                                                        'QSlider::groove:horizontal {background-color: #111111}'
                                                        'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.end_frame_slider.setDisabled(True)

            self.end_frame_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.end_frame_start_value, parent=self.window)
            self.end_frame_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.end_frame_lineedit.setMinimum(self.end_frame_min_value)
            self.end_frame_lineedit.setMaximum(self.end_frame_max_value)
            self.end_frame_lineedit.setMinimumHeight(28)
            self.end_frame_lineedit.setMaximumWidth(100)
            self.end_frame_lineedit.textChanged.connect(end_set_slider)
            self.end_frame_slider.raise_()

            # End Stroke lineedit init - for slider compare

            self.end_stroke_lineedit = ''

            # Start Stroke Slider

            self.start_stroke_min_value = 0
            self.start_stroke_max_value = self.last_stroke
            self.start_stroke_start_value = 0

            def start_set_slider():
                self.start_stroke_slider.setValue(int(self.start_stroke_lineedit.text()))

                # Check value against other slider

                if int(self.start_stroke_lineedit.text()) > int(self.end_stroke_lineedit.text()):
                    self.end_stroke_lineedit.setText(self.start_stroke_lineedit.text())

            self.start_stroke_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.start_stroke_slider.setMaximumHeight(3)
            self.start_stroke_slider.setMaximumWidth(100)
            self.start_stroke_slider.setMinimum(self.start_stroke_min_value)
            self.start_stroke_slider.setMaximum(self.start_stroke_max_value)
            self.start_stroke_slider.setValue(self.start_stroke_start_value)
            self.start_stroke_slider.setStyleSheet('QSlider {color: #111111}'
                                                           'QSlider::groove:horizontal {background-color: #111111}'
                                                           'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.start_stroke_slider.setDisabled(True)

            self.start_stroke_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.start_stroke_start_value, parent=self.window)
            self.start_stroke_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.start_stroke_lineedit.setMinimum(self.start_stroke_min_value)
            self.start_stroke_lineedit.setMaximum(self.start_stroke_max_value)
            self.start_stroke_lineedit.setMinimumHeight(28)
            self.start_stroke_lineedit.setMaximumWidth(100)
            self.start_stroke_lineedit.textChanged.connect(start_set_slider)
            self.start_stroke_slider.raise_()

            # End Stroke Slider

            self.end_stroke_min_value = 0
            self.end_stroke_max_value = self.last_stroke
            self.end_stroke_start_value = self.last_stroke

            def end_set_slider():
                self.end_stroke_slider.setValue(int(self.end_stroke_lineedit.text()))

                # Check value against other slider

                if int(self.end_stroke_lineedit.text()) < int(self.start_stroke_lineedit.text()):
                    self.start_stroke_lineedit.setText(self.end_stroke_lineedit.text())

            self.end_stroke_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.end_stroke_slider.setMaximumHeight(3)
            self.end_stroke_slider.setMaximumWidth(100)
            self.end_stroke_slider.setMinimum(self.end_stroke_min_value)
            self.end_stroke_slider.setMaximum(self.end_stroke_max_value)
            self.end_stroke_slider.setValue(self.end_stroke_start_value)
            self.end_stroke_slider.setStyleSheet('QSlider {color: #111111}'
                                                         'QSlider::groove:horizontal {background-color: #111111}'
                                                         'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.end_stroke_slider.setDisabled(True)

            self.end_stroke_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.end_stroke_start_value, parent=self.window)
            self.end_stroke_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.end_stroke_lineedit.setMinimum(self.end_stroke_min_value)
            self.end_stroke_lineedit.setMaximum(self.end_stroke_max_value)
            self.end_stroke_lineedit.setMinimumHeight(28)
            self.end_stroke_lineedit.setMaximumWidth(100)
            self.end_stroke_lineedit.textChanged.connect(end_set_slider)
            self.end_stroke_slider.raise_()

            # Buttons

            self.apply_btn.clicked.connect(self.editpaint_strokes_range_range)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_stroke_slider, 2, 1, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.start_stroke_lineedit, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_stroke_slider, 2, 4, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.end_stroke_lineedit, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

            self.gridbox.addWidget(self.range4_label, 4, 0, 1, 5)

            self.gridbox.addWidget(self.range5_label, 6, 0)
            self.gridbox.addWidget(self.start_frame_slider, 6, 1, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.start_frame_lineedit, 6, 1)

            self.gridbox.addWidget(self.range6_label, 6, 3)
            self.gridbox.addWidget(self.end_frame_slider, 6, 4, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.end_frame_lineedit, 6, 4)

            self.gridbox.setRowMinimumHeight(7, 35)

        def stroke_to_current_or_sequence_range_window(self):

            if self.range_type == 'sequence range':
                title = 'Paint Strokes to Sequence: Stroke Range'
            else:
                title = 'Paint Strokes to Current Frame: Stroke Range'

            self.window.setWindowTitle('Edit Paint Node %s - %s' % (VERSION, title))

            # Labels

            self.range1_label = QtWidgets.QLabel('Stroke Range', self.window)
            self.range1_label.setAlignment(QtCore.Qt.AlignCenter)
            self.range1_label.setMinimumSize(QtCore.QSize(260, 28))
            self.range1_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')

            self.range2_label = QtWidgets.QLabel('Start', self.window)
            self.range2_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range2_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            self.range3_label = QtWidgets.QLabel('End', self.window)
            self.range3_label.setMinimumSize(QtCore.QSize(100, 28))
            self.range3_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                            'QLabel:disabled {color: #6a6a6a}')

            # End Stroke lineedit init - for slider compare

            self.end_stroke_lineedit = ''

            # Start Stroke Slider

            self.start_stroke_min_value = 0
            self.start_stroke_max_value = self.last_stroke
            self.start_stroke_start_value = 0

            def start_set_slider():
                self.start_stroke_slider.setValue(int(self.start_stroke_lineedit.text()))

                # Check value against other slider

                if int(self.start_stroke_lineedit.text()) > int(self.end_stroke_lineedit.text()):
                    self.end_stroke_lineedit.setText(self.start_stroke_lineedit.text())

            self.start_stroke_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.start_stroke_slider.setMaximumHeight(3)
            self.start_stroke_slider.setMaximumWidth(100)
            self.start_stroke_slider.setMinimum(self.start_stroke_min_value)
            self.start_stroke_slider.setMaximum(self.start_stroke_max_value)
            self.start_stroke_slider.setValue(self.start_stroke_start_value)
            self.start_stroke_slider.setStyleSheet('QSlider {color: #111111}'
                                                   'QSlider::groove:horizontal {background-color: #111111}'
                                                   'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.start_stroke_slider.setDisabled(True)

            self.start_stroke_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.start_stroke_start_value, parent=self.window)
            self.start_stroke_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.start_stroke_lineedit.setMinimum(self.start_stroke_min_value)
            self.start_stroke_lineedit.setMaximum(self.start_stroke_max_value)
            self.start_stroke_lineedit.setMinimumHeight(28)
            self.start_stroke_lineedit.setMaximumWidth(100)
            self.start_stroke_lineedit.textChanged.connect(start_set_slider)
            self.start_stroke_slider.raise_()

            # End Stroke Slider

            self.end_stroke_min_value = 0
            self.end_stroke_max_value = self.last_stroke
            self.end_stroke_start_value = self.last_stroke

            def end_set_slider():
                self.end_stroke_slider.setValue(int(self.end_stroke_lineedit.text()))

                # Check value against other slider

                if int(self.end_stroke_lineedit.text()) < int(self.start_stroke_lineedit.text()):
                    self.start_stroke_lineedit.setText(self.end_stroke_lineedit.text())

            self.end_stroke_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
            self.end_stroke_slider.setMaximumHeight(3)
            self.end_stroke_slider.setMaximumWidth(100)
            self.end_stroke_slider.setMinimum(self.end_stroke_min_value)
            self.end_stroke_slider.setMaximum(self.end_stroke_max_value)
            self.end_stroke_slider.setValue(self.end_stroke_start_value)
            self.end_stroke_slider.setStyleSheet('QSlider {color: #111111}'
                                                 'QSlider::groove:horizontal {background-color: #111111}'
                                                 'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            self.end_stroke_slider.setDisabled(True)

            self.end_stroke_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, self.end_stroke_start_value, parent=self.window)
            self.end_stroke_lineedit.setAlignment(QtCore.Qt.AlignCenter)
            self.end_stroke_lineedit.setMinimum(self.end_stroke_min_value)
            self.end_stroke_lineedit.setMaximum(self.end_stroke_max_value)
            self.end_stroke_lineedit.setMinimumHeight(28)
            self.end_stroke_lineedit.setMaximumWidth(100)
            self.end_stroke_lineedit.textChanged.connect(end_set_slider)
            self.end_stroke_slider.raise_()

            # Buttons

            self.apply_btn.clicked.connect(self.editpaint_strokes_range)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_stroke_slider, 2, 1, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.start_stroke_lineedit, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_stroke_slider, 2, 4, QtCore.Qt.AlignBottom)
            self.gridbox.addWidget(self.end_stroke_lineedit, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(300, self.menu_size))
        self.window.setMaximumSize(QtCore.QSize(600, 500))
        self.window.setWindowTitle('Edit Paint Node %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #212121')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Buttons

        self.apply_btn = QtWidgets.QPushButton('Apply', self.window)
        self.apply_btn.setMinimumSize(QtCore.QSize(110, 28))
        self.apply_btn.setMaximumSize(QtCore.QSize(110, 28))
        self.apply_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.apply_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                                     'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        self.cancel_btn = QtWidgets.QPushButton('Cancel', self.window)
        self.cancel_btn.setMinimumSize(QtCore.QSize(110, 28))
        self.cancel_btn.setMaximumSize(QtCore.QSize(110, 28))
        self.cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                      'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                                      'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
        self.cancel_btn.clicked.connect(self.window.close)

        if self.range_type == 'range all':
            all_strokes_to_range(self)
        elif self.range_type == 'delete strokes':
            delete_strokes_window(self)
        elif self.range_type == 'range range':
            range_window(self)
        elif 'sequence range' or 'current frame range' in self.range_type:
            stroke_to_current_or_sequence_range_window(self)

        # Window Layout

        self.hbox05 = QtWidgets.QHBoxLayout()
        self.hbox05.addStretch(5)
        self.hbox05.addWidget(self.cancel_btn)
        self.hbox05.addStretch(5)
        self.hbox05.addWidget(self.apply_btn)
        self.hbox05.addStretch(5)

        # Main VBox

        vbox = QtWidgets.QVBoxLayout()
        vbox.setMargin(20)

        vbox.addLayout(self.gridbox)
        vbox.addStretch(2)
        vbox.addLayout(self.hbox05)

        self.window.setLayout(vbox)

        self.window.show()

    def editpaint_strokes_range_range(self):
        import re

        # Variables from window

        start_stroke = int(str(self.start_stroke_lineedit.text()))
        end_stroke = int(str(self.end_stroke_lineedit.text()))

        start_frame = int(str(self.start_frame_lineedit.text()))
        end_frame = int(str(self.end_frame_lineedit.text()))

        if end_stroke >= start_stroke:
            if end_frame >= start_frame:
                try:
                    self.window.close()
                except:
                    pass

                # Split paint node into strokes

                split_list = self.paint_node_code.split('<PrStroke')

                loop_range = end_stroke - start_stroke + 1

                # Remove selected strokes

                for s in range(loop_range):
                    stroke_start_name = '<stroke%s>' % start_stroke
                    #stroke_end_name = '</stroke%s>' % start_stroke

                    for stroke in split_list:
                        if stroke_start_name in stroke:
                            stroke = '<PrStroke' + stroke

                            # Replace lifespan values

                            new_stroke = re.sub('LifeSpanStart="(.*?)"', 'LifeSpanStart="%s"' % start_frame, stroke)
                            new_stroke = re.sub('LifeSpanEnd="(.*?)"', 'LifeSpanEnd="%s"' % end_frame, new_stroke)

                            # Replace stroke code

                            self.paint_node_code = self.paint_node_code.replace(stroke, new_stroke)

                    start_stroke = start_stroke + 1

                self.save_paint_node()
            else:
                message_box('End frame should be equal to<br>or higher than start frame')
        else:
            message_box('End stroke should be equal to<br>or higher than start stroke')

    def editpaint_strokes_range(self):
        import re

        start_stroke = int(str(self.start_stroke_lineedit.text()))
        end_stroke = int(str(self.end_stroke_lineedit.text()))

        if end_stroke >= start_stroke:
            self.window.close()

            # Split paint node into strokes

            split_list = self.paint_node_code.split('<PrStroke')

            loop_range = end_stroke - start_stroke + 1
            #print 'loop_range:', loop_range

            # Edit selected strokes

            for s in range(loop_range):
                stroke_start_name = '<stroke%s>' % start_stroke

                for stroke in split_list:
                    if stroke_start_name in stroke:
                        stroke = '<PrStroke' + stroke

                        # Replace lifespan values

                        new_stroke = re.sub('LifeSpanStart="(.*?)"', 'LifeSpanStart="%s"' % self.lifespanstart, stroke)
                        new_stroke = re.sub('LifeSpanEnd="(.*?)"', 'LifeSpanEnd="%s"' % self.lifespanend, new_stroke)

                        # Replace stroke code

                        self.paint_node_code = self.paint_node_code.replace(stroke, new_stroke)

                start_stroke = start_stroke + 1

            self.save_paint_node()

        else:
            message_box('End stroke should be equal to<br>or higher than start stroke')

    def delete_paint_strokes(self):

        delete_start = int(str(self.start_stroke_lineedit.text()))
        delete_end = int(str(self.end_stroke_lineedit.text()))

        print ('delete_start_stroke:', delete_start)
        print ('delete_end_stoke:', delete_end, '\n')

        if delete_end >= delete_start:

            self.window.close()

            delete_start_stroke = delete_start

            # Split paint node into strokes

            split_list = self.paint_node_code.split('<PrStroke')

            split_list_fixed = []

            for line in split_list:
                new_line = line.rsplit('</PrStroke>')[0]
                split_list_fixed.append(new_line)

            loop_range = delete_end - delete_start + 1

            # Remove selected strokes

            for s in range(loop_range):
                stroke_start_name = '<stroke%s>' % delete_start
                stroke_end_name = '</stroke%s>' % delete_start

                for n in split_list_fixed:
                    if stroke_start_name in n:
                        n = '<PrStroke' + n + '</PrStroke>'
                        # print 'stoke_code:', n, '\n', '\n'

                        # Remove selected stroke string

                        self.paint_node_code = self.paint_node_code.replace(n, '')

                delete_start = delete_start + 1

            #print self.paint_node_code

            loop_range = self.last_stroke - delete_end
            stroke_num = delete_end + 1
            new_stroke_num = delete_start_stroke

            for s in range(loop_range):
                stroke_start_name = '<stroke%s>' % stroke_num
                stroke_end_name = '</stroke%s>' % stroke_num
                # print 'stroke_start_name:', stroke_start_name
                # print 'stroke_end_name:', stroke_end_name

                new_stroke_start_name = '<stroke%s>' % new_stroke_num
                new_stroke_end_name = '</stroke%s>' % new_stroke_num
                # print 'new_stroke_start_name:', new_stroke_start_name
                # print 'new_stroke_end_name:', new_stroke_end_name

                self.paint_node_code = self.paint_node_code.replace(stroke_start_name, new_stroke_start_name)
                self.paint_node_code = self.paint_node_code.replace(stroke_end_name, new_stroke_end_name)

                new_stroke_num = new_stroke_num + 1
                stroke_num = stroke_num + 1
                # print 'new_stroke_num:', new_stroke_num
                # print 'stroke_num:', stroke_num

            # print '\n', self.paint_node_code, '\n'

            print ('deleted strokes %s to %s\n' % (delete_start, delete_end))

            self.save_paint_node()
        else:
            message_box('End stroke should be equal to<br>or higher than start stroke')

    def editpaint_node_all(self):
        import re

        # Replace lifespan values

        self.paint_node_code = re.sub('LifeSpanStart="(.*?)"', 'LifeSpanStart="%s"' % self.lifespanstart, self.paint_node_code)
        self.paint_node_code = re.sub('LifeSpanEnd="(.*?)"', 'LifeSpanEnd="%s"' % self.lifespanend, self.paint_node_code)

        self.save_paint_node()

    def editpaint_node_range_all(self):

        start = int(str(self.start_frame_lineedit.text()))
        end = int(str(self.end_frame_lineedit.text()))

        print ('start_frame:', start)
        print ('end_frame:', end)

        if end >= start:
            self.lifespanstart = str(start)
            self.lifespanend = str(end)

            self.window.close()

            self.editpaint_node_all()
        else:
            message_box('End frame should be equal to<br>or higher than start frame')

    #------------------------------------#

    def save_paint_node(self):
        import shutil
        import flame

        # Save paint node setup file

        paint_code = []

        paint_code.insert(0, self.paint_node_code)

        # Overwrite old paint node with new paint node

        out_file = open(self.paint_node_path, 'w')
        for line in paint_code:
            print(line, file=out_file)
        out_file.close()

        self.paint_node.load_node_setup(self.paint_node_path)

        # Delete temp folder

        shutil.rmtree(self.temp_paint_path)

        print ('\n>>> paint node updated <<<\n')

#------------------------------------#

def message_box(message):
    from PySide2 import QtWidgets, QtCore

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

# ----------- #

def edit_sequence_all(selection):

    menu_size = 150

    lifespanstart = '-2147483648'
    lifespanend = '2147483647'

    range_type = 'sequence all'

    EditPaint(selection, lifespanstart, lifespanend, range_type, menu_size)

def edit_current_frame_all(selection):
    import flame

    menu_size = 150

    current_frame = str(flame.batch.current_frame)
    print ('current_frame:', current_frame, '\n')

    lifespanstart = current_frame
    lifespanend = current_frame

    range_type = 'current frame all'

    EditPaint(selection, lifespanstart, lifespanend, range_type, menu_size)

def edit_range_all(selection):

    menu_size = 150

    lifespanstart = 1
    lifespanend = 1

    range_type = 'range all'

    EditPaint(selection, lifespanstart, lifespanend, range_type, menu_size)

# ----------- #

def delete_strokes(selection):

    menu_size = 150

    lifespanstart = 1
    lifespanend = 1

    range_type = 'delete strokes'

    EditPaint(selection, lifespanstart, lifespanend, range_type, menu_size)

def edit_sequence_range(selection):

    menu_size = 150

    lifespanstart = '-2147483648'
    lifespanend = '2147483647'

    range_type = 'sequence range'

    EditPaint(selection, lifespanstart, lifespanend, range_type, menu_size)

def edit_range(selection):

    menu_size = 260

    lifespanstart = 1
    lifespanend = 1

    range_type = 'range range'

    EditPaint(selection, lifespanstart, lifespanend, range_type, menu_size)

def edit_current_frame_range(selection):
    import flame

    menu_size = 150

    current_frame = str(flame.batch.current_frame)
    # print 'current_frame:', current_frame , '\n'

    lifespanstart = current_frame
    lifespanend = current_frame

    range_type = 'current frame range'

    EditPaint(selection, lifespanstart, lifespanend, range_type, menu_size)

#------------------------------------#

def scope_paint_node(selection):
    import flame

    for item in selection:
        if item.type == 'Paint':
            return True
    return False

#------------------------------------#

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Paint Node...',
            'actions': [
                {
                    'name': 'Delete Paint Strokes',
                    'isVisible': scope_paint_node,
                    'execute': delete_strokes,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Paint Strokes to Sequence: All',
                    'isVisible': scope_paint_node,
                    'execute': edit_sequence_all,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Paint Strokes to Range: All',
                    'isVisible': scope_paint_node,
                    'execute': edit_range_all,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Paint Strokes to Current Frame: All',
                    'isVisible': scope_paint_node,
                    'execute': edit_current_frame_all,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Paint Strokes to Sequence: Stroke Range',
                    'isVisible': scope_paint_node,
                    'execute': edit_sequence_range,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Paint Strokes to Range: Stroke Range',
                    'isVisible': scope_paint_node,
                    'execute': edit_range,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Paint Strokes to Current Frame: Stroke Range',
                    'isVisible': scope_paint_node,
                    'execute': edit_current_frame_range,
                    'minimumVersion': '2021.1'
                }
            ]
        }
    ]
