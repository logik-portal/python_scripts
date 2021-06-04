'''
Script Name: Premiere XML Mediahub
Script Version: 1.3
Flame Version: 2020
Written by: Ted Stanley, John Geehreng, and Mike V
Creation Date: 03.03.21
Update Date: 06.04.21

Description: This provides a UI for Ted Stanley's awesome script found on the Logik Forums.
With Mike V's help, it also adds a scale factor to compensate for the difference between proxy resolution
and the full resolution of the clips in Flame.
To obtain the scale factor, divide the proxy resolution by the full resolution of your clips and then multiply by 100.
If you don't like using math, you can also figure it out by creating a new axis in Action, parenting it under the axis that has the repo data on it, and manually find the scale difference.

If the aspect ratios of the proxy files are the same as the full res clips, you can use either the x or y value.
If the proxy files have a letterbox use (proxy x res / full res x res)
If the proxy files have pillar bars, use (proxy y res / full res y res)
If you have multiple resolutions, run the script as many times as needed. It will name them based on the scale factor.


03.19.21 - Python3 Updates
05.17.21 - Added the ability to select multiple .xml's and added Ted's nested layer fix
06.04.21 - Change Default Scale Value to 100 for graphics. Renamed "Cancel" button to say "Close"
'''

from __future__ import print_function
from __future__ import absolute_import
# from six.moves import range

folder_name = "XML Prep"
action_name = "Fix Adobe Premiere XML's"

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

    def ok_button():
        for item in selection:
            global xml_file_path,xml_folder,xml_path_entry
            # xml_file_path = item.path
            xml_path_entry = item.path
            print ("xml_file_path: ", xml_file_path)
            # xml_folder = os.path.dirname(xml_file_path)
            # print ("xml_folder: ", xml_folder)
            fix_xml(item)
        message_box('That Totally Worked!')

        # window.close()

        try:
            flame.execute_shortcut("Refresh the MediaHub's Folders and Files")
        except:
            pass

        print ('\ndone.\n')

    def fix_xml(xml):
        import xml.etree.ElementTree as ET

        xml = xml_path_entry
        clip_path = str(xml).rsplit('/', 1)[0]
        sequence_x_res = int(sequence_x_lineedit.text())
        sequence_y_res = int(sequence_y_lineedit.text())
        scale_factor = float(scale_factor_lineedit.text())
        scale_percent = int(float(scale_factor))

        print (xml)
        print (sequence_x_res)
        print (sequence_y_res)
        print (scale_factor)
        print (scale_percent)

        tree = ET.parse(xml)
        root = tree.getroot()

        # Change Sequence Name
        clips = root.findall(".//sequence")
        for clip in clips:
            xml_name = clip.find('name')
            seq_name = xml_name.text
            print ("seq_name: " + seq_name + " start")
            remove = ["_v1_", "_v2","_01_", "Copy", "_copy", ".Exported.01","_export_", "_exported_", "'","_AAF","_XML","_Conform","_PREP","PREP","_PRE_CONFORM","PRE_CONFORM","_PRE","_CONFORM","CONFORM"]
            underscore = [" - "," ",]
            for items in underscore:
                if items in seq_name:
                    seq_name = seq_name.replace(items, "_")
            for items in remove:
                if items in seq_name:
                    seq_name = seq_name.replace(items, "")
            seq_name = seq_name.split("_Exported")[0]
            seq_name = seq_name.replace('v', "V")
            seq_name = seq_name + "_scaled_by_" + str(scale_percent) + "_percent"
            xml_name.text = str(seq_name)
            print ("seq_name: ", seq_name)

        # clips = root.findall(".//clipitem")
        clips = root.findall(".//sequence/media/video/*/clipitem")
        status = 1
        for clip in clips:
            print ("Clip " + str(status))
            status += 1

            file = clip.find('file')
            if file is None:
                print ("ERROR: No file, maybe a nest?")
                continue
            search = ".//*[@id='{}']".format(list((file.attrib).items())[0][1])
            master = root.find(search)

            cliphoriz = master.find(".//media/video/samplecharacteristics/width").text
            cliphoriz = int(cliphoriz)
            clipvert = master.find(".//media/video/samplecharacteristics/height").text
            clipvert = int(clipvert)

            parameter = clip.find(".//filter/effect/[name='Basic Motion']/parameter/[name='Center']")
            if parameter is None: continue
            xmlhoriz = parameter[2][0].text
            xmlhoriz = float(xmlhoriz)
            xmlvert = parameter[2][1].text
            xmlvert = float(xmlvert)

            newxmlhoriz = (xmlhoriz * cliphoriz) / sequence_x_res
            newxmlvert = (xmlvert * clipvert) / sequence_y_res

            if newxmlhoriz == 0: newxmlhoriz = int(newxmlhoriz)
            if newxmlvert == 0: newxmlvert = int(newxmlvert)
            print ("*" * 100)
            print (parameter[2][0].text + " <-- Old vs New X Repo --> " + str(newxmlhoriz))
            print (parameter[2][1].text + "<-- Old vs New Y Repo -->" + str(newxmlvert))
            print ("*" * 100)
            parameter[2][0].text = str(newxmlhoriz)
            parameter[2][1].text = str(newxmlvert)

            # Edit Keyframe positions
            for center_keyframe_parameter in clip.findall(".//filter/effect/[name='Basic Motion']/parameter/[name='Center']/keyframe"):
                print ("*" * 100)
                print ('center_keyframe_parameter:', center_keyframe_parameter)
                center_x_keyframe_value = float(center_keyframe_parameter[1][0].text)
                center_y_keyframe_value = float(center_keyframe_parameter[1][1].text)
                print ('center_x_keyframe_value: ', center_x_keyframe_value)
                print ('center_y_keyframe_value: ', center_y_keyframe_value)
                print ("*" * 100)

                new_center_x_keyframe_value = (center_x_keyframe_value * cliphoriz) / sequence_x_res
                new_center_y_keyframe_value = (center_y_keyframe_value * clipvert) / sequence_y_res

                if new_center_x_keyframe_value == 0: new_center_x_keyframe_value = int(new_center_x_keyframe_value)
                if new_center_y_keyframe_value == 0: new_center_y_keyframe_value = int(new_center_y_keyframe_value)

                print ("*" * 100)
                print ("new_center_x_keyframe_value: ", new_center_x_keyframe_value)
                print ("new_center_y_keyframe_value: ", new_center_y_keyframe_value)
                print ("*" * 100)

                center_keyframe_parameter[1][0].text = str(new_center_x_keyframe_value)
                center_keyframe_parameter[1][1].text = str(new_center_y_keyframe_value)


            # Edit Scale Value

            scale_parameter = clip.find(".//filter/effect/[name='Basic Motion']/parameter/[name='Scale']")
            if scale_parameter is None: continue
            scale_value = float(scale_parameter[4].text)
            print ('scale_value:', scale_value)

            new_scale_value = scale_value * (scale_factor/100)
            print ('new_scale_value:', new_scale_value)

            scale_parameter[4].text = str(new_scale_value)

            # Edit Scale Keyframed Value

            for scale_keyframe_parameter in clip.findall(".//filter/effect/[name='Basic Motion']/parameter/[name='Scale']/keyframe/value"):
                print ("*" * 100)
                print ('scale_keyframe_parameter:', scale_keyframe_parameter)
                scale_keyframe_value = float(scale_keyframe_parameter.text)
                print ('scale_keyframe_value:', scale_keyframe_value)
                new_scale_kf_value = scale_keyframe_value * (scale_factor/100)
                print ('new_scale_value:', new_scale_kf_value)
                # print ("\n" *2)
                print ("*" * 100)
                scale_keyframe_parameter.text = str(new_scale_kf_value)


        #Fix Stills Duration
        if fix_durations_btn.isChecked():
            print ("checked")
            clips = root.findall(".//sequence/media/video/*/clipitem")
            new_status = 1
            print ("Fixing durations...")
            for clip in clips:
                clipname = clip.find('name').text
                print ("Clip " + str(new_status) + ": " + clipname)

                new_status += 1

                clipstart = int(clip.find('start').text)
                clipend = int(clip.find('end').text)
                clipin = int(clip.find('in').text)
                clipoutxml = int(clip.find('out').text)

                if (clipend - clipstart) == (clipoutxml - clipin): continue
                if (clipstart < 0) or (clipend < 0): continue

                print ("[Fixing Clip Out]")

                clipout = clip.find('out')
                clipout.text = str(clipin + (clipend - clipstart))

            outname = xml[:-4] + "_scaled_" + str(scale_factor) + "_percent_and_fixed_durations.xml"
            tree.write(outname)

        else:
            print ("not checked")
            outname = xml[:-4] + "_scaled_" + str(scale_factor) + "_percent.xml"
            tree.write(outname)

    window = QtWidgets.QWidget()
    window.setMinimumSize(600, 230)
    window.setWindowTitle('Fix Adobe Premiere XML\'s')
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    window.setStyleSheet('background-color: #313131')

    # Center window in linux
    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                (resolution.height() / 2) - (window.frameSize().height() / 2))

    # Center window in linux

    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                (resolution.height() / 2) - (window.frameSize().height() / 2))

    # Labels

    sequence_x_res = QtWidgets.QLabel('Sequence X Res', window)
    sequence_x_res.setMinimumSize(QtCore.QSize(125, 35))
    sequence_x_res.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                 'QLabel:disabled {color: #6a6a6a}')

    sequence_y_res = QtWidgets.QLabel('Sequence Y Res', window)
    sequence_y_res.setMinimumSize(QtCore.QSize(125, 35))
    sequence_y_res.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                 'QLabel:disabled {color: #6a6a6a}')

    scale_factor_label = QtWidgets.QLabel('Scale Multiplier', window)
    scale_factor_label.setMinimumSize(QtCore.QSize(125, 35))
    scale_factor_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                     'QLabel:disabled {color: #6a6a6a}')

    # Sequence X Slider

    sequence_x_min_value = 0
    sequence_x_max_value = 15000
    sequence_x_start_value = 1920

    def set_x_slider():
        sequence_x_slider.setValue(int(sequence_x_lineedit.text()))

    sequence_x_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, window)
    sequence_x_slider.setMaximumHeight(3)
    sequence_x_slider.setMaximumWidth(100)
    sequence_x_slider.setMinimum(sequence_x_min_value)
    sequence_x_slider.setMaximum(sequence_x_max_value)
    sequence_x_slider.setValue(sequence_x_start_value)
    sequence_x_slider.setStyleSheet('QSlider {color: #111111}'
                                    'QSlider::groove:horizontal {background-color: #111111}'
                                    'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
    sequence_x_slider.setDisabled(True)

    sequence_x_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, sequence_x_start_value, parent=window)
    sequence_x_lineedit.setAlignment(QtCore.Qt.AlignCenter)
    sequence_x_lineedit.setMinimum(sequence_x_min_value)
    sequence_x_lineedit.setMaximum(sequence_x_max_value)
    sequence_x_lineedit.setMinimumHeight(28)
    sequence_x_lineedit.setMaximumWidth(100)
    sequence_x_lineedit.textChanged.connect(set_x_slider)
    sequence_x_slider.raise_()

    # Sequence Y Slider

    sequence_y_min_value = 0
    sequence_y_max_value = 15000
    sequence_y_start_value = 1080

    def set_y_slider():
        sequence_y_slider.setValue(int(sequence_y_lineedit.text()))

    sequence_y_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, window)
    sequence_y_slider.setMaximumHeight(3)
    sequence_y_slider.setMaximumWidth(100)
    sequence_y_slider.setMinimum(sequence_y_min_value)
    sequence_y_slider.setMaximum(sequence_y_max_value)
    sequence_y_slider.setValue(sequence_y_start_value)
    sequence_y_slider.setStyleSheet('QSlider {color: #111111}'
                                    'QSlider::groove:horizontal {background-color: #111111}'
                                    'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
    sequence_y_slider.setDisabled(True)

    sequence_y_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, sequence_y_start_value, parent=window)
    sequence_y_lineedit.setAlignment(QtCore.Qt.AlignCenter)
    sequence_y_lineedit.setMinimum(sequence_y_min_value)
    sequence_y_lineedit.setMaximum(sequence_y_max_value)
    sequence_y_lineedit.setMinimumHeight(28)
    sequence_y_lineedit.setMaximumWidth(100)
    sequence_y_lineedit.textChanged.connect(set_y_slider)
    sequence_y_slider.raise_()

    # Scale Factor Slider

    scale_factor_min_value = 0
    scale_factor_max_value = 100
    scale_factor_start_value = 100

    def set_scale_factor_slider():
        scale_factor_slider.setValue(float(scale_factor_lineedit.text()))

    scale_factor_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, window)
    scale_factor_slider.setMaximumHeight(3)
    scale_factor_slider.setMaximumWidth(100)
    scale_factor_slider.setMinimum(scale_factor_min_value)
    scale_factor_slider.setMaximum(scale_factor_max_value)
    scale_factor_slider.setValue(scale_factor_start_value)
    scale_factor_slider.setStyleSheet('QSlider {color: #111111}'
                                      'QSlider::groove:horizontal {background-color: #111111}'
                                      'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
    scale_factor_slider.setDisabled(True)

    scale_factor_lineedit = CustomSpinBox(CustomSpinBox.DoubleSpinBox, scale_factor_start_value, parent=window)
    scale_factor_lineedit.setAlignment(QtCore.Qt.AlignCenter)
    scale_factor_lineedit.setMinimum(scale_factor_min_value)
    scale_factor_lineedit.setMaximum(scale_factor_max_value)
    scale_factor_lineedit.setMinimumHeight(28)
    scale_factor_lineedit.setMaximumWidth(100)
    scale_factor_lineedit.setToolTip('Enter the value of the Proxy Res divided by the Full Res times 100.')
    scale_factor_lineedit.textChanged.connect(set_scale_factor_slider)
    scale_factor_slider.raise_()

    # Fix Stills Pushbutton

    fix_durations_btn = QtWidgets.QPushButton(' Fix Durations', window)
    fix_durations_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    fix_durations_btn.setMinimumSize(100, 28)
    fix_durations_btn.setMaximumSize(100, 28)
    fix_durations_btn.setCheckable(True)
    fix_durations_btn.toggle()
    fix_durations_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #424142, stop: .91 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                                          'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #4f4f4f, stop: .91 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                          'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                                          'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')
    fix_durations_btn.setToolTip('Enable to fix the duration of still frames. Typically graphic elements.')

    ok_btn = QtWidgets.QPushButton('Ok', window)
    ok_btn.clicked.connect(ok_button)

    ok_btn.setMinimumSize(QtCore.QSize(100, 28))
    ok_btn.setMaximumSize(QtCore.QSize(100, 28))
    ok_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    ok_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    cancel_btn = QtWidgets.QPushButton('Close', window)
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

    gridlayout.addWidget(sequence_x_res, 0, 0)
    gridlayout.addWidget(sequence_x_lineedit, 0, 1)
    gridlayout.addWidget(sequence_x_slider, 0, 1, QtCore.Qt.AlignBottom)

    gridlayout.setColumnMinimumWidth(2, 100)

    gridlayout.addWidget(sequence_y_res, 0, 3)
    gridlayout.addWidget(sequence_y_lineedit, 0, 4)
    gridlayout.addWidget(sequence_y_slider, 0, 4, QtCore.Qt.AlignBottom)

    gridlayout.addWidget(scale_factor_label, 1, 0)
    gridlayout.addWidget(scale_factor_lineedit, 1, 1)
    gridlayout.addWidget(scale_factor_slider, 1, 1, QtCore.Qt.AlignBottom)

    gridlayout.addWidget(fix_durations_btn, 1, 4)

    # gridlayout.setRowMinimumHeight(2, 30)
    gridlayout.addWidget(cancel_btn, 2, 1)
    gridlayout.addWidget(ok_btn, 2, 4)

    window.setLayout(gridlayout)

    window.show()

    return window

def message_box(message):
    from PySide2 import QtWidgets, QtCore

    message_box_window = QtWidgets.QMessageBox()
    message_box_window.setWindowTitle('Big Success')
    message_box_window.setText('<b><center>%s' % message)
    msg_box_button = message_box_window.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 28))
    message_box_window.setStyleSheet('QMessageBox {background-color: #313131; font: 14px "Discreet"}'
                                     'QLabel {color: #9a9a9a; font: 14px "Discreet"}'
                                     'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                     'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    message = message_box_window.exec_()

    return message

def scope_xml(selection):
    import flame
    import os
    for item in selection:
        global xml_file_path,xml_folder
        xml_file_path = item.path
        file_name, file_extension = os.path.splitext(xml_file_path)
        # print (file_name)
        # print (file_extension)
        if file_extension == ".xml":
            return True
    return False

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': folder_name,
            'actions': [
                {
                    'name': action_name,
                    'execute': main_window,
                    'isVisible': scope_xml,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
