'''
Script Name: Create Project Folders
Script Version: 1.1
Flame Version: 2021.1
Written by: Michael Vaglienty
Creation Date: 09.22.21
Update Date: 11.03.21

Custom Action Type: Flame Project Launch

Description:

    Create project folder structure on file system for new Flame project.

    Create media panel library/folder structure for new Flame project.

    Menus:

        Setup:

            Main Flame Menu -> pyFlame -> Create Project Folders Setup

    Script will run whenever Flame projects are launched.

    It will only prompt to create folders first time each project is loaded. After
    that folders can be created manually by going to Setup.

    The script will not prompt to create project folders until a projects
    path is set in Setup. The path can be set using tokens for
    Flame project names and Flame project nick names.

    For exmaple: /Jobs/<ProjectNickName>/<ProjectName>

    After the projects path is set the next time Flame is started
    and a project is launched there will be a prompt to create file
    system and media panel folders.

    The file system and media panel folder structure can be set in Setup.

To install:

    Copy script into /opt/Autodesk/shared/python/create_project_folders

Updates:

    v1.1 11.03.21

        Added ability to create media panel libraries and folders on project start up

        Added buttons to manually create file system/media panel folders

        Added buttons to enable/diable creation of either file systems folders or media panel folders

        Setup will now open first time Flame is started after script is installed
'''

from __future__ import print_function
from PySide2 import QtWidgets, QtCore, QtGui
import xml.etree.ElementTree as ET
from functools import partial
import os, re, ast

VERSION = 'v1.1'

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
        self.setMinimumSize(150, 28)
        self.setMaximumSize(150, 28)
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
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
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
        self.setMinimumHeight(200)
        self.setMaximumHeight(200)
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

        # Get Flame values

        self.project_name = flame.project.current_project.name
        self.project_nickname = flame.project.current_project.nickname
        self.workspace = flame.project.current_project.current_workspace
        self.libraries = self.workspace.libraries

        # Load config file

        self.config()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('create_project_folders'):
                self.create_file_system_folders_on_start = ast.literal_eval(setting.find('create_file_system_folders_on_start').text)
                self.create_media_panel_folders_on_start = ast.literal_eval(setting.find('create_media_panel_folders_on_start').text)
                self.ignore_projects = ast.literal_eval(setting.find('ignore_projects').text)
                self.file_system_folders = ast.literal_eval(setting.find('file_system_folders').text)
                self.media_panel_library_folders = ast.literal_eval(setting.find('media_panel_library_folders').text)
                self.projects_path = setting.find('projects_path').text

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
    <create_project_folders>
        <create_file_system_folders_on_start>True</create_file_system_folders_on_start>
        <create_media_panel_folders_on_start>True</create_media_panel_folders_on_start>
        <ignore_projects>[]</ignore_projects>
        <projects_path></projects_path>
        <file_system_folders>{'File System Folders': {'Folder 1': {}, 'Folder 2': {}, 'Folder 3': {}, 'Folder 4': {}}}</file_system_folders>
        <media_panel_library_folders>{'Media Panel Libraries and Folders': {'Library': {'Folder 1': {}, 'Folder 2': {}, 'Folder 3': {}, 'Folder 4': {}}}}</media_panel_library_folders>
    </create_project_folders>
</settings>"""

                with open(self.config_xml, 'a') as config_file:
                    config_file.write(config)
                    config_file.close()

            get_config_values()
            self.setup_window()

        if os.path.isfile(self.config_xml):
            get_config_values()
        else:
            create_config_file()
            if os.path.isfile(self.config_xml):
                get_config_values()

    #-------------------------------------#

    def setup_window(self):

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

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.setup_window, 'Select Directory', self.projects_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.projects_path_lineedit.setText(file_path)

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

            if self.projects_path_lineedit.text() == '/' or not self.projects_path_lineedit.text():
                message_box('Enter projects path')
                return False

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            file_system_folders = root.find('.//file_system_folders')
            file_system_folders.text = str(create_dict(self.file_system_folder_tree))

            media_panel_library_folders = root.find('.//media_panel_library_folders')
            media_panel_library_folders.text = str(create_dict(self.media_panel_library_folders_tree))

            projects_path = root.find('.//projects_path')
            projects_path.text = self.projects_path_lineedit.text()

            create_file_system_folders_on_start = root.find('.//create_file_system_folders_on_start')
            create_file_system_folders_on_start.text = str(self.create_system_folders_push_button.isChecked())

            create_media_panel_folders_on_start = root.find('.//create_media_panel_folders_on_start')
            create_media_panel_folders_on_start.text = str(self.create_media_panel_lib_folders_push_button.isChecked())

            xml_tree.write(self.config_xml)

            print ('>>> config saved <<<\n')

            return True

        def save_button():

            config_saved = save_config()

            if config_saved:
                self.setup_window.close()

        def manually_create_file_system_folders():

            save_config()

            self.config()

            self.create_file_system_folders()

            message_box('File system folders created')

        def manually_create_libraries():

            save_config()

            self.config()

            self.create_media_panel_folders()

        self.setup_window = QtWidgets.QWidget()
        self.setup_window.setMinimumSize(QtCore.QSize(750, 680))
        self.setup_window.setMaximumSize(QtCore.QSize(750, 680))
        self.setup_window.setWindowTitle('Create Project Folders Setup %s' % VERSION)
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #212121')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                               (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        # Labels

        self.projects_path_label = FlameLabel('Projects Path', 'normal', self.setup_window)
        self.project_launch_label = FlameLabel('On New Project Launch', 'background', self.setup_window)

        # LineEdits

        self.projects_path_lineedit = FlameLineEdit(self.projects_path, self.setup_window)

        #------------------------------------------------------------#

        # File System Folders Tree

        file_system_tree_headers = ['File System Folder Template']
        self.file_system_folder_tree = FlameTreeWidget(file_system_tree_headers, self.setup_window)

        # Fill tree

        fill_tree(self.file_system_folder_tree, self.file_system_folders)

        # Set tree top level items

        file_system_tree_top = self.file_system_folder_tree.topLevelItem(0)
        self.file_system_folder_tree.setCurrentItem(file_system_tree_top)

        #------------------------------------------------------------#

        # Media Panel Library/Folder Tree

        media_panel_tree_headers = ['Media Panel Library/Folder Template']
        self.media_panel_library_folders_tree = FlameTreeWidget(media_panel_tree_headers, self.setup_window)

        # Fill tree

        fill_tree(self.media_panel_library_folders_tree, self.media_panel_library_folders)

        # Set tree top level items

        media_panel_tree_top = self.media_panel_library_folders_tree.topLevelItem(0)
        self.media_panel_library_folders_tree.setCurrentItem(media_panel_tree_top)

        #------------------------------------------------------------#

        # Token Button

        token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>'}
        self.setup_token_push_button = FlameTokenPushButton('Add Token', token_dict, self.projects_path_lineedit, self.setup_window)

        # Push Buttons

        self.create_system_folders_push_button = FlamePushButton(' Create Folders', self.create_file_system_folders_on_start, self.setup_window)
        self.create_media_panel_lib_folders_push_button = FlamePushButton(' Create Lib/Folders', self.create_media_panel_folders_on_start, self.setup_window)

        # Buttons

        self.file_system_add_folder_btn = FlameButton('Add Folder', partial(add_tree_item, file_system_tree_top, self.file_system_folder_tree), self.setup_window)
        self.file_system_delete_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, file_system_tree_top, self.file_system_folder_tree), self.setup_window)
        self.file_system_sort_btn = FlameButton('Sort Folders', partial(sort_tree_items, self.file_system_folder_tree), self.setup_window)
        self.file_system_manual_create_btn = FlameButton('Manually Create', manually_create_file_system_folders, self.setup_window)

        self.media_panel_add_folder_btn = FlameButton('Add Lib/Folder', partial(add_tree_item, media_panel_tree_top, self.media_panel_library_folders_tree), self.setup_window)
        self.media_panel_delete_folder_btn = FlameButton('Delete Lib/Folder', partial(del_tree_item, media_panel_tree_top, self.media_panel_library_folders_tree), self.setup_window)
        self.media_panel_sort_btn = FlameButton('Sort Lib/Folders', partial(sort_tree_items, self.media_panel_library_folders_tree), self.setup_window)
        self.media_panel_manual_create_btn = FlameButton('Manually Create', manually_create_libraries, self.setup_window)

        setup_browse_btn = FlameButton('Browse', folder_browse, self.setup_window)
        setup_save_btn = FlameButton('Save', save_button, self.setup_window)
        setup_cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window)

        # Media panel shot folder tree contextual right click menus

        action_add_folder = QtWidgets.QAction('Add Folder', self.setup_window)
        action_add_folder.triggered.connect(partial(add_tree_item, file_system_tree_top, self.file_system_folder_tree))
        self.file_system_folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.file_system_folder_tree.addAction(action_add_folder)

        action_delete_folder = QtWidgets.QAction('Delete Folder', self.setup_window)
        action_delete_folder.triggered.connect(partial(del_tree_item, file_system_tree_top, self.file_system_folder_tree))
        self.file_system_folder_tree.addAction(action_delete_folder)

        #------------------------------------#

        # Window Layout

        self.setup_window.layout = QtWidgets.QGridLayout()
        self.setup_window.layout.setMargin(10)
        self.setup_window.layout.setVerticalSpacing(5)
        self.setup_window.layout.setHorizontalSpacing(5)

        self.setup_window.layout.setRowMinimumHeight(0, 30)

        self.setup_window.layout.addWidget(self.projects_path_label, 1, 0)
        self.setup_window.layout.addWidget(self.projects_path_lineedit, 1, 1, 1, 2)
        self.setup_window.layout.addWidget(self.setup_token_push_button, 1, 3)
        self.setup_window.layout.addWidget(setup_browse_btn, 1, 4)

        self.setup_window.layout.setRowMinimumHeight(2, 30)

        self.setup_window.layout.addWidget(self.file_system_folder_tree, 4, 1, 6, 3)

        self.setup_window.layout.setRowMinimumHeight(11, 30)

        self.setup_window.layout.addWidget(self.project_launch_label, 3, 0)
        self.setup_window.layout.addWidget(self.create_system_folders_push_button, 4, 0)

        self.setup_window.layout.addWidget(self.media_panel_library_folders_tree, 12, 1, 6, 3)

        self.setup_window.layout.addWidget(self.file_system_add_folder_btn, 4, 4)
        self.setup_window.layout.addWidget(self.file_system_delete_folder_btn, 5, 4)
        self.setup_window.layout.addWidget(self.file_system_sort_btn, 6, 4)
        self.setup_window.layout.addWidget(self.file_system_manual_create_btn, 9, 4)

        self.setup_window.layout.addWidget(self.create_media_panel_lib_folders_push_button, 12, 0)

        self.setup_window.layout.addWidget(self.media_panel_add_folder_btn, 12, 4)
        self.setup_window.layout.addWidget(self.media_panel_delete_folder_btn, 13, 4)
        self.setup_window.layout.addWidget(self.media_panel_sort_btn, 14, 4)
        self.setup_window.layout.addWidget(self.media_panel_manual_create_btn, 17, 4)

        self.setup_window.layout.setRowMinimumHeight(18, 30)

        self.setup_window.layout.addWidget(setup_save_btn, 19, 4)
        self.setup_window.layout.addWidget(setup_cancel_btn, 20, 4)

        self.setup_window.setLayout(self.setup_window.layout)

        # ----------------------------------------------

        self.setup_window.show()

        return self.setup_window

    def create_on_start(self):
        import flame

        def save_config():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            ignore_projects = root.find('.//ignore_projects')
            ignore_projects.text = str(self.ignore_projects)

            xml_tree.write(self.config_xml)

            print ('>>> config saved <<<\n')

        # If path has been entered in Setup, create folders

        if self.projects_path:

            # If current project is in ignore_projects list, do not create any folders

            if not self.project_name in self.ignore_projects:

                # If create system folders is selected in Setup, create folders based on template

                if self.create_file_system_folders_on_start:
                    create_folders_now = message_box_confirm('<center>Project file system folders not found.<br>Create now?')
                    if create_folders_now:
                        self.create_file_system_folders()
                    else:
                        print ('>>> Skipping project folder creation <<<\n')

                # If create media panel folders is selected in Setup, create folders based on template

                if self.create_media_panel_folders_on_start:
                    create_media_panel_folders_now = message_box_confirm('<center>Create project libraries/folders? <br>This will delete the Default Library.')
                    if create_media_panel_folders_now:
                        self.create_media_panel_folders()
                        print ('>>> Media panel libraries/folders created. <<<')

            else:
                print ('>>> Skipping project folder creation. Current project in project ignore list. <<<\n')

            # Add project to project ignore list

            if self.project_name not in self.ignore_projects:
                self.ignore_projects.append(self.project_name)
                save_config()

            print ('done.\n')

        else:
            print ('>>> Project folder path not set! Skipping project file system folder creation. <<<')
            print ('>>> Go to Flame Main Menu -> pyFlame -> Create Project Folders Setup to set up folder paths.<<<\n')

    def create_file_system_folders(self):

        def build_file_system_paths():

            def folder_loop(value, root_folder):
                for k, v in iter(value.items()):
                    folder = os.path.join(root_folder, k)
                    self.file_system_folder_path_list.append(folder)
                    folder_loop(v, folder)

            # Create list of file system folders to create

            self.file_system_folder_path_list = []

            for key, value, in iter(self.file_system_folders.items()):
                    self.file_system_folder_path_list.append(self.translated_jobs_root_path)
                    folder_loop(value, self.translated_jobs_root_path)

        # Translate jobs path

        self.translated_jobs_root_path = self.translate_root_path()

        # Create list of project folders to be created

        build_file_system_paths()

        # If path doesn't already exist, create it

        for path in self.file_system_folder_path_list:
            if not os.path.isdir(path):
                os.makedirs(path)
                print ('    created directory: %s' % path)

        print ('\n')

    def create_media_panel_folders(self):
        import flame

        # Delete Default Library

        for lib in self.libraries:
            if lib.name == 'Default Library':
                flame.delete(lib)
                print ('Default Library deleted.\n')

        # Create new libraries and folders

        def folder_loop(v, new_library):

            for key, value in iter(v.items()):
                folder = new_library.create_folder(key)
                folder_loop(value, folder)

        for key, value in iter(self.media_panel_library_folders.items()):
            for lib, folder in iter (value.items()):
                new_library = self.workspace.create_library(lib)
                folder_loop(folder, new_library)

    #-------------------------------------#

    def translate_root_path(self):
        import flame

        # print ('path to translate:', self.jobs_root_path)

        # Replace any tokens in system shot folder path

        new_path = re.sub('<ProjectName>', self.project_name, self.projects_path)
        new_path = re.sub('<ProjectNickName>', self.project_nickname, new_path)

        return new_path

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
        message = message.replace(code, '')

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

    code_list = ['<br>', '<center>']

    for code in code_list:
        message = message.replace(code, '')

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
    script.create_on_start()

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
