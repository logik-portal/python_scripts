'''
Script Name: Uber Save
Script Version: 3.2
Flame Version: 2021
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 07.28.19
Update Date: 10.11.21

Custom Action Type: Batch / Media Panel

Description:

    Save/Save Iterate batch group and batch setup file to custom path in one click

    Run script setup to set batch setup save path:

    Flame Main Menu -> Uber Save Setup

        Custom Root Path:

            The script will always save batch setups into the default project batch folder that is set when creating a project.

            To use an alternate path, click Use Custom Path and select the new path. This path will be used for all projects and should be a root path
            that can then have subfolder defined in the Batch Path entry.

            Example:

                /Jobs/<ProjectNickName>/<ProjectName>

        Batch Path:

            Use this to define the folder structure that batch setups will be saved in. They will be sub folders of the path defined in the Project Root Path.
            This works in a way similar to defining where renders go with the write node.

            Tokens:

                <ProjectName> - Adds name of current Flame project to path
                <ProjectNickName> - Adds Flame project nicknick to path
                <DesktopName> - Adds name of current desktop to path
                <SeqName> - Will try to guess shot seqeunce name from the batch group name - for example: PYT_0100_comp will give a sequence name of PYT
                <SEQNAME> - Will do the same as above but give the sequence name in all caps
                <ShotName> - Will try to guess shot name from the batch group name - for example: PYT_0100_comp will give a shot name of PYT_0100

        Shot Name From:

            Select: Shot Name when naming shots similar to this: PYT_0100, PYT_100, PYT100
            Select: Batch Group Name when shots are named in an episodic format such as: 100_100_100 or PYT_100_100_100

    To use:

    Right-click selected batchgroups in desktop -> Uber Save... -> Save Selected Batchgroups
    Right-click selected batchgroups in desktop -> Uber Save... -> Iterate and Save Selected Batchgroups

    Right-click on desktop in media panel -> Uber Save... -> Save All Batchgroups

    Right-click in batch -> Uber Save... -> Save Current Batchgroup
    Right-click in batch -> Uber Save... -> Iterate and Save Current Batchgroup

To install:

    Copy script into either /opt/Autodesk/shared/python/uber_save

Updates:

v3.2 10.11.21

    Removed JobName token - not needed with new project nick name token

    Removed Desktop Name token

    Shot name token improvements

v3.1 07.10.21

    Fixed problem when trying to save on a flare. Added check for flame and flare batch folders.

    ProjectName token now uses exact flame project name. No longer tries to guess name of project on server. If flame project name is different than server project name, set flame project nickname
    and use ProjectNickName token

    Fixed sequence token when using batch group name as save type

v3.0 06.08.21

    Updated to be compatible with Flame 2022/Python 3.7

    Improvements to shot name detection

    Speed improvements when saving

v2.0 10.08.20:

    Updated UI

    Improved iteration handling

    Added SEQNAME token to add sequence name in caps to path

v1.91 05.13.20:

    Fixed iterating: When previous iterations were not in batchgroup, new itereations would reset to 1.
    Iterations now continue from current iteration number.

v1.9 03.10.20:

    Fixed Setup UI for Linux

v1.7 12.29.19

    Menu now appears as Uber Save in right-click menu
'''

from __future__ import print_function
import os, re, ast
from PySide2 import QtWidgets, QtCore
import xml.etree.ElementTree as ET

VERSION = 'v3.2'

SCRIPT_PATH = '/opt/Autodesk/shared/python/uber_save'

#-------------------------------------#

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget
    Options for normal, label with background color, and label with background color and outline
    """

    def __init__(self, label_name, parent, label_type='normal', *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent)
        self.setMinimumSize(150, 28)
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
            # self.setAlignment(QtCore.Qt.AlignLeft)
            self.setStyleSheet('color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget
    """

    def __init__(self, button_name, connect, parent, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumSize(QtCore.QSize(150, 28))
        self.setMaximumSize(QtCore.QSize(150, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

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
        self.setMinimumWidth(150)
        self.setMaximumWidth(150)
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
        self.setMaximumWidth(150)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #6a6a6a}')

        def token_action_menu():
            from functools import partial

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

#-------------------------------------#

class UberSave(object):

    def __init__(self, selection):
        import flame

        print ('''
                  _    _  _
                 | |  | || |
                 | |  | || |__    ___  _ __
                 | |  | || '_ \  / _ \| '__|
                 | |__| || |_) ||  __/| |
                  \____/ |_.__/  \___||_|
                   _____
                  / ____|
                 | (___    __ _ __   __ ___
                  \___ \  / _` |\ \ / // _ \\
                  ____) || (_| | \ V /|  __/
                 |_____/  \__,_|  \_/  \___|
        ''')

        print ('\n', '>' * 20, ' uber save %s ' % VERSION, '<' * 20, '\n')

        self.selection = selection
        self.iterate = ''
        self.selected_batch = ''
        self.save_path = ''
        self.project_match = ''
        self.job_folder = ''
        self.batch_token_dict = ''

        # Get flame variables

        self.flame_prj_name = flame.project.current_project.project_name
        print ('flame_prj_name:', self.flame_prj_name)

        self.flame_prj_nickname = flame.projects.current_project.nickname
        print ('flame_prj_nickname:', self.flame_prj_nickname)

        self.current_project_path = self.get_current_project_path()
        print ('current_project_path:', self.current_project_path)

        # Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Load config file

        self.config()

        print ('save_custom:', self.use_custom_path)
        print ('custom_path:', self.custom_path)
        print ('batch_path:', self.batch_path)
        print ('shot_name_type:', self.shot_name_type, '\n')

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('uber_save_settings'):
                self.shot_name_type = setting.find('shot_name_type').text
                self.use_custom_path = ast.literal_eval(setting.find('use_custom_path').text)
                self.custom_path = setting.find('custom_path').text
                self.batch_path = setting.find('batch_path').text

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
    <uber_save_settings>
        <shot_name_type>Shot Name</shot_name_type>
        <use_custom_path>False</use_custom_path>
        <custom_path>/</custom_path>
        <batch_path>&lt;ShotName&gt;</batch_path>
    </uber_save_settings>
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

    def get_current_project_path(self):

        # Get default save path from project.db file

        with open('/opt/Autodesk/project/project.db', 'r') as project_db:
            for line in project_db:
                if ':' + self.flame_prj_name + '=' in line:
                    current_project_path = re.search('SetupDir="(.*)",Partition', line)
                    current_project_path = current_project_path.group(1)

                    # If default project is on local drive add autodesk project folder to path

                    if not current_project_path.startswith('/'):
                        current_project_path = os.path.join('/opt/Autodesk/project', current_project_path)
                    return current_project_path

    def translate_path(self):
        import flame

        # If Use Custom button is selected use custom path provided
        # Otherwise use project default batch folder

        flame_batch_folder = os.path.join(self.current_project_path, 'batch/flame')
        flare_batch_folder = os.path.join(self.current_project_path, 'batch/flare')

        if self.use_custom_path:
            self.save_path = os.path.join(self.custom_path, self.batch_path)
        else:
            if os.path.isdir(flame_batch_folder):
                batch_folder = flame_batch_folder
            elif os.path.isdir(flare_batch_folder):
                    batch_folder = flare_batch_folder
            else:
                os.makedirs(flame_batch_folder)
                batch_folder = flame_batch_folder
            print ('batch_folder:', batch_folder)
            self.save_path = os.path.join(batch_folder, self.batch_path)
        print ('save_path:', self.save_path)

        #-------------------------------------#

        batch_name = str(self.selected_batch.name)[1:-1]
        print ('batch_name:', batch_name)

        try:
            if self.shot_name_type == 'Shot Name':
                shot_name_split = re.split(r'(\d+)', batch_name)
                shot_name_split = [s for s in shot_name_split if s != '']
                # print ('shot_name_split:', shot_name_split)

                if len(shot_name_split) > 1:
                    if shot_name_split[1].isalnum():
                        shot_name = shot_name_split[0] + shot_name_split[1]
                    else:
                        shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]
                else:
                    shot_name = batch_name

                # Get sequence name from first split

                seq_name = shot_name_split[0]
                if seq_name.endswith('_'):
                    seq_name = seq_name[:-1]

            else:
                seq_name_split = re.split(r'(\d+)', shot_name)
                seq_name = seq_name_split[0]
                if seq_name.endswith('_'):
                    seq_name = seq_name[:-1]
        except:
            shot_name = batch_name
            seq_name_split = re.split(r'_', shot_name)
            seq_name = seq_name_split[0]
            if seq_name.endswith('_'):
                seq_name = seq_name[:-1]

        print ('shot_name:', shot_name)
        print ('seq_name:', seq_name)

        #-------------------------------------#

        print ('path_to_translate:', self.save_path)

        # Translate tokens in path

        if '<ProjectName>' in self.save_path:
            self.save_path = re.sub('<ProjectName>', self.flame_prj_name, self.save_path)

        if '<ProjectNickName>' in self.save_path:
            self.save_path = re.sub('<ProjectNickName>', self.flame_prj_nickname, self.save_path)

        if '<SeqName>' in self.save_path:
            self.save_path = re.sub('<SeqName>', seq_name, self.save_path)

        if '<SEQNAME>' in self.save_path:
            self.save_path = re.sub('<SEQNAME>', seq_name.upper(), self.save_path)

        if '<ShotName>' in self.save_path:
            self.save_path = re.sub('<ShotName>', shot_name, self.save_path)

        print ('translated save_path:', self.save_path, '\n')

    def save(self):
        import flame

        selected_batch_name = str(self.selected_batch.name)[1:-1]
        print ('selected_batch_name:', selected_batch_name)

        # Open batch if closed

        self.selected_batch.open()

        # Get current iteration
        iteration_split = (re.split(r'(\d+)', str(self.selected_batch.current_iteration.name)[1:-1]))[1:-1]
        # iteration_split = iteration_split[1:-1]
        # iteration_split = filter(None, re.split(r'(\d+)', str(self.selected_batch.current_iteration.name)[1:-1]))
        current_iteration = int(iteration_split[-1])
        print ('current_iteration:', current_iteration)

        # Get latest iteration if iterations are saved
        print ('selected_batch.batch_iterations:', self.selected_batch.batch_iterations)

        if not self.selected_batch.batch_iterations == []:
            print (str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1])
            # print (filter(None, re.split(r'(\d+)', str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1])))
            latest_iteration = int(((re.split(r'(\d+)', str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1]))[1:-1])[-1])

            # latest_iteration = int(filter(None, re.split(r'(\d+)', str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1]))[-1])
        else:
            latest_iteration = current_iteration
        print ('latest_iteration:', latest_iteration)

        # If first save of batch group, create first iteration

        if self.selected_batch.batch_iterations == [] and current_iteration == 1:
            self.iterate = True

        # Iterate up if iterate up menu selected

        print ('iterate:', self.iterate)

        if self.iterate:
            if current_iteration == 1:
                self.selected_batch.iterate()
            elif current_iteration < latest_iteration:
                self.selected_batch.iterate(index = (latest_iteration + 1))
            else:
                self.selected_batch.iterate(index = (current_iteration + 1))
            print ('\n>>> iterating up <<<\n')
        else:
            self.selected_batch.iterate(index=current_iteration)
            print ('\n>>> overwriting existing iteration <<<\n')

        # Get current iteration

        current_iteration = str(self.selected_batch.current_iteration.name)[1:-1]
        current_iteration_no_spaces = current_iteration.replace(' ', '_')
        print ('new current_iteration:', current_iteration)

        # Set batch save path

        shot_save_path = os.path.join(self.save_path, current_iteration)
        print ('shot_save_path:', shot_save_path)

        try:
            # Create shot save folder

            if not os.path.isdir(self.save_path):
                os.makedirs(self.save_path)

            # Hard save current batch iteration

            self.selected_batch.save_setup(shot_save_path)

            # edit_batch()

            print ('\n', '>>> %s uber saved <<<' % selected_batch_name, '\n')

        except:
            message_box('Batch not saved. Check path in setup')

    #-------------------------------------#

    def batchgroup_save_all(self):
        import flame

        self.iterate = False
        batch_groups = flame.project.current_project.current_workspace.desktop.batch_groups

        for self.selected_batch in batch_groups:
            self.translate_path()
            self.save()

        print ('done.\n')

    def batchgroup_save_selected(self):
        import flame

        self.iterate = False

        for self.selected_batch in self.selection:
            self.translate_path()
            self.save()

        print ('done.\n')

    def batchgroup_save_selected_iterate(self):
        import flame

        self.iterate = True

        for self.selected_batch in self.selection:
            self.translate_path()
            self.save()

        print ('done.\n')

    def batchgroup_save(self):
        import flame

        self.iterate = False
        self.selected_batch = flame.batch
        self.translate_path()
        self.save()

        print ('done.\n')

    def batchgroup_save_iterate(self):
        import flame

        self.iterate = True
        self.selected_batch = flame.batch
        self.translate_path()
        self.save()

        print ('done.\n')

    #-------------------------------------#

    def setup(self):

        def custom_path_browse():

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.setup_window, 'Select Directory', self.custom_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.custom_path_lineedit.setText(file_path)

        def save_config():

            if self.custom_path_lineedit.text() == '':
                message_box('Enter Project Root Path')
            elif self.batch_path_lineedit.text() == '':
                message_box('Enter Batch Path')
            else:

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                shot_name_type = root.find('.//shot_name_type')
                shot_name_type.text = self.shot_name_type_push_btn.text()

                use_custom_path = root.find('.//use_custom_path')
                use_custom_path.text = str(self.use_custom_push_btn.isChecked())

                custom_path = root.find('.//custom_path')
                custom_path.text = self.custom_path_lineedit.text()

                batch_path = root.find('.//batch_path')
                batch_path.text = self.batch_path_lineedit.text()

                xml_tree.write(self.config_xml)

                print ('>>> config saved <<<\n')

                self.setup_window.close()

                print ('done.\n')

        self.setup_window = QtWidgets.QWidget()
        self.setup_window.setMinimumSize(QtCore.QSize(1000, 250))
        self.setup_window.setMaximumSize(QtCore.QSize(1000, 250))
        self.setup_window.setWindowTitle('Uber Save Setup %s' % VERSION)
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                               (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        # Labels

        self.custom_path_label = FlameLabel('Custom Root Path', self.setup_window, label_type='normal')
        self.batch_path_label = FlameLabel('Batch Path', self.setup_window, label_type='normal')
        self.shot_name_label = FlameLabel('Shot Name From', self.setup_window, label_type='normal')

        # LineEdits

        self.custom_path_lineedit = FlameLineEdit(self.custom_path, self.setup_window)
        self.batch_path_lineedit = FlameLineEdit(self.batch_path, self.setup_window)

        # Shot Name Type Pushbutton Menu

        shot_name_options = ['Shot Name', 'Batch Group Name']
        self.shot_name_type_push_btn = FlamePushButtonMenu(self.shot_name_type, shot_name_options, self.setup_window)

        # Custom Path Token Pushbutton Menu

        custom_token_dict = {'Project Name': '<ProjectName>', 'Project Nick Name': '<ProjectNickName>'}
        self.custom_token_push_btn = FlameTokenPushButton('Add Token', custom_token_dict, self.custom_path_lineedit, self.setup_window)

        # Batch Path Token Pushbutton Menu

        batch_token_dict = {'Project Name': '<ProjectName>', 'Project Nick Name': '<ProjectNickName>', 'Sequence Name': '<SeqName>',
                            'SEQUENCE NAME': '<SEQNAME>', 'Shot Name': '<ShotName>'} # , 'Episode Number': '<EpisodeNum>'}
        self.batch_token_push_btn = FlameTokenPushButton('Add Token', batch_token_dict, self.batch_path_lineedit, self.setup_window)

        #  Buttons

        self.browse_btn = FlameButton('Browse', custom_path_browse, self.setup_window)
        self.save_btn = FlameButton('Save', save_config, self.setup_window)
        self.cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window)

        # Push Button

        def use_custom_path():
            if self.use_custom_push_btn.isChecked() == True:
                self.custom_path_label.setEnabled(True)
                self.custom_path_lineedit.setEnabled(True)
                self.custom_token_push_btn.setEnabled(True)
                self.browse_btn.setEnabled(True)
            else:
                self.custom_path_label.setEnabled(False)
                self.custom_path_lineedit.setEnabled(False)
                self.custom_token_push_btn.setEnabled(False)
                self.browse_btn.setEnabled(False)

        self.use_custom_push_btn = FlamePushButton(' Use Custom Path', self.use_custom_path, self.setup_window)
        self.use_custom_push_btn.clicked.connect(use_custom_path)
        use_custom_path()

        # Setup window layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setMargin(20)

        gridbox.addWidget(self.use_custom_push_btn, 0, 0)

        gridbox.addWidget(self.custom_path_label, 1 ,0)
        gridbox.addWidget(self.custom_path_lineedit, 1 ,1, 1, 2)
        gridbox.addWidget(self.custom_token_push_btn, 1 ,3)
        gridbox.addWidget(self.browse_btn, 1 ,4)


        gridbox.addWidget(self.batch_path_label, 2 ,0)
        gridbox.addWidget(self.batch_path_lineedit, 2 ,1, 1, 2)
        gridbox.addWidget(self.batch_token_push_btn, 2, 3)

        gridbox.addWidget(self.shot_name_label, 3, 0)
        gridbox.addWidget(self.shot_name_type_push_btn, 3 ,1)

        gridbox.addWidget(self.save_btn, 4, 4)
        gridbox.addWidget(self.cancel_btn, 5, 4)

        self.setup_window.setLayout(gridbox)

        self.setup_window.show()

        return self.setup_window

#-------------------------------------#

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

def uber_save_setup(selection):

    # Opens Uber Save Setup window

    uber_save = UberSave(selection)
    return uber_save.setup()

def uber_batchgroup_save(selection):

    # Saves current batch from batch

    uber_save = UberSave(selection)
    uber_save.batchgroup_save()

def uber_batchgroup_iterate_save(selection):

    # Iterates and saves current batch from batch

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_iterate()

def uber_batchgroup_save_all(selection):

    # Saves all batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_all()

def uber_batchgroup_save_selected(selection):

    # Saves selected batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_selected()

def uber_batchgroup_iterate_save_selected(selection):

    # Saves selected batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_selected_iterate()

# Scopes
#-------------------------------------#

def scope_batch(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyBatch):
            return True
    return False

def scope_desktop(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyDesktop):
            return True
    return False

# Menus
#-------------------------------------#

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Uber Save',
            'actions': [
                {
                    'name': 'Save All Batchgroups',
                    'isVisible': scope_desktop,
                    'execute': uber_batchgroup_save_all,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Save Selected Batchgroups',
                    'isVisible': scope_batch,
                    'execute': uber_batchgroup_save_selected,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Iterate and Save Selected Batchgroups',
                    'isVisible': scope_batch,
                    'execute': uber_batchgroup_iterate_save_selected,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Uber Save',
            'actions': [
                {
                    'name': 'Save Current Batchgroup',
                    'execute': uber_batchgroup_save,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Iterate and Save Current Batchgroup',
                    'execute': uber_batchgroup_iterate_save,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Uber Save Setup',
                    'execute': uber_save_setup,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
