'''
Script Name: Create Media Panel Templates
Script Version: 3.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 05.01.19
Update Date: 03.15.22

Custom Action Type: Media Panel

Description:

    Create templates from libraries and folders in the Media Panel.
    Right-click menus will be created for each template

Menus:

    To create new template menus:

        Right-click on library or folder -> Create Template... -> Create Library Template / Create Folder Template

    Newly created templates:

        Right-click on library or folder -> Library/Folder Templates -> Select from saved templates

To install:

    Copy script into /opt/Autodesk/shared/python/create_media_panel_templates

Updates:

    v3.2 03.15.22

        Moved UI widgets to external file

    v3.1 03.07.22

        Updated UI for Flame 2023
'''

import os, re
from PySide2 import QtWidgets
from flame_widgets_create_media_panel_templates import FlameButton, FlameLabel, FlameLineEdit, FlameWindow, FlameMessageWindow

SCRIPT_PATH = '/opt/Autodesk/shared/python/create_media_panel_templates'

VERSION = 'v3.2'

class CreateTemplate(object):

    def __init__(self, selection):
        import flame

        print ('\n')
        print ('>' * 20, f'create media panel templates {VERSION}', '<' * 20, '\n')

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

        vbox = QtWidgets.QVBoxLayout()
        self.window = FlameWindow(f'Create Media Panel Template <small>{VERSION}', vbox, 400, 220)

        # Labels

        self.name_label = FlameLabel('Template Name', 'normal')

        # Entry

        self.name_entry = FlameLineEdit(self.item_name)

        # Buttons

        self.create_btn = FlameButton('Create Template', self.check_file_paths)
        self.cancel_btn = FlameButton('Cancel', self.window.close)

        #------------------------------------#

        # Window Layout

        hbox01 = QtWidgets.QHBoxLayout()
        hbox01.addWidget(self.name_label)
        hbox01.addWidget(self.name_entry)

        hbox02 = QtWidgets.QHBoxLayout()
        hbox02.addWidget(self.cancel_btn)
        hbox02.addWidget(self.create_btn)

        vbox.setMargin(20)

        vbox.addStretch(5)
        vbox.addLayout(hbox01)
        vbox.addStretch(20)
        vbox.addLayout(hbox02)

        self.window.show()

    def check_file_paths(self):

        # Check for menu folders, create if they don't exist

        if not os.path.isdir(self.folder_menus):
            try:
                os.makedirs(self.folder_menus)
            except:
                return FlameMessageWindow('Error', 'error', 'Could not create menu folder. Check folder permissions')
        if not os.path.isdir(self.library_menus):
            try:
                os.makedirs(self.library_menus)
            except:
                return FlameMessageWindow('Error', 'error', 'Could not create menu folder. Check folder permissions')

        menu_file_name = self.name_entry.text() + '.py'

        # Set possible menu save paths

        folder_menu_file_path = os.path.join(self.folder_menus, menu_file_name)
        library_menu_file_path = os.path.join(self.library_menus, menu_file_name)

        # Select menu file save path

        if self.creation_type == 'Folder':
            self.menu_save_path = folder_menu_file_path
        elif self.creation_type == 'Library':
            self.menu_save_path = library_menu_file_path

        #print ('menu_save_path:', self.menu_save_path, '\n')

        # Check if menu file name already exists, overwrite?

        shared_folders_list = os.listdir(self.folder_menus)
        shared_libraries_list = os.listdir(self.library_menus)

        #print (menu_file_name)
        #print (shared_folders_list)
        #print (shared_libraries_list)

        if menu_file_name in shared_libraries_list or menu_file_name in shared_folders_list:
            if not FlameMessageWindow('Confirm Operation', 'warning', 'Menu Alreadys Exists, Overwrite?'):
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

            print ('--> old menu deleted\n')

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
                    #print ('folder_parent_name:', folder_parent_name)

                    folder_path_list.append(str(folder_parent_name)[1:-1])

                    # Try to loop through to parent of parent if it exists

                    try:
                        get_parent(folder_parent)
                    except:
                        pass

                for folders in folder.folders:
                    folder_path_list = []
                    folder_name = folders.name
                    #print ('folder_name:', folder_name)
                    folder_path_list.append(str(folder_name)[1:-1])

                    get_parent(folders)
                    get_folders(folders)

                    # Reverse folder list order

                    folder_path_list.reverse()
                    #print ('folder_path_list:', folder_path_list)

                    # Convert folder list to string

                    new_folder_path = '/'.join(folder_path_list)
                    new_folder_path = root_folder + new_folder_path.split(root_folder, 1)[1]

                    #print ('new_folder_path:', new_folder_path)

                    # Add folder path string to master folder list for dictionary conversion

                    master_folder_list.append(new_folder_path)

            master_folder_list = []

            # Convert folder tree into list

            for folder in self.selection:
                root_folder = str(folder.name)[1:-1]
                #print ('root_folder:', root_folder)

                get_folders(folder)

            #print ('master_folder_list:', master_folder_list)

            # Convert folder list to dictionary

            self.folder_dict = {}

            for path in master_folder_list:
                p = self.folder_dict
                for x in path.split('/'):
                    p = p.setdefault(x, {})

            # If only a single empty library or folder, make dict root_folder

            if self.folder_dict == {}:
                self.folder_dict = {root_folder: {}}

            #print ('folder_dict:', self.folder_dict, '\n')

        def save_new_menu():

            # Set tokens for menu template file

            menu_template_token_dict = {}

            menu_template_token_dict['<FolderDict>'] = f'{self.folder_dict}'
            menu_template_token_dict['<TopItem>'] = self.top_item
            menu_template_token_dict['<TemplateMenuName>'] = self.menu_name
            menu_template_token_dict['<TemplateName>'] = self.name_entry.text()

            #print ('menu_template_token_dict:', menu_template_token_dict, '\n')

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

        FlameMessageWindow('Operation Complete', 'message', f'Menu created: <b>{self.name_entry.text()}</b>')

        flame.execute_shortcut('Rescan Python Hooks')

        print ('done.\n')

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
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Create Library Template',
                    'isVisible': scope_library,
                    'execute': CreateTemplate,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
