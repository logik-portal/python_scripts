'''
Script Name: Create Project Folders
Script Version: 1.3
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 09.22.21
Update Date: 06.06.22

Custom Action Type: Flame Project Launch

Description:

    Creates project file system folder structure and/or media panel library/folder
    structure on new Flame project startup.

    Script will run whenever a Flame project is launched for the first time.

    Project folder structures can be set using tokens for
    Flame project names and Flame project nick names.

    For exmaple: /Jobs/<ProjectNickName>/<ProjectName>

    After the projects path is set the next time Flame is started
    and a project is launched there will be a prompt to create file
    system and media panel folders.

    Folders can also be created manually through the Setup window.

Menus:

    Setup:

        Main Flame Menu -> pyFlame -> Create Project Folders Setup

To install:

    Copy script into /opt/Autodesk/shared/python/create_project_folders

Updates:

    v1.3 06.06.22

        Messages print to Flame message window - Flame 2023.1 and later

    v1.2 03.28.22

        Tokens for <ProjectName> and <ProjectNickName> can be entered into library and folder names

        Updated UI for Flame 2023

        Moved UI widgets to external file

        Imporved initial script setup

    v1.1 11.03.21

        Added ability to create media panel libraries and folders on project start up

        Added buttons to manually create file system/media panel folders

        Added buttons to enable/diable creation of either file systems folders or media panel folders

        Setup will now open first time Flame is started after script is installed
'''

from PySide2 import QtWidgets, QtCore, QtGui
import xml.etree.ElementTree as ET
from functools import partial
import os, re, ast
from pyflame_lib_create_project_folders import FlameWindow, FlameMessageWindow, FlameButton, FlameLabel, FlameLineEdit, FlameTreeWidget, FlameTokenPushButton, FlamePushButton, pyflame_print, pyflame_file_browser

SCRIPT_NAME = 'Create Project Folders'
SCRIPT_PATH = '/opt/Autodesk/shared/python/create_project_folders'
VERSION = 'v1.3'

class CreateProjectFolders(object):

    def __init__(self, selection):
        import flame

        print ('\n')
        print ('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

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
                self.first_time = ast.literal_eval(setting.find('first_time').text)
                self.create_file_system_folders_on_start = ast.literal_eval(setting.find('create_file_system_folders_on_start').text)
                self.create_media_panel_folders_on_start = ast.literal_eval(setting.find('create_media_panel_folders_on_start').text)
                self.ignore_projects = ast.literal_eval(setting.find('ignore_projects').text)
                self.projects_path = setting.find('projects_path').text
                self.file_system_folders = ast.literal_eval(setting.find('file_system_folders').text)
                self.media_panel_library_folders = ast.literal_eval(setting.find('media_panel_library_folders').text)

            pyflame_print(SCRIPT_NAME, 'Config loaded.')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', f'Unable to create folder: {self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                pyflame_print(SCRIPT_NAME, 'Config file does not exist. Creating new config file.')

                config = """
<settings>
    <create_project_folders>
        <first_time>True</first_time>
        <create_file_system_folders_on_start>False</create_file_system_folders_on_start>
        <create_media_panel_folders_on_start>False</create_media_panel_folders_on_start>
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
            self.setup_main_window()

        if os.path.isfile(self.config_xml):
            get_config_values()
        else:
            create_config_file()
            if os.path.isfile(self.config_xml):
                get_config_values()

    #-------------------------------------#

    def setup_main_window(self):

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
                return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Template must have at least one folder')

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

            if new_item == f'{new_item_name} 0':
                new_item = f'{new_item_name}'

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

            file_path = pyflame_file_browser('Select Directory', [''], self.projects_path_lineedit.text(), select_directory=True, window_to_hide=[self.setup_window])

            if file_path:
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

            if self.create_system_folders_push_button.isChecked() == True:
                if self.projects_path_lineedit.text() == '/' or not self.projects_path_lineedit.text():
                    return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', '<b>Projects Path:</b> Enter path where folders will be created.')

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            first_time = root.find('.//first_time')
            first_time.text = 'False'

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

            pyflame_print(SCRIPT_NAME, 'Config saved.')

            self.setup_window.close()

            self.config()

            self.create_on_start()

        def manually_create_file_system_folders():

            save_config()

            self.config()

            self.create_file_system_folders()

            FlameMessageWindow('message', f'{SCRIPT_NAME}: Operation Complete', 'File system folders created')

        def manually_create_libraries():

            save_config()

            self.config()

            self.create_media_panel_folders()

        grid_layout = QtWidgets.QGridLayout()
        self.setup_window = FlameWindow(f'{SCRIPT_NAME}: Setup <small>{VERSION}', grid_layout, 750, 750)

        # Labels

        self.projects_path_label = FlameLabel('Projects Path')

        # LineEdits

        self.projects_path_lineedit = FlameLineEdit(self.projects_path)

        #------------------------------------------------------------#

        # File System Folders Tree

        file_system_tree_headers = ['File System Folder Template']
        self.file_system_folder_tree = FlameTreeWidget(file_system_tree_headers)

        # Fill tree

        fill_tree(self.file_system_folder_tree, self.file_system_folders)

        # Set tree top level items

        file_system_tree_top = self.file_system_folder_tree.topLevelItem(0)
        self.file_system_folder_tree.setCurrentItem(file_system_tree_top)

        #------------------------------------------------------------#

        # Media Panel Library/Folder Tree

        media_panel_tree_headers = ['Media Panel Library/Folder Template']
        self.media_panel_library_folders_tree = FlameTreeWidget(media_panel_tree_headers)

        # Fill tree

        fill_tree(self.media_panel_library_folders_tree, self.media_panel_library_folders)

        # Set tree top level items

        media_panel_tree_top = self.media_panel_library_folders_tree.topLevelItem(0)
        self.media_panel_library_folders_tree.setCurrentItem(media_panel_tree_top)

        #------------------------------------------------------------#

        # Token Button

        token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>'}
        self.setup_token_push_button = FlameTokenPushButton('Add Token', token_dict, self.projects_path_lineedit)

        # Push Buttons

        self.create_system_folders_push_button = FlamePushButton(' Create Folders', self.create_file_system_folders_on_start)
        self.create_media_panel_lib_folders_push_button = FlamePushButton(' Create Lib/Folders', self.create_media_panel_folders_on_start)

        # Buttons

        self.file_system_add_folder_btn = FlameButton('Add Folder', partial(add_tree_item, file_system_tree_top, self.file_system_folder_tree))
        self.file_system_delete_folder_btn = FlameButton('Delete Folder', partial(del_tree_item, file_system_tree_top, self.file_system_folder_tree))
        self.file_system_sort_btn = FlameButton('Sort Folders', partial(sort_tree_items, self.file_system_folder_tree))
        self.file_system_manual_create_btn = FlameButton('Manually Create', manually_create_file_system_folders)

        self.media_panel_add_folder_btn = FlameButton('Add Lib/Folder', partial(add_tree_item, media_panel_tree_top, self.media_panel_library_folders_tree))
        self.media_panel_delete_folder_btn = FlameButton('Delete Lib/Folder', partial(del_tree_item, media_panel_tree_top, self.media_panel_library_folders_tree))
        self.media_panel_sort_btn = FlameButton('Sort Lib/Folders', partial(sort_tree_items, self.media_panel_library_folders_tree))
        self.media_panel_manual_create_btn = FlameButton('Manually Create', manually_create_libraries)

        setup_browse_btn = FlameButton('Browse', folder_browse)
        setup_save_btn = FlameButton('Save', save_config)
        setup_cancel_btn = FlameButton('Cancel', self.setup_window.close)

        # Media panel shot folder tree contextual right click menus

        action_add_folder = QtWidgets.QAction('Add Folder')
        action_add_folder.triggered.connect(partial(add_tree_item, file_system_tree_top, self.file_system_folder_tree))
        self.file_system_folder_tree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.file_system_folder_tree.addAction(action_add_folder)

        action_delete_folder = QtWidgets.QAction('Delete Folder')
        action_delete_folder.triggered.connect(partial(del_tree_item, file_system_tree_top, self.file_system_folder_tree))
        self.file_system_folder_tree.addAction(action_delete_folder)

        #------------------------------------#

        # UI Widget Layout

        grid_layout.setMargin(10)
        grid_layout.setVerticalSpacing(5)
        grid_layout.setHorizontalSpacing(5)

        grid_layout.setRowMinimumHeight(0, 30)

        grid_layout.addWidget(self.projects_path_label, 1, 0)
        grid_layout.addWidget(self.projects_path_lineedit, 1, 1, 1, 2)
        grid_layout.addWidget(self.setup_token_push_button, 1, 3)
        grid_layout.addWidget(setup_browse_btn, 1, 4)

        grid_layout.setRowMinimumHeight(2, 30)

        grid_layout.addWidget(self.file_system_folder_tree, 4, 1, 6, 3)

        grid_layout.setRowMinimumHeight(11, 30)

        grid_layout.addWidget(self.create_system_folders_push_button, 4, 0)

        grid_layout.addWidget(self.media_panel_library_folders_tree, 12, 1, 6, 3)

        grid_layout.addWidget(self.file_system_add_folder_btn, 4, 4)
        grid_layout.addWidget(self.file_system_delete_folder_btn, 5, 4)
        grid_layout.addWidget(self.file_system_sort_btn, 6, 4)
        grid_layout.addWidget(self.file_system_manual_create_btn, 9, 4)

        grid_layout.addWidget(self.create_media_panel_lib_folders_push_button, 12, 0)

        grid_layout.addWidget(self.media_panel_add_folder_btn, 12, 4)
        grid_layout.addWidget(self.media_panel_delete_folder_btn, 13, 4)
        grid_layout.addWidget(self.media_panel_sort_btn, 14, 4)
        grid_layout.addWidget(self.media_panel_manual_create_btn, 17, 4)

        grid_layout.setRowMinimumHeight(18, 30)

        grid_layout.addWidget(setup_save_btn, 19, 4)
        grid_layout.addWidget(setup_cancel_btn, 20, 4)

        self.setup_window.setLayout(grid_layout)

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

            first_time = root.find('.//first_time')
            first_time.text = 'False'

            xml_tree.write(self.config_xml)

            pyflame_print(SCRIPT_NAME, 'Config saved.')

        if not self.first_time:

            # If current project is in ignore_projects list, do not create any folders

            if not self.project_name in self.ignore_projects:
                file_system_folders = ''
                media_panel_folders = ''

                # If create system folders is selected in Setup, create folders based on template
                if self.create_file_system_folders_on_start:
                    file_system_folders = FlameMessageWindow('confirm', f'{SCRIPT_NAME}: Create File System Folders', 'Project file system folders not found. Create now?')
                    if file_system_folders:
                        self.create_file_system_folders()
                        pyflame_print(SCRIPT_NAME, 'Media panel libraries/folders created.')
                    else:
                        pyflame_print(SCRIPT_NAME, 'Skipped creating file system folders.')

                # If create media panel folders is selected in Setup, create folders based on template

                if self.create_media_panel_folders_on_start:
                    media_panel_folders = FlameMessageWindow('warning', f'{SCRIPT_NAME}: Create Media Panel Folders', 'Create project libraries/folders?<br><br>This will delete the Default library.')
                    if media_panel_folders:
                        self.create_media_panel_folders()
                        pyflame_print(SCRIPT_NAME, 'Media panel libraries/folders created.')
                    else:
                        pyflame_print(SCRIPT_NAME, 'Skipped creating media panel libraries/folders.')

                if self.create_file_system_folders_on_start or self.create_media_panel_folders_on_start:

                    # If either file system or media panel folders are created, do not ask again for this project.

                    if file_system_folders or media_panel_folders:
                        self.ignore_projects.append(self.project_name)
                        save_config()

                    # If neither file system or media panel folders are created, ask if user should be prompted for this project in the future

                    if not file_system_folders and not media_panel_folders:
                        if FlameMessageWindow('confirm', f'{SCRIPT_NAME}: Confirm Operation', 'Skipped Creating system folders and media panel libraries/folders.<br><br>Do not ask to create project folders for this project again?'):
                            self.ignore_projects.append(self.project_name)
                            save_config()

            else:
                print ('--> skipped creating file system folders and media panel libraries/folders.\n')

        else:

            # Update config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            first_time = root.find('.//first_time')
            first_time.text = 'False'

            xml_tree.write(self.config_xml)

    def create_file_system_folders(self):

        def build_file_system_paths():

            def folder_loop(value, root_folder):
                for k, v in iter(value.items()):
                    folder = os.path.join(root_folder, k)
                    folder = self.replace_tokens(folder)
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
                print (f'    created directory: {path}')

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
                key = self.replace_tokens(key)
                folder = new_library.create_folder(key)
                folder_loop(value, folder)

        for key, value in iter(self.media_panel_library_folders.items()):
            for lib, folder in iter (value.items()):
                lib = self.replace_tokens(lib)
                new_library = self.workspace.create_library(lib)
                folder_loop(folder, new_library)

    def replace_tokens(self, item):

        item = item.replace('<ProjectNickName>', self.project_nickname)
        item = item.replace('<ProjectName>', self.project_name)

        return item

    #-------------------------------------#

    def translate_root_path(self):
        import flame

        # Replace any tokens in system shot folder path

        new_path = re.sub('<ProjectName>', self.project_name, self.projects_path)
        new_path = re.sub('<ProjectNickName>', self.project_nickname, new_path)

        return new_path

#-------------------------------------#

def setup(selection):

    script = CreateProjectFolders(selection)
    script.setup_main_window()

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
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def app_initialized(project_name):
    create_folders(project_name)
