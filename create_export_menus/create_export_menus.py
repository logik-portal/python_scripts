'''
Script Name: Create Export Menus
Script Version: 4.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 03.29.20
Update Date: 06.22.22

Custom Action Type: Media Panel

Description:

    Create custom right-click export menu's from saved export presets

Menus:

    To create or edit export menus:

        Flame Main Menu -> pyFlame -> Create Export Menus

    To access newly created menus:

        Right-click on clip -> Project Export Presets... -> Select export
        Right-click on clip -> Shared Export Presets... -> Select export

To install:

    Copy script into /opt/Autodesk/shared/python/create_export_menus

Updates:

    v4.2 06.22.22

        Messages print to Flame message window - Flame 2023.1 and later

        Updated browser window for Flame 2023.1 and later

        Setup window no longer closes after creating a new export preset

        Menu template updated - With template importing new pyflame_lib module, error appears during flame startup when loading
        menu presets. There errors can be ignored. Errors might be due to order flame is loading modules. Menus work fine.

    v4.1 03.19.22

        Moved UI widgets to external file

        Added confirmation window when deleting an existing preset

    v4.0 03.02.22

        Updated UI for Flame 2023

        Code optimization

        Misc bug fixes

    v3.7 01.03.22

        Shared export menus now only work with the major version of Flame they're created with. This avoids errors when using
        a menu with a new version of Flame. For example a menu created with Flame 2022.2 will work with all versions
        of Flame 2022 but not 2021 or 2023. Shared export menus will now also only show up in versions of Flame that they will
        work with.

        Added token for Tape Name to be used if clip has a clip name assigned

    v3.6 11.02.21

        Fixed shot name token translation to work with python 3.7 in menu_template

    v3.5 10.13.21

        Added button to reveal export path in MediaHub after export

        Added button to reveal export path in finder after export

        Export shared movie/file export presets not compatible with working version of Flame are not listed in list drop downs

        Fixed: Exporting using time tokens would create additional folders if time changed during export

        Removed leading zero from hour token if hour less than 10.

        Added lower case ampm token

        Shot name token improvements

        Shot name token will now attempt to get assigned shot name from clip before guessing from clip name

        Added SEQNAME token

    v3.4 05.21.21

        Updated to be compatible with Flame 2022/Python 3.7

    v3.3 05.19.21

        Edited menus now save properly

        Shot name token fixed to handle clip names that start with numbers

    v3.2 02.15.21

        Python hooks refresh after deleting a preset

    v3.1 01.19.21

        Added ability to assign multiple exports to single right-click export menu

        Added ability to edit/rename/delete existing export presets

        When export is done Flame with switch to export destination in the Media Hub (Flame 2021.2 of higher only)

    v2.1 09.19.20

        Updated UI

        Added Shot Name token to export path token list - Shot Name derived from clip name

        Added Sequence Name token to export path token list - Seq Name derived from Shot Name

        Added Batch Group Name token to export path token list - Can only be used when exporting clips from batch groups

        Added Batch Group Shot Name token to export path token list - Can only be used when exporting clips from batch groups

        Saved project export presets can now be found if project is not saved in the default location

        Duplicate preset names no longer allowed - duplicate preset names cause preset not to work

    v2.0 04.27.20

        New UI

        Tokens can be used to dynamically set the export path

        Options to choose to export in foreground, export between marks, and
        export top layer

        Menus can be saved so that they're visible in current project only and
        shared between all projects

    v1.1 04.05.20

        Fixed config path

        Fixed problem when checking for project presets to delete
'''

from PySide2 import QtCore, QtWidgets
import xml.etree.ElementTree as ET
from functools import partial
import os, re, ast
from pyflame_lib_create_export_menus import *

SCRIPT_NAME = 'Create Export Menus'
SCRIPT_PATH = '/opt/Autodesk/shared/python/create_export_menus'
VERSION = 'v4.2'

# ------------------------------------ #

class ExportSetup(object):

    def __init__(self, selection):
        import flame

        print('\n')
        print('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

        # Define Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.project_menus_dir = os.path.join(SCRIPT_PATH, 'project_menus')
        self.shared_menus_dir = os.path.join(SCRIPT_PATH, 'shared_menus')

        # Create menu folders

        if not os.path.isdir(self.project_menus_dir):
            os.makedirs(self.project_menus_dir)

        if not os.path.isdir(self.shared_menus_dir):
            os.makedirs(self.shared_menus_dir)

        # Load config file

        self.config()

        # Get current flame version and full flame version for export preset min/max version compatibility

        self.flame_version = pyflame_get_flame_version()
        self.flame_min_max_version = str(self.flame_version)[:4]

        # Export token menu

        self.export_token_dict = {'Project Name': '<ProjectName>', 'Project Nick Name': '<ProjectNickName>', 'Shot Name': '<ShotName>',
                                  'SEQUENCE NAME': '<SEQNAME>','Sequence Name': '<SeqName>', 'Tape Name': '<TapeName>', 'User Name': '<UserName>',
                                  'User Nickname': '<UserNickName>', 'Clip Name': '<ClipName>', 'Clip Resolution': '<Resolution>',
                                  'Clip Height': '<ClipHeight>', 'Clip Width': '<ClipWidth>', 'Year (YYYY)': '<YYYY>',
                                  'Year (YY)': '<YY>', 'Month': '<MM>', 'Day': '<DD>', 'Hour': '<Hour>', 'Minute': '<Minute>',
                                  'AM/PM': '<AMPM>', 'am/pm': '<ampm>'}

        # Get flame project values

        self.current_project = flame.project.current_project.name

        self.current_project_created_presets_path = os.path.join(SCRIPT_PATH, 'project_menus', self.current_project)
        #print ('current_project_created_presets_path:', self.current_project_created_presets_path)

        self.project_preset_path = '/opt/Autodesk/project/%s/export/presets/flame' % self.current_project

        # If project not saved to default location get project path from project.db file

        if not os.path.isdir(self.project_preset_path):
            project_values = open('/opt/Autodesk/project/project.db', 'r')
            values = project_values.read().splitlines()
            project_values.close()

            project_line = [line for line in values if 'Project:' + self.current_project in line][0]
            project_line = project_line.split('SetupDir="', 1)[1]
            project_line = project_line.split('"', 1)[0]

            self.project_preset_path = os.path.join(project_line, 'export/presets/flame')

        self.shared_preset_path = '/opt/Autodesk/shared/export/presets'

        self.menu_template_path = os.path.join(SCRIPT_PATH, 'menu_template')

        # Build lists of saved presets for pushbutton menus

        try:
            self.project_movie_preset_path = os.path.join(self.project_preset_path, 'movie_file')
            self.project_movie_preset_list = [x for x in os.listdir(self.project_movie_preset_path) if x.endswith('.xml')]
        except:
            self.project_movie_preset_list = []
        #print ('project_movie_preset_list:', self.project_movie_preset_list)

        try:
            self.project_file_seq_preset_path = os.path.join(self.project_preset_path, 'file_sequence')
            self.project_file_seq_preset_list = [x for x in os.listdir(self.project_file_seq_preset_path) if x.endswith('.xml')]
        except:
            self.project_file_seq_preset_list = []
        #print ('project_file_seq_preset_list:', self.project_file_seq_preset_list)

        try:
            self.shared_movie_preset_path = os.path.join(self.shared_preset_path, 'movie_file')
            self.shared_movie_preset_xml = [x for x in os.listdir(self.shared_movie_preset_path) if x.endswith('.xml')]

            # Make sure shared movie presets are compatible with current version of flame

            self.shared_movie_preset_list = []

            for preset in self.shared_movie_preset_xml:
                preset_path = os.path.join(self.shared_movie_preset_path, preset)
                add_preset = self.check_preset_version(preset_path)
                if add_preset:
                    self.shared_movie_preset_list.append(preset)
        except:
            self.shared_movie_preset_list = []
        #print ('shared_movie_preset_list:', self.shared_movie_preset_list)

        try:
            self.shared_file_seq_preset_path = os.path.join(self.shared_preset_path, 'file_sequence')
            self.shared_file_seq_preset_xml = [x for x in os.listdir(self.shared_file_seq_preset_path) if x.endswith('.xml')]

            # Make sure shared file presets are compatible with current version of flame

            self.shared_file_seq_preset_list = []

            for preset in self.shared_file_seq_preset_xml:
                preset_path = os.path.join(self.shared_file_seq_preset_path, preset)
                add_preset = self.check_preset_version(preset_path)
                if add_preset:
                    self.shared_file_seq_preset_list.append(preset)
        except:
            self.shared_file_seq_preset_list = []
        #print ('shared_file_seq_preset_list:', self.shared_file_seq_preset_list, '\n')

        self.export_menu_text = ''
        self.format_preset_text = ''

        self.setup_window()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('create_export_menus_settings'):
                self.export_path = setting.find('export_path').text
                self.top_layer_checked = ast.literal_eval(setting.find('use_top_layer').text)
                self.export_foreground_checked = ast.literal_eval(setting.find('export_in_foreground').text)
                self.export_between_marks = ast.literal_eval(setting.find('export_between_marks').text)
                self.reveal_in_mediahub = ast.literal_eval(setting.find('reveal_in_mediahub').text)
                self.reveal_in_finder = ast.literal_eval(setting.find('reveal_in_finder').text)

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
    <create_export_menus_settings>
        <export_path>/</export_path>
        <use_top_layer>False</use_top_layer>
        <export_in_foreground>True</export_in_foreground>
        <export_between_marks>False</export_between_marks>
        <reveal_in_mediahub>False</reveal_in_mediahub>
        <reveal_in_finder>False</reveal_in_finder>
    </create_export_menus_settings>
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

    def check_preset_version(self, preset_path):
        '''
        Check export presets for flame version compatibility.
        If preset requires newer version of flame, don't list it
        '''

        export_preset_xml_tree = ET.parse(preset_path)
        root = export_preset_xml_tree.getroot()

        # Get version export preset is currently set to

        for setting in root.iter('preset'):
            current_export_version = setting.get('version')

        # Get current flame version whole number

        flame_version = str(self.flame_version)[:4]

        # Set export version for verion of flame being used

        if flame_version == '2021':
            export_version = '10'
        elif flame_version == '2022':
            export_version = '11'
        elif flame_version == '2023':
            export_version = '11'

        # If preset version if different than current export version then update xml

        if current_export_version == export_version:
            return True
        return False

    def setup_window(self):

        self.main_tabs = QtWidgets.QTabWidget()
        self.preset_tabs = QtWidgets.QTabWidget()

        gridbox = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'Create Export Menus <small>{VERSION}', gridbox, 1200, 530)

        # Main Tabs

        self.window.create_tab = QtWidgets.QWidget()
        self.window.edit_tab = QtWidgets.QWidget()

        self.main_tabs.setStyleSheet('QTabWidget {background-color: rgb(36, 36, 36); border: none; font: 14px "Discreet"}'
                                     'QTabWidget::tab-bar {alignment: center}'
                                     'QTabBar::tab {color: rgb(154, 154, 154); background-color: rgb(36, 36, 36); min-width: 20ex; padding: 5px;}'
                                     'QTabBar::tab:selected {color: rgb(186, 186, 186); background-color: rgb(31, 31, 31); border: 1px solid rgb(31, 31, 31); border-bottom: 1px solid rgb(51, 102, 173)}'
                                     'QTabBar::tab:!selected {color: rgb(186, 186, 186); background-color: rgb(36, 36, 36); border: none}'
                                     'QTabWidget::pane {border-top: 1px solid rgb(49, 49, 49)}')

        self.main_tabs.addTab(self.window.create_tab, 'Create')
        self.main_tabs.addTab(self.window.edit_tab, 'Edit')

        self.main_tabs.setFocusPolicy(QtCore.Qt.NoFocus)

        def export_preset_tab(tab, tab_number, export_path, top_layer, export_foreground, export_between_marks):

            def toggle_ui():

                if enable_preset_pushbutton.isChecked():
                    switch = True
                else:
                    switch = False

                saved_preset_type_label.setEnabled(switch)
                saved_presets_label.setEnabled(switch)
                export_path_label.setEnabled(switch)
                export_path_lineedit.setEnabled(switch)
                top_layer_pushbutton.setEnabled(switch)
                foreground_pushbutton.setEnabled(switch)
                between_marks_pushbutton.setEnabled(switch)
                token_push_btn.setEnabled(switch)
                preset_type_menu_pushbutton.setEnabled(switch)
                server_browse_btn.setEnabled(switch)
                presets_menu_pushbutton.setEnabled(switch)

            # Labels

            saved_preset_type_label = FlameLabel('Saved Preset Type', 'normal')
            saved_presets_label = FlameLabel('Saved Presets', 'normal')
            export_path_label = FlameLabel('Export Path', 'normal')

            # LineEdits

            export_path_lineedit = FlameLineEdit(export_path)

            # Pushbuttons

            if tab_number != 'one':
                enable_preset_pushbutton = FlamePushButton('Enable Preset', False, connect=toggle_ui, button_width=160)
            else:
                enable_preset_pushbutton = None

            top_layer_pushbutton = FlamePushButton('Use Top Layer', top_layer, button_width=160)
            foreground_pushbutton = FlamePushButton('Foreground Export', export_foreground, button_width=160)
            between_marks_pushbutton = FlamePushButton('Export Between Marks', export_between_marks, button_width=160)

            # Token Pushbutton

            token_push_btn = FlameTokenPushButton('Add Token', self.export_token_dict, export_path_lineedit)

            # Export Pushbutton Menu

            def set_export_push_button():

                if self.project_movie_preset_list != []:
                    preset_name = str(self.project_movie_preset_list[0])[:-4]
                    preset_type_menu_pushbutton.setText('Project: Movie')
                    presets_menu_pushbutton.setText(preset_name)
                    build_format_preset_menus(self.project_movie_preset_list)
                elif self.shared_movie_preset_list != []:
                    preset_name = str(self.shared_movie_preset_list[0])[:-4]
                    preset_type_menu_pushbutton.setText('Shared: Movie')
                    presets_menu_pushbutton.setText(preset_name)
                    build_format_preset_menus(self.shared_movie_preset_list)
                elif self.project_file_seq_preset_list != []:
                    preset_name = str(self.project_file_seq_preset_list[0])[:-4]
                    preset_type_menu_pushbutton.setText('Project: File Sequence')
                    presets_menu_pushbutton.setText(preset_name)
                    build_format_preset_menus(self.project_file_seq_preset_list)
                elif self.shared_file_seq_preset_list != []:
                    preset_name = str(self.shared_file_seq_preset_list[0])[:-4]
                    preset_type_menu_pushbutton.setText('Shared: File Sequence')
                    presets_menu_pushbutton.setText(preset_name)
                    build_format_preset_menus(self.shared_file_seq_preset_list)
                else:
                    preset_type_menu_pushbutton.setText('No Saved Export Presets')
                    presets_menu_pushbutton.setText('No Saved Export Presets')

            def project_movie_menu():
                preset_type_menu_pushbutton.setText('Project: Movie')
                build_format_preset_menus(self.project_movie_preset_list)

            def project_file_seq_menu():
                preset_type_menu_pushbutton.setText('Project: File Sequence')
                build_format_preset_menus(self.project_file_seq_preset_list)

            def shared_movie_menu():
                preset_type_menu_pushbutton.setText('Shared: Movie')
                build_format_preset_menus(self.shared_movie_preset_list)

            def shared_file_seq_menu():
                preset_type_menu_pushbutton.setText('Shared: File Sequence')
                build_format_preset_menus(self.shared_file_seq_preset_list)

            preset_type_menu = QtWidgets.QMenu(self.window)
            preset_type_menu.addAction('Project: Movie', project_movie_menu)
            preset_type_menu.addAction('Project: File Sequence', project_file_seq_menu)
            preset_type_menu.addAction('Shared: Movie', shared_movie_menu)
            preset_type_menu.addAction('Shared: File Sequence', shared_file_seq_menu)
            preset_type_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#2d3744; border: none; font: 14px "Discreet"}'
                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            preset_type_menu_pushbutton = QtWidgets.QPushButton(self.export_menu_text)
            preset_type_menu_pushbutton.setMenu(preset_type_menu)
            preset_type_menu_pushbutton.setMinimumSize(QtCore.QSize(200, 28))
            preset_type_menu_pushbutton.setMaximumSize(QtCore.QSize(200, 28))
            preset_type_menu_pushbutton.setFocusPolicy(QtCore.Qt.NoFocus)
            preset_type_menu_pushbutton.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #2d3744; border: none; font: 14px "Discreet"}'
                                                      'QPushButton:disabled {color: #747474; background-color: #2d3744; border: none}'
                                                      'QPushButton:hover {border: 1px solid #5a5a5a}'
                                                      'QPushButton::menu-indicator {image: none}')

            # Presets Pushbutton

            def build_format_preset_menus(preset_list):
                from functools import partial

                def menu(menu_name):
                    presets_menu_pushbutton.setText(menu_name)

                # Clear Format Preset menu list

                preset_menu.clear()

                # Set button to first preset in list

                if preset_list != []:
                    presets_menu_pushbutton.setText(str(preset_list[0])[:-4])
                else:
                    presets_menu_pushbutton.setText('No Saved Presets Found')

                # Dynamically create button menus

                for item in preset_list:
                    menu_name = item[:-4]
                    preset_menu.addAction(menu_name, partial(menu, menu_name))

            preset_menu = QtWidgets.QMenu(self.window)
            preset_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#2d3744; border: none; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            presets_menu_pushbutton = QtWidgets.QPushButton(self.format_preset_text)
            presets_menu_pushbutton.setMenu(preset_menu)
            presets_menu_pushbutton.setMinimumSize(QtCore.QSize(200, 28))
            presets_menu_pushbutton.setFocusPolicy(QtCore.Qt.NoFocus)
            presets_menu_pushbutton.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #2d3744; border: none; font: 14px "Discreet"}'
                                                  'QPushButton:disabled {color: #747474; background-color: #2d3744; border: none}'
                                                  'QPushButton:hover {border: 1px solid #5a5a5a}'
                                                  'QPushButton::menu-indicator {image: none}')
            # Buttons

            server_browse_btn = FlameButton('Browse', partial(self.server_path_browse, export_path_lineedit))

            set_export_push_button()

            try:
                toggle_ui()
            except:
                pass

            # Tab Layout

            gridbox_tab = QtWidgets.QGridLayout()
            gridbox_tab.setMargin(30)
            gridbox_tab.setVerticalSpacing(5)
            gridbox_tab.setHorizontalSpacing(5)
            gridbox_tab.setColumnMinimumWidth(4, 100)

            gridbox_tab.addWidget(saved_preset_type_label, 0, 0)
            gridbox_tab.addWidget(preset_type_menu_pushbutton, 0, 1)

            gridbox_tab.addWidget(saved_presets_label, 1, 0)
            gridbox_tab.addWidget(presets_menu_pushbutton, 1, 1)

            gridbox_tab.addWidget(export_path_label, 2, 0)
            gridbox_tab.addWidget(export_path_lineedit, 2, 1)
            gridbox_tab.addWidget(server_browse_btn, 2, 2)
            gridbox_tab.addWidget(token_push_btn, 2, 3)

            if tab_number != 'one':
                gridbox_tab.addWidget(enable_preset_pushbutton, 0, 5)
            gridbox_tab.addWidget(top_layer_pushbutton, 1, 5)
            gridbox_tab.addWidget(foreground_pushbutton, 2, 5)
            gridbox_tab.addWidget(between_marks_pushbutton, 3, 5)

            tab.setLayout(gridbox_tab)

            return preset_type_menu_pushbutton, presets_menu_pushbutton, preset_menu, export_path_lineedit, enable_preset_pushbutton, top_layer_pushbutton, foreground_pushbutton, between_marks_pushbutton, saved_preset_type_label, saved_presets_label, export_path_label, server_browse_btn, token_push_btn

        def create_tab():

            def create_presets():

                # Menus for preset tabs two thru five

                # def set_export_push_button(export_btn, saved_presets_btn, saved_presets_menu):

                #     if self.project_movie_preset_list != []:
                #         preset_name = str(self.project_movie_preset_list[0])[:-4]
                #         export_btn.setText('Project: Movie')
                #         saved_presets_btn.setText(preset_name)
                #         build_format_preset_menus(self.project_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                #     elif self.shared_movie_preset_list != []:
                #         preset_name = str(self.shared_movie_preset_list[0])[:-4]
                #         export_btn.setText('Shared: Movie')
                #         saved_presets_btn.setText(preset_name)
                #         build_format_preset_menus(self.shared_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                #     elif self.project_file_seq_preset_list != []:
                #         preset_name = str(self.project_file_seq_preset_list[0])[:-4]
                #         export_btn.setText('Project: File Sequence')
                #         saved_presets_btn.setText(preset_name)
                #         build_format_preset_menus(self.project_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                #     elif self.shared_file_seq_preset_list != []:
                #         preset_name = str(self.shared_file_seq_preset_list[0])[:-4]
                #         export_btn.setText('Shared: File Sequence')
                #         saved_presets_btn.setText(preset_name)
                #         build_format_preset_menus(self.shared_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                #     else:
                #         export_btn.setText('No Saved Export Presets')
                #         saved_presets_btn.setText('No Saved Export Presets')

                # def project_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):

                #     export_btn.setText('Project: Movie')
                #     build_format_preset_menus(self.project_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # def project_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):

                #     export_btn.setText('Project: File Sequence')
                #     build_format_preset_menus(self.project_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # def shared_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):

                #     export_btn.setText('Shared: Movie')
                #     build_format_preset_menus(self.shared_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # def shared_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):

                #     export_btn.setText('Shared: File Sequence')
                #     build_format_preset_menus(self.shared_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def build_format_preset_menus(preset_list, export_btn, saved_presets_btn, saved_presets_menu):

                    def menu(menu_name):

                        saved_presets_btn.setText(menu_name)

                    # Clear Format Preset menu list

                    saved_presets_menu.clear()

                    # Set button to first preset in list

                    if preset_list != []:
                        saved_presets_btn.setText(str(preset_list[0])[:-4])
                    else:
                        saved_presets_btn.setText('No Saved Presets Found')

                    # Dynamically create button menus

                    for item in preset_list:
                        menu_name = item[:-4]
                        saved_presets_menu.addAction(menu_name, partial(menu, menu_name))

                # -------------------------------------------------------

                self.preset_tabs = QtWidgets.QTabWidget()

                # Preset Tabs

                self.window.tab1 = QtWidgets.QWidget()
                self.window.tab2 = QtWidgets.QWidget()
                self.window.tab3 = QtWidgets.QWidget()
                self.window.tab4 = QtWidgets.QWidget()
                self.window.tab5 = QtWidgets.QWidget()

                self.preset_tabs.setFocusPolicy(QtCore.Qt.NoFocus)

                self.preset_tabs.setStyleSheet('QTabWidget {background-color: rgb(36, 36, 36); border: none; font: 14px "Discreet"}'
                                               'QTabWidget::tab-bar {alignment: center}'
                                               'QTabBar::tab {color: rgb(154, 154, 154); background-color: rgb(36, 36, 36); min-width: 20ex; padding: 5px;}'
                                               'QTabBar::tab:selected {color: rgb(186, 186, 186); background-color: rgb(31, 31, 31); border: 1px solid rgb(31, 31, 31); border-bottom: 1px solid rgb(51, 102, 173)}'
                                               'QTabBar::tab:!selected {color: rgb(186, 186, 186); background-color: rgb(36, 36, 36); border: none}'
                                               'QTabWidget::pane {border-top: 1px solid rgb(49, 49, 49)}')

                self.preset_tabs.addTab(self.window.tab1, 'Export Preset One')
                self.preset_tabs.addTab(self.window.tab2, 'Export Preset Two')
                self.preset_tabs.addTab(self.window.tab3, 'Export Preset Three')
                self.preset_tabs.addTab(self.window.tab4, 'Export Preset Four')
                self.preset_tabs.addTab(self.window.tab5, 'Export Preset Five')

                # Create tabs

                export_preset_one_tab = export_preset_tab(self.window.tab1, 'one', self.export_path, self.top_layer_checked, self.export_foreground_checked, self.export_between_marks)
                export_preset_two_tab = export_preset_tab(self.window.tab2, 'two', '', False, False, False)
                export_preset_three_tab = export_preset_tab(self.window.tab3, 'three', '', False, False, False)
                export_preset_four_tab = export_preset_tab(self.window.tab4, 'four', '', False, False, False)
                export_preset_five_tab = export_preset_tab(self.window.tab5, 'five', '', False, False, False)

                # Get values from tabs

                self.preset_type_menu_pushbutton_01, self.presets_menu_pushbutton_01, self.preset_menu_01, self.export_path_lineedit_01, self.enable_preset_pushbutton_01, self.top_layer_pushbutton_01, self.foreground_pushbutton_01, self.between_marks_pushbutton_01, self.saved_preset_type_label_01, self.saved_presets_label_01, self.export_path_label_01, self.server_browse_btn_01, self.token_push_btn_01 = export_preset_one_tab
                self.preset_type_menu_pushbutton_02, self.presets_menu_pushbutton_02, self.preset_menu_02, self.export_path_lineedit_02, self.enable_preset_pushbutton_02, self.top_layer_pushbutton_02, self.foreground_pushbutton_02, self.between_marks_pushbutton_02, self.saved_preset_type_label_02, self.saved_presets_label_02, self.export_path_label_02, self.server_browse_btn_02, self.token_push_btn_02 = export_preset_two_tab
                self.preset_type_menu_pushbutton_03, self.presets_menu_pushbutton_03, self.preset_menu_03, self.export_path_lineedit_03, self.enable_preset_pushbutton_03, self.top_layer_pushbutton_03, self.foreground_pushbutton_03, self.between_marks_pushbutton_03, self.saved_preset_type_label_03, self.saved_presets_label_03, self.export_path_label_03, self.server_browse_btn_03, self.token_push_btn_03 = export_preset_three_tab
                self.preset_type_menu_pushbutton_04, self.presets_menu_pushbutton_04, self.preset_menu_04, self.export_path_lineedit_04, self.enable_preset_pushbutton_04, self.top_layer_pushbutton_04, self.foreground_pushbutton_04, self.between_marks_pushbutton_04, self.saved_preset_type_label_04, self.saved_presets_label_04, self.export_path_label_04, self.server_browse_btn_04, self.token_push_btn_04 = export_preset_four_tab
                self.preset_type_menu_pushbutton_05, self.presets_menu_pushbutton_05, self.preset_menu_05, self.export_path_lineedit_05, self.enable_preset_pushbutton_05, self.top_layer_pushbutton_05, self.foreground_pushbutton_05, self.between_marks_pushbutton_05, self.saved_preset_type_label_05, self.saved_presets_label_05, self.export_path_label_05, self.server_browse_btn_05, self.token_push_btn_05 = export_preset_five_tab

            # Labels

            self.menu_visibility_label = FlameLabel('Menu Visibility')
            self.menu_name_label = FlameLabel('Menu Name')

            # LineEdits

            self.menu_name_lineedit = FlameLineEdit('', width=200, max_width=450)

            # Menu Pushbutton

            export_type_options = ['Project', 'Shared']
            self.menu_visibility_push_btn = FlamePushButtonMenu('Project', export_type_options)

            # -------------------------------------------------------------

            # Push Button

            self.reveal_in_mediahub_pushbutton = FlamePushButton('Reveal in Mediahub', self.reveal_in_mediahub, button_width=160)
            self.reveal_in_finder_pushbutton = FlamePushButton('Reveal in Finder', self.reveal_in_finder, button_width=160)

            # Buttons

            self.create_btn = FlameButton('Create', partial(self.save_menus, 'Create'), button_width=160)
            self.done_btn = FlameButton('Done', self.window.close, button_width=160)

            # -------------------------------------------------------------

            create_presets()

            # Window Layout

            create_gridbox = QtWidgets.QGridLayout()
            create_gridbox.setRowMinimumHeight(0, 34)
            create_gridbox.setRowMinimumHeight(3, 30)
            create_gridbox.setRowMinimumHeight(5, 30)

            create_gridbox.addWidget(self.menu_visibility_label, 1, 0)
            create_gridbox.addWidget(self.menu_visibility_push_btn, 1, 1)
            create_gridbox.addWidget(self.menu_name_label, 2, 0)
            create_gridbox.addWidget(self.menu_name_lineedit, 2, 1, 1, 4)

            create_gridbox.addWidget(self.reveal_in_mediahub_pushbutton, 2, 5)
            create_gridbox.addWidget(self.reveal_in_finder_pushbutton, 3, 5)

            create_gridbox.addWidget(self.preset_tabs, 4, 0, 1, 6)

            create_gridbox.addWidget(self.done_btn, 6, 4)
            create_gridbox.addWidget(self.create_btn, 6, 5)

            self.window.create_tab.setLayout(create_gridbox)

        def edit_tab():

            def edit_presets():

                # Build button menus for preset tabs

                # def project_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):
                #     export_btn.setText('Project: Movie')
                #     build_format_preset_menus(self.project_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # def project_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):
                #     export_btn.setText('Project: File Sequence')
                #     build_format_preset_menus(self.project_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # def shared_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):
                #     export_btn.setText('Shared: Movie')
                #     build_format_preset_menus(self.shared_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # def shared_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):
                #     export_btn.setText('Shared: File Sequence')
                #     build_format_preset_menus(self.shared_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # -------------------------------------------------------

                self.edit_preset_tabs = QtWidgets.QTabWidget()

                # Preset Tabs

                self.window.edit_tab1 = QtWidgets.QWidget()
                self.window.edit_tab2 = QtWidgets.QWidget()
                self.window.edit_tab3 = QtWidgets.QWidget()
                self.window.edit_tab4 = QtWidgets.QWidget()
                self.window.edit_tab5 = QtWidgets.QWidget()

                self.edit_preset_tabs.setFocusPolicy(QtCore.Qt.NoFocus)

                self.edit_preset_tabs.setStyleSheet('QTabWidget {background-color: #242424; border: none; font: 14px "Discreet"}'
                                                    'QTabWidget::tab-bar {alignment: center}'
                                                    'QTabBar::tab {color: #9a9a9a; background-color: #242424; min-width: 20ex; padding: 5px;}'
                                                    'QTabBar::tab:selected {color: #bababa; background-color: #1f1f1f; border: 1px solid #1f1f1f; border-bottom: 1px solid #3366AD}'
                                                    'QTabBar::tab:!selected {color: #bababa; background-color: #242424; border: none}'
                                                    'QTabWidget::pane {border-top: 1px solid #313131}')

                self.edit_preset_tabs.addTab(self.window.edit_tab1, 'Export Preset One')
                self.edit_preset_tabs.addTab(self.window.edit_tab2, 'Export Preset Two')
                self.edit_preset_tabs.addTab(self.window.edit_tab3, 'Export Preset Three')
                self.edit_preset_tabs.addTab(self.window.edit_tab4, 'Export Preset Four')
                self.edit_preset_tabs.addTab(self.window.edit_tab5, 'Export Preset Five')

                # Create tabs

                edit_preset_one_tab = export_preset_tab(self.window.edit_tab1, 'one', self.export_path, self.top_layer_checked, self.export_foreground_checked, self.export_between_marks)
                edit_preset_two_tab = export_preset_tab(self.window.edit_tab2, 'two', '', False, False, False)
                edit_preset_three_tab = export_preset_tab(self.window.edit_tab3, 'three', '', False, False, False)
                edit_preset_four_tab = export_preset_tab(self.window.edit_tab4, 'four', '', False, False, False)
                edit_preset_five_tab = export_preset_tab(self.window.edit_tab5, 'five', '', False, False, False)

                # Get values from tabs

                self.edit_preset_type_menu_pushbutton_01, self.edit_presets_menu_pushbutton_01, self.edit_preset_menu_01, self.edit_export_path_lineedit_01, self.edit_enable_preset_pushbutton_01, self.edit_top_layer_pushbutton_01, self.edit_foreground_pushbutton_01, self.edit_between_marks_pushbutton_01, self.edit_saved_preset_type_label_01, self.edit_saved_presets_label_01, self.edit_export_path_label_01, self.edit_server_browse_btn_01, self.edit_token_push_btn_01 = edit_preset_one_tab
                self.edit_preset_type_menu_pushbutton_02, self.edit_presets_menu_pushbutton_02, self.edit_preset_menu_02, self.edit_export_path_lineedit_02, self.edit_enable_preset_pushbutton_02, self.edit_top_layer_pushbutton_02, self.edit_foreground_pushbutton_02, self.edit_between_marks_pushbutton_02, self.edit_saved_preset_type_label_02, self.edit_saved_presets_label_02, self.edit_export_path_label_02, self.edit_server_browse_btn_02, self.edit_token_push_btn_02 = edit_preset_two_tab
                self.edit_preset_type_menu_pushbutton_03, self.edit_presets_menu_pushbutton_03, self.edit_preset_menu_03, self.edit_export_path_lineedit_03, self.edit_enable_preset_pushbutton_03, self.edit_top_layer_pushbutton_03, self.edit_foreground_pushbutton_03, self.edit_between_marks_pushbutton_03, self.edit_saved_preset_type_label_03, self.edit_saved_presets_label_03, self.edit_export_path_label_03, self.edit_server_browse_btn_03, self.edit_token_push_btn_03 = edit_preset_three_tab
                self.edit_preset_type_menu_pushbutton_04, self.edit_presets_menu_pushbutton_04, self.edit_preset_menu_04, self.edit_export_path_lineedit_04, self.edit_enable_preset_pushbutton_04, self.edit_top_layer_pushbutton_04, self.edit_foreground_pushbutton_04, self.edit_between_marks_pushbutton_04, self.edit_saved_preset_type_label_04, self.edit_saved_presets_label_04, self.edit_export_path_label_04, self.edit_server_browse_btn_04, self.edit_token_push_btn_04 = edit_preset_four_tab
                self.edit_preset_type_menu_pushbutton_05, self.edit_presets_menu_pushbutton_05, self.edit_preset_menu_05, self.edit_export_path_lineedit_05, self.edit_enable_preset_pushbutton_05, self.edit_top_layer_pushbutton_05, self.edit_foreground_pushbutton_05, self.edit_between_marks_pushbutton_05, self.edit_saved_preset_type_label_05, self.edit_saved_presets_label_05, self.edit_export_path_label_05, self.edit_server_browse_btn_05, self.edit_token_push_btn_05 = edit_preset_five_tab

            def set_export_push_button(export_btn, saved_presets_btn, saved_presets_menu):

                if export_btn.text() == 'Project: Movie':
                    build_format_preset_menus(self.project_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)
                elif export_btn.text() == 'Project: File Sequence':
                    build_format_preset_menus(self.project_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)
                elif export_btn.text() == 'Shared: Movie':
                    build_format_preset_menus(self.shared_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)
                elif export_btn.text() == 'Shared: File Sequence':
                    build_format_preset_menus(self.shared_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)
                else:
                    export_btn.setText('No Saved Export Presets')
                    saved_presets_btn.setText('No Saved Export Presets')

            def build_format_preset_menus(preset_list, export_btn, saved_presets_btn, saved_presets_menu):

                def menu(menu_name):
                    saved_presets_btn.setText(menu_name)

                # Clear Format Preset menu list

                saved_presets_menu.clear()

                # Set button to first preset in list

                if preset_list != []:
                    saved_presets_btn.setText(str(preset_list[0])[:-4])
                else:
                    saved_presets_btn.setText('No Saved Presets Found')

                # Dynamically create button menus

                for item in preset_list:
                    menu_name = item[:-4]
                    saved_presets_menu.addAction(menu_name, partial(menu, menu_name))

            def load_preset():

                #print ('checking for existing presets...\n')

                if self.edit_menu_push_btn.text() != 'No Saved Presets Found':

                    selected_script_name = self.edit_menu_push_btn.text().rsplit(': ', 1)[1]
                    #print ('selected_script_name:', selected_script_name)

                    self.edit_menu_name_lineedit.setText(selected_script_name)

                    if 'Shared: ' in self.edit_menu_push_btn.text():
                        self.edit_menu_visibility_push_btn.setText('Shared')
                        selected_menu_path = os.path.join(self.shared_menus_dir, selected_script_name) + '.py'
                    elif 'Project: ' in self.edit_menu_push_btn.text():
                        self.edit_menu_visibility_push_btn.setText('Project')
                        selected_menu_path = os.path.join(self.project_menus_dir, self.current_project, selected_script_name) + '.py'

                    #print ('selected_menu_path:', selected_menu_path)

                    # Read in menu script
                    #-----------------------------------------

                    get_menu_values = open(selected_menu_path, 'r')
                    menu_lines = get_menu_values.read().splitlines()

                    get_menu_values.close()

                    def get_preset_info(preset_num, enable_btn, saved_preset_type_label, saved_presets_label, export_path_label, export_path_lineedit, top_layer_btn, foreground_btn, between_marks_btn, token_btn, export_btn, server_btn, saved_presets_btn):

                        # Get preset info

                        preset_start_index = menu_lines.index('        # Export preset %s' % preset_num)
                        preset_end_index = menu_lines.index('        # Export preset %s END' % preset_num) + 1
                        preset_lines = menu_lines[preset_start_index:preset_end_index]

                        if enable_btn:

                            enable_btn.setChecked(True)

                            # Enable UI elements

                            saved_preset_type_label.setEnabled(True)
                            saved_presets_label.setEnabled(True)
                            export_path_label.setEnabled(True)
                            export_path_lineedit.setEnabled(True)
                            top_layer_btn.setEnabled(True)
                            foreground_btn.setEnabled(True)
                            between_marks_btn.setEnabled(True)
                            token_btn.setEnabled(True)
                            export_btn.setEnabled(True)
                            server_btn.setEnabled(True)
                            saved_presets_btn.setEnabled(True)

                        # Set UI elements

                        print ('Preset: %s' % preset_num)

                        for line in preset_lines:
                            if line == '        clip_output.use_top_video_track = True':
                                top_layer_btn.setChecked(True)
                                print ('use top layer: True')
                            elif line == '        clip_output.use_top_video_track = False':
                                top_layer_btn.setChecked(False)
                                print ('use top layer: False')

                            elif line == '        clip_output.foreground = True':
                                foreground_btn.setChecked(True)
                                print ('foreground export: True')
                            elif line == '        clip_output.foreground = False':
                                foreground_btn.setChecked(False)
                                print ('foreground export: False')

                            elif line == '        clip_output.export_between_marks = True':
                                between_marks_btn.setChecked(True)
                                print ('export between marks: True')
                            elif line == '        clip_output.export_between_marks = False':
                                between_marks_btn.setChecked(False)
                                print ('export between marks: False')

                            elif '        new_export_path = translate_token_path(clip, ' in line:
                                path = line.split("'", 2)[1]
                                export_path_lineedit.setText(path)
                                print ('export path:', path)

                            elif '        clip_output.export(clip, ' in line:
                                preset_path = line.split("'", 2)[1]
                                preset_name = preset_path.rsplit('/', 1)[1][:-4]
                                saved_presets_btn.setText(preset_name)
                                print ('preset_name:', preset_name)

                            if 'clip_output.export' in line:
                                if 'project' in line:
                                    if 'file_sequence' in line:
                                        export_btn.setText('Project: File Sequence')
                                        print ('saved_preset_type: project file_seq')
                                    elif 'movie_file' in line:
                                        export_btn.setText('Project: Movie')
                                        print ('saved_preset_type: project movie_file')

                                if 'shared' in line:
                                    if 'file_sequence' in line:
                                        export_btn.setText('Shared: File Sequence')
                                        print ('saved_preset_type: shared file_seq')
                                    elif 'movie_file' in line:
                                        export_btn.setText('Shared: Movie')
                                        print ('saved_preset_type: shared movie_file')

                    def disable_ui_elements(enable_btn, saved_preset_type_label, saved_presets_label, export_path_label, export_path_lineedit, top_layer_btn, foreground_btn, between_marks_btn, token_btn, export_btn, server_btn, saved_presets_btn):

                        # Disable UI elements

                        enable_btn.setChecked(False)
                        saved_preset_type_label.setEnabled(False)
                        saved_presets_label.setEnabled(False)
                        export_path_label.setEnabled(False)
                        export_path_lineedit.setText('')
                        export_path_lineedit.setEnabled(False)
                        top_layer_btn.setEnabled(False)
                        foreground_btn.setEnabled(False)
                        between_marks_btn.setEnabled(False)
                        token_btn.setEnabled(False)
                        export_btn.setEnabled(False)
                        server_btn.setEnabled(False)
                        saved_presets_btn.setEnabled(False)

                    for line in menu_lines:
                        if 'open_in_mediahub = True' in line:
                            self.edit_reveal_in_mediahub_pushbutton.setChecked(True)
                        elif 'open_in_mediahub = False' in line:
                            self.edit_reveal_in_mediahub_pushbutton.setChecked(False)

                    # Get preset UI settings. If none are found, disable UI for that tab

                    get_preset_info('One', None, self.edit_saved_presets_label_01, self.edit_saved_presets_label_01, self.edit_export_path_label_01, self.edit_export_path_lineedit_01, self.edit_top_layer_pushbutton_01, self.edit_foreground_pushbutton_01, self.edit_between_marks_pushbutton_01, self.edit_token_push_btn_01, self.edit_preset_type_menu_pushbutton_01, self.edit_server_browse_btn_01, self.edit_presets_menu_pushbutton_01)
                    preset_01_push_btn_text = self.edit_presets_menu_pushbutton_01.text()

                    try:
                        get_preset_info('Two', self.edit_enable_preset_pushbutton_02, self.edit_saved_preset_type_label_02, self.edit_saved_presets_label_02, self.edit_export_path_label_02, self.edit_export_path_lineedit_02, self.edit_top_layer_pushbutton_02, self.edit_foreground_pushbutton_02, self.edit_between_marks_pushbutton_02, self.edit_token_push_btn_02, self.edit_preset_type_menu_pushbutton_02, self.edit_server_browse_btn_02, self.edit_presets_menu_pushbutton_02)
                        preset_02_push_btn_text = self.edit_presets_menu_pushbutton_02.text()
                    except:
                        # Disable UI elements if nothing loaded for preset two
                        disable_ui_elements(self.edit_enable_preset_pushbutton_02, self.edit_saved_preset_type_label_02, self.edit_saved_presets_label_02, self.edit_export_path_label_02, self.edit_export_path_lineedit_02, self.edit_top_layer_pushbutton_02, self.edit_foreground_pushbutton_02, self.edit_between_marks_pushbutton_02, self.edit_token_push_btn_02, self.edit_preset_type_menu_pushbutton_02, self.edit_server_browse_btn_02, self.edit_presets_menu_pushbutton_02)
                    try:
                        get_preset_info('Three', self.edit_enable_preset_pushbutton_03, self.edit_saved_preset_type_label_03, self.edit_saved_presets_label_03, self.edit_export_path_label_03, self.edit_export_path_lineedit_03, self.edit_top_layer_pushbutton_03, self.edit_foreground_pushbutton_03, self.edit_between_marks_pushbutton_03, self.edit_token_push_btn_03, self.edit_preset_type_menu_pushbutton_03, self.edit_server_browse_btn_03, self.edit_presets_menu_pushbutton_03)
                        preset_03_push_btn_text = self.edit_presets_menu_pushbutton_03.text()
                    except:
                        # Disable UI elements if nothing loaded for preset three
                        disable_ui_elements(self.edit_enable_preset_pushbutton_03, self.edit_saved_preset_type_label_03, self.edit_saved_presets_label_03, self.edit_export_path_label_03, self.edit_export_path_lineedit_03, self.edit_top_layer_pushbutton_03, self.edit_foreground_pushbutton_03, self.edit_between_marks_pushbutton_03, self.edit_token_push_btn_03, self.edit_preset_type_menu_pushbutton_03, self.edit_server_browse_btn_03, self.edit_presets_menu_pushbutton_03)
                    try:
                        get_preset_info('Four', self.edit_enable_preset_pushbutton_04, self.edit_saved_preset_type_label_04, self.edit_saved_presets_label_04, self.edit_export_path_label_04, self.edit_export_path_lineedit_04, self.edit_top_layer_pushbutton_04, self.edit_foreground_pushbutton_04, self.edit_between_marks_pushbutton_04, self.edit_token_push_btn_04, self.edit_preset_type_menu_pushbutton_04, self.edit_server_browse_btn_04, self.edit_presets_menu_pushbutton_04)
                        preset_04_push_btn_text = self.edit_presets_menu_pushbutton_04.text()
                    except:
                        # Disable UI elements if nothing loaded for preset four
                        disable_ui_elements(self.edit_enable_preset_pushbutton_04, self.edit_saved_preset_type_label_04, self.edit_saved_presets_label_04, self.edit_export_path_label_04, self.edit_export_path_lineedit_04, self.edit_top_layer_pushbutton_04, self.edit_foreground_pushbutton_04, self.edit_between_marks_pushbutton_04, self.edit_token_push_btn_04, self.edit_preset_type_menu_pushbutton_04, self.edit_server_browse_btn_04, self.edit_presets_menu_pushbutton_04)
                    try:
                        get_preset_info('Five', self.edit_enable_preset_pushbutton_05, self.edit_saved_preset_type_label_05, self.edit_saved_presets_label_05, self.edit_export_path_label_05, self.edit_export_path_lineedit_05, self.edit_top_layer_pushbutton_05, self.edit_foreground_pushbutton_05, self.edit_between_marks_pushbutton_05, self.edit_token_push_btn_05, self.edit_preset_type_menu_pushbutton_05, self.edit_server_browse_btn_05, self.edit_presets_menu_pushbutton_05)
                        preset_05_push_btn_text = self.edit_presets_menu_pushbutton_05.text()
                    except:
                        # Disable UI elements if nothing loaded for preset five
                        disable_ui_elements(self.edit_enable_preset_pushbutton_05, self.edit_saved_preset_type_label_05, self.edit_saved_presets_label_05, self.edit_export_path_label_05, self.edit_export_path_lineedit_05, self.edit_top_layer_pushbutton_05, self.edit_foreground_pushbutton_05, self.edit_between_marks_pushbutton_05, self.edit_token_push_btn_05, self.edit_preset_type_menu_pushbutton_05, self.edit_server_browse_btn_05, self.edit_presets_menu_pushbutton_05)

                    # Fill Saved Presets Pushbutton with list of available saved presets for chosen Saved Preset Type

                    set_export_push_button(self.edit_preset_type_menu_pushbutton_01, self.edit_presets_menu_pushbutton_01, self.edit_preset_menu_01)
                    set_export_push_button(self.edit_preset_type_menu_pushbutton_02, self.edit_presets_menu_pushbutton_02, self.edit_preset_menu_02)
                    set_export_push_button(self.edit_preset_type_menu_pushbutton_03, self.edit_presets_menu_pushbutton_03, self.edit_preset_menu_03)
                    set_export_push_button(self.edit_preset_type_menu_pushbutton_04, self.edit_presets_menu_pushbutton_04, self.edit_preset_menu_04)
                    set_export_push_button(self.edit_preset_type_menu_pushbutton_05, self.edit_presets_menu_pushbutton_05, self.edit_preset_menu_05)

                    self.edit_presets_menu_pushbutton_01.setText(preset_01_push_btn_text)
                    try:
                        self.edit_presets_menu_pushbutton_02.setText(preset_02_push_btn_text)
                    except:
                        pass
                    try:
                        self.edit_presets_menu_pushbutton_03.setText(preset_03_push_btn_text)
                    except:
                        pass
                    try:
                        self.edit_presets_menu_pushbutton_04.setText(preset_04_push_btn_text)
                    except:
                        pass
                    try:
                        self.edit_presets_menu_pushbutton_05.setText(preset_05_push_btn_text)
                    except:
                        pass

                    print ('\n--> existing export presets loaded \n')

                else:
                    self.edit_menu_label.setEnabled(False)
                    self.edit_menu_push_btn.setEnabled(False)
                    self.edit_menu_visibility_label.setEnabled(False)
                    self.edit_menu_visibility_push_btn.setEnabled(False)
                    self.edit_menu_name_label.setEnabled(False)
                    self.edit_menu_name_lineedit.setEnabled(False)
                    self.edit_saved_preset_type_label_01.setEnabled(False)
                    self.edit_saved_presets_label_01.setEnabled(False)
                    self.edit_export_path_label_01.setEnabled(False)
                    self.edit_preset_type_menu_pushbutton_01.setEnabled(False)
                    self.edit_presets_menu_pushbutton_01.setEnabled(False)
                    self.edit_export_path_lineedit_01.setEnabled(False)
                    self.edit_server_browse_btn_01.setEnabled(False)
                    self.edit_token_push_btn_01.setEnabled(False)
                    self.edit_top_layer_pushbutton_01.setEnabled(False)
                    self.edit_foreground_pushbutton_01.setEnabled(False)
                    self.edit_between_marks_pushbutton_01.setEnabled(False)
                    self.edit_enable_preset_pushbutton_02.setEnabled(False)
                    self.edit_enable_preset_pushbutton_03.setEnabled(False)
                    self.edit_enable_preset_pushbutton_04.setEnabled(False)
                    self.edit_enable_preset_pushbutton_05.setEnabled(False)
                    self.edit_delete_btn.setEnabled(False)

                    self.edit_menu_visibility_push_btn.setText('')
                    self.edit_preset_type_menu_pushbutton_01.setText('')
                    self.edit_preset_type_menu_pushbutton_02.setText('')
                    self.edit_preset_type_menu_pushbutton_03.setText('')
                    self.edit_preset_type_menu_pushbutton_04.setText('')
                    self.edit_preset_type_menu_pushbutton_05.setText('')

                    print ('--> no existing presets found \n')

            def delete_preset():

                script_name = self.edit_menu_push_btn.text().split(' ', 1)[1]

                if FlameMessageWindow('warning', f'{SCRIPT_NAME}: Confirm Operation', f'Delete preset: <b>{script_name}'):

                    if 'Shared: ' in self.edit_menu_push_btn.text():
                        script_path = os.path.join(self.shared_menus_dir, script_name)
                    else:
                        script_path = os.path.join(self.project_menus_dir, self.current_project, script_name)
                    print ('script_path:', script_path, '\n')

                    os.remove(script_path + '.py')
                    try:
                        os.remove(script_path + '.pyc')
                    except:
                        pass

                    pyflame_print(SCRIPT_NAME, f'Menu deleted: {script_name}')

                    # Reload button menus

                    build_main_menu_preset_menu(self.edit_menu_push_btn, self.edit_export_name_menu)
                    load_preset()

                    # Refresh python hooks

                    pyflame_refresh_hooks(SCRIPT_NAME)

            def build_main_menu_preset_menu(created_menu_btn, created_presets_menu):

                def add_menu(menu_name):

                    created_menu_btn.setText(menu_name)
                    load_preset()

                # Get list of created presets

                shared_menu_list = ['Shared: ' + menu[:-3] for menu in os.listdir(self.shared_menus_dir) if menu.endswith('.py')]
                shared_menu_list.sort()
                #print ('shared_menu_list:', shared_menu_list)

                if os.path.isdir(self.current_project_created_presets_path):
                    project_menu_list = ['Project: ' + menu[:-3] for menu in os.listdir(self.current_project_created_presets_path) if menu.endswith('.py')]
                    #print ('project_menu_list:', project_menu_list)
                else:
                    project_menu_list = []
                project_menu_list.sort()

                menu_list = shared_menu_list + project_menu_list
                #print ('menu_list:', menu_list)

                # Clear Format Preset menu list

                created_presets_menu.clear()

                # Set button to first preset in list

                if menu_list != []:
                    created_menu_btn.setText(str(menu_list[0]))
                else:
                    created_menu_btn.setText('No Saved Presets Found')

                # Dynamically create button menus

                for menu_name in menu_list:
                    created_presets_menu.addAction(menu_name, partial(add_menu, menu_name))

            # Labels

            self.edit_menu_visibility_label = FlameLabel('Menu Visibility', label_width=110)
            self.edit_menu_label = FlameLabel('Menu', label_width=110)
            self.edit_menu_name_label = FlameLabel('Menu Name', label_width=110)

            # LineEdits

            self.edit_menu_name_lineedit = FlameLineEdit('', width=150, max_width=450)

            ## -------------------------------------------------------------

            ## Select Menu Push Button Menu

            self.edit_export_name_menu = QtWidgets.QMenu(self.window)
            self.edit_export_name_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#2d3744; border: none; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
            self.edit_menu_push_btn = QtWidgets.QPushButton('', self.window)
            self.edit_menu_push_btn.setMenu(self.edit_export_name_menu)
            self.edit_menu_push_btn.setMinimumSize(QtCore.QSize(450, 28))
            self.edit_menu_push_btn.setMaximumSize(QtCore.QSize(450, 28))
            self.edit_menu_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.edit_menu_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #2d3744; border: none; font: 14px "Discreet"}'
                                                  'QPushButton:disabled {color: #747474; background-color: #2d3744; border: none}'
                                                  'QPushButton:hover {border: 1px solid #5a5a5a}'
                                                  'QPushButton::menu-indicator {image: none}')

            build_main_menu_preset_menu(self.edit_menu_push_btn, self.edit_export_name_menu)

            # Menu Pushbutton

            export_type_options = ['Project', 'Shared']
            self.edit_menu_visibility_push_btn = FlamePushButtonMenu('Project', export_type_options)

            # Push Button

            self.edit_reveal_in_mediahub_pushbutton = FlamePushButton('Reveal in Mediahub', self.reveal_in_mediahub, button_width=160)
            self.edit_reveal_in_finder_pushbutton = FlamePushButton('Reveal in Finder', self.reveal_in_finder, button_width=160)

            # Buttons

            self.edit_delete_btn = FlameButton('Delete', delete_preset, button_width=160)
            self.edit_save_btn = FlameButton('Save', partial(self.save_menus, 'Edit'), button_width=160)
            self.edit_done_btn = FlameButton('Done', self.window.close, button_width=160)

            # -------------------------------------------------------------

            edit_presets()
            load_preset()

            # Window Layout

            edit_gridbox = QtWidgets.QGridLayout()
            edit_gridbox.setRowMinimumHeight(3, 30)
            edit_gridbox.setRowMinimumHeight(5, 30)

            edit_gridbox.addWidget(self.edit_menu_label, 0, 0)
            edit_gridbox.addWidget(self.edit_menu_push_btn, 0, 1, 1, 4)
            edit_gridbox.addWidget(self.edit_delete_btn, 0, 5)

            edit_gridbox.addWidget(self.edit_menu_visibility_label, 1, 0)
            edit_gridbox.addWidget(self.edit_menu_visibility_push_btn, 1, 1)

            edit_gridbox.addWidget(self.edit_menu_name_label, 2, 0)
            edit_gridbox.addWidget(self.edit_menu_name_lineedit, 2, 1, 1, 4)

            edit_gridbox.addWidget(self.edit_reveal_in_mediahub_pushbutton, 2, 5)
            edit_gridbox.addWidget(self.edit_reveal_in_finder_pushbutton, 3, 5)

            edit_gridbox.addWidget(self.edit_preset_tabs, 4, 0, 1, 6)

            edit_gridbox.addWidget(self.edit_done_btn, 6, 4)
            edit_gridbox.addWidget(self.edit_save_btn, 6, 5)

            self.window.edit_tab.setLayout(edit_gridbox)

        create_tab()
        edit_tab()

        # Add Widgets to Layout

        gridbox.addWidget(self.main_tabs)

        self.window.show()

    def server_path_browse(self, lineedit):

        export_path = pyflame_file_browser('Select Directory', [''], lineedit.text(), select_directory=True, window_to_hide=[self.window])

        if export_path:
            lineedit.setText(export_path)

    def preset_check(self, tab_options_dict):

        main_tab = str(next(iter(tab_options_dict))).split('_', 1)[0]
        #print ('main_tab:', main_tab)

        # Check Menu Name entry

        if main_tab == 'create':
            if not self.menu_name_lineedit.text():
                return 'Add menu name'
        else:
            if not self.edit_menu_name_lineedit.text():
                return 'Add menu name'

        for key, value in tab_options_dict.items():

            tab_number = key.rsplit('_', 1)[1].capitalize()
            #print ('tab_number:', tab_number)

            if tab_number != 'Zero':

                # If tab is enabled, check settings

                if value['Enabled'] == True:

                    # Make sure on Shared saved presets are used with shared visibility menus

                    if main_tab == 'create':
                        if 'Shared' in self.menu_visibility_push_btn.text() and 'Shared:' not in value['Preset Type Menu']:
                            return '<center>Preset %s: Only a SHARED Saved Preset can be added to a Menu with Shared Menu Visibility.' % tab_number
                    else:
                        if 'Shared' in self.edit_menu_visibility_push_btn.text() and 'Shared:' not in value['Preset Type Menu']:
                            return '<center>Preset %s: Only a SHARED Saved Preset can be added to a Menu with Shared Menu Visibility.' % tab_number

                    # Give message if trying to save with No Save Presets Found

                    if value['Preset Menu'] == 'No Saved Presets Found':
                        return '<center> Preset %s: No saved presets found - Select a different Preset Type or save a preset in Flame.' % tab_number

                    # Check path entry

                    if not value['Export Path']:
                        return '<center>Preset %s: Enter export path.' % tab_number

    def save_menus(self, tab):
        import flame

        def set_menu_save_path():

            # Set path for new menu file

            if menu_visibility == 'Project':
                menu_save_dir = os.path.join(self.project_menus_dir, self.current_project)
                self.script_project = self.current_project
            else:
                menu_save_dir = self.shared_menus_dir
                self.script_project = 'None'

            if not os.path.isdir(menu_save_dir):
                os.makedirs(menu_save_dir)

            self.python_file_name = menu_name.replace('.', '_') + '.py'

            self.menu_save_file = os.path.join(menu_save_dir, self.python_file_name)

            # ('menu_save_file:', self.menu_save_file, '\n')

        def menu_template_replace_tokens():

            # Replace tokens in menu template file

            template_token_dict = {}

            template_token_dict['<ScriptProject>'] = self.script_project
            template_token_dict['<PresetName>'] = menu_name
            template_token_dict['<PresetType>'] = menu_visibility
            template_token_dict['<RevealInMediaHub>'] = reveal_in_mediahub
            template_token_dict['<RevealInFinder>'] = reveal_in_finder
            template_token_dict['<FlameMinMaxVersion>'] = self.flame_min_max_version

            # Open menu template

            get_config_values = open(self.menu_template_path, 'r')
            self.template_lines = get_config_values.read().splitlines()

            # Replace tokens in menu template

            for key, value in template_token_dict.items():
                for line in self.template_lines:
                    if key in line:
                        line_index = self.template_lines.index(line)
                        new_line = re.sub(key, value, line)
                        self.template_lines[line_index] = new_line

        def menu_template_preset_lines():

            def get_preset_path(preset_type_menu, preset_menu):

                # Get selected preset path

                if 'Project' in preset_type_menu:
                    preset_path = self.project_preset_path
                else:
                    preset_path = self.shared_preset_path

                if 'Movie' in preset_type_menu:
                    preset_dir_path = preset_path + '/movie_file'
                else:
                    preset_dir_path = preset_path + '/file_sequence'

                preset_file_path = os.path.join(preset_dir_path, preset_menu) + '.xml'

                #print ('preset path:', preset_file_path, '\n')

                return preset_file_path

            def new_lines(tab_number, top_layer, foreground_export, export_between_marks, export_path, preset_file_path):

                menu_lines.append("")
                menu_lines.append("        # Export preset %s" % tab_number)
                menu_lines.append("")
                menu_lines.append("        # Export using top video track")
                menu_lines.append("")
                menu_lines.append("        clip_output.use_top_video_track = %s" % top_layer)
                menu_lines.append("        print ('\\n--> Export using top layer: %s')" % top_layer)
                menu_lines.append("")
                menu_lines.append("        # Set export to foreground")
                menu_lines.append("")
                menu_lines.append("        clip_output.foreground = %s" % foreground_export)
                menu_lines.append("        print ('--> Export in foreground: %s')" % foreground_export)
                menu_lines.append("")
                menu_lines.append("        # Export between markers")
                menu_lines.append("")
                menu_lines.append("        clip_output.export_between_marks = %s" % export_between_marks)
                menu_lines.append("        print ('--> Export between marks: %s\\n')" % export_between_marks)
                menu_lines.append("")
                menu_lines.append("        # Translate tokens in path")
                menu_lines.append("")
                menu_lines.append("        new_export_path = translate_token_path(clip, '%s')" % export_path)
                menu_lines.append("")
                menu_lines.append("        if not new_export_path:")
                menu_lines.append("            return")
                menu_lines.append("")
                menu_lines.append("        if not os.path.isdir(new_export_path):")
                menu_lines.append("            os.makedirs(new_export_path)")
                menu_lines.append("")
                menu_lines.append("        clip_output.export(clip, '%s', new_export_path)" % preset_file_path)
                menu_lines.append("")
                menu_lines.append("        # Export preset %s END" % tab_number)
                menu_lines.append("")

            # Loop through tabs to build preset menus

            for key, value in tab_options_dict.items():
                tab_number = key.rsplit('_', 1)[1].capitalize()
                if tab_number != 'Zero':
                    if value['Enabled'] == True:
                        preset_file_path = get_preset_path(value['Preset Type Menu'], value['Preset Menu'])
                        new_lines(tab_number, value['Top Layer'], value['Foreground Export'], value['Export Between Marks'], value['Export Path'], preset_file_path)

        def save_config():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            export_path = root.find('.//export_path')
            export_path.text = self.export_path_lineedit_01.text()

            use_top_layer = root.find('.//use_top_layer')
            use_top_layer.text = str(self.top_layer_pushbutton_01.isChecked())

            export_in_foreground = root.find('.//export_in_foreground')
            export_in_foreground.text = str(self.foreground_pushbutton_01.isChecked())

            export_between_marks = root.find('.//export_between_marks')
            export_between_marks.text = str(self.between_marks_pushbutton_01.isChecked())

            reveal_in_mediahub = root.find('.//reveal_in_mediahub')
            reveal_in_mediahub.text = str(self.reveal_in_mediahub_pushbutton.isChecked())

            reveal_in_finder = root.find('.//reveal_in_finder')
            reveal_in_finder.text = str(self.reveal_in_finder_pushbutton.isChecked())

            xml_tree.write(self.config_xml)

            pyflame_print(SCRIPT_NAME, 'Config saved.')

        if tab == 'Create':
            tab_options_dict = {'create_tab_zero':{
                                        'Menu Visibility': self.menu_visibility_push_btn.text(),
                                        'Menu Name': self.menu_name_lineedit.text(),
                                        'Reveal in MediaHub': self.reveal_in_mediahub_pushbutton.isChecked(),
                                        'Reveal in Finder': self.reveal_in_finder_pushbutton.isChecked()},
                                'create_tab_one': {
                                        'Enabled' : True,
                                        'Preset Type Menu' : self.preset_type_menu_pushbutton_01.text(),
                                        'Preset Menu' : self.presets_menu_pushbutton_01.text(),
                                        'Export Path' : self.export_path_lineedit_01.text(),
                                        'Top Layer' : self.top_layer_pushbutton_01.isChecked(),
                                        'Foreground Export' : self.foreground_pushbutton_01.isChecked(),
                                        'Export Between Marks' : self.between_marks_pushbutton_01.isChecked()},
                                'create_tab_two': {
                                        'Enabled' : self.enable_preset_pushbutton_02.isChecked(),
                                        'Preset Type Menu' : self.preset_type_menu_pushbutton_02.text(),
                                        'Preset Menu' : self.presets_menu_pushbutton_02.text(),
                                        'Export Path' : self.export_path_lineedit_02.text(),
                                        'Top Layer' : self.top_layer_pushbutton_02.isChecked(),
                                        'Foreground Export' : self.foreground_pushbutton_02.isChecked(),
                                        'Export Between Marks' : self.between_marks_pushbutton_02.isChecked()},
                                'create_tab_three': {
                                        'Enabled' : self.enable_preset_pushbutton_03.isChecked(),
                                        'Preset Type Menu' : self.preset_type_menu_pushbutton_03.text(),
                                        'Preset Menu' : self.presets_menu_pushbutton_03.text(),
                                        'Export Path' : self.export_path_lineedit_03.text(),
                                        'Top Layer' : self.top_layer_pushbutton_03.isChecked(),
                                        'Foreground Export' : self.foreground_pushbutton_03.isChecked(),
                                        'Export Between Marks' : self.between_marks_pushbutton_03.isChecked()},
                                'create_tab_four': {
                                        'Enabled' : self.enable_preset_pushbutton_04.isChecked(),
                                        'Preset Type Menu' : self.preset_type_menu_pushbutton_04.text(),
                                        'Preset Menu' : self.presets_menu_pushbutton_04.text(),
                                        'Export Path' : self.export_path_lineedit_04.text(),
                                        'Top Layer' : self.top_layer_pushbutton_04.isChecked(),
                                        'Foreground Export' : self.foreground_pushbutton_04.isChecked(),
                                        'Export Between Marks' : self.between_marks_pushbutton_04.isChecked()},
                                'create_tab_five': {
                                        'Enabled' : self.enable_preset_pushbutton_05.isChecked(),
                                        'Preset Type Menu' : self.preset_type_menu_pushbutton_05.text(),
                                        'Preset Menu' : self.presets_menu_pushbutton_05.text(),
                                        'Export Path' : self.export_path_lineedit_05.text(),
                                        'Top Layer' : self.top_layer_pushbutton_05.isChecked(),
                                        'Foreground Export' : self.foreground_pushbutton_05.isChecked(),
                                        'Export Between Marks' : self.between_marks_pushbutton_05.isChecked()}
                                        }
        else:
            tab_options_dict = {'edit_tab_zero':{
                                        'Menu Visibility': self.edit_menu_visibility_push_btn.text(),
                                        'Menu Name': self.edit_menu_name_lineedit.text(),
                                        'Reveal in MediaHub': self.edit_reveal_in_mediahub_pushbutton.isChecked(),
                                        'Reveal in Finder': self.edit_reveal_in_finder_pushbutton.isChecked()},
                                'edit_tab_one': {
                                        'Enabled' : True,
                                        'Preset Type Menu' : self.edit_preset_type_menu_pushbutton_01.text(),
                                        'Preset Menu' : self.edit_presets_menu_pushbutton_01.text(),
                                        'Export Path' : self.edit_export_path_lineedit_01.text(),
                                        'Top Layer' : self.edit_top_layer_pushbutton_01.isChecked(),
                                        'Foreground Export' : self.edit_foreground_pushbutton_01.isChecked(),
                                        'Export Between Marks' : self.edit_between_marks_pushbutton_01.isChecked()},
                                'edit_tab_two': {
                                        'Enabled' : self.edit_enable_preset_pushbutton_02.isChecked(),
                                        'Preset Type Menu' : self.edit_preset_type_menu_pushbutton_02.text(),
                                        'Preset Menu' : self.edit_presets_menu_pushbutton_02.text(),
                                        'Export Path' : self.edit_export_path_lineedit_02.text(),
                                        'Top Layer' : self.edit_top_layer_pushbutton_02.isChecked(),
                                        'Foreground Export' : self.edit_foreground_pushbutton_02.isChecked(),
                                        'Export Between Marks' : self.edit_between_marks_pushbutton_02.isChecked()},
                                'edit_tab_three': {
                                        'Enabled' : self.edit_enable_preset_pushbutton_03.isChecked(),
                                        'Preset Type Menu' : self.edit_preset_type_menu_pushbutton_03.text(),
                                        'Preset Menu' : self.edit_presets_menu_pushbutton_03.text(),
                                        'Export Path' : self.edit_export_path_lineedit_03.text(),
                                        'Top Layer' : self.edit_top_layer_pushbutton_03.isChecked(),
                                        'Foreground Export' : self.edit_foreground_pushbutton_03.isChecked(),
                                        'Export Between Marks' : self.edit_between_marks_pushbutton_03.isChecked()},
                                'edit_tab_four': {
                                        'Enabled' : self.edit_enable_preset_pushbutton_04.isChecked(),
                                        'Preset Type Menu' : self.edit_preset_type_menu_pushbutton_04.text(),
                                        'Preset Menu' : self.edit_presets_menu_pushbutton_04.text(),
                                        'Export Path' : self.edit_export_path_lineedit_04.text(),
                                        'Top Layer' : self.edit_top_layer_pushbutton_04.isChecked(),
                                        'Foreground Export' : self.edit_foreground_pushbutton_04.isChecked(),
                                        'Export Between Marks' : self.edit_between_marks_pushbutton_04.isChecked()},
                                'edit_tab_five': {
                                        'Enabled' : self.edit_enable_preset_pushbutton_05.isChecked(),
                                        'Preset Type Menu' : self.edit_preset_type_menu_pushbutton_05.text(),
                                        'Preset Menu' : self.edit_presets_menu_pushbutton_05.text(),
                                        'Export Path' : self.edit_export_path_lineedit_05.text(),
                                        'Top Layer' : self.edit_top_layer_pushbutton_05.isChecked(),
                                        'Foreground Export' : self.edit_foreground_pushbutton_05.isChecked(),
                                        'Export Between Marks' : self.edit_between_marks_pushbutton_05.isChecked()}
                                        }

        # Get tab zero values

        for key, value in tab_options_dict.items():
            if 'tab_zero' in key:
                menu_visibility = value['Menu Visibility']
                menu_name = value['Menu Name']
                reveal_in_mediahub = str(value['Reveal in MediaHub'])
                reveal_in_finder = str(value['Reveal in Finder'])

        # Check options for proper entries

        preset_error = self.preset_check(tab_options_dict)
        if preset_error:
            return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', f'{preset_error}')

        set_menu_save_path()

        menu_template_replace_tokens()

        menu_lines = []

        menu_template_preset_lines()

        # Insert new preset menu lines into template

        for i in range(len(self.template_lines)):
            if self.template_lines[i] == '    for clip in selection:':
                i += 1
                for line in menu_lines:
                    self.template_lines.insert(i, line)
                    i += 1

        # Check if new preset file already exists in current folder

        if os.path.isfile(self.menu_save_file):
            if not FlameMessageWindow('warning', f'{SCRIPT_NAME}: Confirm Operation', 'Overwrite exisitng file?'):
                print ('--> save cancelled \n')
                return

        # Check other folders for menu with same name

        menu_save_folder = self.menu_save_file.rsplit('/', 1)[0]
        # ('menu_save_folder:', menu_save_folder, '\n')

        for root, dirs, files in os.walk(SCRIPT_PATH):
            if root != menu_save_folder:
                for f in files:
                    if f == self.python_file_name:
                        if not FlameMessageWindow('warning', f'{SCRIPT_NAME}: Confirm Operation', 'Overwrite exisitng file?'):
                            return

                        # Delete old script file before saving new version

                        old_script_path = os.path.join(root, f)
                        os.remove(old_script_path)
                        try:
                            os.remove(old_script_path + 'c')
                        except:
                            pass

        save_config()

        # Save new menu

        out_file = open(self.menu_save_file, 'w')
        for line in self.template_lines:
            print(line, file=out_file)
        out_file.close()

        # Refresh python hooks

        pyflame_refresh_hooks(SCRIPT_NAME)

        FlameMessageWindow('message', f'{SCRIPT_NAME}: Operation Complete', f'Export Menu Saved: {menu_name}')

        # Close setup window

        self.window.close()

        # Reopen setup window. Passing SCRIPT_NAME as selection since some value has to be passed as selection. Selection isn't being used.

        ExportSetup(SCRIPT_NAME)

#-------------------------------------#

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Create Export Menus',
                    'execute': ExportSetup,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
