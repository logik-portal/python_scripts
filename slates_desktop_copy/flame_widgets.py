'''
Custom Qt Flame Widgets v2.1

Created: 02.15.22
Updated 04.11.22

File should be renamed to: flame_widgets_<script name>.py to avoid conflicts with having multiple copies within /opt/Autodesk/shared/python.

Usage:

    import as module in script:

    from flame_wdigets_<script name> import FlameButton, FlameLabel, FlameSlider...
'''

from PySide2 import QtWidgets, QtCore, QtGui

class FlameButton(QtWidgets.QPushButton):
    '''
    Custom Qt Flame Button Widget

    FlameButton(button_name, connect[, button_color='normal', button_width=150, button_max_width=150])

    button_name: button text [str]
    connect: execute when clicked [function]
    button_color: (optional) normal, blue [str]
    button_width: (optional) default is 150 [int]
    button_max_width: (optional) default is 150 [int]

    Usage:

        button = FlameButton('Button Name', do_something_magical_when_pressed, button_color='blue')
    '''

    def __init__(self, button_name, connect, button_color='normal', button_width=150, button_max_width=150):
        super(FlameButton, self).__init__()

        self.setText(button_name)
        self.setMinimumSize(QtCore.QSize(button_width, 28))
        self.setMaximumSize(QtCore.QSize(button_max_width, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        if button_color == 'normal':
            self.setStyleSheet('QPushButton {color: rgb(154, 154, 154); background-color: rgb(58, 58, 58); border: none; font: 14px "Discreet"}'
                               'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                               'QPushButton:pressed {color: rgb(159, 159, 159); background-color: rgb(66, 66, 66); border: 1px solid rgb(90, 90, 90)}'
                               'QPushButton:disabled {color: rgb(116, 116, 116); background-color: rgb(58, 58, 58); border: none}'
                               'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')
        elif button_color == 'blue':
            self.setStyleSheet('QPushButton {color: rgb(190, 190, 190); background-color: rgb(0, 110, 175); border: none; font: 12px "Discreet"}'
                               'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                               'QPushButton:pressed {color: rgb(159, 159, 159); border: 1px solid rgb(90, 90, 90)'
                               'QPushButton:disabled {color: rgb(116, 116, 116); background-color: rgb(58, 58, 58); border: none}'
                               'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')
        elif button_color == 'red':
            self.setStyleSheet('QPushButton {color: rgb(190, 190, 190); background-color: rgb(200, 29, 29); border: none; font: 12px "Discreet"}'
                               'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                               'QPushButton:pressed {color: rgb(159, 159, 159); border: 1px solid rgb(90, 90, 90)'
                               'QPushButton:disabled {color: rgb(116, 116, 116); background-color: rgb(58, 58, 58); border: none}'
                               'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')

#

class FlameClickableLineEdit(QtWidgets.QLineEdit):
    '''
    Custom Qt Flame Clickable Line Edit Widget

    FlameClickableLineEdit(text, connect[, width=150, max_width=2000])

    text: text displayed in line edit [str]
    connect: execute when line edit is clicked on [function]
    width: (optional) width of widget. default is 150. [int]
    max_width: (optional) maximum width of widget. default is 2000 [int]

    Usage:

        clickable_lineedit =  FlameClickableLineEdit('Some Text', some_function)
    '''

    clicked = QtCore.Signal()

    def __init__(self, text, connect, width=150, max_width=2000):
        super(FlameClickableLineEdit, self).__init__()

        self.setText(text)
        self.setMinimumHeight(28)
        self.setMinimumWidth(width)
        self.setMaximumWidth(max_width)
        self.setReadOnly(True)
        self.clicked.connect(connect)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QLineEdit {color: rgb(154, 154, 154); background-color: rgb(55, 65, 75); selection-color: rgb(38, 38, 38); selection-background-color: rgb(184, 177, 167); border: 1px solid rgb(55, 65, 75); padding-left: 5px; font: 14px "Discreet"}'
                           'QLineEdit:focus {background-color: rgb(73, 86, 99)}'
                           'QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}'
                           'QLineEdit:disabled {color: rgb(106, 106, 106); background-color: rgb(55, 55, 55); border: 1px solid rgb(55, 55, 55)}'
                           'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        else:
            super().mousePressEvent(event)

#

class FlameLabel(QtWidgets.QLabel):
    '''
    Custom Qt Flame Label Widget

    FlameLabel(label_name[, label_type='normal', label_width=150])

    label_name: text displayed [str]
    label_type: (optional) select from different styles: normal, underline, background. default is normal [str]
    label_width: (optional) default is 150 [int]

    Usage:

        label = FlameLabel('Label Name', 'normal', 300)
    '''

    def __init__(self, label_name, label_type='normal', label_width=150):
        super(FlameLabel, self).__init__()

        self.setText(label_name)
        self.setMinimumSize(label_width, 28)
        self.setMaximumHeight(28)
        self.setFixedHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet('QLabel {color: rgb(154, 154, 154); font: 14px "Discreet"}'
                               'QLabel:disabled {color: rgb(106, 106, 106)}')
        elif label_type == 'underline':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('QLabel {color: rgb(154, 154, 154); border-bottom: 1px inset rgb(40, 40, 40); font: 14px "Discreet"}'
                               'QLabel:disabled {color: rgb(106, 106, 106)}')
        elif label_type == 'background':
            self.setStyleSheet('QLabel {color: rgb(154, 154, 154); background-color: rgb(30, 30, 30); padding-left: 5px; font: 14px "Discreet"}'
                               'QLabel:disabled {color: rgb(106, 106, 106)}')

#

class FlameLineEdit(QtWidgets.QLineEdit):
    '''
    Custom Qt Flame Line Edit Widget

    FlameLineEdit(text[, width=150, max_width=2000])

    text: text show [str]
    width: (optional) width of widget. default is 150. [int]
    max_width: (optional) maximum width of widget. default is 2000. [int]

    Usage:

        line_edit = FlameLineEdit('Some text here')
    '''

    def __init__(self, text, width=150, max_width=2000):
        super(FlameLineEdit, self).__init__()

        self.setText(text)
        self.setMinimumHeight(28)
        self.setMinimumWidth(width)
        self.setMaximumWidth(max_width)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setStyleSheet('QLineEdit {color: rgb(154, 154, 154); background-color: rgb(55, 65, 75); selection-color: rgb(38, 38, 38); selection-background-color: rgb(184, 177, 167); border: 1px solid rgb(55, 65, 75); padding-left: 5px; font: 14px "Discreet"}'
                           'QLineEdit:focus {background-color: rgb(73, 86, 99)}'
                           'QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}'
                           'QLineEdit:disabled {color: rgb(106, 106, 106); background-color: rgb(55, 55, 55); border: 1px solid rgb(55, 55, 55)}'
                           'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: none}')

#

class FlameListWidget(QtWidgets.QListWidget):
    '''
    Custom Qt Flame List Widget

    FlameListWidget([min_width=200, max_width=2000, min_height=250, max_height=2000])

    Usage:

        list_widget = FlameListWidget()
    '''

    def __init__(self, min_width=200, max_width=2000, min_height=250, max_height=2000):
        super(FlameListWidget, self).__init__()

        self.setMinimumWidth(min_width)
        self.setMaximumWidth(max_width)
        self.setMinimumHeight(min_height)
        self.setMaximumHeight(max_height)
        self.spacing()
        self.setUniformItemSizes(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setStyleSheet('QListWidget {color: rgb(154, 154, 154); background-color: rgb(42, 42, 42); alternate-background-color: rgb(45, 45, 45); outline: 3px rgb(0, 0, 0); font: 14px "Discreet"}'
                           'QListWidget::item:selected {color: rgb(217, 217, 217); background-color: rgb(102, 102, 102); border: 1px solid rgb(102, 102, 102)}'
                           'QScrollBar {background: rgb(61, 61, 61)}'
                           'QScrollBar::handle {background: rgb(31, 31, 31)}'
                           'QScrollBar::add-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                           'QScrollBar::sub-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                           'QScrollBar {background: rgb(61, 61, 61)}'
                           'QScrollBar::handle {background: rgb(31, 31, 31)}'
                           'QScrollBar::add-line:horizontal {border: none; background: none; width: 0px; height: 0px}'
                           'QScrollBar::sub-line:horizontal {border: none; background: none; width: 0px; height: 0px}'
                           'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')

#

class FlamePushButtonMenu(QtWidgets.QPushButton):
    '''
    Custom Qt Flame Menu Push Button Widget

    FlamePushButtonMenu(button_name, menu_options[, menu_width=150, max_menu_width=2000, menu_action=None])

    button_name: text displayed on button [str]
    menu_options: list of options show when button is pressed [list]
    menu_width: (optional) width of widget. default is 150. [int]
    max_menu_width: (optional) set maximum width of widget. default is 2000. [int]
    menu_action: (optional) execute when button is changed. [function]

    Usage:

        push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
        menu_push_button = FlamePushButtonMenu('push_button_name', push_button_menu_options)

        or

        push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
        menu_push_button = FlamePushButtonMenu(push_button_menu_options[0], push_button_menu_options)
    '''

    def __init__(self, button_name, menu_options, menu_width=150, max_menu_width=2000, menu_action=None):
        super(FlamePushButtonMenu, self).__init__()
        from functools import partial

        self.setText(button_name)
        self.setMinimumHeight(28)
        self.setMinimumWidth(menu_width)
        self.setMaximumWidth(max_menu_width)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: rgb(116, 116, 116); background-color: rgb(45, 55, 68); border: none}'
                           'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                           'QPushButton::menu-indicator {image: none}'
                           'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')

        def create_menu(option, menu_action):
            self.setText(option)
            if menu_action:
                menu_action()

        pushbutton_menu = QtWidgets.QMenu(self)
        pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        pushbutton_menu.setStyleSheet('QMenu {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: rgb(217, 217, 217); background-color: rgb(58, 69, 81)}')
        for option in menu_options:
            pushbutton_menu.addAction(option, partial(create_menu, option, menu_action))

        self.setMenu(pushbutton_menu)

#

class FlameMessageWindow(QtWidgets.QDialog):
    '''
    Custom Qt Flame Message Window

    FlameMessageWindow(message_title, message_type, message[, parent=None])

    message_title: text shown in top left of window ie. Confirm Operation [str]
    message_type: confirm, message, error, warning [str] confirm and warning return True or False values
    message: text displayed in body of window [str]
    parent: optional - parent window [object]

    Message Window Types:

        confirm: confirm and cancel button / grey left bar - returns True or False
        message: ok button / blue left bar
        error: ok button / yellow left bar
        warning: confirm and cancel button / red left bar - returns True of False

    Usage:

        FlameMessageWindow('Error', 'error', 'some important message')

        or

        if FlameMessageWindow('Confirm Operation', 'confirm', 'some important message', window):
            do something
    '''

    def __init__(self, message_title, message_type, message, parent=None):
        super(FlameMessageWindow, self).__init__()

        self.message_type = message_type

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumSize(QtCore.QSize(500, 330))
        self.setMaximumSize(QtCore.QSize(500, 330))
        self.setStyleSheet('background-color: rgb(36, 36, 36)')

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

        self.setParent(parent)

        self.grid = QtWidgets.QGridLayout()

        self.main_label = FlameLabel(message_title, label_width=500)
        self.main_label.setStyleSheet('color: rgb(154, 154, 154); font: 18px "Discreet"')

        self.message_text_edit = QtWidgets.QTextEdit(message)
        self.message_text_edit.setDisabled(True)
        self.message_text_edit.setStyleSheet('QTextEdit {color: rgb(154, 154, 154); background-color: rgb(36, 36, 36); selection-color: rgb(190, 190, 190); selection-background-color: rgb(36, 36, 36); border: none; padding-left: 20px; padding-right: 20px; font: 12px "Discreet"}')

        # Set confirm/ok button color

        if message_type == 'confirm':
            self.confirm_button = FlameButton('Confirm', self.confirm, button_color='blue', button_width=110)

        elif message_type == 'warning':
            self.confirm_button = FlameButton('Confirm', self.confirm, button_color='red', button_width=110)

        else:
            self.ok_button = FlameButton('Ok', self.confirm, button_color='blue', button_width=110)

        # Set layout for message window

        if message_type == 'confirm' or message_type == 'warning':
            self.cancel_button = FlameButton('Cancel', self.cancel, button_width=110)
            self.grid.addWidget(self.main_label, 0, 0)
            self.grid.setRowMinimumHeight(1, 30)
            self.grid.addWidget(self.message_text_edit, 2, 0, 4, 8)
            self.grid.setRowMinimumHeight(9, 30)
            self.grid.addWidget(self.cancel_button, 10, 5)
            self.grid.addWidget(self.confirm_button, 10, 6)
            self.grid.setRowMinimumHeight(11, 30)
        else:
            self.grid.addWidget(self.main_label, 0, 0)
            self.grid.setRowMinimumHeight(1, 30)
            self.grid.addWidget(self.message_text_edit, 2, 0, 4, 8)
            self.grid.setRowMinimumHeight(9, 30)
            self.grid.addWidget(self.ok_button, 10, 6)
            self.grid.setRowMinimumHeight(11, 30)

        message = message.replace('<br>', ' ')
        message = message.replace('<center>', '')
        message = message.replace('</center>', '')
        message = message.replace('<dd>', '')
        message = message.replace('<b>', '')
        message = message.replace('</b>', '')

        print (f'\n--> {message_title}: {message}\n')

        self.setLayout(self.grid)
        self.show()
        self.exec_()

    def __bool__(self):

        return self.confirmed

    def cancel(self):

        self.close()
        self.confirmed = False
        print ('--> Cancelled\n')

    def confirm(self):

        self.close()
        self.confirmed = True
        print ('--> Confirmed\n')

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        if self.message_type == 'confirm':
            line_color = QtGui.QColor(71, 71, 71)
        elif self.message_type == 'message':
            line_color = QtGui.QColor(0, 110, 176)
        elif self.message_type == 'error':
            line_color = QtGui.QColor(200, 172, 30)
        elif self.message_type == 'warning':
            line_color = QtGui.QColor(200, 29, 29)

        painter.setPen(QtGui.QPen(line_color, 6, QtCore.Qt.SolidLine))
        painter.drawLine(0, 0, 0, 330)

        painter.setPen(QtGui.QPen(QtGui.QColor(71, 71, 71), .5, QtCore.Qt.SolidLine))
        painter.drawLine(0, 40, 500, 40)

    def mousePressEvent(self, event):
        self.oldPosition = event.globalPos()

    def mouseMoveEvent(self, event):

        try:
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()
        except:
            pass

#

class FlamePasswordWindow(QtWidgets.QDialog):
    '''
    Custom Qt Flame Password Window

    FlamePasswordWindow(window_title, message[, user_name=False, parent=None])

    window_title: text shown in top left of window ie. Confirm Operation [str]
    message: text shown in window [str]
    user_name: if set to true a prompt for a user name will be included [bool]
    parent: (optional) parent window [object]

    Returns password as string

    Usage:

        for system password:

            password = str(FlamePasswordWindow('Enter System Password', 'System password needed to do something.'))

        username and password prompt:

           username, password = iter(FlamePasswordWindow('Login', 'Enter username and password.', user_name=True))
    '''

    def __init__(self, window_title, message, user_name=False, parent=None):
        super(FlamePasswordWindow, self).__init__()

        self.username = ''
        self.password = ''

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumSize(QtCore.QSize(500, 300))
        self.setMaximumSize(QtCore.QSize(500, 230))
        self.setStyleSheet('background-color: rgb(36, 36, 36)')

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

        self.setParent(parent)

        self.main_label = FlameLabel(window_title, label_width=500)
        self.main_label.setStyleSheet('color: rgb(154, 154, 154); font: 18px "Discreet"')

        self.message_label = FlameLabel(message, label_width=480)
        self.message_label.setStyleSheet('QLabel {color: rgb(154, 154, 154); background-color: rgb(36, 36, 36); padding-left: 20px; padding-right: 20px; font: 12px "Discreet"}')

        self.password_label = FlameLabel('Password', label_width=80)

        self.password_entry = FlameLineEdit('', width=300)
        self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)

        if user_name:
            self.username_label = FlameLabel('Username', label_width=80)
            self.username_entry = FlameLineEdit('', width=300)
            self.confirm_button = FlameButton('Confirm', self.username_password, button_color='blue', button_width=110)
        else:
            self.confirm_button = FlameButton('Confirm', self.system_password, button_color='blue', button_width=110)

        self.cancel_button = FlameButton('Cancel', self.cancel, button_width=110)

        # UI Widget Layout

        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(self.main_label, 0, 0)
        self.grid.setRowMinimumHeight(1, 30)
        self.grid.addWidget(self.message_label, 2, 0)
        self.grid.setRowMinimumHeight(3, 30)

        if user_name:
            self.grid.addWidget(self.username_label, 4, 0)
            self.grid.addWidget(self.username_entry, 4, 1)

        self.grid.addWidget(self.password_label, 5, 0)
        self.grid.addWidget(self.password_entry, 5, 1)
        self.grid.setRowMinimumHeight(9, 60)
        self.grid.addWidget(self.cancel_button, 10, 5)
        self.grid.addWidget(self.confirm_button, 10, 6)
        self.grid.setRowMinimumHeight(11, 30)

        message = message.replace('<br>', '')
        message = message.replace('<center>', '')
        message = message.replace('<dd>', '')

        print (f'\n--> {window_title}: {message}\n')

        self.setLayout(self.grid)
        self.show()
        self.exec_()

    def __str__(self):

        return self.password

    def __iter__(self):

        yield from (self.username, self.password)

    def cancel(self):

        self.login = ''
        self.close()
        print ('--> Cancelled\n')
        return

    def username_password(self):

        if self.password_entry.text() and self.username_entry.text():
            self.close()

            self.username = self.username_entry.text()
            self.password = self.password_entry.text()

            return

    def system_password(self):

        password = self.password_entry.text()

        # Test password - return password if correct

        if password:
            import subprocess

            args = "sudo -S echo OK".split()
            kwargs = dict(stdout=subprocess.PIPE, encoding="ascii")

            kwargs.update(input=password)
            cmd = subprocess.run(args, **kwargs)

            if cmd.stdout:
                print ('--> Password Correct\n')
                self.password = password
                self.close()
                return
            else:
                self.message_label.setText('Password incorrect, try again.')
                print ('--> Password Incorrect\n')

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        painter.setPen(QtGui.QPen(QtGui.QColor(200, 29, 29), 6, QtCore.Qt.SolidLine))
        painter.drawLine(0, 0, 0, 330)

        painter.setPen(QtGui.QPen(QtGui.QColor(71, 71, 71), .5, QtCore.Qt.SolidLine))
        painter.drawLine(0, 40, 500, 40)

    def mousePressEvent(self, event):
        self.oldPosition = event.globalPos()

    def mouseMoveEvent(self, event):

        try:
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()
        except:
            pass

#

class FlameProgressWindow(QtWidgets.QDialog):
    '''
    Custom Qt Flame Progress Window

    FlameProgressWindow(window_title, num_to_do[, parent=None])

    window_title: text shown in top left of window ie. Rendering... [str]
    num_to_do: total number of operations to do [int]

    Usage:

        To create window:

            self.progress_window = FlameProgressWindow('Rendering...', 10)

        To add text to window:

            self.progress_window.set_text('Rendering: Batch 1 or 5')

        To update progress bar:

            self.progress_window.set_progress_value(number_of_things_done)

        To enable or disable done button - True or False:

            self.self.progress_window.enable_done_button(True)
    '''

    def __init__(self, window_title, num_to_do, parent=None):
        super(FlameProgressWindow, self).__init__()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumSize(QtCore.QSize(500, 330))
        self.setMaximumSize(QtCore.QSize(500, 330))
        self.setStyleSheet('background-color: rgb(36, 36, 36)')

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

        self.setParent(parent)

        self.grid = QtWidgets.QGridLayout()

        self.main_label = FlameLabel(window_title, label_width=500)
        self.main_label.setStyleSheet('color: rgb(154, 154, 154); font: 18px "Discreet"')

        self.message_text_edit = QtWidgets.QTextEdit('')
        self.message_text_edit.setDisabled(True)
        self.message_text_edit.setStyleSheet('QTextEdit {color: rgb(154, 154, 154); background-color: rgb(36, 36, 36); selection-color: rgb(190, 190, 190); selection-background-color: rgb(36, 36, 36); border: none; padding-left: 20px; padding-right: 20px; font: 12px "Discreet"}')

        # Progress bar

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(num_to_do)
        self.progress_bar.setMaximumHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet('QProgressBar {color: rgb(154, 154, 154); background-color: rgb(45, 45, 45); font: 14px "Discreet"; border: none}'
                                        'QProgressBar:chunk {background-color: rgb(0, 110, 176)}')

        self.done_button = FlameButton('Done', self.close, button_color='blue', button_width=110)

        # Layout

        self.grid.addWidget(self.main_label, 0, 0)
        self.grid.setRowMinimumHeight(1, 30)
        self.grid.addWidget(self.message_text_edit, 2, 0, 1, 4)
        self.grid.addWidget(self.progress_bar, 8, 0, 1, 7)
        self.grid.setRowMinimumHeight(9, 30)
        self.grid.addWidget(self.done_button, 10, 6)
        self.grid.setRowMinimumHeight(11, 30)

        print (f'\n--> {window_title}\n')

        self.setLayout(self.grid)
        self.show()

    def set_text(self, text):

        self.message_text_edit.setText(text)

    def set_progress_value(self, value):

        self.progress_bar.setValue(value)

    def enable_done_button(self, value):

        if value:
            self.done_button.setEnabled(True)
        else:
            self.done_button.setEnabled(False)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(QtGui.QColor(71, 71, 71), .5, QtCore.Qt.SolidLine))
        painter.drawLine(0, 40, 500, 40)
        painter.setPen(QtGui.QPen(QtGui.QColor(71, 71, 71), 6, QtCore.Qt.SolidLine))
        painter.drawLine(0, 0, 0, 330)

    def mousePressEvent(self, event):

        self.oldPosition = event.globalPos()

    def mouseMoveEvent(self, event):

        try:
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()
        except:
            pass

#

class FlamePushButton(QtWidgets.QPushButton):
    '''
    Custom Qt Flame Push Button Widget

    FlamePushButton(button_name, button_checked[, connect=None, button_width=150])

    button_name: text displayed on button [str]
    button_checked: True or False [bool]
    connect: execute when button is pressed [function]
    button_width: (optional) default is 150. [int]

    Usage:

        pushbutton = FlamePushButton('Button Name', False)
    '''

    def __init__(self, button_name, button_checked, connect=None, button_width=150):
        super(FlamePushButton, self).__init__()

        self.setText(button_name)
        self.setCheckable(True)
        self.setChecked(button_checked)
        self.setMinimumSize(button_width, 28)
        self.setMaximumSize(button_width, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: rgb(154, 154, 154); background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 rgb(58, 58, 58), stop: .94 rgb(44, 54, 68)); text-align: left; '
                                        'border-top: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 rgb(58, 58, 58), stop: .94 rgb(44, 54, 68)); '
                                        'border-bottom: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 rgb(58, 58, 58), stop: .94 rgb(44, 54, 68)); '
                                        'border-left: 1px solid rgb(58, 58, 58); '
                                        'border-right: 1px solid rgb(44, 54, 68); '
                                        'padding-left: 5px; font: 14px "Discreet"}'
                           'QPushButton:checked {color: rgb(217, 217, 217); background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 rgb(71, 71, 71), stop: .94 rgb(50, 101, 173)); text-align: left; '
                                        'border-top: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 rgb(71, 71, 71), stop: .94 rgb(50, 101, 173)); '
                                        'border-bottom: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 rgb(71, 71, 71), stop: .94 rgb(50, 101, 173)); '
                                        'border-left: 1px solid rgb(71, 71, 71); '
                                        'border-right: 1px solid rgb(50, 101, 173); '
                                        'padding-left: 5px; font: italic}'
                           'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 rgb(58, 58, 58), stop: .94 rgb(50, 50, 50)); font: light; border: none}'
                           'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')

#

class FlameSlider(QtWidgets.QLineEdit):
    '''
    Custom Qt Flame Slider Widget

    FlameSlider(start_value, min_value, max_value[, value_is_float=False, slider_width=110])

    start_value: int or float value
    min_value: int or float value
    max_value: int or float value
    value_is_float: bool value
    slider_width: (optional) default value is 110. [int]

    Usage:

        slider = FlameSlider(0, -20, 20, False)
    '''

    def __init__(self, start_value, min_value, max_value, value_is_float=False, slider_width=110):

        super(FlameSlider, self).__init__()
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumHeight(28)
        self.setMinimumWidth(slider_width)
        self.setMaximumWidth(slider_width)

        if value_is_float:
            self.spinbox_type = 'Float'
        else:
            self.spinbox_type = 'Interger'

        self.min = min_value
        self.max = max_value
        self.steps = 1
        self.value_at_press = None
        self.pos_at_press = None
        self.setValue(start_value)
        self.setReadOnly(True)
        self.textChanged.connect(self.value_changed)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QLineEdit {color: rgb(154, 154, 154); background-color: rgb(55, 65, 75); selection-color: rgb(38, 38, 38); selection-background-color: rgb(184, 177, 167); border: none; padding-left: 5px; font: 14px "Discreet"}'
                           'QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}'
                           'QLineEdit:disabled {color: rgb(106, 106, 106); background-color: rgb(55, 65, 75)}'
                           'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')
        self.clearFocus()

        class Slider(QtWidgets.QSlider):

            def __init__(self, start_value, min_value, max_value, slider_width):
                super(Slider, self).__init__()

                self.setMaximumHeight(4)
                self.setMinimumWidth(slider_width)
                self.setMaximumWidth(slider_width)
                self.setMinimum(min_value)
                self.setMaximum(max_value)
                self.setValue(start_value)
                self.setOrientation(QtCore.Qt.Horizontal)
                self.setStyleSheet('QSlider {color: rgb(55, 65, 75); background-color: rgb(39, 45, 53)}'
                                   'QSlider::groove {color: rgb(39, 45, 53); background-color: rgb(39, 45, 53)}'
                                   'QSlider::handle:horizontal {background-color: rgb(102, 102, 102); width: 3px}'
                                   'QSlider::disabled {color: rgb(106, 106, 106); background-color: rgb(55, 65, 75)}')
                self.setDisabled(True)
                self.raise_()

        def set_slider():
            slider666.setValue(float(self.text()))

        slider666 = Slider(start_value, min_value, max_value, slider_width)
        self.textChanged.connect(set_slider)

        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.addWidget(slider666)
        self.vbox.setContentsMargins(0, 24, 0, 0)

    def calculator(self):
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
            self.setStyleSheet('QLineEdit {color: rgb(154, 154, 154); background-color: rgb(55, 65, 75); selection-color: rgb(154, 154, 154); selection-background-color: rgb(55, 65, 75); border: none; padding-left: 5px; font: 14pt "Discreet"}'
                               'QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}')
        def revert_color():
            self.setStyleSheet('QLineEdit {color: rgb(154, 154, 154); background-color: rgb(55, 65, 75); selection-color: rgb(154, 154, 154); selection-background-color: rgb(55, 65, 75); border: none; padding-left: 5px; font: 14pt "Discreet"}'
                               'QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}')
        calc_version = '1.2'
        self.clean_line = False

        calc_window = QtWidgets.QWidget()
        calc_window.setMinimumSize(QtCore.QSize(210, 280))
        calc_window.setMaximumSize(QtCore.QSize(210, 280))
        calc_window.setWindowTitle(f'pyFlame Calc {calc_version}')
        calc_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
        calc_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        calc_window.destroyed.connect(revert_color)
        calc_window.move(QtGui.QCursor.pos().x() - 110, QtGui.QCursor.pos().y() - 290)
        calc_window.setStyleSheet('background-color: rgb(36, 36, 36)')

        # Labels

        calc_label = QtWidgets.QLabel('Calculator', calc_window)
        calc_label.setAlignment(QtCore.Qt.AlignCenter)
        calc_label.setMinimumHeight(28)
        calc_label.setStyleSheet('color: rgb(154, 154, 154); background-color: rgb(57, 57, 57); font: 14px "Discreet"')

        #  LineEdit

        calc_lineedit = QtWidgets.QLineEdit('', calc_window)
        calc_lineedit.setMinimumHeight(28)
        calc_lineedit.setFocus()
        calc_lineedit.returnPressed.connect(enter)
        calc_lineedit.setStyleSheet('QLineEdit {color: rgb(154, 154, 154); background-color: rgb(55, 65, 75); selection-color: rgb(38, 38, 38); selection-background-color: rgb(184, 177, 167); border: none; padding-left: 5px; font: 14px "Discreet"}')

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
                self.setStyleSheet('QPushButton {color: rgb(154, 154, 154); background-color: rgb(58, 58, 58); border: none; font: 14px "Discreet"}'
                                   'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                                   'QPushButton:pressed {color: rgb(159, 159, 159); background-color: rgb(66, 66, 66); border: none}'
                                   'QPushButton:disabled {color: rgb(116, 116, 116); background-color: rgb(58, 58, 58); border: none}')

        blank_btn = FlameButton('', 40, 28, calc_null, calc_window)
        blank_btn.setDisabled(True)
        plus_minus_btn = FlameButton('+/-', 40, 28, plus_minus, calc_window)
        plus_minus_btn.setStyleSheet('color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); font: 14px "Discreet"')
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

        _0_btn = FlameButton('0', 89, 28, (partial(button_press, '0')), calc_window)
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

        if event.buttons() == QtCore.Qt.LeftButton:
            self.value_at_press = self.value()
            self.pos_at_press = event.pos()
            self.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
            self.setStyleSheet('QLineEdit {color: rgb(217, 217, 217); background-color: rgb(73, 86, 99); selection-color: rgb(154, 154, 154); selection-background-color: rgb(73, 86, 99); border: none; padding-left: 5px; font: 14pt "Discreet"}'
                               'QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}')

    def mouseReleaseEvent(self, event):

        if event.button() == QtCore.Qt.LeftButton:

            # Open calculator if button is released within 10 pixels of button click

            if event.pos().x() in range((self.pos_at_press.x() - 10), (self.pos_at_press.x() + 10)) and event.pos().y() in range((self.pos_at_press.y() - 10), (self.pos_at_press.y() + 10)):
                self.calculator()
            else:
                self.setStyleSheet('QLineEdit {color: rgb(154, 154, 154); background-color: rgb(55, 65, 75); selection-color: rgb(154, 154, 154); selection-background-color: rgb(55, 65, 75); border: none; padding-left: 5px; font: 14pt "Discreet"}'
                                   'QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}')

            self.value_at_press = None
            self.pos_at_press = None
            self.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
            return

        super(FlameSlider, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):

        if event.buttons() != QtCore.Qt.LeftButton:
            return

        if self.pos_at_press is None:
            return

        steps_mult = self.getStepsMultiplier(event)
        delta = event.pos().x() - self.pos_at_press.x()

        if self.spinbox_type == 'Interger':
            delta /= 10  # Make movement less sensiteve.
        else:
            delta /= 100
        delta *= self.steps * steps_mult

        value = self.value_at_press + delta
        self.setValue(value)

        super(FlameSlider, self).mouseMoveEvent(event)

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

        if self.spinbox_type == 'Interger':
            self.steps = max(steps, 1)
        else:
            self.steps = steps

    def value(self):

        if self.spinbox_type == 'Interger':
            return int(self.text())
        else:
            return float(self.text())

    def setValue(self, value):

        if self.min is not None:
            value = max(value, self.min)

        if self.max is not None:
            value = min(value, self.max)

        if self.spinbox_type == 'Interger':
            self.setText(str(int(value)))
        else:
            # Keep float values to two decimal places

            self.setText('%.2f' % float(value))

#

class FlameTextEdit(QtWidgets.QTextEdit):
    '''
    Custom Qt Flame Text Edit Widget

    FlameTextEdit(text[, read_only=False])

    text: text to be displayed [str]
    read_only: (optional) make text in window read only [bool] - default is False

    To use:

        text_edit = FlameTextEdit('some_text_here', True_or_False)
    '''

    def __init__(self, text, read_only=False):
        super(FlameTextEdit, self).__init__()

        self.setMinimumHeight(50)
        self.setMinimumWidth(150)
        self.setText(text)
        self.setReadOnly(read_only)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        if read_only:
            self.setStyleSheet('QTextEdit {color: rgb(154, 154, 154); background-color: #37414b; selection-color: #262626; selection-background-color: #b8b1a7; border: none; padding-left: 5px; font: 14px "Discreet"}'
                               #'QTextEdit:focus {background-color: #495663}'
                               'QScrollBar {color: #111111; background: rgb(49, 49, 49)}'
                               'QScrollBar::handle {color: #111111; background : 111111;}'
                               'QScrollBar::add-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                               'QScrollBar::sub-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                               'QScrollBar {color: #111111; background: rgb(49, 49, 49)}'
                               'QScrollBar::handle {color: #111111; background : 111111;}'
                               'QScrollBar::add-line:horizontal {border: none; background: none; width: 0px; height: 0px}'
                               'QScrollBar::sub-line:horizontal {border: none; background: none; width: 0px; height: 0px}')
        else:
            self.setStyleSheet('QTextEdit {color: rgb(154, 154, 154); background-color: #37414b; selection-color: #262626; selection-background-color: #b8b1a7; border: none; padding-left: 5px; font: 14px "Discreet"}'
                               'QTextEdit:focus {background-color: #495663}'
                               'QScrollBar {color: #111111; background: rgb(49, 49, 49)}'
                               'QScrollBar::handle {color: #111111; background : 111111;}'
                               'QScrollBar::add-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                               'QScrollBar::sub-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                               'QScrollBar {color: #111111; background: rgb(49, 49, 49)}'
                               'QScrollBar::handle {color: #111111; background : 111111;}'
                               'QScrollBar::add-line:horizontal {border: none; background: none; width: 0px; height: 0px}'
                               'QScrollBar::sub-line:horizontal {border: none; background: none; width: 0px; height: 0px}')

#

class FlameTokenPushButton(QtWidgets.QPushButton):
    '''
    Custom Qt Flame Token Push Button Widget

    FlameTokenPushButton(button_name, token_dict, token_dest[, button_width=150, button_max_width=300])

    button_name: Text displayed on button [str]
    token_dict: Dictionary defining tokens. {'Token Name': '<Token>'} [dict]
    token_dest: LineEdit that token will be applied to [object]
    button_width: (optional) default is 150 [int]
    button_max_width: (optional) default is 300 [int]

    Usage:

        token_dict = {'Token 1': '<Token1>', 'Token2': '<Token2>'}
        token_push_button = FlameTokenPushButton('Add Token', token_dict, token_dest)
    '''

    def __init__(self, button_name, token_dict, token_dest, button_width=150, button_max_width=300):
        super(FlameTokenPushButton, self).__init__()
        from functools import partial

        self.setText(button_name)
        self.setMinimumHeight(28)
        self.setMinimumWidth(button_width)
        self.setMaximumWidth(button_max_width)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                           'QPushButton:hover {border: 1px solid rgb(90, 90, 90)}'
                           'QPushButton:disabled {color: rgb(106, 106, 106); background-color: rgb(45, 55, 68); border: none}'
                           'QPushButton::menu-indicator {subcontrol-origin: padding; subcontrol-position: center right}'
                           'QToolTip {color: rgb(170, 170, 170); background-color: rgb(71, 71, 71); border: 10px solid rgb(71, 71, 71)}')

        def token_action_menu():

            def insert_token(token):
                for key, value in token_dict.items():
                    if key == token:
                        token_name = value
                        token_dest.insert(token_name)

            for key, value in token_dict.items():
                token_menu.addAction(key, partial(insert_token, key))

        token_menu = QtWidgets.QMenu(self)
        token_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        token_menu.setStyleSheet('QMenu {color: rgb(154, 154, 154); background-color: rgb(45, 55, 68); border: none; font: 14px "Discreet"}'
                                 'QMenu::item:selected {color: rgb(217, 217, 217); background-color: rgb(58, 69, 81)}')

        self.setMenu(token_menu)

        token_action_menu()

#

class FlameTreeWidget(QtWidgets.QTreeWidget):
    '''
    Custom Qt Flame Tree Widget

    FlameTreeWidget(tree_headers[, connect=None, tree_min_width=100, tree_min_height=100])

    tree_headers: list of names to be used for column names in tree [list]
    connect: execute when item in tree is clicked on [function]
    tree_min_width = set tree width [int]
    tree_min_height = set tree height [int]

    To use:

        tree_headers = ['Header1', 'Header2', 'Header3', 'Header4']
        tree = FlameTreeWidget(tree_headers)
    '''

    def __init__(self, tree_headers, connect=None, tree_min_width=100, tree_min_height=100):
        super(FlameTreeWidget, self).__init__()

        self.setMinimumWidth(tree_min_width)
        self.setMinimumHeight(tree_min_height)
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.setAlternatingRowColors(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QTreeWidget {color: rgb(154, 154, 154); background-color: rgb(42, 42, 42); alternate-background-color: rgb(45, 45, 45); border: none; font: 14pt "Discreet"}'
                           'QHeaderView::section {color: rgb(154, 154, 154); background-color: rgb(57, 57, 57); border: none; padding-left: 10px; font: 14pt "Discreet"}'
                           'QTreeWidget:item:selected {color: rgb(217, 217, 217); background-color: rgb(71, 71, 71); selection-background-color: rgb(153, 153, 153); border: 1px solid rgb(17, 17, 17)}'
                           'QTreeWidget:item:selected:active {color: rgb(153, 153, 153); border: none}'
                           'QTreeWidget:disabled {color: rgb(101, 101, 101); background-color: rgb(34, 34, 34)}'
                           'QMenu {color: rgb(154, 154, 154); background-color: rgb(36, 48, 61); font: 14pt "Discreet"}'
                           'QMenu::item:selected {color: rgb(217, 217, 217); background-color: rgb(58, 69, 81)}'
                           'QScrollBar {color: rgb(17, 17, 17); background: rgb(49, 49, 49)}'
                           'QScrollBar::handle {color: rgb(17, 17, 17); background : 111111;}'
                           'QScrollBar::add-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                           'QScrollBar::sub-line:vertical {border: none; background: none; width: 0px; height: 0px}'
                           'QScrollBar {color: rgb(17, 17, 17); background: rgb(49, 49, 49)}'
                           'QScrollBar::handle {color: rgb(17, 17, 17); background : 111111;}'
                           'QScrollBar::add-line:horizontal {border: none; background: none; width: 0px; height: 0px}'
                           'QScrollBar::sub-line:horizontal {border: none; background: none; width: 0px; height: 0px}')
        self.setHeaderLabels(tree_headers)

#

class FlameWindow(QtWidgets.QWidget):
    '''
    Custom Qt Flame Window Widget

    FlameWindow(window_title, window_layout, window_width, window_height[, window_bar_color='blue'])

    window_title: text displayed in top left corner of window [str]
    window_layout: QLayout object. QLayout should be defined before adding FlameWindow [object]
    window_width: width of window [int]
    window_height: height of window [int]
    window_bar_color: (optional) color of bar on left side of window. options are red, blue, green, yellow, gray. [str] - default is blue

    Usage:

        grid_layout = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'Import Camera <small>{VERSION}', grid_layout, 400, 200)
    '''

    def __init__(self, window_title, window_layout, window_width, window_height, window_bar_color='blue'):
        super(FlameWindow, self).__init__()

        self.window_bar_color = window_bar_color

        self.window_width = window_width
        self.window_height = window_height
        self.setMinimumSize(QtCore.QSize(window_width, window_height))
        self.setMaximumSize(QtCore.QSize(window_width, window_height))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setStyleSheet('QWidget {background-color: rgb(36, 36, 36)}'
                           'QTabWidget {background-color: rgb(36, 36, 36); border: none; font: 14px "Discreet"}'
                           'QTabWidget::tab-bar {alignment: center}'
                           'QTabBar::tab {color: rgb(154, 154, 154); background-color: rgb(36, 36, 36); min-width: 20ex; padding: 5px;}'
                           'QTabBar::tab:selected {color: rgb(186, 186, 186); background-color: rgb(31, 31, 31); border: 1px solid rgb(31, 31, 31); border-bottom: 1px solid rgb(51, 102, 173)}'
                           'QTabBar::tab:!selected {color: rgb(186, 186, 186); background-color: rgb(36, 36, 36); border: none}'
                           'QTabWidget::pane {border-top: 1px solid rgb(49, 49, 49)}')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

        self.title_label = FlameLabel(window_title, label_width=window_width)
        self.title_label.setStyleSheet('color: rgb(154, 154, 154); font: 18px "Discreet"')

        # Layout

        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(self.title_label, 0, 0)
        self.grid.addLayout(window_layout, 2, 0, 3, 3)
        self.grid.setRowMinimumHeight(3, 100)

        self.setLayout(self.grid)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        if self.window_bar_color == 'blue':
            bar_color = QtGui.QColor(0, 110, 176)
        elif self.window_bar_color == 'red':
            bar_color = QtGui.QColor(200, 29, 29)
        elif self.window_bar_color == 'green':
            bar_color = QtGui.QColor(0, 180, 13)
        elif self.window_bar_color == 'yellow':
            bar_color = QtGui.QColor(200, 172, 30)
        elif self.window_bar_color == 'gray':
            bar_color = QtGui.QColor(71, 71, 71)


        painter.setPen(QtGui.QPen(QtGui.QColor(71, 71, 71), .5, QtCore.Qt.SolidLine))
        painter.drawLine(0, 40, self.window_width, 40)
        painter.setPen(QtGui.QPen(bar_color, 6, QtCore.Qt.SolidLine))
        painter.drawLine(0, 0, 0, self.window_height)

    def mousePressEvent(self, event):

        self.oldPosition = event.globalPos()

    def mouseMoveEvent(self, event):

        try:
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()
        except:
            pass
