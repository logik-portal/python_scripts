'''
Script Name: Batch Nodes
Script Version: 3.4
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 04.18.20
Update Date: 05.31.22

Custom Action Type: Batch / Flame Main Menu

Description:

    Add menus to batch right-click for your favorite nodes.

    Works with standard batch nodes/matchboxes/ofx.

    OFX can only be added by right clicking on an existing node in batch.

    Nodes added by right-clicking on them in batch will be saved with current settings.

    All created node menu scripts are saved in /opt/Autodesk/user/YOURUSER/python/batch_node_menus

Menus:

    To create/rename/delete menus from node lists:

        Flame Main Menu -> pyFlame -> Batch Nodes Setup

    To create menus for nodes with settings applied in batch:

        Right-click on node in batch -> Batch Nodes... -> Create Menu For Selected Node

    To create menus for ofx nodes:

        Right-click on node in batch -> Batch Nodes... -> Create Menu For Selected Node

    To add node from menu to batch:

        Right-click in batch -> Batch Nodes... -> Select Node to be added

    To add node from menu to batch connected to selected node:

        Right-click on node in batch -> Batch Nodes... -> Select Node to be added

To install:

    Copy script into /opt/Autodesk/shared/python/batch_nodes

Updates:

    v3.4 05.31.22

        Messages print to Flame message window - Flame 2023.1 and later

        Flame file browser used to select folders - Flame 2023.1 and later

    v3.3 03.31.22

        UI widgets moved to external file

        Misc bug fixes

    v3.2 03.07.22

        Updated UI for Flame 2023

    v3.1 10.26.21

        Updated config to xml

    v3.0 05.20.21

        Updated to be compatible with Flame 2022/Python 3.7

    v2.5 01.27.21:

        Updated UI

        Menus/Nodes can be renamed after they've been added

    v2.1 05.17.20:

        Misc code updates
'''

import xml.etree.ElementTree as ET
from functools import partial
import os, re, shutil
from PySide2 import QtWidgets, QtCore
from pyflame_lib_batch_nodes import FlameLabel, FlameListWidget, FlameButton, FlameLineEdit, FlameWindow, FlameMessageWindow, pyflame_file_browser, pyflame_print

SCRIPT_NAME = 'Batch Nodes'
SCRIPT_PATH = '/opt/Autodesk/shared/python/batch_nodes'
VERSION = 'v3.4'

class BatchNodes():

    def __init__(self, selection):
        import flame

        print ('\n')
        print ('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

        # Set paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.save_selected_template = os.path.join(SCRIPT_PATH, 'save_selected')
        self.create_node_template = os.path.join(SCRIPT_PATH, 'create_node')

        self.config()

        # Get flame variables

        self.selection = selection

        self.flame_version = flame.get_version()
        self.current_user = flame.users.current_user.name

        self.matchbox_path = f'/opt/Autodesk/presets/{self.flame_version}/matchbox/shaders'

        # Check/create folder to store node scripts in user python folder

        self.node_dir = os.path.join('/opt/Autodesk/user', self.current_user, 'python/batch_node_menus/nodes')
        if not os.path.isdir(self.node_dir):
            os.makedirs(self.node_dir)
            pyflame_print(SCRIPT_NAME, f'Created user node folder: {self.node_dir}')

        if not os.path.isdir(self.logik_path):
            pyflame_print(SCRIPT_NAME, f'Logik matchbox path no longer exists. Set new path in setup.')
            self.logik_path = '/'

        #  Init variables

        self.create_node_line = ''

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('add_batch_nodes_settings'):
                self.logik_path = setting.find('logik_path').text

            pyflame_print(SCRIPT_NAME, 'Config loaded.')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', f'Unable to create folder: {self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file ')

                config = """
<settings>
    <add_batch_nodes_settings>
        <logik_path>/</logik_path>
    </add_batch_nodes_settings>
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

    def main_window(self):

        vbox = QtWidgets.QVBoxLayout()
        self.window = FlameWindow(f'{SCRIPT_NAME} <small>{VERSION}', vbox, 800, 570)

        # Tabs

        self.main_tabs = QtWidgets.QTabWidget()

        self.window.tab1 = QtWidgets.QWidget()
        self.window.tab2 = QtWidgets.QWidget()
        self.window.tab3 = QtWidgets.QWidget()

        self.main_tabs.addTab(self.window.tab1, 'Batch Node List')
        self.main_tabs.addTab(self.window.tab2, 'Matchbox List')
        self.main_tabs.addTab(self.window.tab3, 'Logik List')

        self.batch_node_tab()
        self.matchbox_tab()
        self.logik_tab()

        # Widget Layout

        vbox.setMargin(20)
        vbox.addWidget(self.main_tabs)

        self.window.show()

    def batch_node_tab(self):

        def add_batch_node():

            # Create scripts for nodes in selected list

            for node in self.batch_node_list.selectedItems():
                self.node_name = node.text()

                self.create_node_line = f"new_node = flame.batch.create_node('{self.node_name}')"

                self.create_node()

            # Refresh node menu lists

            self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        # Labels

        self.batch_node_label = FlameLabel('Batch Node Menus', label_type='underline', label_width=110)
        self.batch_node_list_label = FlameLabel('Batch Nodes', label_type='underline', label_width=110)

        # Listboxes

        self.node_menu_list = FlameListWidget()
        self.get_node_scripts_lists(self.node_menu_list, self.node_dir)

        self.batch_node_list = FlameListWidget()
        self.get_batch_node_list()

        # Buttons

        self.batch_add_btn = FlameButton('Add', add_batch_node, button_width=110)
        self.batch_remove_btn = FlameButton('Remove', partial(self.remove_scripts, self.node_menu_list), button_width=110)
        self.batch_rename_btn = FlameButton('Rename', partial(self.rename_menu, self.node_menu_list), button_width=110)
        self.batch_done_btn = FlameButton('Done', self.done_button, button_width=110)

        # List context menu

        self.batch_action_add_node = QtWidgets.QAction('Add Node')
        self.batch_action_add_node.triggered.connect(add_batch_node)
        self.batch_node_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.batch_node_list.addAction(self.batch_action_add_node)

        self.action_remove_node = QtWidgets.QAction('Remove Node/Menu')
        self.action_remove_node.triggered.connect(partial(self.remove_scripts, self.node_menu_list))
        self.node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.node_menu_list.addAction(self.action_remove_node)

        self.action_rename_node = QtWidgets.QAction('Rename Node/Menu')
        self.action_rename_node.triggered.connect(partial(self.rename_menu, self.node_menu_list))
        self.node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.node_menu_list.addAction(self.action_rename_node)

        #  Tab layout

        self.batch_gridbox = QtWidgets.QGridLayout()

        self.batch_gridbox.addWidget(self.batch_node_label, 0, 0)
        self.batch_gridbox.addWidget(self.batch_node_list, 1, 1, 6, 1)

        self.batch_gridbox.addWidget(self.batch_node_list_label, 0, 1)
        self.batch_gridbox.addWidget(self.node_menu_list, 1, 0, 6, 1)

        self.batch_gridbox.addWidget(self.batch_add_btn, 1, 2)
        self.batch_gridbox.addWidget(self.batch_remove_btn, 2, 2)
        self.batch_gridbox.addWidget(self.batch_rename_btn, 3, 2)
        self.batch_gridbox.addWidget(self.batch_done_btn, 6, 2)

        self.window.tab1.layout = QtWidgets.QHBoxLayout()
        self.window.tab1.layout.setMargin(20)
        self.window.tab1.layout.addLayout(self.batch_gridbox)

        self.window.tab1.setLayout(self.window.tab1.layout)

    def matchbox_tab(self):

        def add_matchbox():

            # Create scripts for nodes in selected list

            for node in self.matchbox_list.selectedItems():
                self.node_name = node.text()

                matchbox_node_path = os.path.join(self.matchbox_path, node.text())

                self.create_node_line = f"new_node = flame.batch.create_node('Matchbox', '{matchbox_node_path}.mx')"

                self.create_node()

            # Refresh node menu lists

            self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        # Labels

        self.matchbox_node_label = FlameLabel('Batch Node Menus', label_type='underline', label_width=110)
        self.matchbox_node_list_label = FlameLabel('Autodesk Matchbox', label_type='underline', label_width=110)

        # Listboxes

        self.matchbox_node_menu_list = FlameListWidget()
        self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)

        self.matchbox_list = FlameListWidget()
        self.get_matchbox_list()

        # Buttons

        self.matchbox_add_btn = FlameButton('Add', add_matchbox, button_width=110)
        self.matchbox_remove_node_btn = FlameButton('Remove', partial(self.remove_scripts, self.matchbox_node_menu_list), button_width=110)
        self.matchbox_rename_btn = FlameButton('Rename', partial(self.rename_menu, self.matchbox_node_menu_list), button_width=110)
        self.matchbox_done_btn = FlameButton('Done', self.done_button, button_width=110)

        # List context menu

        self.matchbox_action_add_node = QtWidgets.QAction('Add Node')
        self.matchbox_action_add_node.triggered.connect(add_matchbox)
        self.matchbox_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.matchbox_list.addAction(self.matchbox_action_add_node)

        self.action_remove_node = QtWidgets.QAction('Remove Node')
        self.action_remove_node.triggered.connect(partial(self.remove_scripts, self.matchbox_node_menu_list))
        self.matchbox_node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.matchbox_node_menu_list.addAction(self.action_remove_node)

        self.action_rename_node = QtWidgets.QAction('Rename Node/Menu')
        self.action_rename_node.triggered.connect(partial(self.rename_menu, self.matchbox_node_menu_list))
        self.matchbox_node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.matchbox_node_menu_list.addAction(self.action_rename_node)

        #  Tab layout

        self.matchbox_gridbox = QtWidgets.QGridLayout()

        self.matchbox_gridbox.addWidget(self.matchbox_node_label, 0, 0)
        self.matchbox_gridbox.addWidget(self.matchbox_list, 1, 1, 6, 1)

        self.matchbox_gridbox.addWidget(self.matchbox_node_list_label, 0, 1)
        self.matchbox_gridbox.addWidget(self.matchbox_node_menu_list, 1, 0, 6, 1)

        self.matchbox_gridbox.addWidget(self.matchbox_add_btn, 1, 2)
        self.matchbox_gridbox.addWidget(self.matchbox_remove_node_btn, 2, 2)
        self.matchbox_gridbox.addWidget(self.matchbox_rename_btn, 3, 2)
        self.matchbox_gridbox.addWidget(self.matchbox_done_btn, 6, 2)

        self.window.tab2.layout = QtWidgets.QHBoxLayout()
        self.window.tab2.layout.setMargin(20)
        self.window.tab2.layout.addLayout(self.matchbox_gridbox)

        self.window.tab2.setLayout(self.window.tab2.layout)

    def logik_tab(self):

        def add_logik_matchbox():

            # Create scripts for nodes in selected list

            for node in self.logik_list.selectedItems():

                self.node_name = node.text()

                logik_node_path = os.path.join(self.logik_path, node.text())
                print ('logik_node_path:', logik_node_path)

                self.create_node_line = f"new_node = flame.batch.create_node('Matchbox', '{logik_node_path}.glsl')"

                self.create_node()

            # Refresh node menu lists

            self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        def set_path():

            path = pyflame_file_browser('Select Logik Matchbox Directory', [''], self.logik_path, select_directory=True, window_to_hide=[self.window])

            if path:
                self.logik_path = path

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                logik_path = root.find('.//logik_path')
                logik_path.text = self.logik_path

                xml_tree.write(self.config_xml)

                pyflame_print(SCRIPT_NAME, 'Config saved.')

                self.window.close()

                self.config()

                self.main_window()

                self.main_tabs.setCurrentIndex(2)

        # Labels

        self.logik_node_label = FlameLabel('Batch Node Menus', label_type='underline', label_width=110)
        self.logik_node_list_label = FlameLabel('Logik Matchbox', label_type='underline', label_width=110)

        # Listboxes

        self.logik_node_menu_list = FlameListWidget()
        self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        self.logik_list = FlameListWidget()
        self.get_logik_list()

        # Buttons

        self.logik_setup_btn = FlameButton('Set Path', set_path, button_width=110)
        self.logik_add_btn = FlameButton('Add', add_logik_matchbox, button_width=110)
        self.logik_remove_btn = FlameButton('Remove', partial(self.remove_scripts, self.logik_node_menu_list), button_width=110)
        self.logik_rename_btn = FlameButton('Rename', partial(self.rename_menu, self.logik_node_menu_list), button_width=110)
        self.logik_done_btn = FlameButton('Done', self.done_button, button_width=110)

        # List context menu

        self.logik_action_add_node = QtWidgets.QAction('Add Node')
        self.logik_action_add_node.triggered.connect(add_logik_matchbox)
        self.logik_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.logik_list.addAction(self.logik_action_add_node)

        self.logik_action_remove_node = QtWidgets.QAction('Remove Node')
        self.logik_action_remove_node.triggered.connect(partial(self.remove_scripts, self.logik_node_menu_list))
        self.logik_node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.logik_node_menu_list.addAction(self.logik_action_remove_node)

        self.action_rename_node = QtWidgets.QAction('Rename Node/Menu')
        self.action_rename_node.triggered.connect(partial(self.rename_menu, self.logik_node_menu_list))
        self.logik_node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.logik_node_menu_list.addAction(self.action_rename_node)

        #  Tab layout

        self.matchbox_gridbox = QtWidgets.QGridLayout()

        self.matchbox_gridbox.addWidget(self.logik_node_label, 0, 0)
        self.matchbox_gridbox.addWidget(self.logik_list, 1, 1, 6, 1)

        self.matchbox_gridbox.addWidget(self.logik_node_list_label, 0, 1)
        self.matchbox_gridbox.addWidget(self.logik_node_menu_list, 1, 0, 6, 1)

        self.matchbox_gridbox.addWidget(self.logik_setup_btn, 0, 2)
        self.matchbox_gridbox.addWidget(self.logik_add_btn, 1, 2)
        self.matchbox_gridbox.addWidget(self.logik_remove_btn, 2, 2)
        self.matchbox_gridbox.addWidget(self.logik_rename_btn, 3, 2)
        self.matchbox_gridbox.addWidget(self.logik_done_btn, 6, 2)

        self.window.tab3.layout = QtWidgets.QHBoxLayout()
        self.window.tab3.layout.setMargin(20)
        self.window.tab3.layout.addLayout(self.matchbox_gridbox)

        self.window.tab3.setLayout(self.window.tab3.layout)

    # ----------------------- #

    def get_batch_node_list(self):
        import flame

        for node in flame.batch.node_types:

            # badNodes crash flame when connecting

            bad_nodes = 'Colour Blend', 'Matte Blend'

            if node not in bad_nodes:
                self.batch_node_list.addItem(node)

    def get_matchbox_list(self):

        matchboxes = os.listdir(self.matchbox_path)
        matchboxes.sort()

        for m in matchboxes:
            if not m.startswith('.'):
                if m.endswith('.mx'):
                    m = m[:-3]
                    self.matchbox_list.addItem(m)

    def get_logik_list(self):

        logik_matchboxes = os.listdir(self.logik_path)
        logik_matchboxes.sort()

        for l in logik_matchboxes:
            if l.endswith('.glsl'):
                l = l[:-5]
                self.logik_list.addItem(l)

    def done_button(self):
        import flame

        # Close window and refresh hooks

        self.window.close()

        flame.execute_shortcut('Rescan Python Hooks')

        pyflame_print(SCRIPT_NAME, 'Python hooks refreshed.')

    # ----------------------- #

    def get_node_scripts_lists(self, listbox, folder):

        #  Get list of scripts for nodes

        listbox.clear()

        item_list = os.listdir(folder)
        item_list.sort()

        for item in item_list:
            if item.endswith('.py'):
                item = item[:-3]

                listbox.addItem(item)

    def remove_scripts(self, listbox):

        # Delete script files

        selected_nodes = listbox.selectedItems()

        selected_node_text = []

        for node in selected_nodes:
            node = node.text()
            selected_node_text.append(node)

        file_list = os.listdir(self.node_dir)

        for node in selected_node_text:
            for f in file_list:
                if node in f:
                    try:
                        os.remove(os.path.join(self.node_dir, f))
                    except:
                        shutil.rmtree(os.path.join(self.node_dir, f))
                    pyflame_print(SCRIPT_NAME, f'{f} deleted.')

        self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
        self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
        self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

    # ----------------------- #

    def rename_menu(self, menu_list):

        def rename():
            import flame

            def edit_menu_file(new_menu_name):

                # Edit python menu file to change menu name

                menu_script_path = os.path.join(self.node_dir, selected_menu + '.py')

                menu_lines = open(menu_script_path, 'r')
                lines = menu_lines.read().splitlines()

                menu_lines.close()

                for l in lines:
                    if selected_menu in l:
                        if 'flame.batch.create_node' not in l:
                            line_index = lines.index(l)
                            new_line = l.replace(selected_menu, new_menu_name)
                            lines[line_index] = new_line

                out_file = open(menu_script_path, 'w')
                for line in lines:
                    print(line, file=out_file)
                out_file.close()

            def rename_node_files(new_menu_name):

                # Rename saved node directory if it exists

                for root, dirs, files in os.walk(self.node_dir):
                    for d in dirs:
                        if d == selected_menu:
                            current_dir = os.path.join(root, d)
                            new_dir = current_dir.replace(selected_menu, new_menu_name)
                            os.rename(current_dir, new_dir)

                            # iterate through files in saved setup directory to change file names

                            for file_name in os.listdir(new_dir):
                                if selected_menu in file_name:
                                    new_file_name = file_name.replace(selected_menu, new_menu_name)
                                    os.rename(os.path.join(new_dir, file_name), os.path.join(new_dir, new_file_name))

                # Rename python file and saved setup if it exists

                for f in os.listdir(self.node_dir):
                    if f == selected_menu + '.py':
                        os.rename(os.path.join(self.node_dir, selected_menu + '.py'), os.path.join(self.node_dir, new_menu_name + '.py'))
                    if f == selected_menu + '.pyc':
                        os.rename(os.path.join(self.node_dir, selected_menu + '.pyc'), os.path.join(self.node_dir, new_menu_name + '.pyc'))

            if not new_name_entry.text():
                return

            if new_name_entry.text() == selected_menu:
                if not FlameMessageWindow('warning', f'{SCRIPT_NAME}: Confirm Operation', f'Overwrite existing menu: <b>{selected_menu}?'):
                    return

            new_menu_name = new_name_entry.text()

            edit_menu_file(new_menu_name)

            rename_node_files(new_menu_name)

            self.node_menu_list.clear()
            self.matchbox_node_menu_list.clear()
            self.logik_node_menu_list.clear()

            self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

            flame.execute_shortcut('Rescan Python Hooks')

            pyflame_print(SCRIPT_NAME, f'Python hooks refreshed.')

            pyflame_print(SCRIPT_NAME, f'Menu renamed.')

            rename_window.close()

        if not menu_list.selectedItems():
            return

        selected_menu = [m.text() for m in menu_list.selectedItems()][0]

        gridlayout = QtWidgets.QGridLayout()
        rename_window = FlameWindow(f'{SCRIPT_NAME}: Rename Menu', gridlayout, 450, 170, window_bar_color='green')

        #  Labels

        new_name_label = FlameLabel('Menu Name', label_width=75)

        # Entries

        new_name_entry = FlameLineEdit(selected_menu)

        # Buttons

        rename_btn = FlameButton('Rename', rename)
        cancel_btn = FlameButton('Cancel', rename_window.close)

        #------------------------------------#

        # UI Widget Layout

        gridlayout.addWidget(new_name_label, 0, 0)
        gridlayout.addWidget(new_name_entry, 0, 1, 1, 3)
        gridlayout.addWidget(cancel_btn, 1, 1)
        gridlayout.addWidget(rename_btn, 1, 2)

        rename_window.setLayout(gridlayout)

        rename_window.show()

    def create_node(self):

        def create_node_script():

            def replace_tokens():

                token_dict = {}

                token_dict['<NodeName>'] = node_name
                token_dict['<CreateNodeLine>'] = self.create_node_line
                token_dict['<Version>'] = VERSION

                # Replace tokens in menu template

                for key, value in token_dict.items():
                    for line in template_lines:
                        if key in line:
                            line_index = template_lines.index(line)
                            new_line = re.sub(key, value, line)
                            template_lines[line_index] = new_line

            # Read template

            template = open(self.create_node_template, 'r')
            template_lines = template.read().splitlines()

            # Replace tokens in template

            replace_tokens()

            # Write out temp node

            out_file = open(node_script, 'w')
            for line in template_lines:
                print(line, file=out_file)
            out_file.close()

        # Create node scripts for selected nodes

        node_name = self.node_name.replace('.', '_')
        #print ('node_name:', node_name, '\n')

        node_script = os.path.join(self.node_dir, node_name) + '.py'

        # Create script for new node

        create_node_script()

        pyflame_print(SCRIPT_NAME, f'Node script for {node_name} saved.')

    def save_selected_node(self):

        def create_node_script():

            def replace_tokens():

                token_dict = {}

                token_dict['<NodeName>'] = node_name
                token_dict['<NodeType>'] = node_type
                token_dict['<NodeSetupPathName>'] = node_setup_path_name
                token_dict['<Version>'] = VERSION

                # Replace tokens in menu template

                for key, value in token_dict.items():
                    for line in template_lines:
                        if key in line:
                            line_index = template_lines.index(line)
                            new_line = re.sub(key, value, line)
                            template_lines[line_index] = new_line

            # Read template

            template = open(self.save_selected_template, 'r')
            template_lines = template.read().splitlines()

            # Replace tokens in template

            replace_tokens()

            # Write out temp node

            out_file = open(node_script, 'w')
            for line in template_lines:
                print(line, file=out_file)
            out_file.close()

        selected_node = self.selection[0]

        node_name = str(selected_node.name)[1:-1]

        # Check user python folder for existing node script

        create_node = True

        for n in os.listdir(self.node_dir):
            if n == node_name:
                create_node = FlameMessageWindow('warning', f'{SCRIPT_NAME}: Confirm Operation', f'Overwrite existing menu: <b>{node_name}?')

        if create_node:
            node_type = str(selected_node.type)[1:-1]
            #print ('node_type:', node_type)

            # Create folder to save node setup

            node_setup_path = os.path.join(self.node_dir, node_name)
            #print ('node_setup_path:', node_setup_path, '\n')

            try:
                os.makedirs(node_setup_path)
                pyflame_print(SCRIPT_NAME, f'{node_name} node folder created')
            except:
                pyflame_print(SCRIPT_NAME, f'{node_name} node folder already exists - overwriting setup')

            # Save node setup

            node_setup_path_name = os.path.join(node_setup_path, node_name)
            selected_node.save_node_setup(node_setup_path_name)

            # Set script path

            node_script = os.path.join(self.node_dir, node_name) + '.py'

            # Create script for new node

            create_node_script()

            FlameMessageWindow('message', f'{SCRIPT_NAME}: Operation Complete', f'Menu created: <b>{node_name}')

        else:
            pyflame_print(SCRIPT_NAME, 'Node already exists - Nothing saved .')

# ----------------------- #

def edit_node_lists(selection):

    script = BatchNodes(selection)
    script.main_window()

def save_node(selection):

    script = BatchNodes(selection)
    script.save_selected_node()

# ----------------------- #

def scope_node(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyNode):
            return True
    return False

# ----------------------- #

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Batch Nodes Setup',
                    'execute': edit_node_lists,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Batch Nodes...',
            'actions': [
                {
                    'name': 'Create Menu for Selected Node',
                    'isVisible': scope_node,
                    'execute': save_node,
                    'minimumVersion': '2022'
                },
                {
                    'name': '--------------------------------------',
                    'isVisible': scope_node,
                }
            ]
        }
    ]
