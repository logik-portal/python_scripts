'''
Script Name: Add Batch Nodes
Script Version: 3.0
Flame Version: 2021
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 04.18.20
Update Date: 05.20.21

Custom Action Type: Batch / Flame Main Menu

Description:

    Create menus that can add nodes to batch

    Works with standard batch nodes/matchboxes/ofx

    All created node menu scripts are saved in /opt/Autodesk/user/YOURUSER/python/batch_node_menus

    To create/rename/delete menus from node lists:
    Flame Main Menu -> pyFlame -> Add Batch Nodes Setup

    To create menus for nodes with settings applied in batch:
    Right-click on node in batch -> Add Batch Node Menu... -> Create Menu For Selected Node

    To create menus for ofx nodes:
    Right-click on node in batch -> Add Batch Node Menu... -> Create Menu Dor Selected Node

    To add node from menu to batch:
    Right-click in batch -> Add Batch Nodes... -> Select Node

    To add node from menu to batch connected to selected node:
    Right-click on node in batch -> Add Batch Nodes... -> Select Node

To install:

    Copy script into /opt/Autodesk/shared/python/add_batch_nodes

Updates:

v3.0 05.20.21

    Updated to be compatible with Flame 2022/Python 3.7

v2.5 01.27.21:

    Updated UI

    Menus/Nodes can be renamed after they've been added

v2.1 05.17.20:

    Misc code updates
'''

from __future__ import print_function
from functools import partial
import shutil
import os
from PySide2 import QtWidgets, QtCore
import flame

VERSION = 'v3.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/add_batch_nodes'

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget

    For different label looks use: 'normal', 'background', or 'outline'

    To use:

    label = FlameLabel('Label Name', 'normal', window)
    """

    def __init__(self, label_name, label_type, parent_window, *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent_window)
        self.setMinimumSize(300, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setAlignment(QtCore.Qt.AlignCenter)

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
        self.setMinimumWidth(300)
        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
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
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

class FlameListWidget(QtWidgets.QListWidget):
    """
    Custom Qt Flame List Widget

    To use:

    list_widget = FlameListWidget(window)
    """

    def __init__(self, parent_window, *args, **kwargs):
        super(FlameListWidget, self).__init__(*args, **kwargs)

        self.setMaximumSize(300, 450)
        self.setParent(parent_window)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.clear()
        self.setAcceptDrops(True)
        self.setAlternatingRowColors(True)
        self.setCurrentRow(0)
        self.setStyleSheet('QListWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; outline: none; font: 14px "Discreet"}'
                           'QListWidget::item:selected {color: #d9d9d9; background-color: #474747}')

# -------------------------------------- #

class BatchNodes(object):

    def __init__(self, selection):

        print ('\n', '>' * 20, 'batch node menus %s' % VERSION, '<' * 20, '\n')

        # Set paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')

        self.save_selected_template = os.path.join(SCRIPT_PATH, 'save_selected')
        print ('save_selected_template:', self.save_selected_template)

        self.create_node_template = os.path.join(SCRIPT_PATH, 'create_node')
        print ('create_node:', self.create_node_template)

        self.check_config_file()

        # Get flame variables

        self.selection = selection

        self.flame_version = flame.get_version()
        print ('flameVersion:', self.flame_version)

        self.current_user = flame.users.current_user.name
        print ('current_user:', self.current_user)

        self.matchbox_path = '/opt/Autodesk/presets/%s/matchbox/shaders' % self.flame_version
        print ('matchbox_path:', self.matchbox_path)

        # Check/create folder to store node scripts in user python folder

        self.node_dir = os.path.join('/opt/Autodesk/user', self.current_user, 'python/batch_node_menus/nodes')
        if not os.path.isdir(self.node_dir):
            os.makedirs(self.node_dir)
            print ('>>> created user node folder <<<')

        # Load config file values

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()
        self.logik_path = values[2]
        get_config_values.close()

        if not os.path.isdir(self.logik_path):
            print ('\n>>> logik matchbox path no longer exists - set new path in setup <<<\n')
            self.logik_path = '/'

        #  Init variables

        self.create_node_line = ''

    def check_config_file(self):

        # Check for and load config file
        #-------------------------------

        if not os.path.isdir(self.config_path):
            try:
                os.makedirs(self.config_path)
            except:
                message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)

        if not os.path.isfile(self.config_file):
            print ('>>> config file does not exist, creating new config file <<<')

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame add batch nodes script.')
            config_text.insert(1, 'Logik Path:')
            config_text.insert(2, '/')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

    def main_window(self):

        self.window = QtWidgets.QTabWidget()
        self.window.setMinimumSize(QtCore.QSize(775, 500))
        self.window.setMaximumSize(QtCore.QSize(775, 500))
        self.window.setWindowTitle('Add Batch Nodes %s' % VERSION)
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

        self.window.addTab(self.window.tab1, 'Batch Node List')
        self.window.addTab(self.window.tab2, 'Matchbox List')
        self.window.addTab(self.window.tab3, 'Logik List')

        self.batch_node_tab()
        self.matchbox_tab()
        self.logik_tab()

        self.window.setStyleSheet('QTabWidget {background-color: #212121; font: 14px "Discreet"}'
                                  'QTabWidget::tab-bar {alignment: center}'
                                  'QTabBar::tab {color: #9a9a9a; background-color: #212121; border: 1px solid #3a3a3a; border-bottom-color: #555555; min-width: 20ex; padding: 5px}'
                                  'QTabBar::tab:selected {color: #bababa; border: 1px solid #555555; border-bottom: 1px solid #212121}'
                                  'QTabWidget::pane {border-top: 1px solid #555555; top: -0.05em}')

        #------------------------------------#

        # Window Layout

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setMargin(20)

        self.vbox.addLayout(self.window.tab1.layout)
        self.vbox.addLayout(self.window.tab2.layout)
        self.vbox.addLayout(self.window.tab3.layout)

        self.window.setLayout(self.vbox)

        self.window.show()

    def batch_node_tab(self):

        def add_batch_node():

            # Create scripts for nodes in selected list

            for node in self.batch_node_list.selectedItems():
                self.node_name = node.text()

                self.create_node_line = "new_node = flame.batch.create_node('%s')" % self.node_name

                self.create_node()

            # Refresh node menu lists

            self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        # Labels

        self.batch_node_label = FlameLabel('Batch Node Menus', 'background', self.window.tab1)
        self.batch_node_list_label = FlameLabel('Batch Nodes', 'background', self.window.tab1)

        # Listboxes

        self.node_menu_list = FlameListWidget(self.window.tab1)
        self.get_node_scripts_lists(self.node_menu_list, self.node_dir)


        self.batch_node_list = FlameListWidget(self.window.tab1)
        self.get_batch_node_list()

        # Buttons

        self.batch_add_btn = FlameButton('Add', add_batch_node, self.window.tab1)
        self.batch_remove_btn = FlameButton('Remove', partial(self.remove_scripts, self.node_menu_list, self.node_dir), self.window.tab1)
        self.batch_rename_btn = FlameButton('Rename', partial(self.rename_menu, self.node_menu_list, self.node_dir), self.window.tab1)
        self.batch_done_btn = FlameButton('Done', self.done_button, self.window.tab1)

        # List context menu

        self.batch_action_add_node = QtWidgets.QAction('Add Node', self.window.tab1)
        self.batch_action_add_node.triggered.connect(add_batch_node)
        self.batch_node_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.batch_node_list.addAction(self.batch_action_add_node)

        self.action_remove_node = QtWidgets.QAction('Remove Node/Menu', self.window.tab1)
        self.action_remove_node.triggered.connect(partial(self.remove_scripts, self.node_menu_list, self.node_dir))
        self.node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.node_menu_list.addAction(self.action_remove_node)

        self.action_rename_node = QtWidgets.QAction('Rename Node/Menu', self.window.tab1)
        self.action_rename_node.triggered.connect(partial(self.rename_menu, self.node_menu_list, self.node_dir))
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
                print ('matchbox_node_path:', matchbox_node_path)

                self.create_node_line = "new_node = flame.batch.create_node('Matchbox', '%s.mx')" % matchbox_node_path

                self.create_node()

            # Refresh node menu lists

            self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        # Labels

        self.matchbox_node_label = FlameLabel('Batch Node Menus', 'background', self.window.tab2)
        self.matchbox_node_list_label = FlameLabel('Autodesk Matchbox', 'background', self.window.tab2)

        # Listboxes

        self.matchbox_node_menu_list = FlameListWidget(self.window.tab2)
        self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)

        self.matchbox_list = FlameListWidget(self.window.tab2)
        self.get_matchbox_list()

        # Buttons

        self.matchbox_add_btn = FlameButton('Add', add_matchbox, self.window.tab2)
        self.matchbox_remove_node_btn = FlameButton('Remove', partial(self.remove_scripts, self.matchbox_node_menu_list, self.node_dir), self.window.tab2)
        self.matchbox_rename_btn = FlameButton('Rename', partial(self.rename_menu, self.matchbox_node_menu_list, self.node_dir), self.window.tab2)
        self.matchbox_done_btn = FlameButton('Done', self.done_button, self.window.tab2)

        # List context menu

        self.matchbox_action_add_node = QtWidgets.QAction('Add Node', self.window.tab2)
        self.matchbox_action_add_node.triggered.connect(add_matchbox)
        self.matchbox_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.matchbox_list.addAction(self.matchbox_action_add_node)

        self.action_remove_node = QtWidgets.QAction('Remove Node', self.window.tab2)
        self.action_remove_node.triggered.connect(partial(self.remove_scripts, self.matchbox_node_menu_list, self.node_dir))
        self.matchbox_node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.matchbox_node_menu_list.addAction(self.action_remove_node)

        self.action_rename_node = QtWidgets.QAction('Rename Node/Menu', self.window.tab2)
        self.action_rename_node.triggered.connect(partial(self.rename_menu, self.matchbox_node_menu_list, self.node_dir))
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

                self.create_node_line = "new_node = flame.batch.create_node('Matchbox', '%s.glsl')" % logik_node_path

                self.create_node()

            # Refresh node menu lists

            self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
            self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        # Labels

        self.logik_node_label = FlameLabel('Batch Node Menus', 'background', self.window.tab3)
        self.logik_node_list_label = FlameLabel('Logik Matchbox', 'background', self.window.tab3)

        # Listboxes

        self.logik_node_menu_list = FlameListWidget(self.window.tab3)
        self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

        self.logik_list = FlameListWidget(self.window.tab3)
        self.get_logik_list()

        # Buttons

        self.logik_setup_btn = FlameButton('Setup', self.setup_window, self.window.tab3)
        self.logik_add_btn = FlameButton('Add', add_logik_matchbox, self.window.tab3)
        self.logik_remove_btn = FlameButton('Remove', partial(self.remove_scripts, self.logik_node_menu_list, self.node_dir), self.window.tab3)
        self.logik_rename_btn = FlameButton('Rename', partial(self.rename_menu, self.logik_node_menu_list, self.node_dir), self.window.tab3)
        self.logik_done_btn = FlameButton('Done', self.done_button, self.window.tab3)

        # List context menu

        self.logik_action_add_node = QtWidgets.QAction('Add Node', self.window.tab2)
        self.logik_action_add_node.triggered.connect(add_logik_matchbox)
        self.logik_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.logik_list.addAction(self.logik_action_add_node)

        self.logik_action_remove_node = QtWidgets.QAction('Remove Node', self.window.tab2)
        self.logik_action_remove_node.triggered.connect(partial(self.remove_scripts, self.logik_node_menu_list, self.node_dir))
        self.logik_node_menu_list.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.logik_node_menu_list.addAction(self.logik_action_remove_node)

        self.action_rename_node = QtWidgets.QAction('Rename Node/Menu', self.window.tab3)
        self.action_rename_node.triggered.connect(partial(self.rename_menu, self.logik_node_menu_list, self.node_dir))
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

    def setup_window(self):

        def logik_browse():
            global logik_path

            logik_path_saved = logik_path_entry.text()

            logik_path = str(QtWidgets.QFileDialog.getExistingDirectory(setup_window, "Select Directory", logik_path_saved, QtWidgets.QFileDialog.ShowDirsOnly))

            if logik_path != '':
                logik_path_entry.setText(logik_path)
            else:
                logik_path_entry.setText(logik_path_saved)

        def setup_save():

            self.logik_path = logik_path_entry.text()

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame batch nodes script.')
            config_text.insert(1, 'Logik Path:')
            config_text.insert(2, self.logik_path)

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

            print ('\n>>> config file saved <<<\n')

            setup_window.close()

            self.main_window()

        def cancel():

            setup_window.close()

            print ('\n>>> setup cancelled - nothing saved <<<\n')

        setup_window = QtWidgets.QWidget()
        setup_window.setMinimumSize(QtCore.QSize(700, 150))
        setup_window.setMaximumSize(QtCore.QSize(700, 150))
        setup_window.setWindowTitle('pyFlame Add Batch Nodes Path Setup')
        setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        setup_window.setStyleSheet('background-color: #313131')

        #  Labels

        logik_path_label = FlameLabel('Logik Matchbox Path', 'normal', setup_window)
        logik_path_label.setAlignment(QtCore.Qt.AlignLeft)
        logik_path_label.setMinimumSize(QtCore.QSize(150, 28))

        # Entries

        logik_path_entry = FlameLineEdit(self.logik_path, setup_window)

        # Buttons

        logik_browse_btn = FlameButton('Browse', logik_browse, setup_window)
        setup_save_btn = FlameButton('Save', setup_save, setup_window)
        setup_cancel_btn = FlameButton('Cancel', cancel, setup_window)

        #------------------------------------#

        # Window Layout

        hbox01 = QtWidgets.QHBoxLayout()
        hbox01.addWidget(logik_path_label)
        hbox01.addWidget(logik_path_entry)
        hbox01.addWidget(logik_browse_btn)

        hbox02 = QtWidgets.QHBoxLayout()
        hbox02.addStretch(10)
        hbox02.addWidget(setup_cancel_btn)
        hbox02.addStretch(5)
        hbox02.addWidget(setup_save_btn)

        hbox02.addStretch(10)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setMargin(20)

        vbox.addLayout(hbox01)
        vbox.addLayout(hbox02)

        setup_window.setLayout(vbox)

        setup_window.show()

    # ----------------------- #

    def get_batch_node_list(self):

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

        # Close window and refresh hooks

        self.window.close()

        flame.execute_shortcut('Rescan Python Hooks')

        print ('>' * 10 + '     python hooks refreshed     ' + '<' * 10 + '\n')

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

    def remove_scripts(self, listbox, node_dir):

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
                    print ('\n>>> %s deleted <<<\n' % f)

        self.get_node_scripts_lists(self.node_menu_list, self.node_dir)
        self.get_node_scripts_lists(self.matchbox_node_menu_list, self.node_dir)
        self.get_node_scripts_lists(self.logik_node_menu_list, self.node_dir)

    # ----------------------- #

    def rename_menu(self, menu_list, folder):

        def rename():

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
                            print ('dir:', d)
                            current_dir = os.path.join(root, d)
                            new_dir = current_dir.replace(selected_menu, new_menu_name)
                            os.rename(current_dir, new_dir)

                            # iterate through files in saved setup directory to change file names

                            for file_name in os.listdir(new_dir):
                                print (file_name)
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
                return message_box('Menu with that name already exists')

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

            print ('\n>>> python hooks refreshed <<<\n')

            print ('\n>>> menu renamed <<<\n')

            rename_window.close()

        if not menu_list.selectedItems():
            return

        selected_menu = [m.text() for m in menu_list.selectedItems()][0]
        print ('selected_menu:', selected_menu, '\n')

        rename_window = QtWidgets.QWidget()
        rename_window.setMinimumSize(QtCore.QSize(450, 100))
        rename_window.setMaximumSize(QtCore.QSize(450, 100))
        rename_window.setWindowTitle('pyFlame Add Batch Nodes Path Setup')
        rename_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        rename_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        rename_window.setStyleSheet('background-color: #272727')

        #  Labels

        new_name_label = QtWidgets.QLabel('Menu Name', rename_window)
        new_name_label.setMinimumSize(QtCore.QSize(75, 28))
        new_name_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                     'QLabel:disabled {color: #6a6a6a}')

        # Entries

        new_name_entry = FlameLineEdit(selected_menu, rename_window)

        # Buttons

        rename_btn = FlameButton('Rename', rename, rename_window)
        cancel_btn = FlameButton('Cancel', rename_window.close, rename_window)

        #------------------------------------#

        # Window Layout

        gridlayout = QtWidgets.QGridLayout()

        gridlayout.addWidget(new_name_label, 0, 0)
        gridlayout.addWidget(new_name_entry, 0, 1, 1, 3)
        gridlayout.addWidget(cancel_btn, 1, 1)
        gridlayout.addWidget(rename_btn, 1, 2)

        rename_window.setLayout(gridlayout)

        rename_window.show()

    def create_node(self):

        def create_node_script():

            def replace_tokens():
                import re

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
        print ('node_name:', node_name, '\n')

        node_script = os.path.join(self.node_dir, node_name) + '.py'

        # Create script for new node

        create_node_script()

        print ('>>> node script for %s saved <<<' % node_name, '\n')

    def save_selected_node(self):

        def create_node_script():

            def replace_tokens():
                import re

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
        print ('node_name:', node_name)

        for n in os.listdir(self.node_dir):
            if n == node_name:
                return message_box('<center>Menu with selected nodes name already exists. Rename node or rename/delete existing menu')

        node_type = str(selected_node.type)[1:-1]
        print ('node_type:', node_type)

        # Create folder to save node setup

        node_setup_path = os.path.join(self.node_dir, node_name)
        print ('node_setup_path:', node_setup_path)

        try:
            os.makedirs(node_setup_path)
            print ('\n>>> %s node folder created <<<\n' % node_name)
        except:
            print ('\n>>> %s node folder already exists - overwriting setup <<<\n' % node_name)

        # Save node setup

        node_setup_path_name = os.path.join(node_setup_path, node_name)
        selected_node.save_node_setup(node_setup_path_name)

        # Set script path

        node_script = os.path.join(self.node_dir, node_name) + '.py'

        # Create script for new node

        create_node_script()

        print ('>>> node script for %s saved <<<' % node_name, '\n')

# ----------------------- #

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

    code_list = ['<br>', '<dd>', '<center>']

    for code in code_list:
        message = message.replace(code, '')

    print ('\n>>> %s <<<\n' % message)

# ----------------------- #

def edit_node_lists(selection):

    script = BatchNodes(selection)
    script.main_window()

def save_node(selection):

    script = BatchNodes(selection)
    script.save_selected_node()

# ----------------------- #

def scope_node(selection):

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
                    'name': 'Add Batch Nodes Setup',
                    'execute': edit_node_lists,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Add Batch Node Menu...',
            'actions': [
                {
                    'name': 'Create Menu For Selected Node',
                    'isVisible': scope_node,
                    'execute': save_node,
                    'minimumVersion': '2021'
                },
            ]
        }
    ]
