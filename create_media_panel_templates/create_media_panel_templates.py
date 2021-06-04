'''
Script Name: Create Media Panel Templates
Script Version: 3.0
Flame Version: 2021
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 05.01.19
Update Date: 05.23.21

Custom Action Type: Media Panel

Description:

    Create templates from libraries and folders in the Media Panel.
    Right-click menus will be created for each template

    To create new template menus:

    Right-click on library or folder -> Create Template... -> Create Library Template / Create Folder Template

    Newly created templates:

    Right-click on library or folder -> Library/Folder Templates -> Select from saved templates

To install:

    Copy script into /opt/Autodesk/shared/python/create_media_panel_templates
'''

from __future__ import print_function
import os
from PySide2 import QtWidgets, QtCore

SCRIPT_PATH = '/opt/Autodesk/shared/python/create_media_panel_templates'

VERSION = 'v3.0'

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
        self.setMinimumSize(QtCore.QSize(110, 28))
        self.setMaximumSize(QtCore.QSize(110, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(do_when_pressed)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

# ----------------------------------------------- #

class CreateTemplate(object):

    def __init__(self, selection):
        import flame

        print ('\n', '>' * 20, 'create media panel templates %s' % VERSION, '<' * 20, '\n')

        self.selection = selection
        self.creation_type = ''
        self.user_name = flame.users.current_user.name

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.menu_template_path = os.path.join(SCRIPT_PATH, 'menu_template')
        self.menus_folder = os.path.join(SCRIPT_PATH, 'menus')
        self.folder_menus = os.path.join(self.menus_folder, 'folders')
        self.library_menus = os.path.join(self.menus_folder, 'libraries')

        # Set variables

        for item in self.selection:
            if isinstance(item, (flame.PyFolder)):
                self.top_item = 'item.create_folder'
                self.item_name = str(item.name)[1:-1]
                self.creation_type = 'Folder'
                self.menu_name = 'Folder Templates...'
                self.name_window()

        for item in self.selection:
            if isinstance(item, (flame.PyLibrary)):
                self.top_item = 'flame.project.current_project.current_workspace.create_library'
                self.item_name = str(item.name)[1:-1]
                self.creation_type = 'Library'
                self.menu_name = 'Library Templates...'
                self.name_window()

    def name_window(self):

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(400, 140))
        self.window.setMaximumSize(QtCore.QSize(400, 140))
        self.window.setWindowTitle('Create %s Template %s' % (self.creation_type, VERSION))
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #212121')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.name_label = FlameLabel('New Menu Name', 'normal', self.window)

        # Entry

        self.name_entry = FlameLineEdit(self.item_name, self.window)

        # Buttons

        self.create_btn = FlameButton('Create Template', self.check_file_paths, self.window)
        self.cancel_btn = FlameButton('Cancel', self.window.close, self.window)

        #------------------------------------#

        # Window Layout

        self.hbox01 = QtWidgets.QHBoxLayout()
        self.hbox01.addWidget(self.name_label)
        self.hbox01.addWidget(self.name_entry)

        self.hbox02 = QtWidgets.QHBoxLayout()
        self.hbox02.addWidget(self.cancel_btn)
        self.hbox02.addWidget(self.create_btn)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setMargin(20)

        self.vbox.addStretch(5)
        self.vbox.addLayout(self.hbox01)
        self.vbox.addStretch(20)
        self.vbox.addLayout(self.hbox02)

        self.window.setLayout(self.vbox)

        self.window.show()

    def check_file_paths(self):
        import os

        # Check for menu folders, create if they don't exist

        if not os.path.isdir(self.folder_menus):
            try:
                os.makedirs(self.folder_menus)
            except:
                message_box('Could not create menu folder. Check folder permissions')
                return
        if not os.path.isdir(self.library_menus):
            try:
                os.makedirs(self.library_menus)
            except:
                message_box('Could not create menu folder. Check folder permissions')
                return

        menu_file_name = self.name_entry.text() + '.py'

        # Set possible menu save paths

        folder_menu_file_path = os.path.join(self.folder_menus, menu_file_name)
        library_menu_file_path = os.path.join(self.library_menus, menu_file_name)

        # Select menu file save path

        if self.creation_type == 'Folder':
            self.menu_save_path = folder_menu_file_path
        elif self.creation_type == 'Library':
            self.menu_save_path = library_menu_file_path

        print ('menu_save_path:', self.menu_save_path, '\n')

        # Check if menu file name already exists, overwrite?

        shared_folders_list = os.listdir(self.folder_menus)
        shared_libraries_list = os.listdir(self.library_menus)

        print (menu_file_name)
        print (shared_folders_list)
        print (shared_libraries_list)

        if menu_file_name in shared_libraries_list or menu_file_name in shared_folders_list:
            overwrite = message_box_confirm('Menu Alreadys Exists, Overwrite?')
            if not overwrite:
                return
            try:
                os.remove(folder_menu_file_path)
                os.remove(folder_menu_file_path + 'c')
            except:
                pass
            try:
                os.remove(library_menu_file_path)
                os.remove(library_menu_file_path + 'c')
            except:
                pass
            print ('\n>>> old menu deleted <<<\n')
            return self.create_new_template()
        return self.create_new_template()

    def create_new_template(self):
        import flame

        def get_tree():

            def get_folders(folder):
                import flame

                def get_parent(folders):

                    # Get folder parent name and add to list

                    folder_parent = folders.parent
                    folder_parent_name = folder_parent.name
                    print ('folder_parent_name:', folder_parent_name)

                    folder_path_list.append(str(folder_parent_name)[1:-1])

                    # Try to loop through to parent of parent if it exists

                    try:
                        get_parent(folder_parent)
                    except:
                        pass

                for folders in folder.folders:
                    folder_path_list = []
                    folder_name = folders.name
                    print ('folder_name:', folder_name)
                    folder_path_list.append(str(folder_name)[1:-1])

                    get_parent(folders)
                    get_folders(folders)

                    # Reverse folder list order

                    folder_path_list.reverse()
                    print ('folder_path_list:', folder_path_list)

                    # Convert folder list to string

                    new_folder_path = '/'.join(folder_path_list)
                    new_folder_path = root_folder + new_folder_path.split(root_folder, 1)[1]

                    print ('new_folder_path:', new_folder_path)

                    # Add folder path string to master folder list for dictionary conversion

                    master_folder_list.append(new_folder_path)

            master_folder_list = []

            # Convert folder tree into list

            for folder in self.selection:
                root_folder = str(folder.name)[1:-1]
                print ('root_folder:', root_folder)

                get_folders(folder)

            print ('master_folder_list:', master_folder_list)

            # Convert folder list to dictionary

            self.folder_dict = {}

            for path in master_folder_list:
                p = self.folder_dict
                for x in path.split('/'):
                    p = p.setdefault(x, {})

            # If only a single empty library or folder, make dict root_folder

            if self.folder_dict == {}:
                self.folder_dict = {root_folder: {}}

            print ('folder_dict:', self.folder_dict, '\n')

        def save_new_menu():
            import re

            # Set tokens for menu template file

            menu_template_token_dict = {}

            menu_template_token_dict['<FolderDict>'] = '%s' % self.folder_dict
            menu_template_token_dict['<TopItem>'] = self.top_item
            menu_template_token_dict['<TemplateMenuName>'] = self.menu_name
            menu_template_token_dict['<TemplateName>'] = self.name_entry.text()

            print ('menu_template_token_dict:', menu_template_token_dict, '\n')

            # Open menu template

            menu_template = open(self.menu_template_path, 'r')
            menu_template_lines = menu_template.read().splitlines()

            # Replace tokens in menu template

            for key, value in menu_template_token_dict.items():
                for line in menu_template_lines:
                    if key in line:
                        line_index = menu_template_lines.index(line)
                        new_line = re.sub(key, value, line)
                        menu_template_lines[line_index] = new_line

            # Save new menu

            out_file = open(self.menu_save_path, 'w')
            for line in menu_template_lines:
                print(line, file=out_file)
            out_file.close()

            # Close menu template

            menu_template.close()

        # Build folder or library tree

        get_tree()

        # Save new menu

        save_new_menu()

        self.window.close()

        message_box('%s template menu created' % self.name_entry.text())

        print ('\n', '>' * 10, 'new template menu created', '<' * 10, '\n')

        flame.execute_shortcut('Rescan Python Hooks')

        print ('\n', '>' * 10, 'python hooks refreshed', '<' * 10, '\n')

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

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

def message_box_confirm(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setText('<b><center>%s' % message)
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

    print ('\n>>> %s <<<\n' % message)

    if msg_box.exec_() == QtWidgets.QMessageBox.Yes:
        return True
    return False

# ----------------------------------------------- #

def scope_folder(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PyFolder)):
            return True
    return False

def scope_library(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PyLibrary)):
            return True
    return False

# ----------------------------------------------- #

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Create Template...',
            'actions': [
                {
                    'name': 'Create Folder Template',
                    'isVisible': scope_folder,
                    'execute': CreateTemplate,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Create Library Template',
                    'isVisible': scope_library,
                    'execute': CreateTemplate,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
