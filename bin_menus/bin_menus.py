'''
Script Name: Bin Menus
Script Version: 1.1
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 11.29.21
Update Date: 12.13.21

Custom Action Type: Batch

Description:

    Create right-click batch menus for nodes in User and Project Bins

    Bin nodes can be added to batch by right-clicking any where in the batch view or
    by right-clicking on an existing node. When adding a bin node by right-clicking on a
    node, the bin node will be connected to the selected node.

    After adding nodes to the user or project bins select Create/Refresh Bin Meuns menu to
    create new menus for nodes that have been added. This will also delete  menus for nodes
    that have been removed from bins.

    Menus

        right-click in batch -> Bin: User -> Create/Refresh Bin Menus
        right-click in batch -> Bin: Project -> Create/Refresh Bin Menus

        These menus will only appear when nodes are present in user/project bins

To install:

    Copy script into /opt/Autodesk/shared/python/bin_menus

Updates:

    v1.1 12.13.21

        Only works with 2022 and newer now. 2021.2 had problems properly appending bin node setups.

        Menus auto refresh when Flame is launched.

        Fixed bin menu version number.

        Fixed menus not deleting.
'''

from __future__ import print_function
from PySide2 import QtWidgets, QtCore
import os, re, shutil

VERSION = 'v1.1'

SCRIPT_PATH = '/opt/Autodesk/shared/python/bin_menus'

#-------------------------------------#

class BinMenus(object):

    def __init__(self, selection):
        import flame

        print ('''
 ____  _         __  __
|  _ \(_)       |  \/  |
| |_) |_ _ __   | \  / | ___ _ __  _   _ ___
|  _ <| | '_ \  | |\/| |/ _ \ '_ \| | | / __|
| |_) | | | | | | |  | |  __/ | | | |_| \__ \\
|____/|_|_| |_| |_|  |_|\___|_| |_|\__,_|___/
        \n''')

        print ('>' * 20, 'bin menu %s' % VERSION, '<' * 20, '\n')

        # Paths

        self.user_menu_path = os.path.join(SCRIPT_PATH, 'user_bin_menus')
        self.project_menu_path = os.path.join(SCRIPT_PATH, 'project_bin_menus')
        self.node_template_path = os.path.join(SCRIPT_PATH, 'node_menu_template')

        self.create_menu_folders()

        self.current_user = flame.users.current_user.name
        print ('current_user:', self.current_user)

        self.user_bin_path = os.path.join('/opt/Autodesk/user', self.current_user, 'batch/pref')
        print ('user_bin_path:', self.user_bin_path)

        self.current_project = flame.projects.current_project.name
        print ('current_project:', self.current_project)

        self.project_bin_path = os.path.join('/opt/Autodesk/project', self.current_project, 'batch/pref')
        print ('project_bin_path:', self.project_bin_path, '\n')

        self.refresh_bin_menus()

    def create_menu_folders(self):

        # Create menu folders

        try:
            os.makedirs(self.user_menu_path)
            os.makedirs(self.project_menu_path)
        except:
            pass

    def refresh_bin_menus(self):
        import flame

        # Delete all existing node menus

        self.delete_existing_menus(self.user_menu_path)
        self.delete_existing_menus(self.project_menu_path)

        print ('>>> Existing menus deleted <<<\n')

        self.create_menu_folders()

        # Create menus for bin nodes

        self.create_bin_menus(self.user_bin_path, 'user', self.user_menu_path)
        self.create_bin_menus(self.project_bin_path, 'project', self.project_menu_path)

        # Refresh python hooks

        flame.execute_shortcut('Rescan Python Hooks')

        print ('>>> Menus updated <<<\n')

        print ('Done.\n')

    def delete_existing_menus(self, menu_path):

        shutil.rmtree(menu_path)

    def create_bin_menus(self, bin_path, bin_type, menu_path):

        # Create list of bin nodes

        bin_node_list = [n for n in os.listdir(bin_path) if n.endswith('.batch')]

        for node in bin_node_list:
            node_name = node.split('.', 2)[1]

            # Read menu template file

            template = open(self.node_template_path, 'r')
            template_lines = template.read().splitlines()

            # Replace tokens in template

            token_dict = {}

            token_dict['<BinNode>'] = node_name
            token_dict['<ScriptVersion>'] = VERSION[1:]
            token_dict['<BinNodeSetupPath>'] = bin_path + '/_' + bin_type + '.' + node_name + '.batch'
            token_dict['<ScriptPath>'] = menu_path
            token_dict['<BinType>'] = bin_type[0].upper() + bin_type[1:]

            # Replace tokens in menu template

            for key, value in token_dict.items():
                for line in template_lines:
                    if key in line:
                        line_index = template_lines.index(line)
                        new_line = re.sub(key, value, line)
                        template_lines[line_index] = new_line

            # Write out temp node

            new_node_script_path = os.path.join(menu_path, node_name + '.py')

            out_file = open(new_node_script_path, 'w')
            for line in template_lines:
                print(line, file=out_file)
            out_file.close()

def refresh_on_launch(project_name):

    script = BinMenus(project_name)
    script.refresh_bin_menus()

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

    print ('>>> %s <<<\n' % message)

def user_bin_scope(selection):
    import flame

    bin_nodes = [f for f in os.listdir(os.path.join('/opt/Autodesk/user', flame.users.current_user.name, 'batch/pref')) if f.endswith('.batch')]

    if bin_nodes:
        return True
    menu_dir = os.path.join(SCRIPT_PATH, 'user_bin_menus')
    for menu in os.listdir(menu_dir):
        os.remove(os.path.join(menu_dir, menu))
    return False

def project_bin_scope(selection):
    import flame

    bin_nodes = [f for f in os.listdir(os.path.join('/opt/Autodesk/project', flame.projects.current_project.name, 'batch/pref')) if f.endswith('.batch')]

    if bin_nodes:
        return True
    menu_dir = os.path.join(SCRIPT_PATH, 'project_bin_menus')
    for menu in os.listdir(menu_dir):
        os.remove(os.path.join(menu_dir, menu))
    return False

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Bin: User',
            'actions': [
                {
                    'name': 'Create/Refresh Bin Menus',
                    'isVisible': user_bin_scope,
                    'execute': BinMenus,
                    'minimumVersion': '2022'
                }
            ]
        },
        {
            'name': 'Bin: Project',
            'actions': [
                {
                    'name': 'Create/Refresh Bin Menus',
                    'isVisible': project_bin_scope,
                    'execute': BinMenus,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def app_initialized(project_name):
    refresh_on_launch(project_name)

