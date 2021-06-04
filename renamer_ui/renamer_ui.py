'''
Script Name: Renamer UI
Script Version: 2.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 12.11.20
Update Date: 02.03.21

Description: Use this to add and/or remove a prefix and or suffix. It's a very quick way to add "_Generic" or "_v01" to the end of a name.
'''

from __future__ import print_function

folder_name = "UC Renamers"
action_name = "Renamer UI"

def main_window(selection):
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

    def cancel_button():

        window.close()

    def ok_button():
        import flame

        # Set variables from entries

        rmPrefix = int(remove_prefix_lineedit.text())
        prefix = str(new_prefix_entry.text())
        rmSuffix = int(remove_suffix_lineedit.text())
        suffix = str(new_suffix_entry.text())

        for item in selection:
                print ("*" * 10)

                seq_name = str(item.name)[(rmPrefix+1):-(rmSuffix+1)]
                item.name = prefix + seq_name + suffix

                print ("*" * 10)
                print ("\n")

        # Close window

        window.close()

    window = QtWidgets.QWidget()
    window.setMinimumSize(600, 200)
    window.setWindowTitle('Add and/or Remove Previx and/or Suffix in Name(s)')
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    window.setStyleSheet('background-color: #272727')

    # Center window in linux

    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                (resolution.height() / 2) - (window.frameSize().height() / 2))

    # Labels

    remove_prefix_label = QtWidgets.QLabel('Remove Prefix ', window)
    remove_prefix_label.setAlignment(QtCore.Qt.AlignVCenter)
    # remove_prefix_label.setMinimumWidth(60)
    remove_prefix_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')
    remove_prefix_label.setMinimumSize(QtCore.QSize(80, 26))

    new_prefix_label = QtWidgets.QLabel('New Prefix ', window)
    new_prefix_label.setAlignment(QtCore.Qt.AlignVCenter)
    # new_prefix_label.setMinimumWidth(60)
    new_prefix_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')
    new_prefix_label.setMinimumSize(QtCore.QSize(80, 26))

    remove_suffix_label = QtWidgets.QLabel('Remove Suffix ', window)
    remove_suffix_label.setAlignment(QtCore.Qt.AlignVCenter)
    # remove_suffix_label.setMinimumWidth(60)
    remove_suffix_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')
    remove_suffix_label.setMinimumSize(QtCore.QSize(80, 26))

    new_suffix_label = QtWidgets.QLabel('New Suffix ', window)
    new_suffix_label.setAlignment(QtCore.Qt.AlignVCenter)
    # new_suffix_label.setAlignment(QtCore.Qt.AlignVCenter)
    # new_suffix_label.setMinimumWidth(60)
    new_suffix_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')
    new_suffix_label.setMinimumSize(QtCore.QSize(80, 26))

    # Remove Prefix Slider

    remove_prefix_min_value = 0
    remove_prefix_max_value = 80
    remove_prefix_start_value = 0

    def set_x_slider():
        remove_prefix_slider.setValue(int(remove_prefix_lineedit.text()))

    remove_prefix_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, window)
    remove_prefix_slider.setMaximumHeight(3)
    remove_prefix_slider.setMaximumWidth(100)
    remove_prefix_slider.setMinimum(remove_prefix_min_value)
    remove_prefix_slider.setMaximum(remove_prefix_max_value)
    remove_prefix_slider.setValue(remove_prefix_start_value)
    remove_prefix_slider.setStyleSheet('QSlider {color: #111111}'
                                    'QSlider::groove:horizontal {background-color: #111111}'
                                    'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
    remove_prefix_slider.setDisabled(True)

    remove_prefix_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, remove_prefix_start_value, parent=window)
    remove_prefix_lineedit.setAlignment(QtCore.Qt.AlignCenter)
    remove_prefix_lineedit.setMinimum(remove_prefix_min_value)
    remove_prefix_lineedit.setMaximum(remove_prefix_max_value)
    remove_prefix_lineedit.setMinimumHeight(28)
    remove_prefix_lineedit.setMaximumWidth(100)
    remove_prefix_lineedit.textChanged.connect(set_x_slider)
    remove_prefix_slider.raise_()

    # Remove Suffix Slider

    remove_suffix_min_value = 0
    remove_suffix_max_value = 80
    remove_suffix_start_value = 0

    def set_y_slider():
        remove_suffix_slider.setValue(int(remove_suffix_lineedit.text()))

    remove_suffix_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, window)
    remove_suffix_slider.setMaximumHeight(3)
    remove_suffix_slider.setMaximumWidth(100)
    remove_suffix_slider.setMinimum(remove_suffix_min_value)
    remove_suffix_slider.setMaximum(remove_suffix_max_value)
    remove_suffix_slider.setValue(remove_suffix_start_value)
    remove_suffix_slider.setStyleSheet('QSlider {color: #111111}'
                                    'QSlider::groove:horizontal {background-color: #111111}'
                                    'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
    remove_suffix_slider.setDisabled(True)

    remove_suffix_lineedit = CustomSpinBox(CustomSpinBox.IntSpinBox, remove_suffix_start_value, parent=window)
    remove_suffix_lineedit.setAlignment(QtCore.Qt.AlignCenter)
    remove_suffix_lineedit.setMinimum(remove_suffix_min_value)
    remove_suffix_lineedit.setMaximum(remove_suffix_max_value)
    remove_suffix_lineedit.setMinimumHeight(28)
    remove_suffix_lineedit.setMaximumWidth(100)
    remove_suffix_lineedit.textChanged.connect(set_y_slider)
    remove_suffix_slider.raise_()

    # Entries

    new_prefix_entry = QtWidgets.QLineEdit('', window)
    new_prefix_entry.setPlaceholderText('Enter text here to add to the start of a name.')
    new_prefix_entry.setMinimumHeight(28)
    new_prefix_entry.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                 'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

    new_suffix_entry = QtWidgets.QLineEdit('', window)
    new_suffix_entry.setPlaceholderText('Enter text here to add to the end of a name, like "_Generic" or "_v01"')
    new_suffix_entry.setMinimumHeight(28)
    new_suffix_entry.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                 'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

    # Buttons

    ok_btn = QtWidgets.QPushButton('Ok', window)
    ok_btn.clicked.connect(ok_button)
    ok_btn.setMinimumSize(QtCore.QSize(100, 28))
    ok_btn.setMaximumSize(QtCore.QSize(100, 28))
    ok_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    ok_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    cancel_btn = QtWidgets.QPushButton('Cancel', window)
    cancel_btn.clicked.connect(cancel_button)

    cancel_btn.setMinimumSize(QtCore.QSize(100, 28))
    cancel_btn.setMaximumSize(QtCore.QSize(100, 28))
    cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    # Layout
    gridlayout = QtWidgets.QGridLayout()
    gridlayout.setMargin(20)
    gridlayout.setVerticalSpacing(11)
    gridlayout.setHorizontalSpacing(5)

    gridlayout.addWidget(remove_prefix_label, 0, 0)
    # gridlayout.addWidget(remove_prefix_entry, 0, 1)
    gridlayout.addWidget(remove_prefix_lineedit, 0, 1)
    gridlayout.addWidget(remove_prefix_slider, 0, 1, QtCore.Qt.AlignBottom)

    gridlayout.setColumnMinimumWidth(1, 450)

    gridlayout.addWidget(new_prefix_label, 1, 0)
    gridlayout.addWidget(new_prefix_entry, 1, 1)


    gridlayout.addWidget(remove_suffix_label, 2, 0)
    # gridlayout.addWidget(remove_suffix_entry, 2, 1)
    gridlayout.addWidget(remove_suffix_lineedit, 2, 1)
    gridlayout.addWidget(remove_suffix_slider, 2, 1, QtCore.Qt.AlignBottom)

    gridlayout.addWidget(new_suffix_label, 3, 0)
    gridlayout.addWidget(new_suffix_entry, 3, 1)

    gridlayout.setRowMinimumHeight(3, 50)

    gridlayout.addWidget(cancel_btn, 4, 0, QtCore.Qt.AlignHCenter)
    gridlayout.addWidget(ok_btn, 4, 1, QtCore.Qt.AlignRight)

    window.setLayout(gridlayout)

    window.show()

    return window

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

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
                    'isVisible': scope_not_desktop,
                    'execute': main_window,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
