'''
Script Name: mp4 gui
Script Version: 1.1
Flame Version: 2022
Written by: Autodesk - modified by John Geehreng
Creation Date: 01.23.21
Update Date: 02.26.21

Description: Make MP4's using a GUI. Modify lines 551-553 to customize the default paths. ffmpeg must be installed for this to work.
'''
from __future__ import print_function

folder_name = "Encoder"
action_name = "Export MP4's GUI"

import logging
import os
import shlex
import traceback
import errno


global export_ffmpegs

def main_window(selection):
    import os
    import flame
    from PySide2 import QtWidgets, QtCore

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
                self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
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

                    if calc_lineedit.text() != '':

                        new_value = calculate_entry()

                        self.setValue(float(new_value))

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
                delta /= 5  # Make movement less sensitive.
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

    def export_browse():
        import datetime
        global export_path, now, today

        dateandtime = datetime.datetime.now()
        today = (dateandtime.strftime("%Y-%m-%d"))
        now = (dateandtime.strftime("%H%M"))
        jobsFolder = "/Volumes/vfx/UC_Jobs"
        projectName = flame.project.current_project.nickname
        export_base_dir = os.path.join(jobsFolder, projectName, "FROM_FLAME", today, now)
        try:
            os.makedirs(export_base_dir)
        except Exception as e:
            if e.errno == errno.EEXIST:
                pass
        export_path = QtWidgets.QFileDialog()
        export_path.setDirectory(export_base_dir)
        export_path.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        export_path.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        export_path.setFileMode(QtWidgets.QFileDialog.Directory)
        if export_path.exec_():
            export_path = str(export_path.selectedFiles()[0])
            export_path_entry.setText(export_path)
            return export_path

    def ok_button():
        global crf_entry, audio_bitrate_entry, scale_factor
        window.close()
        # Testing Entries
        print ("\n" *1)
        print ("*" * 10)
        print ("Export Path: " + export_path)
        crf_entry = int(crf_lineedit.text())
        print ("CRF: " + str(crf_entry))
        audio_bitrate_entry = str(audio_btn.currentText()).replace("   ","")+"k"
        print ("Audio Bitrate: " + audio_bitrate_entry)
        resolution_entry = str(scale_btn.currentText())

        if resolution_entry == "  Full Res":
            # print ("scale by a factor of 1")
            scale_factor = 1
        if resolution_entry == "  1/2 Res":
            # print ("scale by a factor of .5")
            scale_factor = 2
        if resolution_entry == "  1/4 Res":
            # print ("scale by a factor of  .25")
            scale_factor = 4

        print ("Resolution: " + str(resolution_entry))
        print ("scale_factor: " + str(scale_factor))

        bg_entry = str(background_btn.currentText())
        print ("FG or BG Entry: " + str(bg_entry))

        if bg_entry == "Background":
            # print ("False")
            bg_entry = False
            print ("Foreground Processing: " + str(bg_entry))
            print ("*" * 10)
            print ("\n" *1)
            export_ffmpegs(selection, export_path, foreground=False)
            qt_app_instance = QtWidgets.QApplication.instance()
            qt_app_instance.clipboard().setText(export_path)
            # copy_me(selection)
            job_message = "Exporting to " + str(export_path) + " and path copied! Opening Finder..."
            return message_box(job_message)

        else:
            # print ("True")
            bg_entry = True
            print ("Foreground Processing: " + str(bg_entry))
            print ("*" * 10)
            print ("\n" *1)
            export_ffmpegs(selection, export_path, foreground=True)
            qt_app_instance = QtWidgets.QApplication.instance()
            qt_app_instance.clipboard().setText(export_path)
            # copy_me(selection)
            job_message = "Exported to " + str(export_path) + " and path copied! Opening Finder..."
            return message_box(job_message)



    window = QtWidgets.QWidget()
    window.setMinimumSize(600, 230)
    window.setWindowTitle("Export MP4's")
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    window.setStyleSheet('background-color: #313131')

    # Center window in linux

    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                (resolution.height() / 2) - (window.frameSize().height() / 2))

    # Labels

    crf_label = QtWidgets.QLabel('CRF', window)
    crf_label.setMinimumSize(QtCore.QSize(125, 35))
    crf_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                 'QLabel:disabled {color: #6a6a6a}')

    audio_bitrate_label = QtWidgets.QLabel('Audio Bitrate [kbps]', window)
    audio_bitrate_label.setMinimumSize(QtCore.QSize(125, 35))
    audio_bitrate_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                 'QLabel:disabled {color: #6a6a6a}')

    scale_factor_label = QtWidgets.QLabel('Resolution', window)
    scale_factor_label.setMinimumSize(QtCore.QSize(125, 35))
    scale_factor_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                     'QLabel:disabled {color: #6a6a6a}')

    background_label = QtWidgets.QLabel('FG or BG Export', window)
    background_label.setMinimumSize(QtCore.QSize(125, 35))
    background_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                     'QLabel:disabled {color: #6a6a6a}')

    export_label = QtWidgets.QLabel('Export Path', window)
    export_label.setMinimumSize(QtCore.QSize(125, 35))
    export_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                            'QLabel:disabled {color: #6a6a6a}')

    # CRF Slider

    crf_min_value = 0
    crf_max_value = 51
    crf_start_value = 18

    def constant_rate_factor_slider():
        crf_slider.setValue(int(crf_lineedit.text()))

    crf_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, window)
    crf_slider.setMaximumHeight(3)
    crf_slider.setMaximumWidth(100)
    crf_slider.setMinimum(crf_min_value)
    crf_slider.setMaximum(crf_max_value)
    crf_slider.setValue(crf_start_value)
    crf_slider.setStyleSheet('QSlider {color: #111111}'
                                    'QSlider::groove:horizontal {background-color: #111111}'
                                    'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
    crf_slider.setDisabled(True)

    crf_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, crf_start_value, parent=window)
    crf_lineedit.setAlignment(QtCore.Qt.AlignCenter)
    crf_lineedit.setMinimum(crf_min_value)
    crf_lineedit.setMaximum(crf_max_value)
    crf_lineedit.setMinimumHeight(28)
    crf_lineedit.setMaximumWidth(100)
    crf_lineedit.setToolTip('With 0 being Lossless, 51 being terrible, and 17 or 18 being the sweet spot.')
    crf_lineedit.textChanged.connect(constant_rate_factor_slider)
    crf_slider.raise_()

    # Entry

    export_path_entry = QtWidgets.QLineEdit('', window)
    export_path_entry.setMinimumHeight(28)
    export_path_entry.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                 'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

    # Buttons

    export_path_btn = QtWidgets.QPushButton('Browse', window)
    export_path_btn.clicked.connect(export_browse)
    export_path_btn.setMinimumSize(QtCore.QSize(100, 28))
    export_path_btn.setMaximumSize(QtCore.QSize(100, 28))
    export_path_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    export_path_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                 'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    #Push buttons
    audio_btn = QtWidgets.QComboBox(window)
    audio_btn_options = ['   96','   128','   160','   192','   256','   320']
    audio_btn.addItems(audio_btn_options)
    audio_btn.setCurrentIndex(3)
    audio_btn.setMinimumSize(QtCore.QSize(100, 26))
    audio_btn.setStyleSheet('background: #373e47; font: 14pt "Discreet"')

    background_btn = QtWidgets.QComboBox(window)
    background_btn_options = ['Foreground', 'Background']
    background_btn.addItems(background_btn_options)
    background_btn.setCurrentIndex(1)
    background_btn.setMinimumSize(QtCore.QSize(100, 26))
    background_btn.setMaximumSize(QtCore.QSize(100, 28))
    background_btn.setStyleSheet('background: #373e47; font: 14pt "Discreet"')
    background_btn.setToolTip('Set to Background as default because Foreground takes a while to encode.')

    scale_btn = QtWidgets.QComboBox(window)
    scale_btn_options = ['  Full Res', '  1/2 Res', '  1/4 Res']
    scale_btn.addItems(scale_btn_options)
    scale_btn.setCurrentIndex(0)
    scale_btn.setMinimumSize(QtCore.QSize(100, 26))
    scale_btn.setMaximumSize(QtCore.QSize(100, 28))
    scale_btn.setStyleSheet('background: #373e47; font: 14pt "Discreet"')

    ok_btn = QtWidgets.QPushButton('Ok', window)
    ok_btn.clicked.connect(ok_button)

    ok_btn.setMinimumSize(QtCore.QSize(100, 28))
    ok_btn.setMaximumSize(QtCore.QSize(100, 28))
    ok_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    ok_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    cancel_btn = QtWidgets.QPushButton('Cancel', window)
    cancel_btn.clicked.connect(window.close)
    cancel_btn.setMinimumSize(QtCore.QSize(100, 28))
    cancel_btn.setMaximumSize(QtCore.QSize(100, 28))
    cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                             'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                             'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    # Layout

    gridlayout = QtWidgets.QGridLayout()
    gridlayout.setMargin(30)
    gridlayout.setVerticalSpacing(5)
    gridlayout.setHorizontalSpacing(5)

    gridlayout.addWidget(crf_label, 0, 0)
    gridlayout.addWidget(crf_lineedit, 0, 1)
    gridlayout.addWidget(crf_slider, 0, 1, QtCore.Qt.AlignBottom)

    gridlayout.setColumnMinimumWidth(2, 100)

    gridlayout.addWidget(audio_bitrate_label, 0, 3)
    gridlayout.addWidget(audio_btn, 0, 4)

    gridlayout.addWidget(scale_factor_label, 1, 0)
    gridlayout.addWidget(scale_btn, 1, 1)

    gridlayout.addWidget(export_label, 2, 0)
    gridlayout.addWidget(export_path_entry, 2, 1, 1, 3)
    gridlayout.addWidget(export_path_btn, 2, 4)


    gridlayout.addWidget(background_label, 1, 3)
    gridlayout.addWidget(background_btn, 1, 4)

    gridlayout.setRowMinimumHeight(3, 30)
    gridlayout.addWidget(cancel_btn, 3, 1)
    gridlayout.addWidget(ok_btn, 3, 3, QtCore.Qt.AlignRight)

    window.setLayout(gridlayout)

    window.show()

    return window

def run_ffmpeg(audio_pipe_name, read_audio_cmd, read_frame_cmd, ffmpeg_cmd):
    """
    Make named pipe. Launch read_audio_cmd and pipe output to named pipe.
    Launch read_frame_cmd and pipe output to ffmpeg_cmd.
    """

    import errno
    import subprocess

    print(read_audio_cmd)
    print()
    print(read_frame_cmd)
    print()
    print(ffmpeg_cmd)
    print()

    # Remove left-over audio pipe if any
    try:
        os.unlink(audio_pipe_name)
    except OSError as err:
        # Suppress the exception if it is a file not found error.
        # Otherwise, re-raise the exception.
        if err.errno != errno.ENOENT:
            raise

    try:
        # Create new audio pipe
        os.mkfifo(audio_pipe_name, 0o644)

        # Launch read_frame command
        read_frame_args = shlex.split(read_frame_cmd)
        read_frame_process = subprocess.Popen(read_frame_args, stdout=subprocess.PIPE)

        try:
            # Launch ffmpeg command
            ffmpeg_args = shlex.split(ffmpeg_cmd)
            ffmpeg_process = subprocess.Popen(
                ffmpeg_args, stdin=read_frame_process.stdout, stderr=subprocess.STDOUT
            )
        except Exception as err:
            # Clean-up dangling read_frame process
            read_frame_process.kill()
            read_frame_process.wait()
            raise

        try:
            # Open audio pipe and run read_audio
            audio_pipe = os.open(audio_pipe_name, os.O_WRONLY)
            audio_args = shlex.split(read_audio_cmd)
            audio_process = subprocess.check_call(audio_args, stdout=audio_pipe)
        except Exception as err:
            # Clean-up dangling ffmpeg and read_frame processes
            ffmpeg_process.kill()
            ffmpeg_process.wait()
            read_frame_process.kill()
            read_frame_process.wait()
            raise
        finally:
            # Closing audio pipe so ffmpeg stops waiting for input
            os.close(audio_pipe)

        # Let read_frame and ffmpeg do their thing
        ffmpeg_process.wait()
        read_frame_process.wait()

    except Exception as err:
        logging.error(traceback.format_exc())
        raise

    finally:
        # Remove audio pipe
        os.unlink(audio_pipe_name)

def export_ffmpeg(clip, export_dir, foreground):
    """
    Export a clip to QuickTime using /usr/local/bin/ffmpeg
    """

    import subprocess
    import platform

    from libwiretapPythonClientAPI import (
        WireTapServerHandle,
        WireTapNodeHandle,
    )

    # Specify output dimensions here
    # width = 1920
    # height = 1080
    # Could alternatively use source dimensions
    width = clip.width #* float(scale_factor)
    height = clip.height # * float(scale_factor)

    # Specify output video codec and options here
    output_vcodec = str("-codec:v libx264 -preset slow -crf ") + str(crf_entry) + str(" -x264-params ref=4:qpmin=4 -vf \"scale=(iw)/") + str(scale_factor) + str("\":(-ih)/") + str(scale_factor) + str(",format=yuv420p")
    output_vcodec_is_rgb = False

    # Specify output audio codec and options here
    output_acodec = str("-codec:a aac -b:a ")+ str(audio_bitrate_entry) + str(" -strict -2")

    print()
    print("Export with ffmpeg")

    # Render clip (in foreground) if needed and commit library before extracting
    # clip information like the node id because they could change upon render
    # and commit.
    #
    # In a real workflow, you might want to consider copying the clip so it does
    # not get altered by the user while the export is ongoing.
    #
    clip.render()
    clip.commit()

    # Extract metadata from source clip
    storage_id = clip.get_wiretap_storage_id()
    print("Clip server: " + storage_id)

    node_id = clip.get_wiretap_node_id()
    print("Clip Id: " + node_id)

    clipname = clip.name.get_value()
    print("Clip Name: " + clipname)

    tc = "%s" % clip.start_time
    print("Timecode (Flame): " + tc)

    fps = clip.frame_rate
    print("Frame rate: %s" % clip.frame_rate)
    drop = fps.find(" DF") > 0

    tc = tc[:2] + ":" + tc[3:5] + ":" + tc[6:8] + (";" if drop else ":") + tc[9:]
    print("Timecode (FFmpeg): " + tc)

    fps = fps[0 : fps.find("fps") - 1]
    print("Clip fps: " + fps)

    print("Clip depth: %d" % clip.bit_depth)
    need_16_bpc = clip.bit_depth > 8

    audio_pipe_name = os.path.join(export_dir, "%s.audio.pipe" % clipname)
    print("Audio pipe: " + audio_pipe_name)

    output_file = os.path.join(export_dir, "%s.mp4" % clipname)
    if os.path.exists(output_file):
        if not show_confirm_dialog(
            "%s already exists. Do want to overwrite?" % output_file, "Overwrite?"
        ):
            return
    print("Output file: " + output_file)
    print()

    # Prepare read_frame command
    read_frame_cmd = (
        "/opt/Autodesk/io/bin/read_frame -S '%s' -n '%s' -N -1 -W %d -H %d -b %d"
        % (storage_id, node_id, width, height, 48 if need_16_bpc else 24)
    )

    # Prepare transfer of clip's color metadata to ffmpeg
    color_space = (
        "-color_primaries %d -color_trc %d -colorspace %d "
        "-movflags write_colr "
        % (
            clip.colour_primaries,
            clip.transfer_characteristics,
            0 if output_vcodec_is_rgb else clip.matrix_coefficients,
        )
    )

    # Prepare ffmpeg command: will get its audio input from audio pipe above
    # and its video input from stdin (piped read_frame command)
    ffmpeg_cmd = (
        "/usr/local/bin/ffmpeg "
        +
        # Video input options
        "-f rawvideo -pix_fmt %s -s %dx%d -r '%s' -i - "
        +
        # Audio input options
        "-ar 48000 -f s16le -ac 2 -i '%s' "
        +
        # Video output options
        output_vcodec
        + " "
        +
        # Audio output options
        output_acodec
        + " "
        +
        # Metadata output options
        color_space
        + "-timecode '%s' "
        + "-metadata:s:v:0 reel_name='%s' "
        + "-metadata title='%s' "
        +
        # Output file
        "-y '%s'"
    ) % (
        "rgb48le" if need_16_bpc else "rgb24",
        width,
        height,
        fps,
        audio_pipe_name,
        tc,
        clip.tape_name,
        clipname,
        output_file,
    )

    # Prepare audio command
    read_audio_cmd = (
        "/opt/Autodesk/io/bin/read_audio -S " + storage_id + " -n " + node_id
    )

    # Run the commands
    if foreground:
        run_ffmpeg(audio_pipe_name, read_audio_cmd, read_frame_cmd, ffmpeg_cmd)

    else:
        # Background execution is performed via Backburner cmdjob.
        # Everything is packaged in a python command line for cmdjob consumption.

        cmdjob = (
            "/opt/Autodesk/backburner/cmdjob "
            + "-jobName:'FFmpeg - "
            + clipname
            + "' "
            + "-description:'"
            + clipname
            + " -> "
            + output_file
            + "' "
            + "-servers:"
            + platform.node().split(".")[0]
            + ' /usr/bin/python -c "'
            + "import sys; import os;"
            + "sys.path.insert(1,'"
            + os.path.dirname(os.path.realpath(__file__))
            + "');"
            + "import mp4_gui;"
            + "mp4_gui.run_ffmpeg('"
            + audio_pipe_name
            + "','"
            + read_audio_cmd.replace("'", "\\'")
            + "','"
            + read_frame_cmd.replace("'", "\\'")
            + "','"
            + ffmpeg_cmd.replace("'", "\\'")
            + "')"
            + '"'
        )

        print(cmdjob)
        print()
        try:
            cmdjob_args = shlex.split(cmdjob)
            subprocess.check_call(cmdjob_args)
        except Exception as err:
            logging.error(traceback.format_exc())
            raise

    # Invalidate exported clip in WTG
    try:
        server = WireTapServerHandle("localhost:Gateway")
        node = WireTapNodeHandle(server, output_file + "@CLIP")
        if not node.setMetaData("Invalidate", ""):
            print("Unable to set meta data: " + node.lastError())
    finally:
        # Must destroy WireTapServerHandle and WireTapNodeHandle before
        # uninitializing the Wiretap Client API.
        #
        node = None
        server = None

def export_ffmpegs(selection, export_dir, foreground):
    """
    Export all clips in a selection with ffmpeg.
    """

    import flame

    # Iterate the selection.
    #
    for item in selection:
        # Check if the item is a folder like object
        #
        if isinstance(
            item,
            (
                flame.PyReelGroup,
                flame.PyReel,
                flame.PyFolder,
                flame.PyLibrary,
                flame.PyDesktop,
            ),
        ):
            export_sub_dir = os.path.join(export_dir, item.name.get_value())
            print("Creating %s" % (export_sub_dir))
            make_dirs(export_sub_dir)
            export_ffmpegs(item.children, export_sub_dir, foreground)

        # Check if the item in the selection is a sequence or a clip
        #
        elif isinstance(item, (flame.PySequence, flame.PyClip)):
            export_ffmpeg(item, export_dir, foreground)

def copy_me(selection):
    import flame
    import os, sys
    from PySide2 import QtWidgets

    #set variables
    sharedlib = flame.projects.current_project.shared_libraries[0]

    #Get SubFolder Names
    folder_names = [f.name for f in sharedlib.folders]

        ##  Says if a dated folder exists or not.
    for i in [i for i, x in enumerate(folder_names) if not x == today]:
            search = 0

    for i in [i for i, x in enumerate(folder_names) if x == today]:
        todaysFolderNum = i
        todaysFolder = sharedlib.folders[todaysFolderNum]
        search = 1

    if search == 1:
        #print ('make timed folder')
        sharedlib.acquire_exclusive_access()
        #todaysfolder = sharedlib.folders[todaysFolderNum]
        postingfolder = sharedlib.folders[todaysFolderNum].create_folder(now)
        tab = flame.get_current_tab()
        if tab == 'MediaHub':
            flame.set_current_tab("Timeline")
        for item in selection:
            flame.media_panel.copy(item, postingfolder)
            #postingfolder.expanded = True
        sharedlib.release_exclusive_access()

    else:
        #print ('make dated and time folders')
        sharedlib.acquire_exclusive_access()
        postingfolder = sharedlib.create_folder(today).create_folder(now)
        tab = flame.get_current_tab()
        if tab == 'MediaHub':
            flame.set_current_tab("Timeline")
        for item in selection:
            flame.media_panel.copy(item, postingfolder)
        #postingfolder.expanded = True
        sharedlib.release_exclusive_access()

def openFinder(exportPath):
    import platform
    import subprocess

    if platform.system() == 'Darwin':
        subprocess.Popen(['open', exportPath])
    else:
        subprocess.Popen(['xdg-open', exportPath])

def show_confirm_dialog(text, title):
    """
    Show a dialog box using PySide/QT.
    """
    from PySide2.QtWidgets import QMessageBox

    msg_box = QMessageBox()
    msg_box.setText(text)
    msg_box.setWindowTitle(title)
    msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg_box.setDefaultButton(QMessageBox.Ok)
    return msg_box.exec_() == QMessageBox.Ok

def message_box(message):
    from PySide2 import QtWidgets

    message_box_window = QtWidgets.QMessageBox()
    message_box_window.setWindowTitle('Big Success')
    message_box_window.setText('<b><center>%s' % message)
    message_box_window.setStandardButtons(QtWidgets.QMessageBox.Ok)
    message = message_box_window.exec_()
    openFinder(export_path)

    return message

def scope_not_desktop(selection):
    import flame

    for item in selection:
        if not isinstance(item, flame.PyDesktop):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': folder_name,
            'actions': [
                {
                    'name': action_name,
                    'execute': main_window,
                    'isVisible': scope_not_desktop,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_main_menu_custom_ui_actions():
    return get_media_panel_custom_ui_actions()
