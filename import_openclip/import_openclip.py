'''
Script Name: Import Openclip
Script Version: 2.2
Flame Version: 2020.3
Written by: Michael Vaglienty
Creation Date: 05.26.19
Update Date: 11.02.21

Custom Action Type: Batch

Description:

    Import openclip created by selected write node into Batch/Open clip schematic reel
    or Batch Renders shelf reel

    Image sequence created by write file node can also be auto imported after render is
    completed. Options to turn this on are in Setup.

    Menus:

        Setup:

            Flame Main Menu -> pyFlame -> Import Openclip Setup

        To import openclips:

            Right-click on write file node in batch -> Import... -> Import Openclip to Batch
            Right-click on write file node in batch -> Import... -> Import Openclip to Renders Reel

To install:

    Copy script into /opt/Autodesk/shared/python/import_openclip

Updates:

v2.2 11.02.21

    Write file image sequence can now be automatically be imported when render is completed. Options
    to turn this off and on can be found in Setup.

    Openclip/Image sequence destination reels can be set in Setup.

v2.1 09.24.21

    Added token translation for project nickname

v2.0 05.25.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.5 09.19.20

    Pops up message box when openclip doesn't exist

v1.4 07.01.20

    Open clips can be imported to Batch Renders shelf reel - Batch group must have shelf reel called Batch Renders

    Added token for version name

v1.3 11.01.19

    Right-click menu now appears under Import...

v1.1 09.29.19

    Code cleanup
'''

from __future__ import print_function
from PySide2 import QtWidgets, QtCore
import xml.etree.ElementTree as ET
import os, ast

VERSION = 'v2.2'

SCRIPT_PATH = '/opt/Autodesk/shared/python/import_openclip'

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
        self.setMinimumSize(110, 28)
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
            self.setAlignment(QtCore.Qt.AlignCenter)
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
        self.setMinimumWidth(150)
        self.setMaximumWidth(300)
        # self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                           'QLineEdit:focus {background-color: #474e58}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}'
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
        self.setMinimumSize(150, 28)
        self.setMaximumSize(150, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #424142, stop: .94 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #4f4f4f, stop: .94 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget

    To use:

    button = FlameButton('Button Name', do_when_pressed, window)
    """

    def __init__(self, button_name, do_when_pressed, parent_window, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setMinimumSize(QtCore.QSize(150, 28))
        self.setMaximumSize(QtCore.QSize(150, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(do_when_pressed)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

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

# -------------------------------------------- #

class Import(object):

    def __init__(self, selection, *args, **kwargs):
        import flame

        print ('''
  _____                            _      ____                        _ _
 |_   _|                          | |    / __ \                      | (_)
   | |  _ __ ___  _ __   ___  _ __| |_  | |  | |_ __   ___ _ __   ___| |_ _ __
   | | | '_ ` _ \| '_ \ / _ \| '__| __| | |  | | '_ \ / _ \ '_ \ / __| | | '_ \\
  _| |_| | | | | | |_) | (_) | |  | |_  | |__| | |_) |  __/ | | | (__| | | |_) |
 |_____|_| |_| |_| .__/ \___/|_|   \__|  \____/| .__/ \___|_| |_|\___|_|_| .__/
                 | |                           | |                       | |
                 |_|                           |_|                       |_|
        ''')

        print ('>' * 28, 'import openclip %s' % VERSION, '<' * 29, '\n')

        self.selection = selection

        # Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.batchgroup = flame.batch

        # Load config settings

        self.config()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('import_openclip_settings'):
                self.schematic_reel = setting.find('schematic_reel').text
                self.shelf_reel = setting.find('shelf_reel').text
                self.import_after_render = ast.literal_eval(setting.find('import_after_render').text)
                self.schematic_reel_import = ast.literal_eval(setting.find('schematic_reel_import').text)
                self.shelf_reel_import = ast.literal_eval(setting.find('shelf_reel_import').text)
                self.import_again = ast.literal_eval(setting.find('import_again').text)

            print ('>>> config loaded <<<\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)

            if not os.path.isfile(self.config_xml):
                print ('>>> config file does not exist, creating new config file <<<\n')

                config = """
<settings>
    <import_openclip_settings>
        <schematic_reel>Renders</schematic_reel>
        <shelf_reel>Batch Renders</shelf_reel>
        <import_after_render>True</import_after_render>
        <schematic_reel_import>True</schematic_reel_import>
        <shelf_reel_import>True</shelf_reel_import>
        <import_again>False</import_again>
    </import_openclip_settings>
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

    def translate_write_node_path(self):
        import flame

        # Translate write node tokens

        for self.write_node in self.selection:
            media_path = str(self.write_node.media_path)[1:-1]
            print ('media path:', media_path)
            openclip_path = str(self.write_node.create_clip_path)[1:-1]
            print ('openclip_path:', openclip_path)
            project = str(flame.project.current_project.name)
            project_nickname = str(flame.project.current_project.nickname)
            batch_iteration = str(flame.batch.current_iteration.name)
            batch_name = str(flame.batch.name)[1:-1]
            ext = str(self.write_node.format_extension)[1:-1]
            name = str(self.write_node.name)[1:-1]
            shot_name = str(self.write_node.shot_name)[1:-1]

            token_dict = {'<project>': project,
                          '<project nickname>': project_nickname,
                          '<batch iteration>': batch_iteration,
                          '<batch name>': batch_name,
                          '<ext>': ext,
                          '<name>': name,
                          '<shot name>':shot_name,
                          '<version name>': batch_iteration,}

            for token, value in token_dict.items():
                openclip_path = openclip_path.replace(token, value)
            print ('openclip_path:', openclip_path)

            self.openclip_path = os.path.join(media_path, openclip_path) + '.clip'

    # -------------------------------------------- #

    def setup(self):

        def save_config():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            schematic_reel = root.find('.//schematic_reel')
            schematic_reel.text = self.schematic_reel_lineedit.text()

            shelf_reel = root.find('.//shelf_reel')
            shelf_reel.text = self.shelf_reel_lineedit.text()

            import_after_render = root.find('.//import_after_render')
            import_after_render.text = str(self.import_after_render_push_button.isChecked())

            schematic_reel_import = root.find('.//schematic_reel_import')
            schematic_reel_import.text = str(self.schematic_reel_import_push_button.isChecked())

            shelf_reel_import = root.find('.//shelf_reel_import')
            shelf_reel_import.text = str(self.shelf_reel_import_push_button.isChecked())

            import_again = root.find('.//import_again')
            import_again.text = str(self.import_again_push_button.isChecked())

            xml_tree.write(self.config_xml)

            print ('>>> Config saved <<<\n')

            self.setup_window.close()

            print ('Done.\n')

        self.setup_window = QtWidgets.QWidget()
        self.setup_window.setMinimumSize(QtCore.QSize(1000, 260))
        self.setup_window.setMaximumSize(QtCore.QSize(1000, 260))
        self.setup_window.setWindowTitle('Import Openclip Setup %s' % VERSION)
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                                   (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        # Labels

        self.import_settings_label = FlameLabel('Openclip Destination Reels', 'background', self.setup_window)
        self.auto_import_options_label = FlameLabel('Write File Image Sequence Automatic Import Options', 'background', self.setup_window)
        self.schematic_reel_label = FlameLabel('Schematic Reel Name', 'normal', self.setup_window)
        self.batch_shelf_label = FlameLabel('Batch Shelf Name', 'normal', self.setup_window)
        self.import_dest_label = FlameLabel('Import Destination', 'normal', self.setup_window)
        self.clip_exists_label = FlameLabel('Clip already exists in dest', 'normal', self.setup_window)

        # LineEdit

        self.schematic_reel_lineedit = FlameLineEdit(self.schematic_reel, self.setup_window)
        self.shelf_reel_lineedit = FlameLineEdit(self.shelf_reel, self.setup_window)

        # Push buttons

        def import_toggle():

            if self.import_after_render_push_button.isChecked():
                self.schematic_reel_import_push_button.setEnabled(True)
                self.shelf_reel_import_push_button.setEnabled(True)
                self.import_dest_label.setEnabled(True)
                self.clip_exists_label.setEnabled(True)
                self.import_again_push_button.setEnabled(True)
            else:
                self.schematic_reel_import_push_button.setEnabled(False)
                self.shelf_reel_import_push_button.setEnabled(False)
                self.shelf_reel_import_push_button.setEnabled(False)
                self.import_dest_label.setEnabled(False)
                self.clip_exists_label.setEnabled(False)
                self.import_again_push_button.setEnabled(False)

        self.import_after_render_push_button = FlamePushButton(' Import After Render', self.import_after_render, self.setup_window)
        self.import_after_render_push_button.clicked.connect(import_toggle)

        self.schematic_reel_import_push_button = FlamePushButton(' Schematic Reel', self.schematic_reel_import, self.setup_window)
        self.shelf_reel_import_push_button = FlamePushButton(' Shelf Reel', self.shelf_reel_import, self.setup_window)
        self.import_again_push_button = FlamePushButton(' Import Again', self.import_again, self.setup_window)

        #  Buttons

        self.save_btn = FlameButton('Save', save_config, self.setup_window)
        self.cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window)

        import_toggle()

        # Setup window layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setMargin(20)

        gridbox.setRowMinimumHeight(1, 30)
        gridbox.setRowMinimumHeight(3, 30)
        gridbox.setRowMinimumHeight(6, 30)

        gridbox.setColumnMinimumWidth(3, 25)

        gridbox.addWidget(self.import_settings_label, 0 ,0, 1, 2)

        gridbox.addWidget(self.schematic_reel_label, 1 ,0)
        gridbox.addWidget(self.schematic_reel_lineedit, 1, 1, 1, 1)

        gridbox.addWidget(self.batch_shelf_label, 2 ,0)
        gridbox.addWidget(self.shelf_reel_lineedit, 2 ,1, 1, 2)

        gridbox.addWidget(self.auto_import_options_label, 0 ,4, 1, 3)

        gridbox.addWidget(self.import_after_render_push_button, 1 ,4)
        gridbox.addWidget(self.import_dest_label, 1 ,5)

        gridbox.addWidget(self.schematic_reel_import_push_button, 1 ,6)
        gridbox.addWidget(self.shelf_reel_import_push_button, 2 ,6)

        gridbox.addWidget(self.clip_exists_label, 3 ,5)
        gridbox.addWidget(self.import_again_push_button, 3 ,6)

        gridbox.addWidget(self.save_btn, 12, 6)
        gridbox.addWidget(self.cancel_btn, 13, 6)

        self.setup_window.setLayout(gridbox)

        self.setup_window.show()

        return self.setup_window

    def import_to_schematic_reel(self):

        self.translate_write_node_path()

        if not os.path.isfile(self.openclip_path):
            return message_box('Openclip not found')

        self.create_schematic_reel()

        self.import_schematic_reel()

    def import_to_shelf_reel(self):

        self.translate_write_node_path()

        if not os.path.isfile(self.openclip_path):
            return message_box('Openclip not found')

        self.create_shelf_reel()

        self.import_shelf_reel()

    def post_render_import(self):
        import flame

        if self.import_after_render:

            self.openclip_path = os.path.join(self.selection["exportPath"], self.selection["resolvedPath"])

            openclip_name = self.openclip_path.rsplit('/', 1)[1]
            openclip_name = openclip_name.rsplit('.', 2)[0]

            # Import write file image sequence to schematic/shelf reel if Import After Render is selected in Setup
            # If Import Again is selected, import image sequence
            # If not then check if image sequence is already imported to reel, if not, import

            if self.import_after_render:

                # Import to schematic reel

                if self.schematic_reel_import:
                    self.create_schematic_reel()

                    if self.import_again:
                        self.import_schematic_reel()
                    else:
                        if not [clip for clip in self.schematic_reel_for_import.clips if clip.name == openclip_name]:
                            self.import_schematic_reel()

                # Import to shelf reel

                if self.shelf_reel_import:
                    self.create_shelf_reel()

                    # Import to shelf reel

                    if self.import_again:
                        self.import_shelf_reel()
                    else:
                        if not [clip for clip in self.shelf_reel_for_import.clips if clip.name == openclip_name]:
                            self.import_shelf_reel()

        print ('>>> write file image sequence imported <<<\n')

        print ('done.\n')

    # -------------------------------------------- #

    def create_schematic_reel(self):
        import flame

        # Create Openclip schematic reel if doesn't exist

        if self.schematic_reel not in [reel.name for reel in flame.batch.reels]:
            self.schematic_reel_for_import = flame.batch.create_reel(self.schematic_reel)
        else:
            self.schematic_reel_for_import = [reel for reel in flame.batch.reels if reel.name == self.schematic_reel][0]

    def create_shelf_reel(self):
        import flame

        # Create Batch Renders shelf reel if doesn't exist

        if self.shelf_reel not in [reel.name for reel in flame.batch.shelf_reels]:
            self.shelf_reel_for_import = flame.batch.create_shelf_reel(self.shelf_reel)
        else:
            self.shelf_reel_for_import = import_reel = [reel for reel in flame.batch.shelf_reels if reel.name == self.shelf_reel][0]

    def import_schematic_reel(self):
        import flame

        # Import openclip to schematic reel

        flame.batch.import_clip(self.openclip_path, self.schematic_reel)

    def import_shelf_reel(self):
        import flame

        # Import openclip to shelf reel

        flame.import_clips(self.openclip_path, self.shelf_reel_for_import)

# -------------------------------------------- #

def message_box(message):
    from PySide2 import QtWidgets, QtCore

    msg_box = QtWidgets.QMessageBox()
    msg_box.setText('<center>%s' % message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 24))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; color: #9a9a9a}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
    msg_box.exec_()

    message = message.replace('<br>', '-')

    print ('\n>>> %s <<<\n' % message)

def schematic_import(selection):

    script = Import(selection)
    script.import_to_schematic_reel()

    print ('>>> openclip imported <<<\n')
    print ('done.\n')

def shelf_import(selection):

    script = Import(selection)
    script.import_to_shelf_reel()

    print ('>>> openclip imported <<<\n')
    print ('done.\n')

def setup(selection):

    script = Import(selection)
    script.setup()

# -------------------------------------------- #

def scope_write_node(selection):

    for item in selection:
        if item.type == 'Write File':
            return True
    return False

# -------------------------------------------- #

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Import Openclip Setup',
                    'execute': setup,
                    'minimumVersion': '2020.3'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Import...',
            'actions': [
                {
                    'name': 'Import Openclip to Batch',
                    'isVisible': scope_write_node,
                    'execute': schematic_import,
                    'minimumVersion': '2020.3'
                },
                {
                    'name': 'Import Openclip to Renders Reel',
                    'isVisible': scope_write_node,
                    'execute': shelf_import,
                    'minimumVersion': '2020.3'
                }
            ]
        }
    ]

def batch_export_end(info, userData, *args, **kwargs):

    script = Import(info)
    script.post_render_import()

