# -*- coding: utf-8 -*-
'''
Script Name: Logik Portal
Script Version: 2.9
Flame Version: 2021
Written by: Michael Vaglienty
Crying Croc Design by: Enid Dalkoff
Creation Date: 10.31.20
Update Date: 12.02.21

Custom Action Type: Flame Main Menu

Description:

    Share/install python scripts, batch setups, archives, and download matchboxes

    Menu:

        Flame Main Menu -> Logik -> Logik Portal

To install:

    Copy script into /opt/Autodesk/shared/python/logik_portal

Updates:

    v2.9 12.02.21

        Login bug fix

    v2.8 11.17.21

        Login info for uploading scripts only needs to be entered first time something is uploaded.

    v2.7 10.16.21

        Install Local button added to python tab to install python scripts from local drive

        Improved Flame version detection

        Script will now attempt to download matchbox collection from website. If website is down, it will download from portal ftp.

    v2.6 09.06.21

        Misc bug fixes / fixed problem with not being able to enter system password to load matchboxes to write protected folder

    v2.5 07.30.21

        Added ability to upload/download archives - Archive size limit is 200MB

        Config is now XML

    v2.4 07.23.21

        Added python submit button back. User name and password now required to submit scripts.

        Fixed bug - files starting with . sometimes caused script to not work

    v2.3 07.06.21

        Added Logik Matchbox archive to Portal FTP. Matchbox archive now stored on FTP instead of pulling directly from logik-matchbook.org

    v2.2 06.03.21

        Updated to be compatible with Flame 2022/Python 3.7

        Removed python script submission ability. Scripts can now be added through github submissions only.

    v1.6 03.14.21

        UI improvements/updates - UI elements to classes

        Added contextual menus to python tab to install and delete scripts and to batch tab to download batch setups

        User will be prompted for system password when trying to download matchboxes to protected folders such as /opt/Autodesk/presets/2021.1/matchbox/shaders

        If newer version of installed script is available on portal it will be highlighted in portal list

        If newer version of flame is required for a script, script entry will be greyed out

        If newer version of flame is required for a batch setup, batch setup entry will be greyed out

        Batch setups now properly download into paths with spaces in folder names

        User will get message if script folder needs permissions changed to create temp folders/files

        File browse buttons removed - browser now opens when clicking lineedit field

        If new version of a python script is submitted old script will be removed

    v1.5 02.27.21

        UI code updates

        Fixed bug causing script to hang when reading descriptions on certain scripts

        Fixed batch submit button

    v1.4 01.25.21

        Fixed temp path for logik matchbox install

    v1.3 01.14.21

        Script description info can now be entered in Portal UI instead of being in script header.

        Fixed font size for linux

    v1.2 12.29.20

        Fixed problems with script running on Flame with extra .x in Flame version
'''

from __future__ import print_function
import os, re, ast, time, urllib, shutil
from subprocess import Popen, PIPE
from ftplib import FTP
from functools import partial
import xml.etree.ElementTree as ET
from PySide2 import QtWidgets, QtCore, QtGui

VERSION = 'v2.9'

SCRIPT_PATH = '/opt/Autodesk/shared/python/logik_portal'

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget
    Options for normal, label with background color, and label with background color and outline
    For different label looks use: label_type='normal', label_type='background', or label_type='outline'
    """

    def __init__(self, label_name, label_type, parent, *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent)
        self.setMinimumSize(110, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px solid #282828; font: 14px "Discreet"}'
                               'QLabel: disabled {color: #6a6a6a}')
        elif label_type == 'background':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')
        elif label_type == 'outline':
            self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.setStyleSheet('color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget
    """

    def __init__(self, button_name, connect, parent, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumSize(QtCore.QSize(110, 28))
        self.setMaximumSize(QtCore.QSize(110, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

class FlamePushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Widget
    """

    def __init__(self, button_name, checked, parent, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setMinimumSize(110, 28)
        self.setMaximumSize(110, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #424142, stop: .91 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #4f4f4f, stop: .91 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #383838, stop: .91 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlamePushButtonMenu(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Menu Widget
    """

    def __init__(self, button_name, menu_options, parent, *args, **kwargs):
        super(FlamePushButtonMenu, self).__init__(*args, **kwargs)
        from functools import partial

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        def create_menu(option):
            self.setText(option)

        pushbutton_menu = QtWidgets.QMenu(parent)
        pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        pushbutton_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        for option in menu_options:
            pushbutton_menu.addAction(option, partial(create_menu, option))

        self.setMenu(pushbutton_menu)

class FlameClickableLineEdit(QtWidgets.QLineEdit):
    """
    Custom Qt Flame Clickable Line Edit Widget
    """

    clicked = QtCore.Signal()

    def __init__(self, text, parent, *args, **kwargs):
        super(FlameClickableLineEdit, self).__init__(*args, **kwargs)

        self.setText(text)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setReadOnly(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; font: 14px "Discreet"}'
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

class FlameLineEdit(QtWidgets.QLineEdit):
    """
    Custom Qt Flame Line Edit Widget
    """
    clicked = QtCore.Signal()

    def __init__(self, text, parent, *args, **kwargs):
        super(FlameLineEdit, self).__init__(*args, **kwargs)

        self.setText(text)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setMinimumWidth(300)

        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                           'QLineEdit:selected {color: #222222}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}'
                           'QLineEdit:focus {background-color: #474e58}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlameTextEdit(QtWidgets.QTextEdit):
    """
    Custom Qt Flame Text Edit Widget
    read_only value is bool(True or False)
    """

    def __init__(self, text, read_only, parent, *args, **kwargs):
        super(FlameTextEdit, self).__init__(*args, **kwargs)

        self.setMinimumHeight(50)
        self.setMinimumWidth(150)
        self.setReadOnly(read_only)
        if read_only:
            self.setStyleSheet('color: #9a9a9a; selection-color: #262626; selection-background-color: #b8b1a7; border: 1px inset #404040; font: 14px "Discreet"')
        else:
            self.setStyleSheet('QTextEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; border: 1px inset #404040; font: 14px "Discreet"}'
                               'QTextEdit:focus {background-color: #474e58}')

        self.verticalScrollBar().setStyleSheet('color: #818181; background-color: #313131')
        self.horizontalScrollBar().setStyleSheet('color: #818181; background-color: #313131')

class FlameTreeWidget(QtWidgets.QTreeWidget):
    """
    Custom Qt Flame Tree Widget
    """

    def __init__(self, description, description_text_edit, headers, parent, *args, **kwargs):
        super(FlameTreeWidget, self).__init__(*args, **kwargs)
        from functools import partial

        self.setMinimumWidth(550)
        self.setMinimumHeight(300)
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.setAlternatingRowColors(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(partial(description, description_text_edit, self))
        self.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; font: 14px "Discreet"}'
                           'QTreeWidget::item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                           'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14px "Discreet"}'
                           'QTreeWidget::item:selected {selection-background-color: #111111}'
                           'QMenu {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        self.verticalScrollBar().setStyleSheet('color: #818181')
        self.horizontalScrollBar().setStyleSheet('color: #818181')
        self.setHeaderLabels(headers)

# ------------------------------------------------- #

class LogikPortal(object):

    def __init__(self, selection):
        import flame

        print ('''
 _                 _ _      _____           _        _
| |               (_) |    |  __ \         | |      | |
| |     ___   __ _ _| | __ | |__) |__  _ __| |_ __ _| |
| |    / _ \ / _` | | |/ / |  ___/ _ \| '__| __/ _` | |
| |___| (_) | (_| | |   <  | |  | (_) | |  | || (_| | |
|______\___/ \__, |_|_|\_\ |_|   \___/|_|   \__\__,_|_|
              __/ |
             |___/
        ''')

        # print ('\n')
        print ('>' * 18, 'logik portal %s' % VERSION, '<' * 18)

        # Define paths

        self.shared_script_path = '/opt/Autodesk/shared/python'
        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Load config file

        self.config()

        # Get user

        self.flame_current_user = flame.users.current_user.name

        self.temp_folder = os.path.join(SCRIPT_PATH, 'temp')
        if not os.path.isdir(self.temp_folder):
            try:
                os.makedirs(self.temp_folder)
            except:
                return message_box('<center>Script needs full permissions to script folder.<br><br>In shell/terminal type:<br><br>chmod 777 /opt/Autodesk/shared/python/logik_portal<br>')

        # Get version of flame and convert to float

        self.flame_version = flame.get_version()

        if len(self.flame_version) > 6:
            self.flame_version = self.flame_version[:6]
        self.flame_version = float(self.flame_version)
        print ('    flame_version:', self.flame_version, '\n')

        # Check internet connection to ftp

        try:
            self.ftp_download_connect()
        except:
            message_box("<center>Can't connect to Logik Portal.<br>Check internet connection and try again.")
            return

        #  Init variables

        self.ftp_script_list = []
        self.installed_script_dict = {}
        self.file_description = ''
        self.tar_path = ''
        self.tar_file_name = ''
        self.batch_setups_xml_path = ''
        self.python_scripts_xml_path = ''
        self.sudo_password = ''

        self.main_window()

        self.get_installed_scripts(self.installed_scripts_tree, self.shared_script_path)

        self.get_batch_setups(self.batch_setups_tree)

        self.get_archives(self.archives_tree)

        self.get_ftp_scripts(self.portal_scripts_tree)

        # Close ftp connection

        self.ftp.quit()

        # Check first items in tree lists for install/download button disable

        self.check_archive_flame_version(self.archives_tree, 0)

        self.check_batch_flame_version(self.batch_setups_tree, 0)

        self.check_script_flame_version(self.portal_scripts_tree, 0)

        print ('>>> logik portal loaded <<<\n')

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get UI settings

            for setting in root.iter('logik_portal_settings'):
                self.matchbox_path = setting.find('matchbox_path').text
                self.batch_setup_download_path = setting.find('batch_setup_download_path').text
                self.batch_submit_path = setting.find('batch_submit_path').text
                self.script_submit_path = setting.find('script_submit_path').text
                self.open_batch = ast.literal_eval(setting.find('open_batch').text)
                self.archive_download_path = setting.find('archive_download_path').text
                self.archive_submit_path = setting.find('archive_submit_path').text
                self.username = setting.find('username').text
                self.password = setting.find('password').text

            print ('\n>>> config loaded <<<\n')

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
    <logik_portal_settings>
        <matchbox_path></matchbox_path>
        <batch_setup_download_path>/</batch_setup_download_path>
        <batch_submit_path>/</batch_submit_path>
        <script_submit_path>/</script_submit_path>
        <open_batch>False</open_batch>
        <archive_download_path>/</archive_download_path>
        <archive_submit_path>/</archive_submit_path>
        <username></username>
        <password></password>
    </logik_portal_settings>
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

    # ----------------------------------------------------------------- #

    def ftp_download_connect(self):

        # Connect to ftp

        self.ftp = FTP('logik.hostedftp.com')
        self.ftp.login('logik', 'L0gikD0wnL0ad#20')

        print ('>>> connected to portal <<<\n')

    def ftp_upload_connect(self):

        # Connect to ftp

        self.ftp = FTP('logik.hostedftp.com')
        self.ftp.login('logik_upload', 'L0gikUpl0ad#20')
        self.ftp.cwd('/Submit')

        print ('>>> connected to portal <<<\n')

    def ftp_disconnect(self):

        self.ftp.quit()

        print ('>>> disconnected from portal <<<\n')

    # ----------------------------------------------------------------- #

    def main_window(self):

        self.window = QtWidgets.QTabWidget()
        self.window.setMinimumSize(QtCore.QSize(1200, 750))
        self.window.setMaximumSize(QtCore.QSize(1200, 750))
        self.window.setWindowTitle('Logik Portal %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #212121')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Tabs

        self.window.tab1 = QtWidgets.QWidget()
        self.window.tab2 = QtWidgets.QWidget()
        self.window.tab3 = QtWidgets.QWidget()
        self.window.tab4 = QtWidgets.QWidget()
        self.window.tab5 = QtWidgets.QWidget()

        self.window.setStyleSheet('QTabWidget {background-color: #212121; font: 14px "Discreet"}'
                                  'QTabWidget::tab-bar {alignment: center}'
                                  'QTabBar::tab {color: #9a9a9a; background-color: #212121; border: 1px solid #3a3a3a; border-bottom-color: #555555; min-width: 20ex; padding: 5px}'
                                  'QTabBar::tab:selected {color: #bababa; border: 1px solid #555555; border-bottom: 1px solid #212121}'
                                  'QTabWidget::pane {border-top: 1px solid #555555; top: -0.05em}')

        self.window.addTab(self.window.tab1, 'Python Scripts')
        self.window.addTab(self.window.tab3, 'Matchbox')
        self.window.addTab(self.window.tab4, 'Batch Setups')
        self.window.addTab(self.window.tab5, 'Archives')

        self.python_scripts = self.python_scripts_tab()
        self.matchbox = self.matchbox_tab()
        self.batch_setups = self.batch_setups_tab()
        self.archives = self.archives_tab()

        #------------------------------------#

        # Window Layout

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setMargin(15)

        self.vbox.addLayout(self.window.tab1.layout)
        self.vbox.addLayout(self.window.tab3.layout)
        self.vbox.addLayout(self.window.tab4.layout)
        self.vbox.addLayout(self.window.tab5.layout)

        self.window.setLayout(self.vbox)

        self.window.show()

        return self.window

    def python_scripts_tab(self):

        def login_check():

            if self.username and self.password:
                submit_script()
            else:
                submit_ftp_login()

        def submit_ftp_login():

            def check_password():

                def save_config():

                    # Save path to config file

                    xml_tree = ET.parse(self.config_xml)
                    root = xml_tree.getroot()

                    username = root.find('.//username')
                    username.text = self.username

                    password = root.find('.//password')
                    password.text = self.password

                    xml_tree.write(self.config_xml)

                    print ('>>> config saved <<<\n')

                if not self.username or not self.password:

                    # Try connecting to ftp

                    self.username = str(username_lineedit.text())
                    self.password = str(password_lineedit.text())

                    if self.username and self.password:
                        try:
                            ftp = FTP('logik.hostedftp.com')
                            ftp.login(self.username, self.password)
                            ftp.cwd('/')
                            save_config()
                            # self.upload_user = self.username
                            # self.upload_pass = self.password
                            submit_script()
                            self.password_window.close()
                        except:
                            self.username = ''
                            self.password = ''
                            return message_box('login incorrect')
                    else:
                        self.username = ''
                        self.password = ''
                        return message_box('Enter username and password')

                else:
                    submit_script()

            self.password_window = QtWidgets.QWidget()
            self.password_window.setMinimumSize(QtCore.QSize(500, 130))
            self.password_window.setMaximumSize(QtCore.QSize(500, 130))
            self.password_window.setWindowTitle('Submit Python Script Login %s' % VERSION)
            self.password_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.password_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.password_window.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.password_window.setStyleSheet('background-color: #272727')

            username_label = FlameLabel('Username', 'normal', self.password_window)
            username_label.setMaximumSize(110, 28)

            password_label = FlameLabel('Password', 'normal', self.password_window)
            password_label.setMaximumSize(110, 28)


            username_lineedit = FlameLineEdit('', self.password_window)
            username_lineedit.setMaximumWidth(60)
            password_lineedit = FlameLineEdit('', self.password_window)
            password_lineedit.setMaximumWidth(60)

            password_lineedit.setEchoMode(QtWidgets.QLineEdit.Password)

            cancel_btn = FlameButton('Cancel', self.password_window.close, self.password_window)
            login_btn = FlameButton('Login', check_password, self.password_window)

            layout = QtWidgets.QGridLayout(self.password_window)

            layout.addWidget(username_label, 0, 0)
            layout.addWidget(username_lineedit, 0, 1, 1, 2)
            layout.addWidget(password_label, 1, 0)
            layout.addWidget(password_lineedit, 1, 1, 1, 2)


            layout.addWidget(cancel_btn, 2, 0)
            layout.addWidget(login_btn, 2, 1)

            self.password_window.show()

            return self.password_window

        def submit_script():

            def upload_script():

                def upload():

                    def save_config():

                        # Save path to config file

                        xml_tree = ET.parse(self.config_xml)
                        root = xml_tree.getroot()

                        script_submit_path = root.find('.//script_submit_path')
                        script_submit_path.text = self.submit_script_path_lineedit.text()

                        xml_tree.write(self.config_xml)

                        print ('>>> config saved <<<\n')

                    def create_script_xml(self):

                        description_text = self.submit_script_description_text_edit.toPlainText()
                        description_text = description_text.replace("'", "\"")
                        description_text = description_text.replace('&', '-')

                        # Create batch info file

                        text = []

                        text.insert(0, "    <script name='%s'>" % self.submit_script_name_label_02.text())
                        text.insert(1, "        <script_version>'%s'</script_version>" % self.submit_script_version_lineedit.text())
                        text.insert(2, "        <flame_version>'%s'</flame_version>" % self.submit_script_flame_version_lineedit.text())
                        text.insert(3, "        <date>'%s'</date>" % self.submit_script_date_lineedit.text())
                        text.insert(4, "        <developer>'%s'</developer>" % self.submit_script_dev_name_lineedit.text())
                        text.insert(5, "        <description>'%s'</description>" % description_text)
                        text.insert(6, '    </script>')

                        out_file = open(script_xml_path, 'w')
                        for line in text:
                            print(line, file=out_file)
                        out_file.close()

                        print ('>>> script xml created <<<\n')

                    def create_tar():

                        if self.all_files_btn.isChecked():
                            print ('button checked')

                            tar_file_list = ''

                            for x in os.listdir(script_folder):
                                if not x.startswith('.'):
                                    tar_file_list = tar_file_list + ' ' + x
                            tar_file_list.strip()
                            print ('tar_file_list:', tar_file_list)
                            tar_command = 'tar -cvf %s  %s' % (script_tar_path, tar_file_list)
                            print ('tar_command:', tar_command)
                        else:
                            print ('button not checked')
                            tar_command = 'tar -cvf %s  %s' % (script_tar_path, script_name + '.py')
                            print ('tar_command:', tar_command)

                        os.chdir(script_folder)
                        os.system(tar_command)

                        print ('\n>>> batch tar file created <<<\n')

                    def upload_files():

                        # Connect to ftp

                        ftp = FTP('logik.hostedftp.com')
                        ftp.login(self.username, self.password)
                        ftp.cwd('/Submit_Scripts')

                        print ('\n>>> connected to portal <<<\n')

                        # Upload script tgz

                        print ('\nuploading...\n')

                        script_ftp_path = os.path.join('/Submit_Scripts', script_name) + '.tgz'
                        print ('script_ftp_path:', script_ftp_path)

                        with open(script_tar_path, 'rb') as ftpup:
                            ftp.storbinary('STOR ' + script_ftp_path, ftpup)

                        # Upload script xml

                        script_xml_ftp_path = os.path.join('/Submit_Scripts', script_name) + '.xml'
                        print ('script_xml_ftp_path:', script_xml_ftp_path)

                        with open(script_xml_path, 'rb') as ftpup:
                            ftp.storbinary('STOR ' + script_xml_ftp_path, ftpup)

                        print ('\n>>> upload done <<<\n')

                        # Close window

                        self.submit_script_window.close()

                        # Close ftp connection

                        ftp.quit()

                        return message_box('<center>Python script uploaded!<br>It will be added to the portal shortly</center>')

                    # Upload script and xml to ftp

                    script_xml_path = os.path.join(self.temp_folder, '%s.xml' % self.submit_script_path_lineedit.text().rsplit('/', 1)[1][:-3])
                    # print ('script_xml_path:', script_xml_path)

                    save_config()

                    create_script_xml(self)

                    script_name = self.submit_script_path_lineedit.text().rsplit('/', 1)[1][:-3]
                    script_path = self.submit_script_path_lineedit.text()
                    script_folder = script_path.rsplit('/', 1)[0]

                    script_tar_path = os.path.join(self.temp_folder, script_name) + '.tgz'
                    # print ('script_tar_path:', script_tar_path)

                    create_tar()

                    upload_files()

                    self.config()

                # Check script path field

                if not os.path.isfile(self.submit_script_path_lineedit.text()):
                    return message_box('Enter path to python script')

                # Check script version field

                elif not self.submit_script_version_lineedit.text():
                    return message_box('Enter script version')

                # Check script version field for alpha characters

                alpha = [n for n in self.submit_script_version_lineedit.text() if n.isalpha()]
                if alpha:
                    return message_box('Script Version should be numbers only. Such as: 1.0')

                decimal = str(self.submit_script_version_lineedit.text()).count('.')
                if decimal > 1:
                    return message_box('Script Version should not have more than one decimal')

                # Check flame version field

                if not self.submit_script_flame_version_lineedit.text():
                    return message_box('Enter minimum version of Flame needed to run script')

                # Check flame version field for alpha characters

                alpha = [n for n in self.submit_script_version_lineedit.text() if n.isalpha()]
                if alpha:
                    return message_box('Flame Version should be numbers only. Such as: 2021.2')

                # Check script date field

                if not self.submit_script_date_lineedit.text():
                    return message_box('Enter date script was written or updated. Whichever is later.')

                # Check date field for proper formatting

                if not re.search('^\\d{2}.\\d{2}.\\d{2}',self.submit_script_date_lineedit.text()):
                    return message_box('Script date should be entered in dd.mm.yy format')

                if not len(self.submit_script_date_lineedit.text()) == 8:
                    return message_box('Script date should be entered in dd.mm.yy format')

                # Check script dev field

                if not self.submit_script_dev_name_lineedit.text():
                    return message_box('Enter name of person who wrote the script')

                # Check script description field

                elif not self.submit_script_description_text_edit.toPlainText():
                    return message_box('Enter description of script and any notes on working with script')

                elif self.submit_script_name_label_02.text() in self.ftp_script_list:

                    overwrite = message_box_confirm('Script already exists on Logik Portal. Overwrite?')
                    if overwrite:
                        upload()
                else:
                    upload()

            def python_script_browse():

                script_path = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Select Python File', self.submit_script_path_lineedit.text(), 'Python Files (*.py)')[0]

                if os.path.isfile(script_path):
                    self.submit_script_path_lineedit.setText(script_path)

                    # Clear submit fields

                    self.submit_script_version_lineedit.setText('')
                    self.submit_script_flame_version_lineedit.setText('')
                    self.submit_script_date_lineedit.setText('')
                    self.submit_script_dev_name_lineedit.setText('')
                    self.submit_script_description_text_edit.setPlainText('')

                    self.get_script_info()

            self.submit_script_window = QtWidgets.QWidget()
            self.submit_script_window.setMinimumSize(QtCore.QSize(800, 500))
            self.submit_script_window.setMaximumSize(QtCore.QSize(800, 500))
            self.submit_script_window.setWindowTitle('Logik Portal Submit')
            self.submit_script_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.submit_script_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.submit_script_window.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.submit_script_window.setStyleSheet('background-color: #272727')

            # Center window in linux

            resolution = QtWidgets.QDesktopWidget().screenGeometry()
            self.submit_script_window.move((resolution.width() / 2) - (self.submit_script_window.frameSize().width() / 2),
                                           (resolution.height() / 2) - (self.submit_script_window.frameSize().height() / 2))

            # Labels

            self.submit_script_label = FlameLabel('Logik Portal Python Script Submit', 'background', self.window.tab1)
            self.submit_script_path_label = FlameLabel('Script Path', 'normal', self.window.tab1)
            self.submit_script_name_label_01 = FlameLabel('Script Name', 'normal', self.window.tab1)
            self.submit_script_name_label_02 = FlameLabel('', 'outline', self.window.tab1)
            self.submit_script_version_label_01 = FlameLabel('Script Version', 'normal', self.window.tab1)
            self.submit_script_flame_version_label_01 = FlameLabel('Flame Version', 'normal', self.window.tab1)
            self.submit_script_date_label_01 = FlameLabel('Date', 'normal', self.window.tab1)
            self.submit_script_dev_name_label_01 = FlameLabel('Developer Name', 'normal', self.window.tab1)
            self.submit_script_description_label = FlameLabel('Script Description', 'normal', self.window.tab1)

            # LineEdits

            self.submit_script_path_lineedit = FlameClickableLineEdit(self.script_submit_path, self.submit_script_window)
            self.submit_script_path_lineedit.clicked.connect(python_script_browse)

            self.submit_script_version_lineedit = FlameLineEdit('', self.submit_script_window)
            self.submit_script_flame_version_lineedit = FlameLineEdit('', self.submit_script_window)
            self.submit_script_date_lineedit = FlameLineEdit('', self.submit_script_window)
            self.submit_script_dev_name_lineedit = FlameLineEdit('', self.submit_script_window)

            # Text Edit

            self.submit_script_description_text_edit = FlameTextEdit(self.file_description, False, self.submit_script_window)

            # Push Buttons

            self.all_files_btn = FlamePushButton(' All Files', False, self.submit_script_window)

            # Buttons

            self.submit_script_upload_btn = FlameButton('Upload', upload_script, self.submit_script_window)
            self.submit_script_cancel_btn = FlameButton('Cancel', self.submit_script_window.close, self.submit_script_window)

            #------------------------------------#

            #  Window grid layout

            gridlayout = QtWidgets.QGridLayout()
            gridlayout.setMargin(30)
            gridlayout.setVerticalSpacing(5)
            gridlayout.setHorizontalSpacing(5)

            gridlayout.addWidget(self.submit_script_label, 0, 0, 1, 6)

            gridlayout.addWidget(self.submit_script_path_label, 1, 0)
            gridlayout.addWidget(self.submit_script_name_label_01, 2, 0)
            gridlayout.addWidget(self.submit_script_version_label_01, 3, 0)
            gridlayout.addWidget(self.submit_script_flame_version_label_01, 4, 0)
            gridlayout.addWidget(self.submit_script_date_label_01, 5, 0)
            gridlayout.addWidget(self.submit_script_dev_name_label_01, 6, 0)
            gridlayout.addWidget(self.submit_script_description_label, 7, 0)

            gridlayout.addWidget(self.submit_script_path_lineedit, 1, 1, 1, 4)
            gridlayout.addWidget(self.submit_script_name_label_02, 2, 1, 1, 4)
            gridlayout.addWidget(self.submit_script_version_lineedit, 3, 1, 1, 4)
            gridlayout.addWidget(self.submit_script_flame_version_lineedit, 4, 1, 1, 4)
            gridlayout.addWidget(self.submit_script_date_lineedit, 5, 1, 1, 4)
            gridlayout.addWidget(self.submit_script_dev_name_lineedit, 6, 1, 1, 4)
            gridlayout.addWidget(self.submit_script_description_text_edit, 7, 1, 6, 4)

            gridlayout.addWidget(self.all_files_btn, 1, 5)
            gridlayout.addWidget(self.submit_script_upload_btn, 11, 5)
            gridlayout.addWidget(self.submit_script_cancel_btn, 12, 5)

            self.submit_script_window.setLayout(gridlayout)

            self.submit_script_window.show()

            if self.submit_script_path_lineedit.text().endswith('.py'):
                if os.path.isfile(self.submit_script_path_lineedit.text()):
                    self.update_script_info()

        def install_local_script():
            import flame

            script_path = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Select Python File', '/', 'Python Files (*.py)')[0]

            if os.path.isfile(script_path):
                script_name = script_path.rsplit('/', 1)[1][:-3]
                install_script = message_box_confirm('Install: %s ?' % script_name)
                if install_script:

                    dest_folder = os.path.join(self.shared_script_path, script_name)

                    if os.path.isdir(dest_folder):
                        overwrite_script = message_box_confirm('Script already exists. Overwrite?')

                        if not overwrite_script:
                            print ('>>> script not installed <<<\n')
                            return
                        else:
                            shutil.rmtree(dest_folder)

                    # Create local folder for script

                    try:
                        os.makedirs(dest_folder)
                    except:
                        pass

                    # Copy script to dest folder

                    shutil.copy(script_path, dest_folder)

                    # Refresh installed scripts tree list

                    self.get_installed_scripts(self.installed_scripts_tree, self.shared_script_path)

                    # Refresh python hooks

                    flame.execute_shortcut('Rescan Python Hooks')
                    print ('>>> python hooks refreshed <<<\n')

                    if os.path.isfile(os.path.join(dest_folder, script_name + '.py')):
                        return message_box('%s script installed' % script_name.replace('_', ' '))
                    return message_box('script install failed')

        # Tab 1

        # Labels

        self.installed_scripts_label = FlameLabel('Installed Scripts', 'background', self.window.tab1)
        self.portal_scripts_label = FlameLabel('Portal Scripts', 'background', self.window.tab1)
        self.script_description_label = FlameLabel('Script Description', 'background', self.window.tab1)

        # Logos

        self.logik_logo_label = QtWidgets.QLabel(self.window.tab1)
        self.logo_label_pixmap = QtGui.QPixmap(os.path.join(SCRIPT_PATH, 'logik_logo.png'))
        self.logik_logo_label.setPixmap(self.logo_label_pixmap)

        # Text Edit

        self.script_description_text_edit = FlameTextEdit(self.file_description, True, self.window.tab1)

        # Installed Scripts TreeWidget

        installed_tree_headers = ['Name', 'Version', 'Flame', 'Date', 'Developer', 'Path']
        self.installed_scripts_tree = FlameTreeWidget(self.installed_script_description, self.script_description_text_edit, installed_tree_headers, self.window.tab1)

        # Available Scripts TreeWidget

        available_tree_headers = ['Name', 'Version', 'Flame', 'Date', 'Developer']
        self.portal_scripts_tree = FlameTreeWidget(self.ftp_script_description, self.script_description_text_edit, available_tree_headers, self.window.tab1)

        # Buttons

        self.script_submit_btn = FlameButton('Submit', login_check, self.window.tab1)
        self.install_script_btn = FlameButton('Install', partial(self.install_script, self.portal_scripts_tree, self.installed_scripts_tree, self.shared_script_path), self.window.tab1)
        self.install_local_script_btn = FlameButton('Install Local', install_local_script, self.window.tab1)
        self.delete_script_btn = FlameButton('Delete', partial(self.delete_script, self.installed_scripts_tree, self.shared_script_path), self.window.tab1)
        self.script_done_btn = FlameButton('Done', self.done, self.window.tab1)

        # Disable script download button if current flame version older than script minimum

        self.portal_scripts_tree.clicked.connect(partial(self.check_script_flame_version, self.portal_scripts_tree))

        # Contextual Menus

        self.action_delete_script = QtWidgets.QAction('Delete Script', self.window.tab1)
        self.action_delete_script.triggered.connect(partial(self.delete_script, self.installed_scripts_tree, self.shared_script_path))
        self.installed_scripts_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.installed_scripts_tree.addAction(self.action_delete_script)

        self.action_install_script = QtWidgets.QAction('Install Script', self.window.tab1)
        self.action_install_script.triggered.connect(partial(self.install_script, self.portal_scripts_tree, self.installed_scripts_tree, self.shared_script_path))
        self.portal_scripts_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.portal_scripts_tree.addAction(self.action_install_script)

        #------------------------------------#

        #  Tab layout

        self.window.tab1.layout = QtWidgets.QGridLayout()
        self.window.tab1.layout.setMargin(30)
        self.window.tab1.layout.setVerticalSpacing(5)
        self.window.tab1.layout.setHorizontalSpacing(5)

        self.window.tab1.layout.addWidget(self.installed_scripts_label, 0, 0, 1, 5)
        self.window.tab1.layout.addWidget(self.portal_scripts_label, 0, 7, 1, 5)

        self.window.tab1.layout.addWidget(self.installed_scripts_tree, 1, 0, 1, 5)
        self.window.tab1.layout.addWidget(self.portal_scripts_tree, 1, 7, 1, 5)

        self.window.tab1.layout.addWidget(self.delete_script_btn, 2, 3)
        self.window.tab1.layout.addWidget(self.install_local_script_btn, 2, 4)

        self.window.tab1.layout.addWidget(self.script_submit_btn, 2, 10)
        self.window.tab1.layout.addWidget(self.install_script_btn, 2, 11)

        self.window.tab1.layout.addWidget(self.script_description_label, 4, 0, 1, 12)
        self.window.tab1.layout.addWidget(self.script_description_text_edit, 5, 0, 1, 12)

        self.window.tab1.layout.addWidget(self.logik_logo_label, 6, 0)
        self.window.tab1.layout.addWidget(self.script_done_btn, 6, 11)

        self.window.tab1.setLayout(self.window.tab1.layout)

    def matchbox_tab(self):

        def matchbox_browse_dir():

            file_browser = QtWidgets.QFileDialog()
            file_browser.setDirectory(self.matchbox_path_lineedit.text())
            file_browser.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            if file_browser.exec_():
                self.matchbox_path_lineedit.setText(str(file_browser.selectedFiles()[0]))

        def download_logik():

            def save_config():

                # Save path to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                matchbox_path = root.find('.//matchbox_path')
                matchbox_path.text = self.matchbox_install_path

                xml_tree.write(self.config_xml)

                print ('\n>>> config saved <<<\n')

            def get_system_password():

                def ok():
                    from subprocess import Popen, PIPE

                    temp_folder = '/opt/Autodesk/password_test_folder'

                    self.sudo_password = self.password_lineedit.text()

                    p = Popen(['sudo', '-S', 'mkdir', temp_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                    p.communicate(self.sudo_password + '\n')[1]

                    if os.path.isdir(temp_folder):

                        # Remove temp folder

                        p = Popen(['sudo', '-S', 'rmdir', temp_folder], stdin=PIPE, stderr=PIPE, universal_newlines=True)
                        p.communicate(self.sudo_password + '\n')[1]

                        self.password_window.close()

                        download()
                    else:
                        message_box('System Password Incorrect')
                        return

                def cancel():
                    self.password_window.close()

                self.password_window = QtWidgets.QWidget()
                self.password_window.setMinimumSize(QtCore.QSize(400, 120))
                self.password_window.setMaximumSize(QtCore.QSize(400, 120))
                self.password_window.setWindowTitle('Enter System Password')
                self.password_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                self.password_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                self.password_window.setFocusPolicy(QtCore.Qt.StrongFocus)
                self.password_window.setStyleSheet('background-color: #272727')
                self.password_window.setWindowModality(QtCore.Qt.WindowModal)

                # Center window in linux

                resolution = QtWidgets.QDesktopWidget().screenGeometry()
                self.password_window.move((resolution.width() / 2) - (self.password_window.frameSize().width() / 2),
                                          (resolution.height() / 2) - (self.password_window.frameSize().height() / 2))

                #  Labels

                self.password_label = FlameLabel('System Password', 'normal', self.password_window)
                self.password_label.setMinimumWidth(125)
                self.password_label.setMaximumWidth(125)

                # LineEdits

                self.password_lineedit = FlameLineEdit('', self.password_window)
                self.password_lineedit.setEchoMode(QtWidgets.QLineEdit.Password)
                self.password_lineedit.setMinimumWidth(150)

                self.password_lineedit.setMaximumWidth(150)

                #  Buttons

                self.password_ok_btn = FlameButton('Ok', ok, self.password_window)
                self.password_cancel_btn = FlameButton('Cancel', cancel, self.password_window)

                #------------------------------------#

                #  Window Layout

                hbox = QtWidgets.QHBoxLayout()

                hbox.addWidget(self.password_cancel_btn)
                hbox.addWidget(self.password_ok_btn)


                hbox2 = QtWidgets.QHBoxLayout()

                hbox2.addWidget(self.password_label)
                hbox2.addWidget(self.password_lineedit)

                vbox = QtWidgets.QVBoxLayout()
                vbox.addLayout(hbox2)
                vbox.addLayout(hbox)

                self.password_window.setLayout(vbox)

                self.password_window.show()

                message_box('<center>Folder is write protected.<br>Enter system password to continue.')

            def download():

                def matchbox_file_write(data):

                    matchbox_file.write(data)
                    self.matchbox_downloaded += len(data)
                    # print (self.matchbox_downloaded)

                # Change cursor to busy

                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)

                # Set download path

                tar_path = '/opt/Autodesk/shared/python/logik_portal/MatchboxShaderCollection.tgz'

                # Try to download from logik matchbox website. If site is down, download from portal ftp

                try:

                    print ('downloading Logik Matchboxes from logik-matchbook.org...\n')

                    # Download matchbox archive from logik matchbox website

                    urllib.request.urlretrieve('https://logik-matchbook.org/MatchboxShaderCollection.tgz', tar_path)

                except:

                    print ('>>> Unable to download from website... downloading from logik portal ftp')

                    # Download matchbox archive from ftp

                    self.ftp_download_connect()

                    ftp_file_size = self.ftp.size('/Logik_Matchbox/MatchboxShaderCollection.tgz')

                    matchbox_file = open(tar_path, 'wb')

                    self.ftp.retrbinary('RETR ' + '/Logik_Matchbox/MatchboxShaderCollection.tgz', matchbox_file_write)

                # Untar matchbox archive

                command = 'tar -xvpzf /opt/Autodesk/shared/python/logik_portal/MatchboxShaderCollection.tgz --strip-components 1 -C %s' % self.matchbox_install_path
                command = command.split(' ', 6)

                if not self.folder_write_permission:

                    # Sudo untar

                    p = Popen(['sudo', '-S'] + command, stdin=PIPE, stderr=PIPE, universal_newlines=True)
                    p.communicate(self.sudo_password + '\n')[1]

                else:

                    # Normal untar

                    Popen(command, stdin=PIPE, stderr=PIPE, universal_newlines=True)

                time.sleep(5)

                QtWidgets.QApplication.restoreOverrideCursor()

                if os.listdir(self.matchbox_install_path) != []:
                    os.remove(tar_path)
                    message_box('Logik Matchboxes installed')
                else:
                    message_box('Install Failed')

            self.matchbox_install_path = self.matchbox_path_lineedit.text()

            if not os.path.isdir(self.matchbox_install_path):
                message_box('Select valid install path')
                return

            save_config()

            self.folder_write_permission = os.access(self.matchbox_install_path, os.W_OK)
            # print ('folder write permission:', self.folder_write_permission)

            if not self.folder_write_permission:
                get_system_password()
            else:
                download()

        # Tab 3

        # Labels

        self.matchbox_install_logik_label = FlameLabel('Install Logik Matchboxes', 'background', self.window.tab3)
        self.matchbox_install_label = FlameLabel('Install Path', 'normal', self.window.tab3)

        # Logos

        self.logik_logo_label = QtWidgets.QLabel(self.window.tab3)
        self.logik_logo_label_pixmap = QtGui.QPixmap(os.path.join(SCRIPT_PATH, 'logik_logo.png'))
        self.logik_logo_label.setPixmap(self.logo_label_pixmap)

        self.croc_logo_label = QtWidgets.QLabel(self.window.tab3)
        self.croc_logo_label_pixmap = QtGui.QPixmap(os.path.join(SCRIPT_PATH, 'croc_logo.png'))
        self.croc_logo_label.setPixmap(self.croc_logo_label_pixmap)
        self.croc_logo_label.setAlignment(QtCore.Qt.AlignCenter)

        # LineEdits

        self.matchbox_path_lineedit = FlameClickableLineEdit(self.matchbox_path, self.window.tab3)
        self.matchbox_path_lineedit.clicked.connect(matchbox_browse_dir)

        # Buttons

        self.matchbox_download_btn = FlameButton('Download', download_logik, self.window.tab3)
        self.matchbox_done_btn = FlameButton('Done', self.done, self.window.tab3)

        # Layout

        self.window.tab3.layout = QtWidgets.QGridLayout()
        self.window.tab3.layout.setMargin(30)
        self.window.tab3.layout.setVerticalSpacing(5)
        self.window.tab3.layout.setHorizontalSpacing(5)
        self.window.tab3.layout.setColumnStretch(1, 110)

        self.window.tab3.layout.addWidget(self.matchbox_install_logik_label, 0, 0, 1, 5)

        self.window.tab3.layout.addWidget(self.matchbox_install_label, 1, 0)
        self.window.tab3.layout.addWidget(self.matchbox_path_lineedit, 1, 1, 1, 3)
        self.window.tab3.layout.addWidget(self.matchbox_download_btn, 1, 4)

        self.window.tab3.layout.addWidget(self.croc_logo_label, 2, 1)

        self.window.tab3.layout.addWidget(self.logik_logo_label, 4, 0)
        self.window.tab3.layout.addWidget(self.matchbox_done_btn, 4, 4)

        self.window.tab3.setLayout(self.window.tab3.layout)

    def batch_setups_tab(self):

        def batch_setups_download():

            def save_config():

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                batch_setup_download_path = root.find('.//batch_setup_download_path')
                batch_setup_download_path.text = self.batch_setup_download_path
                open_batch = root.find('.//open_batch')
                open_batch.text = str(self.open_batch_btn.isChecked())

                xml_tree.write(self.config_xml)

                print ('>>> config saved <<<\n')

            def open_batch():
                import flame

                # Get batch setup path

                for f in os.listdir(self.batch_setup_download_path):
                    if f.split('.', 1)[0] == batch_name and f.endswith('.batch'):
                        setup_path = os.path.join(self.batch_setup_download_path, f)
                        # print ('setup_path:', setup_path)

                # Create new batch group
                # Names for shelf and schematic reels can be added or deleted here
                # Each reel name must be in quotes and seperated by commas

                schematic_reel_list = ['Plates', 'Elements', 'PreRenders', 'Ref']
                shelf_reel_list = ['Batch Renders']

                self.batch_group = flame.batch.create_batch_group(str(batch_item.text(0)), duration=100, reels=schematic_reel_list, shelf_reels=shelf_reel_list)

                # Load batch setup

                self.batch_group.load_setup(setup_path)

                print ('>>> batch setup loaded <<<\n')

            def batch_browse():

                file_browser = QtWidgets.QFileDialog()
                file_browser.setDirectory(self.batch_setup_download_path)
                file_browser.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
                if file_browser.exec_():
                    return str(file_browser.selectedFiles()[0])

            self.batch_setup_download_path = batch_browse()
            # print ('batch_setup_download_path:', self.batch_setup_download_path)

            if self.batch_setup_download_path:

                save_config()

                # Read description from script

                selected_batch = self.batch_setups_tree.selectedItems()
                batch_item = selected_batch[0]
                batch_name = batch_item.text(0)
                # print ('batch_name:', batch_name)

                # Check path to see if batch already exists

                batch_exists = [b for b in os.listdir(self.batch_setup_download_path) if b.split('.', 1)[0] == batch_name]
                # print ('batch_exists:', batch_exists)

                # If batch already exists prompt to overwrite or cancel

                if batch_exists:
                    overwrite_batch = message_box_confirm('Batch Already Exists. Overwrite?')
                    if not overwrite_batch:
                        print ('>>> download cancelled <<<\n')
                        return
                    else:
                        for b in batch_exists:
                            path_to_delete = os.path.join(self.batch_setup_download_path, b)
                            if os.path.isfile(path_to_delete):
                                os.remove(path_to_delete)
                            elif os.path.isdir(path_to_delete):
                                shutil.rmtree(path_to_delete)

                # Connect to ftp

                self.ftp_download_connect()

                # Download dest path

                tgz_path = os.path.join(self.batch_setup_download_path, batch_name + '.tgz')
                # print ('tgz_path:', tgz_path)

                # Download batch tgz file

                self.ftp.retrbinary('RETR ' + os.path.join('/Batch_Setups', batch_item.text(1), batch_name + '.tgz'), open(tgz_path, 'wb').write)

                # Uncompress tgz file

                tgz_escaped_path = tgz_path.replace(' ', '\ ')
                download_escaped_path = self.batch_setup_download_path.replace(' ', '\ ')

                tar_command = 'tar -xvf %s -C %s' % (tgz_escaped_path, download_escaped_path + '/')
                # print ('tar_command:', tar_command)

                os.system(tar_command)

                # Delete tgz file

                os.remove(tgz_path)

                # Disconnect ftp

                self.ftp.quit()

                if self.open_batch_btn.isChecked():
                    open_batch()

                message_box('%s downloaded' % batch_name)

        def submit_batch_setup():

            def batch_setup_browse():

                batch_setup_path = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Select .batch File', self.submit_batch_path_lineedit.text(), 'Batch Files (*.batch)')[0]

                if os.path.isfile(batch_setup_path):
                    self.submit_batch_path_lineedit.setText(batch_setup_path)

                    batch_name = batch_setup_path.rsplit('/', 1)[1][:-6]
                    if batch_name.endswith('.flare'):
                        batch_name = batch_name[:-6]
                    self.submit_batch_name_02_label.setText(batch_name)

            def batch_setup_upload():

                def save_config():

                    # Save path to config file

                    xml_tree = ET.parse(self.config_xml)
                    root = xml_tree.getroot()

                    batch_submit_path = root.find('.//batch_submit_path')
                    batch_submit_path.text = self.submit_batch_path_lineedit.text()

                    xml_tree.write(self.config_xml)

                    print ('>>> config saved <<<\n')

                def compress_batch_setup():

                    # Add batch files to tar file

                    batch_folder_path = self.submit_batch_path_lineedit.text()[:-6]
                    print ('batch_folder_path:', batch_folder_path)

                    batch_root_folder = batch_folder_path.rsplit('/', 1)[0]
                    batch_folder = batch_folder_path.rsplit('/', 1)[1]

                    tar_file_list = batch_folder + ' ' + batch_folder + '.batch'
                    print ('tar_file_list:', tar_file_list)

                    if batch_folder_path.endswith('.flare'):
                        self.tar_file_name = batch_folder_path.rsplit('/', 1)[1][:-6]
                    else:
                        self.tar_file_name = batch_folder_path.rsplit('/', 1)[1]
                    print ('tar_file_name:', self.tar_file_name)

                    self.tar_path = os.path.join(self.temp_folder, self.tar_file_name) + '.tgz'
                    print ('tar_path:', self.tar_path)

                    tar_command = 'tar -cvf %s  %s' % (self.tar_path, tar_file_list)
                    print ('tar_command:', tar_command)

                    os.chdir(batch_root_folder)
                    os.system(tar_command)

                    print ('\n>>> batch tar file created <<<\n')

                def create_batch_xml_file():

                    description_text = self.submit_batch_description_text_edit.toPlainText()
                    description_text = description_text.replace("'", "\"")
                    description_text = description_text.replace('&', '-')

                    # Create batch info file

                    text = []

                    text.insert(0, "    <batch name='%s'>" % self.tar_file_name)
                    text.insert(1, "        <artist>'%s'</artist>" % self.submit_batch_artist_name_lineedit.text())
                    text.insert(2, "        <flame_version>'%s'</flame_version>" % self.submit_batch_flame_version_label2.text())
                    text.insert(3, "        <description>'%s'</description>" % description_text)
                    text.insert(4, '    </batch>')

                    out_file = open(xml_file, 'w')
                    for line in text:
                        print(line, file=out_file)
                    out_file.close()

                def upload_batch():

                    QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)

                    self.ftp_upload_connect()

                    # Check to see if file already exists on ftp

                    ftp_file_list = self.ftp.nlst('/Submit/Batch_Setups')

                    if self.tar_file_name + '.tgz' in ftp_file_list:
                        QtWidgets.QApplication.restoreOverrideCursor()
                        self.ftp.quit()
                        return message_box('Batch setup already exists. Rename and try again.')

                    print ('uploading...\n')

                    # Upload tar to ftp

                    tar_ftp_path = os.path.join('/Submit/Batch_Setups', self.tar_file_name) + '.tgz'

                    with open(self.tar_path, 'rb') as ftpup:
                        self.ftp.storbinary('STOR ' + tar_ftp_path, ftpup)

                    # Delete local tar file

                    os.remove(self.tar_path)

                    # Upload batch xml file

                    batch_xml_ftp_path = os.path.join('/Submit/Batch_Setups', self.tar_file_name) + '.xml'

                    with open(xml_file, 'rb') as ftpup:
                        self.ftp.storbinary('STOR ' + batch_xml_ftp_path, ftpup)

                    QtWidgets.QApplication.restoreOverrideCursor()

                    # Check that both files were uploaded to site

                    ftp_file_list = self.ftp.nlst('/Submit/Batch_Setups')

                    if self.tar_file_name + '.tgz' and self.tar_file_name + '.xml' not in ftp_file_list:
                        QtWidgets.QApplication.restoreOverrideCursor()
                        self.ftp.quit()
                        return message_box('Upload failed. Try again.')

                    print ('>>> upload done <<<\n')

                    os.remove(xml_file)

                    # Close window

                    self.submit_batch_window.close()

                    # Close ftp connection

                    self.ftp.quit()

                    # Confirm file uploaded

                    return message_box('<center>Batch setup uploaded!<br>It will be added to the Logik Portal shortly</center>')

                if not os.path.isfile(self.submit_batch_path_lineedit.text()):
                    return message_box('Enter path to batch setup')
                elif self.submit_batch_artist_name_lineedit.text() == '':
                    return message_box('Enter Artist name')
                elif self.submit_batch_description_text_edit.toPlainText() == '':
                    return message_box('Enter batch setup description')
                else:
                    save_config()
                    compress_batch_setup()
                    xml_file = os.path.join(SCRIPT_PATH, '%s.xml' % self.tar_file_name)
                    create_batch_xml_file()
                    upload_batch()

            flame_version = str(self.flame_version)
            if flame_version.endswith('.0'):
                flame_version = flame_version[:-2]

            self.submit_batch_window = QtWidgets.QWidget()
            self.submit_batch_window.setMinimumSize(QtCore.QSize(800, 400))
            self.submit_batch_window.setMaximumSize(QtCore.QSize(800, 400))
            self.submit_batch_window.setWindowTitle('Logik Portal Batch Setup Submit')
            self.submit_batch_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.submit_batch_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.submit_batch_window.setStyleSheet('background-color: #272727')

            # Center window in linux

            resolution = QtWidgets.QDesktopWidget().screenGeometry()
            self.submit_batch_window.move((resolution.width() / 2) - (self.submit_batch_window.frameSize().width() / 2),
                                          (resolution.height() / 2) - (self.submit_batch_window.frameSize().height() / 2))

            # Labels

            self.submit_batch_label = FlameLabel('Logik Portal Batch Setup Submit', 'background', self.submit_batch_window)
            self.submit_batch_path_label = FlameLabel('Batch Path', 'normal', self.submit_batch_window)
            self.submit_batch_name_01_label = FlameLabel('Batch Name', 'normal', self.submit_batch_window)
            self.submit_batch_name_02_label = FlameLabel('', 'outline', self.submit_batch_window)
            self.submit_batch_flame_version_label = FlameLabel('Flame Version', 'normal', self.submit_batch_window)
            self.submit_batch_flame_version_label2 = FlameLabel(flame_version, 'outline', self.submit_batch_window)
            self.submit_batch_artist_name_label = FlameLabel('Artist Name', 'normal', self.submit_batch_window)
            self.submit_batch_description_label = FlameLabel('Batch Description', 'normal', self.submit_batch_window)

            # LineEdits

            def get_batch_name():

                # Fill in Batch Name field once valid batch path is entered. Must end with .batch
                # If .flare is in file path, remove it

                if self.submit_batch_path_lineedit.text().endswith('.batch'):
                    batch_name = self.submit_batch_path_lineedit.text().rsplit('/', 1)[1][:-6]
                    if batch_name.endswith('.flare'):
                        batch_name = batch_name[:-6]
                    self.submit_batch_name_02_label.setText(batch_name)
                else:
                    self.submit_batch_name_02_label.setText('')

            self.submit_batch_path_lineedit = FlameClickableLineEdit(self.batch_submit_path, self.submit_batch_window)
            self.submit_batch_path_lineedit.clicked.connect(batch_setup_browse)

            self.submit_batch_artist_name_lineedit = FlameLineEdit('', self.submit_batch_window)

            get_batch_name()

            # Text Edit

            self.submit_batch_description_text_edit = FlameTextEdit(self.file_description, False, self.submit_batch_window)

            # Buttons

            self.submit_batch_upload_btn = FlameButton('Upload', batch_setup_upload, self.submit_batch_window)
            self.submit_cancel_btn = FlameButton('Cancel', self.submit_batch_window.close, self.submit_batch_window)

            #------------------------------------#

            #  Window grid layout

            gridlayout = QtWidgets.QGridLayout()
            gridlayout.setMargin(30)
            gridlayout.setVerticalSpacing(5)
            gridlayout.setHorizontalSpacing(5)

            gridlayout.addWidget(self.submit_batch_label, 0, 0, 1, 6)
            gridlayout.addWidget(self.submit_batch_path_label, 1, 0)
            gridlayout.addWidget(self.submit_batch_name_01_label, 2, 0)
            gridlayout.addWidget(self.submit_batch_artist_name_label, 3, 0)
            gridlayout.addWidget(self.submit_batch_flame_version_label, 4, 0)
            gridlayout.addWidget(self.submit_batch_description_label, 5, 0)

            gridlayout.addWidget(self.submit_batch_path_lineedit, 1, 1, 1, 4)
            gridlayout.addWidget(self.submit_batch_name_02_label, 2, 1, 1, 4)
            gridlayout.addWidget(self.submit_batch_artist_name_lineedit, 3, 1, 1, 4)
            gridlayout.addWidget(self.submit_batch_flame_version_label2, 4, 1)
            gridlayout.addWidget(self.submit_batch_description_text_edit, 5, 1, 6, 4)

            gridlayout.addWidget(self.submit_batch_upload_btn, 9, 5)
            gridlayout.addWidget(self.submit_cancel_btn, 10, 5)

            self.submit_batch_window.setLayout(gridlayout)

            self.submit_batch_window.show()

        #  Tab 4

        # Labels

        self.batch_setups_label = FlameLabel('Batch Setups', 'background', self.window.tab4)
        self.batch_setups_desciption_label = FlameLabel('Batch Setup Description', 'background', self.window.tab4)

        # Logo

        self.logik_logo_label = QtWidgets.QLabel(self.window.tab1)
        self.logo_label_pixmap = QtGui.QPixmap(os.path.join(SCRIPT_PATH, 'logik_logo.png'))
        self.logik_logo_label.setPixmap(self.logo_label_pixmap)

        # Text Edit

        self.batch_setups_text_edit = FlameTextEdit(self.file_description, True, self.window.tab4)

        # Batch Setups TreeWidget

        logik_batch_setups_tree_headers = ['Name', 'Flame', 'Artist']
        self.batch_setups_tree = FlameTreeWidget(self.get_batch_description, self.batch_setups_text_edit, logik_batch_setups_tree_headers, self.window.tab4)

        self.batch_setups_tree.setColumnWidth(0, 600)
        self.batch_setups_tree.setColumnWidth(1, 100)
        self.batch_setups_tree.setColumnWidth(2, 300)
        self.batch_setups_tree.setTextElideMode(QtCore.Qt.ElideNone)

        # Disable batch download button if current flame version older than batch minimum

        self.batch_setups_tree.clicked.connect(partial(self.check_batch_flame_version, self.batch_setups_tree))

        # Push Buttons

        self.open_batch_btn = FlamePushButton(' Open Batch', self.open_batch, self.window)
        self.open_batch_btn.setToolTip('Opens batch setup after download is finished')

        # Buttons

        self.batch_setups_submit_btn = FlameButton('Submit', submit_batch_setup, self.window.tab4)
        self.batch_setups_download_btn = FlameButton('Download', batch_setups_download, self.window.tab4)
        self.batch_setups_done_btn = FlameButton('Done', self.done, self.window.tab4)

        # Contextual menu

        self.action_download_batch = QtWidgets.QAction('Download Batch Setup', self.window.tab4)
        self.action_download_batch.triggered.connect(batch_setups_download)
        self.batch_setups_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.batch_setups_tree.addAction(self.action_download_batch)

        #------------------------------------#

        #  Tab layout

        self.window.tab4.layout = QtWidgets.QGridLayout()
        self.window.tab4.layout.setMargin(30)
        self.window.tab4.layout.setVerticalSpacing(5)
        self.window.tab4.layout.setHorizontalSpacing(5)

        self.window.tab4.layout.addWidget(self.batch_setups_label, 0, 0, 1, 5)

        self.window.tab4.layout.addWidget(self.batch_setups_tree, 1, 0, 1, 5)

        self.window.tab4.layout.addWidget(self.batch_setups_submit_btn, 2, 3)
        self.window.tab4.layout.addWidget(self.batch_setups_download_btn, 2, 4)

        self.window.tab4.layout.addWidget(self.open_batch_btn, 2, 0)

        self.window.tab4.layout.addWidget(self.batch_setups_desciption_label, 4, 0, 1, 5)
        self.window.tab4.layout.addWidget(self.batch_setups_text_edit, 5, 0, 1, 5)

        self.window.tab4.layout.addWidget(self.logik_logo_label, 6, 0)
        self.window.tab4.layout.addWidget(self.batch_setups_done_btn, 6, 4)

        self.window.tab4.setLayout(self.window.tab4.layout)

    def archives_tab(self):

        def archive_download():

            def save_config():

                # Save path to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                archive_download_path = root.find('.//archive_download_path')
                archive_download_path.text = self.archive_download_path

                xml_tree.write(self.config_xml)

                print ('>>> config saved <<<\n')

            def browse():

                file_browser = QtWidgets.QFileDialog()
                file_browser.setDirectory(self.archive_download_path)
                file_browser.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
                if file_browser.exec_():
                    return str(file_browser.selectedFiles()[0])

            self.archive_download_path = browse()

            if self.archive_download_path:

                save_config()

                # Read description from script

                selected_archive = self.archives_tree.selectedItems()
                archive_item = selected_archive[0]
                archive_name = archive_item.text(0)
                # print ('archive_name:', archive_name)

                # Check path to see if batch already exists

                archive_exists = [a for a in os.listdir(self.archive_download_path) if a.split('.', 1)[0] == archive_name]
                # print ('archive_exists:', archive_exists)

                # If archive already exists prompt to overwrite or cancel

                if archive_exists:
                    overwrite_archive = message_box_confirm('Archive Already Exists. Overwrite?')
                    if not overwrite_archive:
                        print ('>>> download cancelled <<<\n')
                        return
                    else:
                        for a in archive_exists:
                            path_to_delete = os.path.join(self.archive_download_path, a)
                            if os.path.isfile(path_to_delete):
                                os.remove(path_to_delete)
                            elif os.path.isdir(path_to_delete):
                                shutil.rmtree(path_to_delete)
                        print ('\n')

                # Connect to ftp

                self.ftp_download_connect()

                # Download dest path

                tgz_path = os.path.join(self.archive_download_path, archive_name + '.tgz')
                # print ('tgz_path:', tgz_path)

                # Download archive tgz file

                self.ftp.retrbinary('RETR ' + os.path.join('/Archives', archive_item.text(1), archive_name + '.tgz'), open(tgz_path, 'wb').write)

                # Uncompress tgz file

                tgz_escaped_path = tgz_path.replace(' ', '\ ')
                download_escaped_path = self.archive_download_path.replace(' ', '\ ')

                tar_command = 'tar -xvf %s -C %s' % (tgz_escaped_path, download_escaped_path + '/')
                # print ('tar_command:', tar_command)

                os.system(tar_command)

                # Delete tgz file

                os.remove(tgz_path)

                # Disconnect ftp

                self.ftp.quit()

                # if self.open_archive_btn.isChecked():
                    # open_archive()

                message_box('archive %s downloaded' % archive_name)

        def submit_archive():

            def archive_browse():

                archive_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.submit_archive_window, 'Select Directory', self.submit_archive_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

                # Check selected folder for archive seg file. Give error if not found.

                if os.path.isdir(archive_path):
                    seg_file = [f for f in os.listdir(archive_path) if f.endswith('.seg')]
                    if not seg_file:
                        self.submit_archive_path_lineedit.setText('')
                        self.submit_archive_name_02_label.setText('')
                        return message_box('Archive not found in selected folder')
                    else:
                        self.submit_archive_path_lineedit.setText(archive_path)
                        for f in os.listdir(archive_path):
                            file_ext = os.path.splitext(f)[-1]
                            if '' == file_ext:
                                self.submit_archive_name_02_label.setText(f)

            def archive_upload():

                def save_config():

                    # Save path to config file

                    xml_tree = ET.parse(self.config_xml)
                    root = xml_tree.getroot()

                    archive_submit_path = root.find('.//archive_submit_path')
                    archive_submit_path.text = self.submit_archive_path_lineedit.text()

                    xml_tree.write(self.config_xml)

                    print ('>>> config saved <<<\n')

                def compress_archive():

                    # Add batch files to tar file

                    archive_folder = self.submit_archive_path_lineedit.text()
                    print ('archive_folder:', archive_folder, '\n')

                    self.tar_file_name = self.submit_archive_name_02_label.text()
                    # print ('tar_file_name:', self.tar_file_name)

                    self.tar_path = os.path.join(self.temp_folder, self.tar_file_name) + '.tgz'
                    # print ('tar_path:', self.tar_path)

                    tar_file_list = ''

                    for f in os.listdir(archive_folder):
                        if not f.startswith('.'):
                            tar_file_list = tar_file_list + ' ' + f
                    tar_file_list.strip()
                    # print ('tar_file_list:', tar_file_list)

                    tar_command = 'tar -cvf %s  %s' % (self.tar_path, tar_file_list)
                    # print ('tar_command:', tar_command)

                    os.chdir(archive_folder)
                    os.system(tar_command)

                    print ('>>> archive tar file created <<<\n')

                def create_archive_xml_file():

                    description_text = self.submit_archive_description_text_edit.toPlainText()
                    description_text = description_text.replace("'", "\"")
                    description_text = description_text.replace('&', '-')

                    # Get tar file size. If file is larger than 200mb, give error

                    tar_file_size = os.path.getsize(self.tar_path)

                    if len(str(tar_file_size)) > 6:
                        tar_file_size = int(str(tar_file_size)[:-6])
                        if tar_file_size > 200:
                            return message_box('Archive to large. Reduce size and try again.')
                        else:
                            tar_file_size = str(tar_file_size) + 'mb'
                    else:
                        tar_file_size = '> 1mb'

                    # print ('tar_file_size:', tar_file_size)

                    # Create batch info file

                    text = []

                    text.insert(0, "    <archive name='%s'>" % self.tar_file_name)
                    text.insert(1, "        <flame_version>'%s'</flame_version>" % self.submit_archive_flame_version_label2.text())
                    text.insert(2, "        <file_size>'%s'</file_size>" % tar_file_size)
                    text.insert(3, "        <artist>'%s'</artist>" % self.submit_archive_artist_name_lineedit.text())
                    text.insert(4, "        <description>'%s'</description>" % description_text)
                    text.insert(5, '    </archive>')

                    out_file = open(xml_file, 'w')
                    for line in text:
                        print (line, file=out_file)
                    out_file.close()

                def upload_archive():

                    QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)

                    submit_archive_path = '/Submit/Archives'

                    self.ftp_upload_connect()

                    # Check to see if file already exists on ftp

                    ftp_file_list = self.ftp.nlst(submit_archive_path)

                    if self.tar_file_name + '.tgz' in ftp_file_list:
                        QtWidgets.QApplication.restoreOverrideCursor()
                        self.ftp.quit()
                        return message_box('Archive already exists. Rename and try again.')

                    print ('uploading...\n')

                    # Upload archive tar to ftp

                    tar_ftp_path = os.path.join(submit_archive_path, self.tar_file_name) + '.tgz'

                    with open(self.tar_path, 'rb') as ftpup:
                        self.ftp.storbinary('STOR ' + tar_ftp_path, ftpup)

                    # Delete local tar file

                    os.remove(self.tar_path)

                    # Upload archive xml file

                    archive_xml_ftp_path = os.path.join(submit_archive_path, self.tar_file_name) + '.xml'

                    with open(xml_file, 'rb') as ftpup:
                        self.ftp.storbinary('STOR ' + archive_xml_ftp_path, ftpup)

                    QtWidgets.QApplication.restoreOverrideCursor()

                    # Check that both files were uploaded to site

                    ftp_file_list = self.ftp.nlst(submit_archive_path)

                    if self.tar_file_name + '.tgz' and self.tar_file_name + '.xml' not in ftp_file_list:
                        QtWidgets.QApplication.restoreOverrideCursor()
                        self.ftp.quit()
                        return message_box('Upload failed. Try again.')

                    print ('>>> upload done <<<\n')

                    os.remove(xml_file)

                    # Close window

                    self.submit_archive_window.close()

                    # Close ftp connection

                    self.ftp.quit()

                    # Confirm file uploaded

                    return message_box('<center>Archive uploaded!<br>It will be added to the Logik Portal shortly.</center>')

                if not os.path.isdir(self.submit_archive_path_lineedit.text()):
                    return message_box('Enter path to archive')
                seg_file = [f for f in os.listdir(self.submit_archive_path_lineedit.text()) if f.endswith('.seg')]
                if not seg_file:
                    return message_box('Archive not found in selected folder')
                if self.submit_archive_artist_name_lineedit.text() == '':
                    return message_box('Enter Artist name')
                elif self.submit_archive_description_text_edit.toPlainText() == '':
                    return message_box('Enter archive description')
                else:
                    upload = message_box_confirm('All files in selected folder will be uploaded')

                    if upload:
                        save_config()
                        compress_archive()
                        xml_file = os.path.join(self.temp_folder, '%s.xml' % self.tar_file_name)
                        create_archive_xml_file()
                        upload_archive()

            flame_version = str(self.flame_version)
            if flame_version.endswith('.0'):
                flame_version = flame_version[:-2]

            self.submit_archive_window = QtWidgets.QWidget()
            self.submit_archive_window.setMinimumSize(QtCore.QSize(800, 400))
            self.submit_archive_window.setMaximumSize(QtCore.QSize(800, 400))
            self.submit_archive_window.setWindowTitle('Logik Portal Archive Submit')
            self.submit_archive_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.submit_archive_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.submit_archive_window.setStyleSheet('background-color: #272727')

            # Center window in linux

            resolution = QtWidgets.QDesktopWidget().screenGeometry()
            self.submit_archive_window.move((resolution.width() / 2) - (self.submit_archive_window.frameSize().width() / 2),
                                            (resolution.height() / 2) - (self.submit_archive_window.frameSize().height() / 2))

            # Labels

            self.submit_archive_label = FlameLabel('Logik Portal Archive Submit', 'background', self.submit_archive_window)
            self.submit_archive_path_label = FlameLabel('Archive Path', 'normal', self.submit_archive_window)
            self.submit_archive_name_01_label = FlameLabel('Archive Name', 'normal', self.submit_archive_window)
            self.submit_archive_name_02_label = FlameLabel('', 'outline', self.submit_archive_window)
            self.submit_archive_flame_version_label = FlameLabel('Flame Version', 'normal', self.submit_archive_window)
            self.submit_archive_flame_version_label2 = FlameLabel(flame_version, 'outline', self.submit_archive_window)
            self.submit_archive_artist_name_label = FlameLabel('Artist Name', 'normal', self.submit_archive_window)
            self.submit_archive_description_label = FlameLabel('Archive Description', 'normal', self.submit_archive_window)

            # LineEdits

            def get_archive_name():

                archive_path = self.submit_archive_path_lineedit.text()

                if os.path.isdir(archive_path):
                    seg_file = [f for f in os.listdir(archive_path) if f.endswith('.seg')]
                    if not seg_file:
                        self.submit_archive_path_lineedit.setText('')
                        self.submit_archive_name_02_label.setText('')
                    else:
                        for f in os.listdir(self.submit_archive_path_lineedit.text()):
                            if not f.startswith('.'):
                                file_ext = os.path.splitext(f)[-1]
                                if '' == file_ext:
                                    self.submit_archive_name_02_label.setText(f)
                else:
                    self.submit_archive_path_lineedit.setText('')
                    self.submit_archive_name_02_label.setText('')

            self.submit_archive_path_lineedit = FlameClickableLineEdit(self.archive_submit_path, self.submit_archive_window)
            self.submit_archive_path_lineedit.clicked.connect(archive_browse)

            self.submit_archive_artist_name_lineedit = FlameLineEdit('', self.submit_archive_window)

            get_archive_name()

            # Text Edit

            self.submit_archive_description_text_edit = FlameTextEdit(self.file_description, False, self.submit_archive_window)

            # Buttons

            self.submit_archive_upload_btn = FlameButton('Upload', archive_upload, self.submit_archive_window)
            self.submit_archive_cancel_btn = FlameButton('Cancel', self.submit_archive_window.close, self.submit_archive_window)

            #------------------------------------#

            #  Window grid layout

            gridlayout = QtWidgets.QGridLayout()
            gridlayout.setMargin(30)
            gridlayout.setVerticalSpacing(5)
            gridlayout.setHorizontalSpacing(5)

            gridlayout.addWidget(self.submit_archive_label, 0, 0, 1, 6)
            gridlayout.addWidget(self.submit_archive_path_label, 1, 0)
            gridlayout.addWidget(self.submit_archive_name_01_label, 2, 0)
            gridlayout.addWidget(self.submit_archive_artist_name_label, 3, 0)
            gridlayout.addWidget(self.submit_archive_flame_version_label, 4, 0)
            gridlayout.addWidget(self.submit_archive_description_label, 5, 0)

            gridlayout.addWidget(self.submit_archive_path_lineedit, 1, 1, 1, 4)
            gridlayout.addWidget(self.submit_archive_name_02_label, 2, 1, 1, 4)
            gridlayout.addWidget(self.submit_archive_artist_name_lineedit, 3, 1, 1, 4)
            gridlayout.addWidget(self.submit_archive_flame_version_label2, 4, 1)
            gridlayout.addWidget(self.submit_archive_description_text_edit, 5, 1, 6, 4)

            gridlayout.addWidget(self.submit_archive_upload_btn, 9, 5)
            gridlayout.addWidget(self.submit_archive_cancel_btn, 10, 5)

            self.submit_archive_window.setLayout(gridlayout)

            self.submit_archive_window.show()

        #  Tab 5

        # Labels

        self.archives_label = FlameLabel('Archives', 'background', self.window.tab4)
        self.archives_desciption_label = FlameLabel('Archive Description', 'background', self.window.tab5)

        # Logo

        self.logik_logo_label = QtWidgets.QLabel(self.window.tab1)
        self.logo_label_pixmap = QtGui.QPixmap(os.path.join(SCRIPT_PATH, 'logik_logo.png'))
        self.logik_logo_label.setPixmap(self.logo_label_pixmap)

        # Text Edit

        self.archives_text_edit = FlameTextEdit(self.file_description, True, self.window.tab5)

        # Batch Setups TreeWidget

        archive_tree_headers = ['Name', 'Flame', 'Size', 'Artist']
        self.archives_tree = FlameTreeWidget(self.get_archive_description, self.archives_text_edit, archive_tree_headers, self.window.tab5)

        self.archives_tree.setColumnWidth(0, 600)
        self.archives_tree.setColumnWidth(1, 100)
        self.archives_tree.setColumnWidth(2, 100)
        self.archives_tree.setColumnWidth(3, 300)
        self.archives_tree.setTextElideMode(QtCore.Qt.ElideNone)

        # Disable batch download button if current flame version older than batch minimum

        self.archives_tree.clicked.connect(partial(self.check_archive_flame_version, self.archives_tree))

        # Buttons

        self.archives_submit_btn = FlameButton('Submit', submit_archive, self.window.tab5)
        self.archives_download_btn = FlameButton('Download', archive_download, self.window.tab5)
        self.archives_done_btn = FlameButton('Done', self.done, self.window.tab5)

        # Contextual menu

        self.action_download_archive = QtWidgets.QAction('Download Archive', self.window.tab5)
        self.action_download_archive.triggered.connect(archive_download)
        self.archives_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.archives_tree.addAction(self.action_download_archive)

        #------------------------------------#

        #  Tab layout

        self.window.tab5.layout = QtWidgets.QGridLayout()
        self.window.tab5.layout.setMargin(30)
        self.window.tab5.layout.setVerticalSpacing(5)
        self.window.tab5.layout.setHorizontalSpacing(5)

        self.window.tab5.layout.addWidget(self.archives_label, 0, 0, 1, 5)

        self.window.tab5.layout.addWidget(self.archives_tree, 1, 0, 1, 5)

        self.window.tab5.layout.addWidget(self.archives_submit_btn, 2, 3)
        self.window.tab5.layout.addWidget(self.archives_download_btn, 2, 4)

        self.window.tab5.layout.addWidget(self.archives_desciption_label, 4, 0, 1, 5)
        self.window.tab5.layout.addWidget(self.archives_text_edit, 5, 0, 1, 5)

        self.window.tab5.layout.addWidget(self.logik_logo_label, 6, 0)
        self.window.tab5.layout.addWidget(self.archives_done_btn, 6, 4)

        self.window.tab5.setLayout(self.window.tab5.layout)

    # ----------------------------------------------------------------- #

    def clear_submit_script_ui(self):

        self.script_submit_path = self.submit_script_path_lineedit.text()

        if os.path.isfile(self.script_submit_path):
            self.submit_script_path_lineedit.setText(self.script_submit_path)

            # Clear submit fields

            self.submit_script_version_lineedit.setText('')
            self.submit_script_flame_version_lineedit.setText('')
            self.submit_script_date_lineedit.setText('')
            self.submit_script_dev_name_lineedit.setText('')
            self.submit_script_description_text_edit.setPlainText('')

            self.get_script_info()

    def get_script_info(self):

        # Get script info

        script_path = self.submit_script_path_lineedit.text()
        # print ('script_path:', script_path)

        with open(script_path, 'r') as script:
            script_lines = script.read()

        try:
            file_description = script_lines.split("'''", 1)[1]
            file_description = file_description.split("'''", 1)[0]
            file_description = file_description.strip()
        except:
            file_description = ''
        # print ('file_description:', file_description)

        file_description_lines = file_description.splitlines()

        script_name = self.submit_script_path_lineedit.text().rsplit('/', 1)[1][:-3]
        script_name = script_name.replace('_', ' ')
        self.submit_script_name_label_02.setText(script_name)
        # print ('script_name:', script_name)

        # Fill submit fields if data in present in script

        for line in file_description_lines:
            if 'Script Version: ' in line:
                script_version = line.split('Script Version: ', 1)[1]
                self.submit_script_version_lineedit.setText(script_version)
                # print ('script_version:', script_version)
            elif 'Flame Version: ' in line:
                flame_version = line.split('Flame Version: ', 1)[1]
                self.submit_script_flame_version_lineedit.setText(flame_version)
                # print ('flame_version:', flame_version)
            elif 'Written by: ' in line:
                script_dev = line.split('Written by: ', 1)[1]
                self.submit_script_dev_name_lineedit.setText(script_dev)
                # print ('script_dev:', script_dev)
            elif 'Creation Date: ' in line:
                script_date = line.split('Creation Date: ', 1)[1]
            elif 'Update Date: ' in line:
                script_date = line.split('Update Date: ', 1)[1]
                self.submit_script_date_lineedit.setText(script_date)
                # print ('script_date:', script_date, '\n')

        self.submit_script_description_text_edit.setPlainText(file_description)

    def update_script_info(self):

        # Fill in Script info fields once valid script path is entered. Must end with .py

        if self.submit_script_path_lineedit.text().endswith('.py'):
            self.get_script_info()
        else:
            self.submit_script_name_label_02.setText('')
            self.submit_script_version_label_02.setText('')
            self.submit_script_flame_version_label_02.setText('')
            self.submit_script_date_label_02.setText('')
            self.submit_script_dev_name_label_02.setText('')
            self.submit_script_description_text_edit.setPlainText('')

    def installed_script_description(self, text_edit, tree, tree_index):

        # Read description from script

        selected_script = tree.selectedItems()
        script_item = selected_script[0]
        script_path = script_item.text(5)

        with open(script_path, 'r') as script:
            script_lines = script.read()

        try:
            file_description = script_lines.split("'''", 1)[1]
            file_description = file_description.split("'''", 1)[0]
            file_description = file_description.strip()
        except:
            file_description = ''

        text_edit.setPlainText(file_description)

    def get_installed_scripts(self, tree, scripts_root_path):

        # Clear tree list

        tree.clear()

        # print ('scripts_root_path:', scripts_root_path, flush=True)

        for root, dirs, files in os.walk(scripts_root_path, followlinks=True):
            for script in files:
                if script.endswith('.py'):
                    if not script.startswith('.'):
                        # Get script name from .py file name

                        script_name = script[:-3]
                        script_name = script_name.replace('_', ' ')
                        # print ('script_name:', script_name)

                        script_path = os.path.join(root, script)
                        # print ('script_path:', script_path)

                        # Read in script to separate out comments

                        script_code = open(script_path, 'r')
                        script_lines = script_code.read().splitlines()[1:]
                        script_code.close()

                        # Split out script info to comment list

                        comment_lines = []

                        for line in script_lines:
                            if line != '':
                                comment_lines.append(line)
                            else:
                                break

                        # Get script info from comment list

                        try:
                            script_version = [line.split('Script Version: ', 1)[1] for line in comment_lines if 'Script Version: ' in line]
                            if script_version:
                                script_version = script_version[0]
                            else:
                                script_version = [line.split("'", 2)[1] for line in script_lines if 'VERSION = ' in line] # For old scripts
                                if script_version:
                                    script_version = script_version[0]
                                    if 'v' in script_version:
                                        script_version = script_version[1:]
                                else:
                                    script_version = ''
                        except:
                            script_version = ''
                        # print ('script_version:', script_version)

                        try:
                            script_date = [line.split('Update Date: ', 1)[1] for line in comment_lines if 'Update Date: ' in line]
                            if script_date:
                                script_date = script_date[0]
                            else:
                                script_date = [line.split(' ', 1)[1] for line in comment_lines if 'Updated:' in line] # For old scripts
                                if script_date:
                                    script_date = script_date[0]
                                else:
                                    script_date = ''
                        except:
                            script_date = ''
                        # print ('script_date:', script_date)

                        try:
                            script_dev = [line.split('Written by: ', 1)[1] for line in comment_lines if 'Written by' in line]
                            if script_dev:
                                script_dev = script_dev[0]
                            else:
                                script_dev = [line.split('Created by ', 1)[1] for line in comment_lines if 'Created by' in line] # For old scripts
                                if script_dev:
                                    script_dev = script_dev[0]
                                else:
                                    script_dev = ''
                        except:
                            script_dev = ''
                        # print ('script_dev:', script_dev)

                        try:
                            script_flame_version = [line.split('Flame Version: ', 1)[1] for line in comment_lines if 'Flame Version: ' in line]
                            if script_flame_version:
                                script_flame_version = script_flame_version[0].split(' ', 1)[0]
                            else:
                                script_flame_version = [line.split(' ', 1)[1] for line in comment_lines if 'Flame 20' in line] # For old scripts
                                if script_flame_version:
                                    script_flame_version = script_flame_version[0].split(' ', 1)[0]
                                else:
                                    script_flame_version = ''
                        except:
                            script_version = ''
                        # print ('script_min_flame_version:', script_flame_version)

                        # Add script to tree

                        QtWidgets.QTreeWidgetItem(tree, [script_name, script_version, script_flame_version, script_date, script_dev, script_path])

                        self.installed_script_dict.update({script_name : script_version})

        # Set width of tree headers

        self.installed_scripts_tree.resizeColumnToContents(0)
        self.installed_scripts_tree.resizeColumnToContents(4)
        self.installed_scripts_tree.resizeColumnToContents(5)
        self.installed_scripts_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.installed_scripts_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.installed_scripts_tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        self.installed_scripts_tree.header().setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        self.installed_scripts_tree.header().setSectionResizeMode(4, QtWidgets.QHeaderView.Fixed)
        self.installed_scripts_tree.header().setSectionResizeMode(5, QtWidgets.QHeaderView.Fixed)

        self.installed_scripts_tree.setTextElideMode(QtCore.Qt.ElideNone)

        # Select first item in tree

        tree.setCurrentItem(tree.topLevelItem(0))

    def delete_script(self, tree, root_script_path):
        import shutil

        # Get script path

        selected_script = tree.selectedItems()
        script_item = selected_script[0]
        script_name = script_item.text(0)
        script_name = script_name.replace(' ', '_')
        script_path = script_item.text(5)
        script_folder_name = script_path.rsplit('/', 2)[1]
        script_folder_path = script_path.rsplit('/', 1)[0]

        # print ('script_name:', script_name, flush=True)
        # print ('script_path:', script_path, flush=True)
        # print ('script_folder_name:', script_folder_name, flush=True)
        # print ('script_folder_path:', script_folder_path, flush=True)

        # Confirm deletion

        delete_script = message_box_confirm('Delete: %s ?' % script_name)

        if not delete_script:
            print ('>>> delete cancelled <<<\n')
        else:

            # Remove script
            # If script is in folder with the same name of script, remove the folder

            if script_folder_name == script_name:
                shutil.rmtree(script_folder_path)
            else:
                os.remove(script_path)
                try:
                    os.remove(script_path + 'c')
                except:
                    pass

            print ('>>> DELETED: %s <<<\n' % script_name)

            # Update list of installed scripts

            self.get_installed_scripts(tree, root_script_path)

    def install_script(self, portal_tree, installed_tree, script_path):
        import flame

        print ('>>> downloading script <<<\n')

        self.ftp_download_connect()

        # Get selected script info from selection

        selected_script = portal_tree.selectedItems()
        script_item = selected_script[0]
        script_name = script_item.text(0).strip()
        script_name = script_name.replace(' ', '_')
        script_flame_version = script_item.text(2)

        print ('script_name:', script_name)
        print ('script_flame_version:', script_flame_version)

        # Set source and destination paths

        source_script_path = os.path.join('/Scripts', script_flame_version, script_name) + '.tgz'
        print ('source_script_path: ', source_script_path)

        dest_script_path = os.path.join(script_path, script_name, script_name) + '.tgz'
        print ('dest_script_path: ', dest_script_path)

        dest_folder = dest_script_path.rsplit('/', 1)[0]
        print ('dest_folder:', dest_folder)

        if os.path.isdir(dest_folder):
            overwrite_script = message_box_confirm('Script already exists. Overwrite?')

            if not overwrite_script:
                print ('>>> script not installed <<<\n')
                return
            else:
                shutil.rmtree(dest_folder)

        # Create local folder for script

        try:
            os.makedirs(dest_folder)
        except:
            pass

        # Download script tgz file

        self.ftp.retrbinary('RETR ' + source_script_path, open(dest_script_path, 'wb').write)

        # Uncompress tgz file

        tar_command = 'tar -xvf %s -C %s' % (dest_script_path, dest_folder)
        # print ('tar_command:', tar_command)

        os.system(tar_command)

        # delete tgz file

        os.remove(dest_script_path)

        # Disconnect from ftp

        self.ftp_disconnect()

        # Refresh installed scripts tree list

        self.get_installed_scripts(installed_tree, script_path)

        # Set color of selected script in portal tree to normal color

        script_item.setForeground(0, QtGui.QColor('#9a9a9a'))

        # Refresh python hooks

        flame.execute_shortcut('Rescan Python Hooks')
        print ('>>> python hooks refreshed <<<\n')

        if os.path.isfile(dest_script_path[:-3] + 'py'):
            return message_box('%s script installed' % script_name.replace('_', ' '))
        return message_box('download failed')

    # ----------------------------------------------------------------- #
    # Python Scripts

    def check_script_flame_version(self, tree, tree_index):

        # print ('\n>>> checking script version <<<\n')

        # Get selected script date

        selected_script = tree.selectedItems()
        script_item = selected_script[0]
        script_name = script_item.text(0)
        script_flame_version = script_item.text(2)

        # print ('current_flame_version:', self.flame_version)
        # print ('script_flame_version:', script_flame_version, '\n')
        # print (float(script_flame_version) > float(self.flame_version))

        if float(script_flame_version) > float(self.flame_version):
            print ('>>> %s requires newer version of flame <<<\n' % script_name)
            self.install_script_btn.setEnabled(False)
        else:
            self.install_script_btn.setEnabled(True)

    def ftp_script_description(self, text_edit, tree, tree_index):

        print ('>>> getting script description <<<\n')

        selected_item = self.portal_scripts_tree.selectedItems()
        script = selected_item[0]
        script_name = script.text(0)
        # print ('script_name:', script_name, '\n')

        # Add items from xml to batch list

        xml_tree = ET.parse(self.python_scripts_xml_path)
        root = xml_tree.getroot()

        for script in root.findall('script'):
            if script.get('name') == script_name:
                text_edit.setPlainText(script[-1].text[1:-1])

    def get_ftp_scripts(self, tree):

        print ('>>> downloading python script list <<<\n')

        # Download xml to temp folder

        self.python_scripts_xml_path = os.path.join(self.temp_folder, 'python_scripts.xml')

        self.ftp.retrbinary('RETR ' + '/Scripts/python_scripts.xml', open(self.python_scripts_xml_path, 'wb').write)

        # Add items from xml to scripts tree list

        xml_tree = ET.parse(self.python_scripts_xml_path)
        root = xml_tree.getroot()

        for script in root.findall('script'):
            script_name = str(script.get('name'))
            script_version = str(script[0].text[1:-1])
            flame_version = str(script[1].text[1:-1])
            date = str(script[2].text[1:-1])
            developer_name = str(script[3].text[1:-1])

            #print ('script_name:', script_name)
            #print ('script_version:', script_version)
            #print ('flame_version:', flame_version)
            #print ('date:', date)
            #print ('developer_name:', developer_name, '\n')

            new_script = QtWidgets.QTreeWidgetItem(self.portal_scripts_tree, [script_name, script_version, flame_version, date, developer_name])

            # If newer version of script exists on ftp, highlight script entry

            if script_name in self.installed_script_dict:
                installed_script_version = self.installed_script_dict.get(script_name)
                # print ('installed_script_version:', installed_script_version)
                try:
                    if float(script_version) > float(installed_script_version):
                        new_script.setForeground(0, QtGui.QColor('#ffffff'))
                        new_script.setForeground(1, QtGui.QColor('#ffffff'))
                        new_script.setForeground(2, QtGui.QColor('#ffffff'))
                        new_script.setForeground(3, QtGui.QColor('#ffffff'))
                        new_script.setForeground(4, QtGui.QColor('#ffffff'))
                except:
                    pass

            # if script requires newer version of flame grey out script entry

            if float(self.flame_version) < float(flame_version):
                new_script.setForeground(0, QtGui.QColor('#555555'))
                new_script.setForeground(1, QtGui.QColor('#555555'))
                new_script.setForeground(2, QtGui.QColor('#555555'))
                new_script.setForeground(3, QtGui.QColor('#555555'))
                new_script.setForeground(4, QtGui.QColor('#555555'))

            self.ftp_script_list.append(script_name)

        # print ('install_script_dict:', self.installed_script_dict, '\n')
        # print ('ftp_script_list:', self.ftp_script_list)

        # Select top item in script setup list

        tree.setCurrentItem(tree.topLevelItem(0))

        # Get selected script setup description

        self.ftp_script_description(self.script_description_text_edit, tree, tree)

        # Set width of tree headers

        self.portal_scripts_tree.resizeColumnToContents(0)
        self.portal_scripts_tree.resizeColumnToContents(4)
        self.portal_scripts_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.portal_scripts_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.portal_scripts_tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        self.portal_scripts_tree.header().setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        self.portal_scripts_tree.header().setSectionResizeMode(4, QtWidgets.QHeaderView.Fixed)
        self.portal_scripts_tree.setTextElideMode(QtCore.Qt.ElideNone)

    # ----------------------------------------------------------------- #
    # Batch Setups

    def check_batch_flame_version(self, tree, tree_index):

        print ('>>> checking batch version <<<\n')

        # Get selected script date

        selected_batch = tree.selectedItems()
        batch_item = selected_batch[0]
        batch_name = batch_item.text(0)
        batch_flame_version = batch_item.text(1)

        # print ('current_flame_version:', self.flame_version)
        # print ('batch_flame_version:', batch_flame_version, '\n')

        if float(batch_flame_version) > float(self.flame_version):
            print ('>>> %s requires newer version of flame <<<\n' % batch_name)
            self.batch_setups_download_btn.setEnabled(False)
        else:
            self.batch_setups_download_btn.setEnabled(True)

    def get_batch_description(self, text_edit, tree, tree_index):

        selected_script = tree.selectedItems()
        batch_item = selected_script[0]
        batch_name = batch_item.text(0)
        batch_name = batch_name.replace(' ', '_')

        # Add items from xml to batch list

        xml_tree = ET.parse(self.batch_setups_xml_path)
        root = xml_tree.getroot()

        for batch in root.findall('batch'):
            if batch.get('name') == batch_name:
                text_edit.setPlainText(batch[2].text[1:-1])

    def get_batch_setups(self, tree):

        print ('>>> downloading batch setups list <<<\n')

        # Download xml to temp folder

        self.batch_setups_xml_path = os.path.join(self.temp_folder, 'batch_setups.xml')

        self.ftp.retrbinary('RETR ' + '/Batch_Setups/batch_setups.xml', open(self.batch_setups_xml_path, 'wb').write)

        # Add items from xml to batch list

        xml_tree = ET.parse(self.batch_setups_xml_path)
        root = xml_tree.getroot()

        for batch in root.findall('batch'):
            batch_name = str(batch.get('name'))
            artist_name = str(batch[0].text[1:-1])
            flame_version = str(batch[1].text[1:-1])

            # print ('batch_name:', batch_name)
            # print ('artist_name:', artist_name)
            # print ('flame_version:', flame_version, '\n')

            batch_setup = QtWidgets.QTreeWidgetItem(tree, [batch_name, flame_version, artist_name])

            # if batch setup requires newer version of flame grey out script entry

            if float(self.flame_version) < float(flame_version):
                batch_setup.setForeground(0, QtGui.QColor('#555555'))
                batch_setup.setForeground(1, QtGui.QColor('#555555'))
                batch_setup.setForeground(2, QtGui.QColor('#555555'))

        # Select top item in batch setup list

        tree.setCurrentItem(tree.topLevelItem(0))

        # Get selected batch setup description

        self.get_batch_description(self.batch_setups_text_edit, tree, tree)

    # ----------------------------------------------------------------- #
    # Archives

    def check_archive_flame_version(self, tree, tree_index):

        print ('>>> checking archive version <<<\n')

        # Get selected script date

        selected_archive = tree.selectedItems()
        archive_item = selected_archive[0]
        archive_name = archive_item.text(0)
        archive_flame_version = archive_item.text(1)

        # print ('current_flame_version:', self.flame_version)
        # print ('archive_flame_version:', archive_flame_version, '\n')

        if float(archive_flame_version) > float(self.flame_version):
            print ('>>> %s requires newer version of flame <<<\n' % archive_name)
            self.archives_download_btn.setEnabled(False)
        else:
            self.archives_download_btn.setEnabled(True)

    def get_archive_description(self, text_edit, tree, tree_index):

        selected_archive = tree.selectedItems()
        archive_item = selected_archive[0]
        archive_name = archive_item.text(0)
        archive_name = archive_name.replace(' ', '_')

        # Add items from xml to archive list

        xml_tree = ET.parse(self.archives_xml_path)
        root = xml_tree.getroot()

        for archive in root.findall('archive'):
            if archive.get('name') == archive_name:
                text_edit.setPlainText(archive[3].text[1:-1])

    def get_archives(self, tree):

        print ('>>> downloading archive list <<<\n')

        # Download xml to temp folder

        self.archives_xml_path = os.path.join(self.temp_folder, 'archives.xml')

        self.ftp.retrbinary('RETR ' + '/Archives/archives.xml', open(self.archives_xml_path, 'wb').write)

        # Add items from xml to archive list

        xml_tree = ET.parse(self.archives_xml_path)
        root = xml_tree.getroot()

        for arc in root.findall('archive'):
            archive_name = str(arc.get('name'))
            flame_version = str(arc[0].text[1:-1])
            archive_size = str(arc[1].text[1:-1])
            artist_name = str(arc[2].text[1:-1])

            archive = QtWidgets.QTreeWidgetItem(tree, [archive_name, flame_version, archive_size, artist_name])

            # if archive requires newer version of flame grey out script entry

            if float(self.flame_version) < float(flame_version):
                archive.setForeground(0, QtGui.QColor('#555555'))
                archive.setForeground(1, QtGui.QColor('#555555'))
                archive.setForeground(2, QtGui.QColor('#555555'))
                archive.setForeground(3, QtGui.QColor('#555555'))

        # Select top item in batch setup list

        tree.setCurrentItem(tree.topLevelItem(0))

        # Get selected batch setup description

        self.get_archive_description(self.archives_text_edit, tree, tree)

    # ----------------------------------------------------------------- #

    def done(self):

        self.window.close()

        try:
            self.submit_script_window.close()
        except:
            pass

        try:
            self.submit_batch_window.close()
        except:
            pass

        try:
            self.ftp.quit()
        except:
            pass

        try:
            shutil.rmtree(self.temp_folder)
            print ('>>> clearing temp files <<<\n')
        except:
            pass

        print ('done.\n')

def message_box(message):

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

    code_list = ['<br>', '<dd>', '<center>', '</center>']

    for code in code_list:
        message = message.replace(code, ' ')

    print ('>>> %s <<<\n' % message)

def message_box_confirm(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setText('<center>%s' % message)
    msg_box_yes_button = msg_box.addButton(QtWidgets.QMessageBox.Yes)
    msg_box_yes_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_yes_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box_no_button = msg_box.addButton(QtWidgets.QMessageBox.No)
    msg_box_no_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_no_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14px "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14px "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

    code_list = ['<br>', '<dd>', '<center>', '</center>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('>>> %s <<<\n' % message)

    if msg_box.exec_() == QtWidgets.QMessageBox.Yes:
        return True
    return False

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'Logik',
            'actions': [
                {
                    'name': 'Logik Portal',
                    'execute': LogikPortal,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
