'''
Script Name: Create Project Folders
Script Version: 1.0
Flame Version: 2021.1
Written by: Michael Vaglienty
Creation Date: 09.22.21
Update Date: 09.22.21

Custom Action Type: Flame Project Launch

Description:

    Create basic project folder structure on file system

    Setup menu:

        Main Flame Menu -> pyFlame -> Create Project Folders Setup

    Script will run whenever Flame projects are launched.

    The script will not prompt to create project folders until a jobs
    root path is set in Setup. The path can be set using tokens for
    Flame project names and Flame project nick names.

    For exmaple: /Jobs/<ProjectNickName>/<ProjectName>

    After the jobs root path is set the next time Flame is started
    and a project is launched there will be a prompt to create a
    project folder if one does not already exist.

    The project folder structure can also be created in Setup.

To install:

Copy script into /opt/Autodesk/shared/python/create_project_folders
'''

from __future__ import print_function
from PySide2 import QtWidgets, QtCore, QtGui
import xml.etree.ElementTree as ET
from functools import partial
import os, re, ast

VERSION = 'v1.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/create_project_folders'

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
        self.setMinimumSize(125, 28)
        self.setMaximumSize(125, 28)
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
        self.setMinimumSize(QtCore.QSize(125, 28))
        self.setMaximumSize(QtCore.QSize(125, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(do_when_pressed)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}'
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
        self.setMinimumWidth(125)
        self.setMaximumWidth(125)
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

class FlameTreeWidget(QtWidgets.QTreeWidget):
    """
    Custom Qt Flame Tree Widget

    To use:

    tree_headers = ['Header1', 'Header2', 'Header3', 'Header4']
    tree = FlameTreeWidget(tree_headers, window)
    """

    def __init__(self, tree_headers, parent_window, *args, **kwargs):
        super(FlameTreeWidget, self).__init__(*args, **kwargs)

        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.setAlternatingRowColors(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QTreeWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; font: 14px "Discreet"}'
                           'QTreeWidget::item:selected {color: #d9d9d9; background-color: #474747; border: 1px solid #111111}'
                           'QHeaderView {color: #9a9a9a; background-color: #393939; font: 14px "Discreet"}'
                           'QTreeWidget::item:selected {selection-background-color: #111111}'
                           'QMenu {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        self.verticalScrollBar().setStyleSheet('color: #818181')
        self.horizontalScrollBar().setStyleSheet('color: #818181')
        self.setHeaderLabels(tree_headers)

#-------------------------------------#

class CreateProjectFolders(object):

    def __init__(self, selection):
        import flame

        print ('\n')
        print ('>' * 20, 'create project folders %s' % VERSION, '<' * 20, '\n')

        # Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Load config file

        self.config()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('create_project_folders'):
                self.project_folders = ast.literal_eval(setting.find('project_folders').text)
                self.jobs_root_path = setting.find('jobs_root_path').text

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
    <create_project_folders>
        <jobs_root_path></jobs_root_path>
        <project_folders>{'Project Folders': {'Folder 1': {}, 'Folder 2': {}, 'Folder 3': {}, 'Folder 4': {}}}</project_folders>
    </create_project_folders>
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

    def translate_root_path(self):
        import flame

        # print ('path to translate:', self.jobs_root_path)

        # Replace any tokens in system shot folder path

        root_folder_path = re.sub('<ProjectName>', flame.project.current_project.name, self.jobs_root_path)
        root_folder_path = re.sub('<ProjectNickName>', flame.project.current_project.nickname, root_folder_path)

        return root_folder_path

    def confirm_create_folders(self):

        if self.jobs_root_path:

            # Translate jobs path

            self.translated_jobs_root_path = self.translate_root_path()

            if not os.path.isdir(self.translated_jobs_root_path):
                create_now = message_box_confirm('Project file system folders not found. Create now?')
                if create_now:
                    self.create_folders()
                else:
                    print ('>>> Skipping project file system folder creation <<<\n')
            else:
                print ('>>> Project file system folders found! Skipping folder creation <<<\n')
        else:
            print ('>>> Project folder path not set! Skipping project file system folder creation. <<<')
            print ('>>> Go to Flame Main Menu -> pyFlame -> Create Project Folders Setup to set up folder paths.<<<\n')

    def create_folders(self):
        import flame

        def folder_loop(value, root_folder):
            for k, v in iter(value.items()):
                folder = os.path.join(root_folder, k)
                os.makedirs(folder)
                folder_loop(v, folder)

        # Create shot folders

        for key, value, in iter(self.project_folders.items()):
            if not os.path.isdir(self.translated_jobs_root_path):
                os.makedirs(self.translated_jobs_root_path)
                folder_loop(value, self.translated_jobs_root_path)

        if os.path.isdir(self.translated_jobs_root_path):
            print ('    Project folder created: %s' % self.translated_jobs_root_path, '\n')
            print ('done.\n')
        else:
            message_box('Job folder could not be created. Check path and permissions.')

    def setup_window(self):

        def save_config():

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

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            project_folders = root.find('.//project_folders')
            project_folders.text = str(create_dict(self.folder_tree))
            jobs_root_path = root.find('.//jobs_root_path')
            jobs_root_path.text = self.jobs_root_path_lineedit.text()

            xml_tree.write(self.config_xml)

            print ('>>> config saved <<<\n')

            self.setup_window.close()

        def fill_tree(tree_widget, tree_dict):

            def fill_item(item, value):

                # Set top level item so name can not be changed except for reel group tree

                if str(item.parent()) != 'None':
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled)
                else:
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled)

                item.setExpanded(True)

                if type(value) is dict:
                    for key, val in iter(value.items()):
                        child = QtWidgets.QTreeWidgetItem()
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
                return message_box('Template must have at least one folder')

        def add_tree_item(tree_top, tree, new_item_num=0):

            # Get list of exisiting schematic reels for new reel numbering

            existing_item_names = []

            iterator = QtWidgets.QTreeWidgetItemIterator(tree)
            while iterator.value():
                item = iterator.value()
                existing_item = item.text(0)
                existing_item_names.append(existing_item)
                iterator += 1

            # Set New Item name

            new_item_name = 'New Folder'

            new_item = new_item_name + ' ' + str(new_item_num)

            if new_item == '%s 0' % new_item_name:
                new_item = '%s' % new_item_name

            # Check if new item name exists, if it does add one to file name

            if new_item not in existing_item_names:

                # Create new tree item

                parent = tree.currentItem()

                # Expand folder

                tree.expandItem(parent)

                item = QtWidgets.QTreeWidgetItem(parent)
                item.setText(0, new_item)
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled)

            else:
                # Add 1 to item name and try again

                new_item_num += 1
                add_tree_item(tree_top, tree, new_item_num)

        def sort_tree_items(tree):
            tree.sortItems(0, QtGui.Qt.AscendingOrder)

        def folder_browse():

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.setup_window, 'Select Directory', self.jobs_root_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.jobs_root_path_lineedit.setText(file_path)

        self.setup_window = QtWidgets.QWidget()
        self.setup_window.setMinimumSize(QtCore.QSize(750, 500))
        self.setup_window.setMaximumSize(QtCore.QSize(750, 500))
        self.setup_window.setWindowTitle('Create Project Folders Setup %s' % VERSION)
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #212121')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                               (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        # Labels

        self.jobs_root_path_label = FlameLabel('Jobs Root Path', 'normal', self.setup_window)

        # LineEdits

        self.jobs_root_path_lineedit = FlameLineEdit(self.jobs_root_path, self.setup_window)

        # Media Panel Shot Folder Tree

        tree_headers = ['Project Folder Template']
        self.folder_tree = FlameTreeWidget(tree_headers, self.setup_window)

        # Fill tree

        fill_tree(self.folder_tree, self.project_folders)

        # Set tree top level items

        folder_tree_top = self.folder_tree.topLevelItem(0)
        self.folder_tree.setCurrentItem(folder_tree_top)

        # Token Button

        token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>'}
        self.setup_token_push_button = FlameTokenPushButton('Add Token', token_dict, self.jobs_root_path_lineedit, self.setup_window)

        # Buttons

        self.folder_sort_btn = FlameButton('Sort Folders', partial(sort_tree_items, self.folder_tree), self.setup_window)
        self.add_folder_btn = FlameButton('Add Folder', partial(add_tree_item, folder_tree_top, self.folder_tree), self.setup_window)
        self.delete_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, folder_tree_top, self.folder_tree), self.setup_window)

        setup_browse_btn = FlameButton('Browse', folder_browse, self.setup_window)
        setup_save_btn = FlameButton('Save', save_config, self.setup_window)
        setup_cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window)

        # Media panel shot folder tree contextual right click menus

        action_add_folder = QtWidgets.QAction('Add Folder', self.setup_window)
        action_add_folder.triggered.connect(partial(add_tree_item, folder_tree_top, self.folder_tree))
        self.folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.folder_tree.addAction(action_add_folder)

        action_delete_folder = QtWidgets.QAction('Delete Folder', self.setup_window)
        action_delete_folder.triggered.connect(partial(del_tree_item, folder_tree_top, self.folder_tree))
        self.folder_tree.addAction(action_delete_folder)

        #------------------------------------#

        # Window Layout

        self.setup_window.layout = QtWidgets.QGridLayout()
        self.setup_window.layout.setMargin(10)
        self.setup_window.layout.setVerticalSpacing(5)
        self.setup_window.layout.setHorizontalSpacing(5)

        self.setup_window.layout.setRowMinimumHeight(0, 28)

        self.setup_window.layout.addWidget(self.jobs_root_path_label, 1, 0)
        self.setup_window.layout.addWidget(self.jobs_root_path_lineedit, 1, 1, 1, 2)
        self.setup_window.layout.addWidget(self.setup_token_push_button, 1, 3)
        self.setup_window.layout.addWidget(setup_browse_btn, 1, 4)

        self.setup_window.layout.setRowMinimumHeight(2, 28)

        self.setup_window.layout.addWidget(self.folder_tree, 3, 1, 6, 3)

        self.setup_window.layout.addWidget(self.add_folder_btn, 3, 4)
        self.setup_window.layout.addWidget(self.delete_folder_btn, 4, 4)
        self.setup_window.layout.addWidget(self.folder_sort_btn, 5, 4)

        self.setup_window.layout.addWidget(setup_save_btn, 13, 4)
        self.setup_window.layout.addWidget(setup_cancel_btn, 14, 4)

        self.setup_window.setLayout(self.setup_window.layout)

        # ----------------------------------------------

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
    msg_box.setStyleSheet('QMessageBox {background-color: #313131}'
                          'QLabel {color: #9a9a9a; font: 14pt "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

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

    print ('>>> %s <<<\n' % message)

    if msg_box.exec_() == QtWidgets.QMessageBox.Yes:
        return True
    return False

#-------------------------------------#

def setup(selection):

    script = CreateProjectFolders(selection)
    script.setup_window()

def create_folders(selection):

    script = CreateProjectFolders(selection)
    script.confirm_create_folders()

#-------------------------------------#

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Create Project Folders Setup',
                    'execute': setup,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def app_initialized(project_name):
    create_folders(project_name)

