'''
Script Name: Create Export Menus
Script Version: 3.4
Flame Version: 2020.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 03.29.20
Update Date: 05.21.21

Custom Action Type: Media Panel

Description:

    Create custom right-click export menu's from saved export presets

    To create menus:

    Flame Main Menu -> pyFlame -> Create Export Menus

    To access newly created menus:

    Right-click on clip -> Project Export Presets... -> Select export
    Right-click on clip -> Shared Export Presets... -> Select export

To install:

    Copy script into /opt/Autodesk/shared/python/create_export_menus

Updates:

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

from __future__ import print_function
import os

VERSION = 'v3.4'

SCRIPT_PATH = '/opt/Autodesk/shared/python/create_export_menus'

class ExportSetup(object):

    def __init__(self, selection):
        import flame
        import ast

        print ('\n', '>' * 20, 'create export menus %s' % VERSION, '<' * 20, '\n')

        #  Create/Check for folders and config file

        # Define Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')
        self.project_menus_dir = os.path.join(SCRIPT_PATH, 'project_menus')
        self.shared_menus_dir = os.path.join(SCRIPT_PATH, 'shared_menus')

        if not os.path.isdir(self.project_menus_dir):
            os.makedirs(self.project_menus_dir)

        if not os.path.isdir(self.shared_menus_dir):
            os.makedirs(self.shared_menus_dir)

        if not os.path.isdir(self.config_path):
            os.makedirs(self.config_path)

        if not os.path.isfile(self.config_file):
            print ('>>> config file does not exist, creating new config file <<<')

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame Create Export Menus script.')
            config_text.insert(1, 'Export Path')
            config_text.insert(2, '/')
            config_text.insert(3, 'Use Top Layer')
            config_text.insert(4, 'False')
            config_text.insert(5, 'Export in Foreground')
            config_text.insert(6, 'False')
            config_text.insert(7, 'Export Between Marks')
            config_text.insert(8, 'False')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

        # Get config file values
        #-----------------------------------------

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.export_path = values[2]
        self.top_layer_checked = ast.literal_eval(values[4])
        self.export_foreground_checked = ast.literal_eval(values[6])
        self.export_between_marks = ast.literal_eval(values[8])

        get_config_values.close()

        print ('\n>>> config loaded <<<\n')

        #-----------------------------------------

        # Paths

        self.current_project = flame.project.current_project.name

        self.current_project_created_presets_path = os.path.join(SCRIPT_PATH, 'project_menus', self.current_project)
        print ('current_project_created_presets_path:', self.current_project_created_presets_path)

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
        print ('project_movie_preset_list:', self.project_movie_preset_list)

        try:
            self.project_file_seq_preset_path = os.path.join(self.project_preset_path, 'file_sequence')
            self.project_file_seq_preset_list = [x for x in os.listdir(self.project_file_seq_preset_path) if x.endswith('.xml')]
        except:
            self.project_file_seq_preset_list = []
        print ('project_file_seq_preset_list:', self.project_file_seq_preset_list)

        try:
            self.shared_movie_preset_path = os.path.join(self.shared_preset_path, 'movie_file')
            self.shared_movie_preset_list = [x for x in os.listdir(self.shared_movie_preset_path) if x.endswith('.xml')]
        except:
            self.shared_movie_preset_list = []
        print ('shared_movie_preset_list:', self.shared_movie_preset_list)

        try:
            self.shared_file_seq_preset_path = os.path.join(self.shared_preset_path, 'file_sequence')
            self.shared_file_seq_preset_list = [x for x in os.listdir(self.shared_file_seq_preset_path) if x.endswith('.xml')]
        except:
            self.shared_file_seq_preset_list = []
        print ('shared_file_seq_preset_list:', self.shared_file_seq_preset_list, '\n')

        self.export_menu_text = ''
        self.format_preset_text = ''


        self.setup_window()

    def setup_window(self):
        from PySide2 import QtCore, QtWidgets

        self.window = QtWidgets.QWidget()
        self.main_tabs = QtWidgets.QTabWidget()
        self.preset_tabs = QtWidgets.QTabWidget()

        self.window.setMinimumSize(QtCore.QSize(1200, 500))
        self.window.setMaximumSize(QtCore.QSize(1200, 500))
        self.window.setWindowTitle('Create Export Menus %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #212121')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Main Tabs

        self.window.create_tab = QtWidgets.QWidget()
        self.window.edit_tab = QtWidgets.QWidget()

        self.main_tabs.setStyleSheet('QTabWidget {background-color: #313131; font: 14px "Discreet"}'
                                     'QTabWidget::tab-bar {alignment: center}'
                                     'QTabBar::tab {color: #9a9a9a; background-color: #212121; border: 1px solid #3a3a3a; border-bottom-color: #555555; min-width: 20ex; padding: 5px}'
                                     'QTabBar::tab:selected {color: #bababa; border: 1px solid #555555; border-bottom: 1px solid #212121}'
                                     'QTabWidget::pane {border-top: 1px solid #555555; top: -0.05em}')

        self.main_tabs.addTab(self.window.create_tab, 'Create')
        self.main_tabs.addTab(self.window.edit_tab, 'Edit')

        self.main_tabs.setFocusPolicy(QtCore.Qt.NoFocus)

        def create_tab():

            def create_presets(self):
                from PySide2 import QtCore, QtWidgets

                # Menus for preset tabs two thru five

                def token_action_menu(lineedit, token_menu):
                    from functools import partial

                    def insert_token(token):
                        for key, value in token_dict.items():
                            if key == token:
                                token_name = value
                        lineedit.insert(token_name)

                    token_list = ['Project Name', 'Shot Name', 'Batch Group Name', 'Batch Group Shot Name', 'Sequence Name', 'User Name', 'Clip Name',
                                  'Clip Resolution', 'Clip Height', 'Clip Width', 'Year (YYYY)', 'Year (YY)', 'Month', 'Day', 'Hour', 'Minute', 'AM/PM']

                    token_dict = {'Project Name': '<ProjectName>', 'Shot Name': '<ShotName>', 'Batch Group Name': '<BatchGroupName>',
                                  'Batch Group Shot Name': '<BatchGroupShotName>', 'Sequence Name': '<SeqName>', 'User Name': '<UserName>',
                                  'Clip Name': '<ClipName>', 'Clip Resolution': '<Resolution>', 'Clip Height': '<ClipHeight>',
                                  'Clip Width': '<ClipWidth>', 'Year (YYYY)': '<YYYY>', 'Year (YY)': '<YY>', 'Month': '<MM>',
                                  'Day': '<DD>', 'Hour': '<Hour>', 'Minute': '<Minute>', 'AM/PM': '<AMPM>',}

                    for token in token_list:
                        token_menu.addAction(token, partial(insert_token, token))

                def set_export_push_button(export_btn, saved_presets_btn, saved_presets_menu):

                    if self.project_movie_preset_list != []:
                        preset_name = str(self.project_movie_preset_list[0])[:-4]
                        export_btn.setText('Project: Movie')
                        saved_presets_btn.setText(preset_name)
                        build_format_preset_menus(self.project_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                    elif self.shared_movie_preset_list != []:
                        preset_name = str(self.shared_movie_preset_list[0])[:-4]
                        export_btn.setText('Shared: Movie')
                        saved_presets_btn.setText(preset_name)
                        build_format_preset_menus(self.shared_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                    elif self.project_file_seq_preset_list != []:
                        preset_name = str(self.project_file_seq_preset_list[0])[:-4]
                        export_btn.setText('Project: File Sequence')
                        saved_presets_btn.setText(preset_name)
                        build_format_preset_menus(self.project_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                    elif self.shared_file_seq_preset_list != []:
                        preset_name = str(self.shared_file_seq_preset_list[0])[:-4]
                        export_btn.setText('Shared: File Sequence')
                        saved_presets_btn.setText(preset_name)
                        build_format_preset_menus(self.shared_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                    else:
                        export_btn.setText('No Saved Export Presets')
                        saved_presets_btn.setText('No Saved Export Presets')

                def project_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Project: Movie')
                    build_format_preset_menus(self.project_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def project_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Project: File Sequence')
                    build_format_preset_menus(self.project_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def shared_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Shared: Movie')
                    build_format_preset_menus(self.shared_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def shared_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Shared: File Sequence')
                    build_format_preset_menus(self.shared_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def build_format_preset_menus(preset_list, export_btn, saved_presets_btn, saved_presets_menu):
                    from functools import partial

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

                def export_preset_one_tab():
                    from functools import partial

                    # Labels

                    self.saved_preset_type_label_01 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.saved_preset_type_label_01.setMinimumWidth(140)
                    self.saved_preset_type_label_01.setMaximumWidth(150)
                    self.saved_preset_type_label_01.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"')

                    self.saved_presets_label_01 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.saved_presets_label_01.setMinimumWidth(140)
                    self.saved_presets_label_01.setMaximumWidth(150)
                    self.saved_presets_label_01.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"')

                    self.export_path_label_01 = QtWidgets.QLabel('Export Path ', self.window)
                    self.export_path_label_01.setMinimumWidth(140)
                    self.export_path_label_01.setMaximumWidth(150)
                    self.export_path_label_01.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"')

                    # LineEdits

                    self.export_path_lineedit_01 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.export_path_lineedit_01.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_path_lineedit_01.setMaximumSize(QtCore.QSize(450, 28))
                    self.export_path_lineedit_01.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"')

                    # Checkable Pushbuttons

                    self.top_layer_pushbutton_01 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.top_layer_pushbutton_01.setMinimumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_01.setMaximumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_01.setCheckable(True)
                    self.top_layer_pushbutton_01.setChecked(self.top_layer_checked)
                    self.top_layer_pushbutton_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.top_layer_pushbutton_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                               'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                               'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.foreground_pushbutton_01 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.foreground_pushbutton_01.setMinimumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_01.setMaximumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_01.setCheckable(True)
                    self.foreground_pushbutton_01.setChecked(self.export_foreground_checked)
                    self.foreground_pushbutton_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.foreground_pushbutton_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.between_marks_pushbutton_01 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.between_marks_pushbutton_01.setMinimumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_01.setMaximumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_01.setCheckable(True)
                    self.between_marks_pushbutton_01.setChecked(self.export_between_marks)
                    self.between_marks_pushbutton_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.between_marks_pushbutton_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.token_menu_01 = QtWidgets.QMenu(self.window)
                    self.token_menu_01.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.token_push_btn_01 = QtWidgets.QPushButton('Add Token', self.window)
                    self.token_push_btn_01.setMenu(self.token_menu_01)
                    self.token_push_btn_01.setMinimumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_01.setMaximumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.token_push_btn_01.setStyleSheet('color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"')

                    token_action_menu(self.export_path_lineedit_01, self.token_menu_01)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    def set_export_push_button_01():

                        if self.project_movie_preset_list != []:
                            preset_name = str(self.project_movie_preset_list[0])[:-4]
                            self.export_push_btn_01.setText('Project: Movie')
                            self.saved_presets_push_btn_01.setText(preset_name)
                            self.menu_name_lineedit.setText(preset_name)
                            build_format_preset_menus(self.project_movie_preset_list)

                        elif self.shared_movie_preset_list != []:
                            preset_name = str(self.shared_movie_preset_list[0])[:-4]
                            self.export_push_btn_01.setText('Shared: Movie')
                            self.saved_presets_push_btn_01.setText(preset_name)
                            self.menu_name_lineedit.setText(preset_name)
                            build_format_preset_menus(self.shared_movie_preset_list)

                        elif self.project_file_seq_preset_list != []:
                            preset_name = str(self.project_file_seq_preset_list[0])[:-4]
                            self.export_push_btn_01.setText('Project: File Sequence')
                            self.saved_presets_push_btn_01.setText(preset_name)
                            self.menu_name_lineedit.setText(preset_name)
                            build_format_preset_menus(self.project_file_seq_preset_list)

                        elif self.shared_file_seq_preset_list != []:
                            preset_name = str(self.shared_file_seq_preset_list[0])[:-4]
                            self.export_push_btn_01.setText('Shared: File Sequence')
                            self.saved_presets_push_btn_01.setText(preset_name)
                            self.menu_name_lineedit.setText(preset_name)
                            build_format_preset_menus(self.shared_file_seq_preset_list)

                        else:
                            self.export_push_btn_01.setText('No Saved Export Presets')
                            self.saved_presets_push_btn_01.setText('No Saved Export Presets')

                    def project_movie_menu_01():
                        self.export_push_btn_01.setText('Project: Movie')
                        build_format_preset_menus(self.project_movie_preset_list)
                        if self.project_movie_preset_list != []:
                            self.menu_name_lineedit.setText(str(self.project_movie_preset_list[0])[:-4])

                    def project_file_seq_menu_01():
                        self.export_push_btn_01.setText('Project: File Sequence')
                        build_format_preset_menus(self.project_file_seq_preset_list)
                        if self.project_file_seq_preset_list != []:
                            self.menu_name_lineedit.setText(str(self.project_file_seq_preset_list[0])[:-4])

                    def shared_movie_menu_01():
                        self.export_push_btn_01.setText('Shared: Movie')
                        build_format_preset_menus(self.shared_movie_preset_list)
                        if self.shared_movie_preset_list != []:
                            self.menu_name_lineedit.setText(str(self.shared_movie_preset_list[0])[:-4])

                    def shared_file_seq_menu_01():
                        self.export_push_btn_01.setText('Shared: File Sequence')
                        build_format_preset_menus(self.shared_file_seq_preset_list)
                        if self.shared_file_seq_preset_list != []:
                            self.menu_name_lineedit.setText(str(self.shared_file_seq_preset_list[0])[:-4])

                    self.export_menu_01 = QtWidgets.QMenu(self.window)
                    self.export_menu_01.addAction('Project: Movie', project_movie_menu_01)
                    self.export_menu_01.addAction('Project: File Sequence', project_file_seq_menu_01)
                    self.export_menu_01.addAction('Shared: Movie', shared_movie_menu_01)
                    self.export_menu_01.addAction('Shared: File Sequence', shared_file_seq_menu_01)
                    self.export_menu_01.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.export_push_btn_01 = QtWidgets.QPushButton(self.export_menu_text, self.window)
                    self.export_push_btn_01.setMenu(self.export_menu_01)
                    self.export_push_btn_01.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_01.setMaximumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.export_push_btn_01.setStyleSheet('color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    def build_format_preset_menus(preset_list):
                        from functools import partial

                        def menu(menu_name):
                            self.saved_presets_push_btn_01.setText(menu_name)
                            self.menu_name_lineedit.setText(menu_name)

                        # Clear Format Preset menu list

                        self.saved_preset_menu_01.clear()

                        # Set button to first preset in list

                        if preset_list != []:
                            self.saved_presets_push_btn_01.setText(str(preset_list[0])[:-4])
                        else:
                            self.saved_presets_push_btn_01.setText('No Saved Presets Found')

                        # Dynamically create button menus

                        for item in preset_list:
                            menu_name = item[:-4]
                            self.saved_preset_menu_01.addAction(menu_name, partial(menu, menu_name))

                    self.saved_preset_menu_01 = QtWidgets.QMenu(self.window)
                    self.saved_preset_menu_01.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                            'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.saved_presets_push_btn_01 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.saved_presets_push_btn_01.setMenu(self.saved_preset_menu_01)
                    self.saved_presets_push_btn_01.setMinimumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_01.setMaximumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.saved_presets_push_btn_01.setStyleSheet('color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"')

                    set_export_push_button_01()

                    # -------------------------------------------------------------

                    self.server_browse_btn_01 = QtWidgets.QPushButton('Browse', self.window)
                    self.server_browse_btn_01.setMinimumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_01.setMaximumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.server_browse_btn_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
                    self.server_browse_btn_01.clicked.connect(partial(self.server_path_browse, self.export_path_lineedit_01))

                    # Tab Layout

                    gridbox_tab1 = QtWidgets.QGridLayout()
                    gridbox_tab1.setMargin(30)
                    gridbox_tab1.setVerticalSpacing(5)
                    gridbox_tab1.setHorizontalSpacing(5)
                    gridbox_tab1.setColumnMinimumWidth(4, 100)

                    gridbox_tab1.addWidget(self.saved_preset_type_label_01, 0, 0)
                    gridbox_tab1.addWidget(self.export_push_btn_01, 0, 1)

                    gridbox_tab1.addWidget(self.saved_presets_label_01, 1, 0)
                    gridbox_tab1.addWidget(self.saved_presets_push_btn_01, 1, 1)

                    gridbox_tab1.addWidget(self.export_path_label_01, 2, 0)
                    gridbox_tab1.addWidget(self.export_path_lineedit_01, 2, 1)
                    gridbox_tab1.addWidget(self.server_browse_btn_01, 2, 2)
                    gridbox_tab1.addWidget(self.token_push_btn_01, 2, 3)

                    gridbox_tab1.addWidget(self.top_layer_pushbutton_01, 1, 5)
                    gridbox_tab1.addWidget(self.foreground_pushbutton_01, 2, 5)
                    gridbox_tab1.addWidget(self.between_marks_pushbutton_01, 3, 5)

                    self.window.tab1.setLayout(gridbox_tab1)

                def export_preset_two_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.enable_preset_pushbutton_02.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.saved_preset_type_label_02.setEnabled(switch)
                        self.saved_presets_label_02.setEnabled(switch)
                        self.export_path_label_02.setEnabled(switch)
                        self.export_path_lineedit_02.setEnabled(switch)
                        self.top_layer_pushbutton_02.setEnabled(switch)
                        self.foreground_pushbutton_02.setEnabled(switch)
                        self.between_marks_pushbutton_02.setEnabled(switch)
                        self.token_push_btn_02.setEnabled(switch)
                        self.export_push_btn_02.setEnabled(switch)
                        self.server_browse_btn_02.setEnabled(switch)
                        self.saved_presets_push_btn_02.setEnabled(switch)

                    # Labels

                    self.saved_preset_type_label_02 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.saved_preset_type_label_02.setMinimumWidth(140)
                    self.saved_preset_type_label_02.setMaximumWidth(150)
                    self.saved_preset_type_label_02.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                  'QLabel:disabled {color: #6a6a6a}')

                    self.saved_presets_label_02 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.saved_presets_label_02.setMinimumWidth(140)
                    self.saved_presets_label_02.setMaximumWidth(150)
                    self.saved_presets_label_02.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                              'QLabel:disabled {color: #6a6a6a}')

                    self.export_path_label_02 = QtWidgets.QLabel('Export Path ', self.window)
                    self.export_path_label_02.setMinimumWidth(140)
                    self.export_path_label_02.setMaximumWidth(150)
                    self.export_path_label_02.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                            'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.export_path_lineedit_02 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.export_path_lineedit_02.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_path_lineedit_02.setMaximumSize(QtCore.QSize(450, 28))
                    self.export_path_lineedit_02.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

                    # Checkable Pushbuttons

                    self.enable_preset_pushbutton_02 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.enable_preset_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_02.setCheckable(True)
                    self.enable_preset_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.enable_preset_pushbutton_02.clicked.connect(toggle_ui)
                    self.enable_preset_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')


                    self.top_layer_pushbutton_02 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.top_layer_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_02.setCheckable(True)
                    self.top_layer_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.top_layer_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                               'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                               'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')


                    self.foreground_pushbutton_02 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.foreground_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_02.setCheckable(True)
                    self.foreground_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.foreground_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.between_marks_pushbutton_02 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.between_marks_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_02.setCheckable(True)
                    self.between_marks_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.between_marks_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.token_menu_02 = QtWidgets.QMenu(self.window)
                    self.token_menu_02.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.token_push_btn_02 = QtWidgets.QPushButton('Add Token', self.window)
                    self.token_push_btn_02.setMenu(self.token_menu_02)
                    self.token_push_btn_02.setMinimumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_02.setMaximumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.token_push_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.export_path_lineedit_02, self.token_menu_02)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.export_menu_02 = QtWidgets.QMenu(self.window)
                    self.export_menu_02.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.export_push_btn_02 = QtWidgets.QPushButton('None Selected', self.window)
                    self.export_push_btn_02.setMenu(self.export_menu_02)
                    self.export_push_btn_02.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_02.setMaximumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.export_push_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                          'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.saved_preset_menu_02 = QtWidgets.QMenu(self.window)
                    self.saved_preset_menu_02.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                            'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.saved_presets_push_btn_02 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.saved_presets_push_btn_02.setMenu(self.saved_preset_menu_02)
                    self.saved_presets_push_btn_02.setMinimumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_02.setMaximumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.saved_presets_push_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    set_export_push_button(self.export_push_btn_02, self.saved_presets_push_btn_02, self.saved_preset_menu_02)

                    # -------------------------------------------------------------

                    self.server_browse_btn_02 = QtWidgets.QPushButton('Browse', self.window)
                    self.server_browse_btn_02.setMinimumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_02.setMaximumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.server_browse_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                            'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.server_browse_btn_02.clicked.connect(partial(self.server_path_browse, self.export_path_lineedit_02))

                    toggle_ui()

                    # Export pushbutton menus

                    self.export_menu_02.addAction('Project: Movie', partial(project_movie_menu, self.export_push_btn_02, self.saved_presets_push_btn_02, self.saved_preset_menu_02))
                    self.export_menu_02.addAction('Project: File Sequence', partial(project_file_seq_menu, self.export_push_btn_02, self.saved_presets_push_btn_02, self.saved_preset_menu_02))
                    self.export_menu_02.addAction('Shared: Movie', partial(shared_movie_menu, self.export_push_btn_02, self.saved_presets_push_btn_02, self.saved_preset_menu_02))
                    self.export_menu_02.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.export_push_btn_02, self.saved_presets_push_btn_02, self.saved_preset_menu_02))

                    # Tab Layout

                    gridbox_tab2 = QtWidgets.QGridLayout()
                    gridbox_tab2.setMargin(30)
                    gridbox_tab2.setVerticalSpacing(5)
                    gridbox_tab2.setHorizontalSpacing(5)
                    gridbox_tab2.setColumnMinimumWidth(4, 100)

                    gridbox_tab2.addWidget(self.saved_preset_type_label_02, 0, 0)
                    gridbox_tab2.addWidget(self.export_push_btn_02, 0, 1)

                    gridbox_tab2.addWidget(self.saved_presets_label_02, 1, 0)
                    gridbox_tab2.addWidget(self.saved_presets_push_btn_02, 1, 1)

                    gridbox_tab2.addWidget(self.export_path_label_02, 2, 0)
                    gridbox_tab2.addWidget(self.export_path_lineedit_02, 2, 1)
                    gridbox_tab2.addWidget(self.server_browse_btn_02, 2, 2)
                    gridbox_tab2.addWidget(self.token_push_btn_02, 2, 3)

                    gridbox_tab2.addWidget(self.enable_preset_pushbutton_02, 0, 5)
                    gridbox_tab2.addWidget(self.top_layer_pushbutton_02, 1, 5)
                    gridbox_tab2.addWidget(self.foreground_pushbutton_02, 2, 5)
                    gridbox_tab2.addWidget(self.between_marks_pushbutton_02, 3, 5)

                    self.window.tab2.setLayout(gridbox_tab2)

                def export_preset_three_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.enable_preset_pushbutton_03.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.saved_preset_type_label_03.setEnabled(switch)
                        self.saved_presets_label_03.setEnabled(switch)
                        self.export_path_label_03.setEnabled(switch)
                        self.export_path_lineedit_03.setEnabled(switch)
                        self.top_layer_pushbutton_03.setEnabled(switch)
                        self.foreground_pushbutton_03.setEnabled(switch)
                        self.between_marks_pushbutton_03.setEnabled(switch)
                        self.token_push_btn_03.setEnabled(switch)
                        self.export_push_btn_03.setEnabled(switch)
                        self.server_browse_btn_03.setEnabled(switch)
                        self.saved_presets_push_btn_03.setEnabled(switch)

                    # Labels

                    self.saved_preset_type_label_03 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.saved_preset_type_label_03.setMinimumWidth(140)
                    self.saved_preset_type_label_03.setMaximumWidth(150)
                    self.saved_preset_type_label_03.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                  'QLabel:disabled {color: #6a6a6a}')

                    self.saved_presets_label_03 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.saved_presets_label_03.setMinimumWidth(140)
                    self.saved_presets_label_03.setMaximumWidth(150)
                    self.saved_presets_label_03.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                              'QLabel:disabled {color: #6a6a6a}')

                    self.export_path_label_03 = QtWidgets.QLabel('Export Path ', self.window)
                    self.export_path_label_03.setMinimumWidth(140)
                    self.export_path_label_03.setMaximumWidth(150)
                    self.export_path_label_03.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                            'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.export_path_lineedit_03 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.export_path_lineedit_03.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_path_lineedit_03.setMaximumSize(QtCore.QSize(450, 28))
                    self.export_path_lineedit_03.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

                    # Checkable Pushbuttons

                    self.enable_preset_pushbutton_03 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.enable_preset_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_03.setCheckable(True)
                    self.enable_preset_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.enable_preset_pushbutton_03.clicked.connect(toggle_ui)
                    self.enable_preset_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.top_layer_pushbutton_03 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.top_layer_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_03.setCheckable(True)
                    self.top_layer_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.top_layer_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                               'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                               'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.foreground_pushbutton_03 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.foreground_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_03.setCheckable(True)
                    self.foreground_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.foreground_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.between_marks_pushbutton_03 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.between_marks_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_03.setCheckable(True)
                    self.between_marks_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.between_marks_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.token_menu_03 = QtWidgets.QMenu(self.window)
                    self.token_menu_03.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.token_push_btn_03 = QtWidgets.QPushButton('Add Token', self.window)
                    self.token_push_btn_03.setMenu(self.token_menu_03)
                    self.token_push_btn_03.setMinimumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_03.setMaximumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.token_push_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.export_path_lineedit_03, self.token_menu_03)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.export_menu_03 = QtWidgets.QMenu(self.window)
                    self.export_menu_03.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.export_push_btn_03 = QtWidgets.QPushButton('None Selected', self.window)
                    self.export_push_btn_03.setMenu(self.export_menu_03)
                    self.export_push_btn_03.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_03.setMaximumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.export_push_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                          'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.saved_preset_menu_03 = QtWidgets.QMenu(self.window)
                    self.saved_preset_menu_03.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                            'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.saved_presets_push_btn_03 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.saved_presets_push_btn_03.setMenu(self.saved_preset_menu_03)
                    self.saved_presets_push_btn_03.setMinimumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_03.setMaximumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.saved_presets_push_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    set_export_push_button(self.export_push_btn_03, self.saved_presets_push_btn_03, self.saved_preset_menu_03)

                    # -------------------------------------------------------------

                    self.server_browse_btn_03 = QtWidgets.QPushButton('Browse', self.window)
                    self.server_browse_btn_03.setMinimumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_03.setMaximumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.server_browse_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                            'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.server_browse_btn_03.clicked.connect(partial(self.server_path_browse, self.export_path_lineedit_03))

                    toggle_ui()

                    # Export pushbutton menus

                    self.export_menu_03.addAction('Project: Movie', partial(project_movie_menu, self.export_push_btn_03, self.saved_presets_push_btn_03, self.saved_preset_menu_03))
                    self.export_menu_03.addAction('Project: File Sequence', partial(project_file_seq_menu, self.export_push_btn_03, self.saved_presets_push_btn_03, self.saved_preset_menu_03))
                    self.export_menu_03.addAction('Shared: Movie', partial(shared_movie_menu, self.export_push_btn_03, self.saved_presets_push_btn_03, self.saved_preset_menu_03))
                    self.export_menu_03.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.export_push_btn_03, self.saved_presets_push_btn_03, self.saved_preset_menu_03))

                    # Tab Layout

                    gridbox_tab3 = QtWidgets.QGridLayout()
                    gridbox_tab3.setMargin(30)
                    gridbox_tab3.setVerticalSpacing(5)
                    gridbox_tab3.setHorizontalSpacing(5)
                    gridbox_tab3.setColumnMinimumWidth(4, 100)

                    gridbox_tab3.addWidget(self.saved_preset_type_label_03, 0, 0)
                    gridbox_tab3.addWidget(self.export_push_btn_03, 0, 1)

                    gridbox_tab3.addWidget(self.saved_presets_label_03, 1, 0)
                    gridbox_tab3.addWidget(self.saved_presets_push_btn_03, 1, 1)

                    gridbox_tab3.addWidget(self.export_path_label_03, 2, 0)
                    gridbox_tab3.addWidget(self.export_path_lineedit_03, 2, 1)
                    gridbox_tab3.addWidget(self.server_browse_btn_03, 2, 2)
                    gridbox_tab3.addWidget(self.token_push_btn_03, 2, 3)

                    gridbox_tab3.addWidget(self.enable_preset_pushbutton_03, 0, 5)
                    gridbox_tab3.addWidget(self.top_layer_pushbutton_03, 1, 5)
                    gridbox_tab3.addWidget(self.foreground_pushbutton_03, 2, 5)
                    gridbox_tab3.addWidget(self.between_marks_pushbutton_03, 3, 5)

                    self.window.tab3.setLayout(gridbox_tab3)

                def export_preset_four_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.enable_preset_pushbutton_04.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.saved_preset_type_label_04.setEnabled(switch)
                        self.saved_presets_label_04.setEnabled(switch)
                        self.export_path_label_04.setEnabled(switch)
                        self.export_path_lineedit_04.setEnabled(switch)
                        self.top_layer_pushbutton_04.setEnabled(switch)
                        self.foreground_pushbutton_04.setEnabled(switch)
                        self.between_marks_pushbutton_04.setEnabled(switch)
                        self.token_push_btn_04.setEnabled(switch)
                        self.export_push_btn_04.setEnabled(switch)
                        self.server_browse_btn_04.setEnabled(switch)
                        self.saved_presets_push_btn_04.setEnabled(switch)

                    # Labels

                    self.saved_preset_type_label_04 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.saved_preset_type_label_04.setMinimumWidth(140)
                    self.saved_preset_type_label_04.setMaximumWidth(150)
                    self.saved_preset_type_label_04.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                  'QLabel:disabled {color: #6a6a6a}')

                    self.saved_presets_label_04 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.saved_presets_label_04.setMinimumWidth(140)
                    self.saved_presets_label_04.setMaximumWidth(150)
                    self.saved_presets_label_04.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                              'QLabel:disabled {color: #6a6a6a}')

                    self.export_path_label_04 = QtWidgets.QLabel('Export Path ', self.window)
                    self.export_path_label_04.setMinimumWidth(140)
                    self.export_path_label_04.setMaximumWidth(150)
                    self.export_path_label_04.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                            'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.export_path_lineedit_04 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.export_path_lineedit_04.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_path_lineedit_04.setMaximumSize(QtCore.QSize(450, 28))
                    self.export_path_lineedit_04.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

                    # Checkable Pushbuttons

                    self.enable_preset_pushbutton_04 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.enable_preset_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_04.setCheckable(True)
                    self.enable_preset_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.enable_preset_pushbutton_04.clicked.connect(toggle_ui)
                    self.enable_preset_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.top_layer_pushbutton_04 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.top_layer_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_04.setCheckable(True)
                    self.top_layer_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.top_layer_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                               'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                               'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.foreground_pushbutton_04 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.foreground_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_04.setCheckable(True)
                    self.foreground_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.foreground_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.between_marks_pushbutton_04 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.between_marks_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_04.setCheckable(True)
                    self.between_marks_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.between_marks_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.token_menu_04 = QtWidgets.QMenu(self.window)
                    self.token_menu_04.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.token_push_btn_04 = QtWidgets.QPushButton('Add Token', self.window)
                    self.token_push_btn_04.setMenu(self.token_menu_04)
                    self.token_push_btn_04.setMinimumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_04.setMaximumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.token_push_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.export_path_lineedit_04, self.token_menu_04)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.export_menu_04 = QtWidgets.QMenu(self.window)
                    self.export_menu_04.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.export_push_btn_04 = QtWidgets.QPushButton('None Selected', self.window)
                    self.export_push_btn_04.setMenu(self.export_menu_04)
                    self.export_push_btn_04.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_04.setMaximumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.export_push_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                          'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.saved_preset_menu_04 = QtWidgets.QMenu(self.window)
                    self.saved_preset_menu_04.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                            'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.saved_presets_push_btn_04 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.saved_presets_push_btn_04.setMenu(self.saved_preset_menu_04)
                    self.saved_presets_push_btn_04.setMinimumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_04.setMaximumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.saved_presets_push_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    set_export_push_button(self.export_push_btn_04, self.saved_presets_push_btn_04, self.saved_preset_menu_04)

                    # -------------------------------------------------------------

                    self.server_browse_btn_04 = QtWidgets.QPushButton('Browse', self.window)
                    self.server_browse_btn_04.setMinimumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_04.setMaximumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.server_browse_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                            'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.server_browse_btn_04.clicked.connect(partial(self.server_path_browse, self.export_path_lineedit_04))

                    toggle_ui()

                    # Export pushbutton menus

                    self.export_menu_04.addAction('Project: Movie', partial(project_movie_menu, self.export_push_btn_04, self.saved_presets_push_btn_04, self.saved_preset_menu_04))
                    self.export_menu_04.addAction('Project: File Sequence', partial(project_file_seq_menu, self.export_push_btn_04, self.saved_presets_push_btn_04, self.saved_preset_menu_04))
                    self.export_menu_04.addAction('Shared: Movie', partial(shared_movie_menu, self.export_push_btn_04, self.saved_presets_push_btn_04, self.saved_preset_menu_04))
                    self.export_menu_04.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.export_push_btn_04, self.saved_presets_push_btn_04, self.saved_preset_menu_04))

                    # Tab Layout

                    gridbox_tab4 = QtWidgets.QGridLayout()
                    gridbox_tab4.setMargin(30)
                    gridbox_tab4.setVerticalSpacing(5)
                    gridbox_tab4.setHorizontalSpacing(5)
                    gridbox_tab4.setColumnMinimumWidth(4, 100)

                    gridbox_tab4.addWidget(self.saved_preset_type_label_04, 0, 0)
                    gridbox_tab4.addWidget(self.export_push_btn_04, 0, 1)

                    gridbox_tab4.addWidget(self.saved_presets_label_04, 1, 0)
                    gridbox_tab4.addWidget(self.saved_presets_push_btn_04, 1, 1)

                    gridbox_tab4.addWidget(self.export_path_label_04, 2, 0)
                    gridbox_tab4.addWidget(self.export_path_lineedit_04, 2, 1)
                    gridbox_tab4.addWidget(self.server_browse_btn_04, 2, 2)
                    gridbox_tab4.addWidget(self.token_push_btn_04, 2, 3)

                    gridbox_tab4.addWidget(self.enable_preset_pushbutton_04, 0, 5)
                    gridbox_tab4.addWidget(self.top_layer_pushbutton_04, 1, 5)
                    gridbox_tab4.addWidget(self.foreground_pushbutton_04, 2, 5)
                    gridbox_tab4.addWidget(self.between_marks_pushbutton_04, 3, 5)

                    self.window.tab4.setLayout(gridbox_tab4)

                def export_preset_five_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.enable_preset_pushbutton_05.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.saved_preset_type_label_05.setEnabled(switch)
                        self.saved_presets_label_05.setEnabled(switch)
                        self.export_path_label_05.setEnabled(switch)
                        self.export_path_lineedit_05.setEnabled(switch)
                        self.top_layer_pushbutton_05.setEnabled(switch)
                        self.foreground_pushbutton_05.setEnabled(switch)
                        self.between_marks_pushbutton_05.setEnabled(switch)
                        self.token_push_btn_05.setEnabled(switch)
                        self.export_push_btn_05.setEnabled(switch)
                        self.server_browse_btn_05.setEnabled(switch)
                        self.saved_presets_push_btn_05.setEnabled(switch)

                    # Labels

                    self.saved_preset_type_label_05 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.saved_preset_type_label_05.setMinimumWidth(140)
                    self.saved_preset_type_label_05.setMaximumWidth(150)
                    self.saved_preset_type_label_05.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                  'QLabel:disabled {color: #6a6a6a}')

                    self.saved_presets_label_05 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.saved_presets_label_05.setMinimumWidth(140)
                    self.saved_presets_label_05.setMaximumWidth(150)
                    self.saved_presets_label_05.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                              'QLabel:disabled {color: #6a6a6a}')

                    self.export_path_label_05 = QtWidgets.QLabel('Export Path ', self.window)
                    self.export_path_label_05.setMinimumWidth(140)
                    self.export_path_label_05.setMaximumWidth(150)
                    self.export_path_label_05.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                            'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.export_path_lineedit_05 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.export_path_lineedit_05.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_path_lineedit_05.setMaximumSize(QtCore.QSize(450, 28))
                    self.export_path_lineedit_05.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

                    # Checkable Pushbuttons

                    self.enable_preset_pushbutton_05 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.enable_preset_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.enable_preset_pushbutton_05.setCheckable(True)
                    self.enable_preset_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.enable_preset_pushbutton_05.clicked.connect(toggle_ui)
                    self.enable_preset_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.top_layer_pushbutton_05 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.top_layer_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.top_layer_pushbutton_05.setCheckable(True)
                    self.top_layer_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.top_layer_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                               'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                               'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.foreground_pushbutton_05 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.foreground_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.foreground_pushbutton_05.setCheckable(True)
                    self.foreground_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.foreground_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.between_marks_pushbutton_05 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.between_marks_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.between_marks_pushbutton_05.setCheckable(True)
                    self.between_marks_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.between_marks_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                   'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                   'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.token_menu_05 = QtWidgets.QMenu(self.window)
                    self.token_menu_05.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.token_push_btn_05 = QtWidgets.QPushButton('Add Token', self.window)
                    self.token_push_btn_05.setMenu(self.token_menu_05)
                    self.token_push_btn_05.setMinimumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_05.setMaximumSize(QtCore.QSize(110, 28))
                    self.token_push_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.token_push_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.export_path_lineedit_05, self.token_menu_05)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.export_menu_05 = QtWidgets.QMenu(self.window)
                    self.export_menu_05.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.export_push_btn_05 = QtWidgets.QPushButton('None Selected', self.window)
                    self.export_push_btn_05.setMenu(self.export_menu_05)
                    self.export_push_btn_05.setMinimumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_05.setMaximumSize(QtCore.QSize(200, 28))
                    self.export_push_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.export_push_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                          'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.saved_preset_menu_05 = QtWidgets.QMenu(self.window)
                    self.saved_preset_menu_05.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                            'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.saved_presets_push_btn_05 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.saved_presets_push_btn_05.setMenu(self.saved_preset_menu_05)
                    self.saved_presets_push_btn_05.setMinimumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_05.setMaximumSize(QtCore.QSize(450, 28))
                    self.saved_presets_push_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.saved_presets_push_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    set_export_push_button(self.export_push_btn_05, self.saved_presets_push_btn_05, self.saved_preset_menu_05)

                    # -------------------------------------------------------------

                    self.server_browse_btn_05 = QtWidgets.QPushButton('Browse', self.window)
                    self.server_browse_btn_05.setMinimumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_05.setMaximumSize(QtCore.QSize(110, 28))
                    self.server_browse_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.server_browse_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                            'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                            'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.server_browse_btn_05.clicked.connect(partial(self.server_path_browse, self.export_path_lineedit_05))

                    toggle_ui()

                    # Export pushbutton menus

                    self.export_menu_05.addAction('Project: Movie', partial(project_movie_menu, self.export_push_btn_05, self.saved_presets_push_btn_05, self.saved_preset_menu_05))
                    self.export_menu_05.addAction('Project: File Sequence', partial(project_file_seq_menu, self.export_push_btn_05, self.saved_presets_push_btn_05, self.saved_preset_menu_05))
                    self.export_menu_05.addAction('Shared: Movie', partial(shared_movie_menu, self.export_push_btn_05, self.saved_presets_push_btn_05, self.saved_preset_menu_05))
                    self.export_menu_05.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.export_push_btn_05, self.saved_presets_push_btn_05, self.saved_preset_menu_05))

                    # Tab Layout

                    gridbox_tab5 = QtWidgets.QGridLayout()
                    gridbox_tab5.setMargin(30)
                    gridbox_tab5.setVerticalSpacing(5)
                    gridbox_tab5.setHorizontalSpacing(5)
                    gridbox_tab5.setColumnMinimumWidth(4, 100)

                    gridbox_tab5.addWidget(self.saved_preset_type_label_05, 0, 0)
                    gridbox_tab5.addWidget(self.export_push_btn_05, 0, 1)

                    gridbox_tab5.addWidget(self.saved_presets_label_05, 1, 0)
                    gridbox_tab5.addWidget(self.saved_presets_push_btn_05, 1, 1)

                    gridbox_tab5.addWidget(self.export_path_label_05, 2, 0)
                    gridbox_tab5.addWidget(self.export_path_lineedit_05, 2, 1)
                    gridbox_tab5.addWidget(self.server_browse_btn_05, 2, 2)
                    gridbox_tab5.addWidget(self.token_push_btn_05, 2, 3)

                    gridbox_tab5.addWidget(self.enable_preset_pushbutton_05, 0, 5)
                    gridbox_tab5.addWidget(self.top_layer_pushbutton_05, 1, 5)
                    gridbox_tab5.addWidget(self.foreground_pushbutton_05, 2, 5)
                    gridbox_tab5.addWidget(self.between_marks_pushbutton_05, 3, 5)

                    self.window.tab5.setLayout(gridbox_tab5)

                self.preset_tabs = QtWidgets.QTabWidget()

                # Preset Tabs

                self.window.tab1 = QtWidgets.QWidget()
                self.window.tab2 = QtWidgets.QWidget()
                self.window.tab3 = QtWidgets.QWidget()
                self.window.tab4 = QtWidgets.QWidget()
                self.window.tab5 = QtWidgets.QWidget()

                self.preset_tabs.setFocusPolicy(QtCore.Qt.NoFocus)

                self.preset_tabs.setStyleSheet('QTabWidget {background-color: #313131; font: 14px "Discreet"}'
                                               'QTabWidget::tab-bar {alignment: center}'
                                               'QTabBar::tab {color: #777777; background: #212121; border: 1px solid #000000; border-bottom-color: #000000; min-width: 20ex; padding: 5px}'
                                               'QTabBar::tab:selected {color: #bababa; background-color: #2e2e2e; border: 1px solid #000000; border-bottom: 1px solid #2e2e2e}'
                                               'QTabWidget::pane {border: 1px solid #000000; top: -0.05em}'
                                               'QWidget {background-color: #2e2e2e}')

                self.preset_tabs.addTab(self.window.tab1, 'Export Preset One')
                self.preset_tabs.addTab(self.window.tab2, 'Export Preset Two')
                self.preset_tabs.addTab(self.window.tab3, 'Export Preset Three')
                self.preset_tabs.addTab(self.window.tab4, 'Export Preset Four')
                self.preset_tabs.addTab(self.window.tab5, 'Export Preset Five')

                export_preset_one_tab()
                export_preset_two_tab()
                export_preset_three_tab()
                export_preset_four_tab()
                export_preset_five_tab()

            # Labels

            self.menu_visibility_label = QtWidgets.QLabel('Menu Visibility', self.window)
            self.menu_visibility_label.setMinimumWidth(140)
            self.menu_visibility_label.setMaximumWidth(150)
            self.menu_visibility_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"')

            self.menu_name_label = QtWidgets.QLabel('Menu Name', self.window)
            self.menu_name_label.setMinimumWidth(140)
            self.menu_name_label.setMaximumWidth(150)
            self.menu_name_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"')

            # LineEdits

            self.menu_name_lineedit = QtWidgets.QLineEdit('', self.window)
            self.menu_name_lineedit.setMinimumSize(QtCore.QSize(200, 28))
            self.menu_name_lineedit.setMaximumSize(QtCore.QSize(450, 28))
            self.menu_name_lineedit.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"')

            # -------------------------------------------------------------

            # Menu Visibility Push Button Menu

            def project_preset_menu():
                self.menu_visibility_push_btn.setText('Project')

            def shared_preset_menu():
                self.menu_visibility_push_btn.setText('Shared')

            self.export_type_menu = QtWidgets.QMenu(self.window)
            self.export_type_menu.addAction('Project', project_preset_menu)
            self.export_type_menu.addAction('Shared', shared_preset_menu)
            self.export_type_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            self.menu_visibility_push_btn = QtWidgets.QPushButton('Project', self.window)
            self.menu_visibility_push_btn.setMenu(self.export_type_menu)
            self.menu_visibility_push_btn.setMinimumSize(QtCore.QSize(150, 28))
            self.menu_visibility_push_btn.setMaximumSize(QtCore.QSize(150, 28))
            self.menu_visibility_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.menu_visibility_push_btn.setStyleSheet('color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"')

            # -------------------------------------------------------------

            # Buttons

            self.create_btn = QtWidgets.QPushButton('Create', self.window)
            self.create_btn.setMinimumSize(QtCore.QSize(110, 28))
            self.create_btn.setMaximumSize(QtCore.QSize(110, 28))
            self.create_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.create_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
            self.create_btn.clicked.connect(self.create_menu)

            self.done_btn = QtWidgets.QPushButton('Done', self.window)
            self.done_btn.setMinimumSize(QtCore.QSize(110, 28))
            self.done_btn.setMaximumSize(QtCore.QSize(110, 28))
            self.done_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.done_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                        'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
            self.done_btn.clicked.connect(self.window.close)

            # -------------------------------------------------------------

            create_presets(self)

            # Window Layout

            create_gridbox = QtWidgets.QGridLayout()
            create_gridbox.setRowMinimumHeight(0, 34)
            create_gridbox.setRowMinimumHeight(3, 30)
            create_gridbox.setRowMinimumHeight(5, 30)

            create_gridbox.addWidget(self.menu_visibility_label, 1, 0)
            create_gridbox.addWidget(self.menu_visibility_push_btn, 1, 1)
            create_gridbox.addWidget(self.menu_name_label, 2, 0)
            create_gridbox.addWidget(self.menu_name_lineedit, 2, 1, 1, 2)

            create_gridbox.addWidget(self.preset_tabs, 4, 0, 1, 6)

            create_gridbox.addWidget(self.done_btn, 6, 4)
            create_gridbox.addWidget(self.create_btn, 6, 5)

            self.window.create_tab.setLayout(create_gridbox)

        def edit_tab():

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
                from functools import partial

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

            def edit_presets():
                from PySide2 import QtCore, QtWidgets

                # Build button menus for preset tabs

                def token_action_menu(lineedit, token_menu):
                    from functools import partial

                    def insert_token(token):
                        for key, value in token_dict.items():
                            if key == token:
                                token_name = value
                        lineedit.insert(token_name)

                    token_list = ['Project Name', 'Shot Name', 'Batch Group Name', 'Batch Group Shot Name', 'Sequence Name', 'User Name', 'Clip Name',
                                  'Clip Resolution', 'Clip Height', 'Clip Width', 'Year (YYYY)', 'Year (YY)', 'Month', 'Day', 'Hour', 'Minute', 'AM/PM']

                    token_dict = {'Project Name': '<ProjectName>', 'Shot Name': '<ShotName>', 'Batch Group Name': '<BatchGroupName>',
                                  'Batch Group Shot Name': '<BatchGroupShotName>', 'Sequence Name': '<SeqName>', 'User Name': '<UserName>',
                                  'Clip Name': '<ClipName>', 'Clip Resolution': '<Resolution>', 'Clip Height': '<ClipHeight>',
                                  'Clip Width': '<ClipWidth>', 'Year (YYYY)': '<YYYY>', 'Year (YY)': '<YY>', 'Month': '<MM>',
                                  'Day': '<DD>', 'Hour': '<Hour>', 'Minute': '<Minute>', 'AM/PM': '<AMPM>',}

                    for token in token_list:
                        token_menu.addAction(token, partial(insert_token, token))

                def project_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Project: Movie')
                    build_format_preset_menus(self.project_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def project_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Project: File Sequence')
                    build_format_preset_menus(self.project_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def shared_movie_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Shared: Movie')
                    build_format_preset_menus(self.shared_movie_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                def shared_file_seq_menu(export_btn, saved_presets_btn, saved_presets_menu):
                    export_btn.setText('Shared: File Sequence')
                    build_format_preset_menus(self.shared_file_seq_preset_list, export_btn, saved_presets_btn, saved_presets_menu)

                # -------------------------------------------------------

                def edit_preset_one_tab():
                    from functools import partial

                    # Labels

                    self.edit_saved_preset_type_label_01 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.edit_saved_preset_type_label_01.setMinimumWidth(140)
                    self.edit_saved_preset_type_label_01.setMaximumWidth(150)
                    self.edit_saved_preset_type_label_01.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                       'QLabel:disabled {color: #6a6a6a}')

                    self.edit_saved_presets_label_01 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.edit_saved_presets_label_01.setMinimumWidth(140)
                    self.edit_saved_presets_label_01.setMaximumWidth(150)
                    self.edit_saved_presets_label_01.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                   'QLabel:disabled {color: #6a6a6a}')

                    self.edit_export_path_label_01 = QtWidgets.QLabel('Export Path ', self.window)
                    self.edit_export_path_label_01.setMinimumWidth(140)
                    self.edit_export_path_label_01.setMaximumWidth(150)
                    self.edit_export_path_label_01.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                 'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.edit_export_path_lineedit_01 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.edit_export_path_lineedit_01.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_path_lineedit_01.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_export_path_lineedit_01.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                                    'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
                    self.edit_export_path_lineedit_01.setText('/')

                    # Checkable Pushbuttons

                    self.edit_top_layer_pushbutton_01 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.edit_top_layer_pushbutton_01.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_01.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_01.setCheckable(True)
                    self.edit_top_layer_pushbutton_01.setChecked(self.top_layer_checked)
                    self.edit_top_layer_pushbutton_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_top_layer_pushbutton_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                    'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                    'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_foreground_pushbutton_01 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.edit_foreground_pushbutton_01.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_01.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_01.setCheckable(True)
                    self.edit_foreground_pushbutton_01.setChecked(self.export_foreground_checked)
                    self.edit_foreground_pushbutton_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_foreground_pushbutton_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                     'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                     'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_between_marks_pushbutton_01 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.edit_between_marks_pushbutton_01.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_01.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_01.setCheckable(True)
                    self.edit_between_marks_pushbutton_01.setChecked(self.export_between_marks)
                    self.edit_between_marks_pushbutton_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_between_marks_pushbutton_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.edit_token_menu_01 = QtWidgets.QMenu(self.window)
                    self.edit_token_menu_01.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                          'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_token_push_btn_01 = QtWidgets.QPushButton('Add Token', self.window)
                    self.edit_token_push_btn_01.setMenu(self.edit_token_menu_01)
                    self.edit_token_push_btn_01.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_01.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_token_push_btn_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                              'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    token_action_menu(self.edit_export_path_lineedit_01, self.edit_token_menu_01)

                    # -------------------------------------------------------------

                    # Saved Presets Type Pushbutton
                    # -------------------------

                    self.edit_export_menu_01 = QtWidgets.QMenu(self.window)
                    self.edit_export_menu_01.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_export_push_btn_01 = QtWidgets.QPushButton(self.export_menu_text, self.window)
                    self.edit_export_push_btn_01.setMenu(self.edit_export_menu_01)
                    self.edit_export_push_btn_01.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_01.setMaximumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_export_push_btn_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                               'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.edit_saved_preset_menu_01 = QtWidgets.QMenu(self.window)
                    self.edit_saved_preset_menu_01.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                                 'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_saved_presets_push_btn_01 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.edit_saved_presets_push_btn_01.setMenu(self.edit_saved_preset_menu_01)
                    self.edit_saved_presets_push_btn_01.setMinimumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_01.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_saved_presets_push_btn_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                      'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    # -------------------------------------------------------------

                    self.edit_server_browse_btn_01 = QtWidgets.QPushButton('Browse', self.window)
                    self.edit_server_browse_btn_01.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_01.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_01.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_server_browse_btn_01.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                 'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.edit_server_browse_btn_01.clicked.connect(partial(self.server_path_browse, self.edit_export_path_lineedit_01))

                    # Export pushbutton menus

                    self.edit_export_menu_01.addAction('Project: Movie', partial(project_movie_menu, self.edit_export_push_btn_01, self.edit_saved_presets_push_btn_01, self.edit_saved_preset_menu_01))
                    self.edit_export_menu_01.addAction('Project: File Sequence', partial(project_file_seq_menu, self.edit_export_push_btn_01, self.edit_saved_presets_push_btn_01, self.edit_saved_preset_menu_01))
                    self.edit_export_menu_01.addAction('Shared: Movie', partial(shared_movie_menu, self.edit_export_push_btn_01, self.edit_saved_presets_push_btn_01, self.edit_saved_preset_menu_01))
                    self.edit_export_menu_01.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.edit_export_push_btn_01, self.edit_saved_presets_push_btn_01, self.edit_saved_preset_menu_01))

                    # Tab Layout

                    edit_gridbox_tab1 = QtWidgets.QGridLayout()
                    edit_gridbox_tab1.setMargin(30)
                    edit_gridbox_tab1.setVerticalSpacing(5)
                    edit_gridbox_tab1.setHorizontalSpacing(5)
                    edit_gridbox_tab1.setColumnMinimumWidth(4, 100)

                    edit_gridbox_tab1.addWidget(self.edit_saved_preset_type_label_01, 0, 0)
                    edit_gridbox_tab1.addWidget(self.edit_export_push_btn_01, 0, 1)

                    edit_gridbox_tab1.addWidget(self.edit_saved_presets_label_01, 1, 0)
                    edit_gridbox_tab1.addWidget(self.edit_saved_presets_push_btn_01, 1, 1)

                    edit_gridbox_tab1.addWidget(self.edit_export_path_label_01, 2, 0)
                    edit_gridbox_tab1.addWidget(self.edit_export_path_lineedit_01, 2, 1)
                    edit_gridbox_tab1.addWidget(self.edit_server_browse_btn_01, 2, 2)
                    edit_gridbox_tab1.addWidget(self.edit_token_push_btn_01, 2, 3)

                    edit_gridbox_tab1.addWidget(self.edit_top_layer_pushbutton_01, 1, 5)
                    edit_gridbox_tab1.addWidget(self.edit_foreground_pushbutton_01, 2, 5)
                    edit_gridbox_tab1.addWidget(self.edit_between_marks_pushbutton_01, 3, 5)

                    self.window.edit_tab1.setLayout(edit_gridbox_tab1)

                def edit_preset_two_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.edit_enable_preset_pushbutton_02.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.edit_saved_preset_type_label_02.setEnabled(switch)
                        self.edit_saved_presets_label_02.setEnabled(switch)
                        self.edit_export_path_label_02.setEnabled(switch)
                        self.edit_export_path_lineedit_02.setEnabled(switch)
                        self.edit_top_layer_pushbutton_02.setEnabled(switch)
                        self.edit_foreground_pushbutton_02.setEnabled(switch)
                        self.edit_between_marks_pushbutton_02.setEnabled(switch)
                        self.edit_token_push_btn_02.setEnabled(switch)
                        self.edit_export_push_btn_02.setEnabled(switch)
                        self.edit_server_browse_btn_02.setEnabled(switch)
                        self.edit_saved_presets_push_btn_02.setEnabled(switch)

                    # Labels

                    self.edit_saved_preset_type_label_02 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.edit_saved_preset_type_label_02.setMinimumWidth(140)
                    self.edit_saved_preset_type_label_02.setMaximumWidth(150)
                    self.edit_saved_preset_type_label_02.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                       'QLabel:disabled {color: #6a6a6a}')

                    self.edit_saved_presets_label_02 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.edit_saved_presets_label_02.setMinimumWidth(140)
                    self.edit_saved_presets_label_02.setMaximumWidth(150)
                    self.edit_saved_presets_label_02.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                   'QLabel:disabled {color: #6a6a6a}')

                    self.edit_export_path_label_02 = QtWidgets.QLabel('Export Path ', self.window)
                    self.edit_export_path_label_02.setMinimumWidth(140)
                    self.edit_export_path_label_02.setMaximumWidth(150)
                    self.edit_export_path_label_02.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                 'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.edit_export_path_lineedit_02 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.edit_export_path_lineedit_02.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_path_lineedit_02.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_export_path_lineedit_02.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                                    'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
                    self.edit_export_path_lineedit_02.setText('/')

                    # Checkable Pushbuttons

                    self.edit_enable_preset_pushbutton_02 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.edit_enable_preset_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_02.setCheckable(True)
                    self.edit_enable_preset_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_enable_preset_pushbutton_02.clicked.connect(toggle_ui)
                    self.edit_enable_preset_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_top_layer_pushbutton_02 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.edit_top_layer_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_02.setCheckable(True)
                    self.edit_top_layer_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_top_layer_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                    'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                    'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_foreground_pushbutton_02 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.edit_foreground_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_02.setCheckable(True)
                    self.edit_foreground_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_foreground_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                     'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                     'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_between_marks_pushbutton_02 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.edit_between_marks_pushbutton_02.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_02.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_02.setCheckable(True)
                    self.edit_between_marks_pushbutton_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_between_marks_pushbutton_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.edit_token_menu_02 = QtWidgets.QMenu(self.window)
                    self.edit_token_menu_02.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                          'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_token_push_btn_02 = QtWidgets.QPushButton('Add Token', self.window)
                    self.edit_token_push_btn_02.setMenu(self.edit_token_menu_02)
                    self.edit_token_push_btn_02.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_02.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_token_push_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                              'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.edit_export_path_lineedit_02, self.edit_token_menu_02)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.edit_export_menu_02 = QtWidgets.QMenu(self.window)
                    self.edit_export_menu_02.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_export_push_btn_02 = QtWidgets.QPushButton('None Selected', self.window)
                    self.edit_export_push_btn_02.setMenu(self.edit_export_menu_02)
                    self.edit_export_push_btn_02.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_02.setMaximumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_export_push_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                               'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.edit_saved_preset_menu_02 = QtWidgets.QMenu(self.window)
                    self.edit_saved_preset_menu_02.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                                 'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_saved_presets_push_btn_02 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.edit_saved_presets_push_btn_02.setMenu(self.edit_saved_preset_menu_02)
                    self.edit_saved_presets_push_btn_02.setMinimumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_02.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_saved_presets_push_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                      'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    self.edit_server_browse_btn_02 = QtWidgets.QPushButton('Browse', self.window)
                    self.edit_server_browse_btn_02.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_02.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_02.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_server_browse_btn_02.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                 'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.edit_server_browse_btn_02.clicked.connect(partial(self.server_path_browse, self.edit_export_path_lineedit_02))

                    toggle_ui()

                    # Export pushbutton menus

                    self.edit_export_menu_02.addAction('Project: Movie', partial(project_movie_menu, self.edit_export_push_btn_02, self.edit_saved_presets_push_btn_02, self.edit_saved_preset_menu_02))
                    self.edit_export_menu_02.addAction('Project: File Sequence', partial(project_file_seq_menu, self.edit_export_push_btn_02, self.edit_saved_presets_push_btn_02, self.edit_saved_preset_menu_02))
                    self.edit_export_menu_02.addAction('Shared: Movie', partial(shared_movie_menu, self.edit_export_push_btn_02, self.edit_saved_presets_push_btn_02, self.edit_saved_preset_menu_02))
                    self.edit_export_menu_02.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.edit_export_push_btn_02, self.edit_saved_presets_push_btn_02, self.edit_saved_preset_menu_02))

                    # Tab Layout

                    edit_gridbox_tab2 = QtWidgets.QGridLayout()
                    edit_gridbox_tab2.setMargin(30)
                    edit_gridbox_tab2.setVerticalSpacing(5)
                    edit_gridbox_tab2.setHorizontalSpacing(5)
                    edit_gridbox_tab2.setColumnMinimumWidth(4, 100)

                    edit_gridbox_tab2.addWidget(self.edit_saved_preset_type_label_02, 0, 0)
                    edit_gridbox_tab2.addWidget(self.edit_export_push_btn_02, 0, 1)

                    edit_gridbox_tab2.addWidget(self.edit_saved_presets_label_02, 1, 0)
                    edit_gridbox_tab2.addWidget(self.edit_saved_presets_push_btn_02, 1, 1)

                    edit_gridbox_tab2.addWidget(self.edit_export_path_label_02, 2, 0)
                    edit_gridbox_tab2.addWidget(self.edit_export_path_lineedit_02, 2, 1)
                    edit_gridbox_tab2.addWidget(self.edit_server_browse_btn_02, 2, 2)
                    edit_gridbox_tab2.addWidget(self.edit_token_push_btn_02, 2, 3)

                    edit_gridbox_tab2.addWidget(self.edit_enable_preset_pushbutton_02, 0, 5)
                    edit_gridbox_tab2.addWidget(self.edit_top_layer_pushbutton_02, 1, 5)
                    edit_gridbox_tab2.addWidget(self.edit_foreground_pushbutton_02, 2, 5)
                    edit_gridbox_tab2.addWidget(self.edit_between_marks_pushbutton_02, 3, 5)

                    self.window.edit_tab2.setLayout(edit_gridbox_tab2)

                def edit_preset_three_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.edit_enable_preset_pushbutton_03.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.edit_saved_preset_type_label_03.setEnabled(switch)
                        self.edit_saved_presets_label_03.setEnabled(switch)
                        self.edit_export_path_label_03.setEnabled(switch)
                        self.edit_export_path_lineedit_03.setEnabled(switch)
                        self.edit_top_layer_pushbutton_03.setEnabled(switch)
                        self.edit_foreground_pushbutton_03.setEnabled(switch)
                        self.edit_between_marks_pushbutton_03.setEnabled(switch)
                        self.edit_token_push_btn_03.setEnabled(switch)
                        self.edit_export_push_btn_03.setEnabled(switch)
                        self.edit_server_browse_btn_03.setEnabled(switch)
                        self.edit_saved_presets_push_btn_03.setEnabled(switch)

                    # Labels

                    self.edit_saved_preset_type_label_03 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.edit_saved_preset_type_label_03.setMinimumWidth(140)
                    self.edit_saved_preset_type_label_03.setMaximumWidth(150)
                    self.edit_saved_preset_type_label_03.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                       'QLabel:disabled {color: #6a6a6a}')

                    self.edit_saved_presets_label_03 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.edit_saved_presets_label_03.setMinimumWidth(140)
                    self.edit_saved_presets_label_03.setMaximumWidth(150)
                    self.edit_saved_presets_label_03.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                   'QLabel:disabled {color: #6a6a6a}')

                    self.edit_export_path_label_03 = QtWidgets.QLabel('Export Path ', self.window)
                    self.edit_export_path_label_03.setMinimumWidth(140)
                    self.edit_export_path_label_03.setMaximumWidth(150)
                    self.edit_export_path_label_03.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                 'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.edit_export_path_lineedit_03 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.edit_export_path_lineedit_03.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_path_lineedit_03.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_export_path_lineedit_03.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                                    'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
                    self.edit_export_path_lineedit_03.setText('/')

                    # Checkable Pushbuttons

                    self.edit_enable_preset_pushbutton_03 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.edit_enable_preset_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_03.setCheckable(True)
                    self.edit_enable_preset_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_enable_preset_pushbutton_03.clicked.connect(toggle_ui)
                    self.edit_enable_preset_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_top_layer_pushbutton_03 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.edit_top_layer_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_03.setCheckable(True)
                    self.edit_top_layer_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_top_layer_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                    'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                    'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_foreground_pushbutton_03 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.edit_foreground_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_03.setCheckable(True)
                    self.edit_foreground_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_foreground_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                     'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                     'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_between_marks_pushbutton_03 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.edit_between_marks_pushbutton_03.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_03.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_03.setCheckable(True)
                    self.edit_between_marks_pushbutton_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_between_marks_pushbutton_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.edit_token_menu_03 = QtWidgets.QMenu(self.window)
                    self.edit_token_menu_03.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                          'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_token_push_btn_03 = QtWidgets.QPushButton('Add Token', self.window)
                    self.edit_token_push_btn_03.setMenu(self.edit_token_menu_03)
                    self.edit_token_push_btn_03.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_03.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_token_push_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                              'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.edit_export_path_lineedit_03, self.edit_token_menu_03)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.edit_export_menu_03 = QtWidgets.QMenu(self.window)
                    self.edit_export_menu_03.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_export_push_btn_03 = QtWidgets.QPushButton('None Selected', self.window)
                    self.edit_export_push_btn_03.setMenu(self.edit_export_menu_03)
                    self.edit_export_push_btn_03.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_03.setMaximumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_export_push_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                               'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.edit_saved_preset_menu_03 = QtWidgets.QMenu(self.window)
                    self.edit_saved_preset_menu_03.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                                 'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_saved_presets_push_btn_03 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.edit_saved_presets_push_btn_03.setMenu(self.edit_saved_preset_menu_03)
                    self.edit_saved_presets_push_btn_03.setMinimumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_03.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_saved_presets_push_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                      'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    self.edit_server_browse_btn_03 = QtWidgets.QPushButton('Browse', self.window)
                    self.edit_server_browse_btn_03.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_03.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_03.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_server_browse_btn_03.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                 'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.edit_server_browse_btn_03.clicked.connect(partial(self.server_path_browse, self.edit_export_path_lineedit_03))

                    toggle_ui()

                    # Export pushbutton menus

                    self.edit_export_menu_03.addAction('Project: Movie', partial(project_movie_menu, self.edit_export_push_btn_03, self.edit_saved_presets_push_btn_03, self.edit_saved_preset_menu_03))
                    self.edit_export_menu_03.addAction('Project: File Sequence', partial(project_file_seq_menu, self.edit_export_push_btn_03, self.edit_saved_presets_push_btn_03, self.edit_saved_preset_menu_03))
                    self.edit_export_menu_03.addAction('Shared: Movie', partial(shared_movie_menu, self.edit_export_push_btn_03, self.edit_saved_presets_push_btn_03, self.edit_saved_preset_menu_03))
                    self.edit_export_menu_03.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.edit_export_push_btn_03, self.edit_saved_presets_push_btn_03, self.edit_saved_preset_menu_03))

                    # Tab Layout

                    edit_gridbox_tab3 = QtWidgets.QGridLayout()
                    edit_gridbox_tab3.setMargin(30)
                    edit_gridbox_tab3.setVerticalSpacing(5)
                    edit_gridbox_tab3.setHorizontalSpacing(5)
                    edit_gridbox_tab3.setColumnMinimumWidth(4, 100)

                    edit_gridbox_tab3.addWidget(self.edit_saved_preset_type_label_03, 0, 0)
                    edit_gridbox_tab3.addWidget(self.edit_export_push_btn_03, 0, 1)

                    edit_gridbox_tab3.addWidget(self.edit_saved_presets_label_03, 1, 0)
                    edit_gridbox_tab3.addWidget(self.edit_saved_presets_push_btn_03, 1, 1)

                    edit_gridbox_tab3.addWidget(self.edit_export_path_label_03, 2, 0)
                    edit_gridbox_tab3.addWidget(self.edit_export_path_lineedit_03, 2, 1)
                    edit_gridbox_tab3.addWidget(self.edit_server_browse_btn_03, 2, 2)
                    edit_gridbox_tab3.addWidget(self.edit_token_push_btn_03, 2, 3)

                    edit_gridbox_tab3.addWidget(self.edit_enable_preset_pushbutton_03, 0, 5)
                    edit_gridbox_tab3.addWidget(self.edit_top_layer_pushbutton_03, 1, 5)
                    edit_gridbox_tab3.addWidget(self.edit_foreground_pushbutton_03, 2, 5)
                    edit_gridbox_tab3.addWidget(self.edit_between_marks_pushbutton_03, 3, 5)

                    self.window.edit_tab3.setLayout(edit_gridbox_tab3)

                def edit_preset_four_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.edit_enable_preset_pushbutton_04.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.edit_saved_preset_type_label_04.setEnabled(switch)
                        self.edit_saved_presets_label_04.setEnabled(switch)
                        self.edit_export_path_label_04.setEnabled(switch)
                        self.edit_export_path_lineedit_04.setEnabled(switch)
                        self.edit_top_layer_pushbutton_04.setEnabled(switch)
                        self.edit_foreground_pushbutton_04.setEnabled(switch)
                        self.edit_between_marks_pushbutton_04.setEnabled(switch)
                        self.edit_token_push_btn_04.setEnabled(switch)
                        self.edit_export_push_btn_04.setEnabled(switch)
                        self.edit_server_browse_btn_04.setEnabled(switch)
                        self.edit_saved_presets_push_btn_04.setEnabled(switch)

                    # Labels

                    self.edit_saved_preset_type_label_04 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.edit_saved_preset_type_label_04.setMinimumWidth(140)
                    self.edit_saved_preset_type_label_04.setMaximumWidth(150)
                    self.edit_saved_preset_type_label_04.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                       'QLabel:disabled {color: #6a6a6a}')

                    self.edit_saved_presets_label_04 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.edit_saved_presets_label_04.setMinimumWidth(140)
                    self.edit_saved_presets_label_04.setMaximumWidth(150)
                    self.edit_saved_presets_label_04.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                   'QLabel:disabled {color: #6a6a6a}')

                    self.edit_export_path_label_04 = QtWidgets.QLabel('Export Path ', self.window)
                    self.edit_export_path_label_04.setMinimumWidth(140)
                    self.edit_export_path_label_04.setMaximumWidth(150)
                    self.edit_export_path_label_04.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                 'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.edit_export_path_lineedit_04 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.edit_export_path_lineedit_04.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_path_lineedit_04.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_export_path_lineedit_04.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                                    'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
                    self.edit_export_path_lineedit_04.setText('/')

                    # Checkable Pushbuttons

                    self.edit_enable_preset_pushbutton_04 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.edit_enable_preset_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_04.setCheckable(True)
                    self.edit_enable_preset_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_enable_preset_pushbutton_04.clicked.connect(toggle_ui)
                    self.edit_enable_preset_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_top_layer_pushbutton_04 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.edit_top_layer_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_04.setCheckable(True)
                    self.edit_top_layer_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_top_layer_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                    'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                    'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_foreground_pushbutton_04 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.edit_foreground_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_04.setCheckable(True)
                    self.edit_foreground_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_foreground_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                     'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                     'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_between_marks_pushbutton_04 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.edit_between_marks_pushbutton_04.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_04.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_04.setCheckable(True)
                    self.edit_between_marks_pushbutton_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_between_marks_pushbutton_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.edit_token_menu_04 = QtWidgets.QMenu(self.window)
                    self.edit_token_menu_04.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                          'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_token_push_btn_04 = QtWidgets.QPushButton('Add Token', self.window)
                    self.edit_token_push_btn_04.setMenu(self.edit_token_menu_04)
                    self.edit_token_push_btn_04.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_04.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_token_push_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                              'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.edit_export_path_lineedit_04, self.edit_token_menu_04)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.edit_export_menu_04 = QtWidgets.QMenu(self.window)
                    self.edit_export_menu_04.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_export_push_btn_04 = QtWidgets.QPushButton('None Selected', self.window)
                    self.edit_export_push_btn_04.setMenu(self.edit_export_menu_04)
                    self.edit_export_push_btn_04.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_04.setMaximumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_export_push_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                               'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.edit_saved_preset_menu_04 = QtWidgets.QMenu(self.window)
                    self.edit_saved_preset_menu_04.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                                 'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_saved_presets_push_btn_04 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.edit_saved_presets_push_btn_04.setMenu(self.edit_saved_preset_menu_04)
                    self.edit_saved_presets_push_btn_04.setMinimumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_04.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_saved_presets_push_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                      'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # set_export_push_button(self.edit_export_push_btn_04, self.edit_saved_presets_push_btn_04, self.edit_saved_preset_menu_04)

                    # -------------------------------------------------------------

                    self.edit_server_browse_btn_04 = QtWidgets.QPushButton('Browse', self.window)
                    self.edit_server_browse_btn_04.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_04.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_04.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_server_browse_btn_04.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                 'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.edit_server_browse_btn_04.clicked.connect(partial(self.server_path_browse, self.edit_export_path_lineedit_04))

                    toggle_ui()

                    # Export pushbutton menus

                    self.edit_export_menu_04.addAction('Project: Movie', partial(project_movie_menu, self.edit_export_push_btn_04, self.edit_saved_presets_push_btn_04, self.edit_saved_preset_menu_04))
                    self.edit_export_menu_04.addAction('Project: File Sequence', partial(project_file_seq_menu, self.edit_export_push_btn_04, self.edit_saved_presets_push_btn_04, self.edit_saved_preset_menu_04))
                    self.edit_export_menu_04.addAction('Shared: Movie', partial(shared_movie_menu, self.edit_export_push_btn_04, self.edit_saved_presets_push_btn_04, self.edit_saved_preset_menu_04))
                    self.edit_export_menu_04.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.edit_export_push_btn_04, self.edit_saved_presets_push_btn_04, self.edit_saved_preset_menu_04))

                    # Tab Layout

                    edit_gridbox_tab4 = QtWidgets.QGridLayout()
                    edit_gridbox_tab4.setMargin(30)
                    edit_gridbox_tab4.setVerticalSpacing(5)
                    edit_gridbox_tab4.setHorizontalSpacing(5)
                    edit_gridbox_tab4.setColumnMinimumWidth(4, 100)

                    edit_gridbox_tab4.addWidget(self.edit_saved_preset_type_label_04, 0, 0)
                    edit_gridbox_tab4.addWidget(self.edit_export_push_btn_04, 0, 1)

                    edit_gridbox_tab4.addWidget(self.edit_saved_presets_label_04, 1, 0)
                    edit_gridbox_tab4.addWidget(self.edit_saved_presets_push_btn_04, 1, 1)

                    edit_gridbox_tab4.addWidget(self.edit_export_path_label_04, 2, 0)
                    edit_gridbox_tab4.addWidget(self.edit_export_path_lineedit_04, 2, 1)
                    edit_gridbox_tab4.addWidget(self.edit_server_browse_btn_04, 2, 2)
                    edit_gridbox_tab4.addWidget(self.edit_token_push_btn_04, 2, 3)

                    edit_gridbox_tab4.addWidget(self.edit_enable_preset_pushbutton_04, 0, 5)
                    edit_gridbox_tab4.addWidget(self.edit_top_layer_pushbutton_04, 1, 5)
                    edit_gridbox_tab4.addWidget(self.edit_foreground_pushbutton_04, 2, 5)
                    edit_gridbox_tab4.addWidget(self.edit_between_marks_pushbutton_04, 3, 5)

                    self.window.edit_tab4.setLayout(edit_gridbox_tab4)

                def edit_preset_five_tab():
                    from functools import partial

                    def toggle_ui():

                        if self.edit_enable_preset_pushbutton_05.isChecked():
                            switch = True
                        else:
                            switch = False

                        self.edit_saved_preset_type_label_05.setEnabled(switch)
                        self.edit_saved_presets_label_05.setEnabled(switch)
                        self.edit_export_path_label_05.setEnabled(switch)
                        self.edit_export_path_lineedit_05.setEnabled(switch)
                        self.edit_top_layer_pushbutton_05.setEnabled(switch)
                        self.edit_foreground_pushbutton_05.setEnabled(switch)
                        self.edit_between_marks_pushbutton_05.setEnabled(switch)
                        self.edit_token_push_btn_05.setEnabled(switch)
                        self.edit_export_push_btn_05.setEnabled(switch)
                        self.edit_server_browse_btn_05.setEnabled(switch)
                        self.edit_saved_presets_push_btn_05.setEnabled(switch)

                    # Labels

                    self.edit_saved_preset_type_label_05 = QtWidgets.QLabel('Saved Preset Type', self.window)
                    self.edit_saved_preset_type_label_05.setMinimumWidth(140)
                    self.edit_saved_preset_type_label_05.setMaximumWidth(150)
                    self.edit_saved_preset_type_label_05.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                       'QLabel:disabled {color: #6a6a6a}')

                    self.edit_saved_presets_label_05 = QtWidgets.QLabel('Saved Presets', self.window)
                    self.edit_saved_presets_label_05.setMinimumWidth(140)
                    self.edit_saved_presets_label_05.setMaximumWidth(150)
                    self.edit_saved_presets_label_05.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                   'QLabel:disabled {color: #6a6a6a}')

                    self.edit_export_path_label_05 = QtWidgets.QLabel('Export Path ', self.window)
                    self.edit_export_path_label_05.setMinimumWidth(140)
                    self.edit_export_path_label_05.setMaximumWidth(150)
                    self.edit_export_path_label_05.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                                 'QLabel:disabled {color: #6a6a6a}')

                    # LineEdits

                    self.edit_export_path_lineedit_05 = QtWidgets.QLineEdit(self.export_path, self.window)
                    self.edit_export_path_lineedit_05.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_path_lineedit_05.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_export_path_lineedit_05.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                                    'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
                    self.edit_export_path_lineedit_05.setText('/')

                    # Checkable Pushbuttons

                    self.edit_enable_preset_pushbutton_05 = QtWidgets.QPushButton(' Enable Preset', self.window)
                    self.edit_enable_preset_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_enable_preset_pushbutton_05.setCheckable(True)
                    self.edit_enable_preset_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_enable_preset_pushbutton_05.clicked.connect(toggle_ui)
                    self.edit_enable_preset_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_top_layer_pushbutton_05 = QtWidgets.QPushButton(' Use Top Layer', self.window)
                    self.edit_top_layer_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_top_layer_pushbutton_05.setCheckable(True)
                    self.edit_top_layer_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_top_layer_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                    'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                    'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_foreground_pushbutton_05 = QtWidgets.QPushButton(' Foreground Export', self.window)
                    self.edit_foreground_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_foreground_pushbutton_05.setCheckable(True)
                    self.edit_foreground_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_foreground_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                     'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                     'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    self.edit_between_marks_pushbutton_05 = QtWidgets.QPushButton(' Export Between Marks', self.window)
                    self.edit_between_marks_pushbutton_05.setMinimumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_05.setMaximumSize(QtCore.QSize(160, 28))
                    self.edit_between_marks_pushbutton_05.setCheckable(True)
                    self.edit_between_marks_pushbutton_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_between_marks_pushbutton_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #424142, stop: .93 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                        'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #4f4f4f, stop: .93 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                                                                        'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .92 #383838, stop: .93 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

                    # -------------------------------------------------------------

                    # Token pushbutton

                    self.edit_token_menu_05 = QtWidgets.QMenu(self.window)
                    self.edit_token_menu_05.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                          'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_token_push_btn_05 = QtWidgets.QPushButton('Add Token', self.window)
                    self.edit_token_push_btn_05.setMenu(self.edit_token_menu_05)
                    self.edit_token_push_btn_05.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_05.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_token_push_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_token_push_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                              'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    token_action_menu(self.edit_export_path_lineedit_05, self.edit_token_menu_05)

                    # -------------------------------------------------------------

                    # Export Pushbutton
                    # -------------------------

                    self.edit_export_menu_05 = QtWidgets.QMenu(self.window)
                    self.edit_export_menu_05.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                           'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_export_push_btn_05 = QtWidgets.QPushButton('None Selected', self.window)
                    self.edit_export_push_btn_05.setMenu(self.edit_export_menu_05)
                    self.edit_export_push_btn_05.setMinimumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_05.setMaximumSize(QtCore.QSize(200, 28))
                    self.edit_export_push_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_export_push_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                               'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    self.edit_export_push_btn_05.setText('None')

                    # -------------------------------------------------------------

                    # Saved Format Presets Pushbutton

                    self.edit_saved_preset_menu_05 = QtWidgets.QMenu(self.window)
                    self.edit_saved_preset_menu_05.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                                 'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

                    self.edit_saved_presets_push_btn_05 = QtWidgets.QPushButton(self.format_preset_text, self.window)
                    self.edit_saved_presets_push_btn_05.setMenu(self.edit_saved_preset_menu_05)
                    self.edit_saved_presets_push_btn_05.setMinimumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_05.setMaximumSize(QtCore.QSize(450, 28))
                    self.edit_saved_presets_push_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_saved_presets_push_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                                      'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                    # set_export_push_button(self.edit_export_push_btn_05, self.edit_saved_presets_push_btn_05, self.edit_saved_preset_menu_05)

                    # -------------------------------------------------------------

                    self.edit_server_browse_btn_05 = QtWidgets.QPushButton('Browse', self.window)
                    self.edit_server_browse_btn_05.setMinimumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_05.setMaximumSize(QtCore.QSize(110, 28))
                    self.edit_server_browse_btn_05.setFocusPolicy(QtCore.Qt.NoFocus)
                    self.edit_server_browse_btn_05.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                                                 'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}'
                                                                 'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
                    self.edit_server_browse_btn_05.clicked.connect(partial(self.server_path_browse, self.edit_export_path_lineedit_05))

                    toggle_ui()

                    # Export pushbutton menus

                    self.edit_export_menu_05.addAction('Project: Movie', partial(project_movie_menu, self.edit_export_push_btn_05, self.edit_saved_presets_push_btn_05, self.edit_saved_preset_menu_05))
                    self.edit_export_menu_05.addAction('Project: File Sequence', partial(project_file_seq_menu, self.edit_export_push_btn_05, self.edit_saved_presets_push_btn_05, self.edit_saved_preset_menu_05))
                    self.edit_export_menu_05.addAction('Shared: Movie', partial(shared_movie_menu, self.edit_export_push_btn_05, self.edit_saved_presets_push_btn_05, self.edit_saved_preset_menu_05))
                    self.edit_export_menu_05.addAction('Shared: File Sequence', partial(shared_file_seq_menu, self.edit_export_push_btn_05, self.edit_saved_presets_push_btn_05, self.edit_saved_preset_menu_05))

                    # Tab Layout

                    edit_gridbox_tab5 = QtWidgets.QGridLayout()
                    edit_gridbox_tab5.setMargin(30)
                    edit_gridbox_tab5.setVerticalSpacing(5)
                    edit_gridbox_tab5.setHorizontalSpacing(5)
                    edit_gridbox_tab5.setColumnMinimumWidth(4, 100)

                    edit_gridbox_tab5.addWidget(self.edit_saved_preset_type_label_05, 0, 0)
                    edit_gridbox_tab5.addWidget(self.edit_export_push_btn_05, 0, 1)

                    edit_gridbox_tab5.addWidget(self.edit_saved_presets_label_05, 1, 0)
                    edit_gridbox_tab5.addWidget(self.edit_saved_presets_push_btn_05, 1, 1)

                    edit_gridbox_tab5.addWidget(self.edit_export_path_label_05, 2, 0)
                    edit_gridbox_tab5.addWidget(self.edit_export_path_lineedit_05, 2, 1)
                    edit_gridbox_tab5.addWidget(self.edit_server_browse_btn_05, 2, 2)
                    edit_gridbox_tab5.addWidget(self.edit_token_push_btn_05, 2, 3)

                    edit_gridbox_tab5.addWidget(self.edit_enable_preset_pushbutton_05, 0, 5)
                    edit_gridbox_tab5.addWidget(self.edit_top_layer_pushbutton_05, 1, 5)
                    edit_gridbox_tab5.addWidget(self.edit_foreground_pushbutton_05, 2, 5)
                    edit_gridbox_tab5.addWidget(self.edit_between_marks_pushbutton_05, 3, 5)

                    self.window.edit_tab5.setLayout(edit_gridbox_tab5)

                self.edit_preset_tabs = QtWidgets.QTabWidget()

                # Preset Tabs

                self.window.edit_tab1 = QtWidgets.QWidget()
                self.window.edit_tab2 = QtWidgets.QWidget()
                self.window.edit_tab3 = QtWidgets.QWidget()
                self.window.edit_tab4 = QtWidgets.QWidget()
                self.window.edit_tab5 = QtWidgets.QWidget()

                self.edit_preset_tabs.setFocusPolicy(QtCore.Qt.NoFocus)

                self.edit_preset_tabs.setStyleSheet('QTabWidget {background-color: #313131; font: 14px "Discreet"}'
                                                    'QTabWidget::tab-bar {alignment: center}'
                                                    'QTabBar::tab {color: #777777; background: #212121; border: 1px solid #000000; border-bottom-color: #000000; min-width: 20ex; padding: 5px}'
                                                    'QTabBar::tab:selected {color: #bababa; background-color: #2e2e2e; border: 1px solid #000000; border-bottom: 1px solid #2e2e2e}'
                                                    'QTabWidget::pane {border: 1px solid #000000; top: -0.05em}'
                                                    'QWidget {background-color: #2e2e2e}')

                self.edit_preset_tabs.addTab(self.window.edit_tab1, 'Export Preset One')
                self.edit_preset_tabs.addTab(self.window.edit_tab2, 'Export Preset Two')
                self.edit_preset_tabs.addTab(self.window.edit_tab3, 'Export Preset Three')
                self.edit_preset_tabs.addTab(self.window.edit_tab4, 'Export Preset Four')
                self.edit_preset_tabs.addTab(self.window.edit_tab5, 'Export Preset Five')

                edit_preset_one_tab()
                edit_preset_two_tab()
                edit_preset_three_tab()
                edit_preset_four_tab()
                edit_preset_five_tab()

            def load_preset():

                print ('\nchecking for existing presets...\n')

                if self.edit_menu_push_btn.text() != 'No Saved Presets Found':

                    selected_script_name = self.edit_menu_push_btn.text().rsplit(': ', 1)[1]
                    print ('selected_script_name:', selected_script_name)

                    self.edit_menu_name_lineedit.setText(selected_script_name)

                    if 'Shared: ' in self.edit_menu_push_btn.text():
                        self.edit_menu_visibility_push_btn.setText('Shared')
                        selected_menu_path = os.path.join(self.shared_menus_dir, selected_script_name) + '.py'
                    elif 'Project: ' in self.edit_menu_push_btn.text():
                        self.edit_menu_visibility_push_btn.setText('Project')
                        selected_menu_path = os.path.join(self.project_menus_dir, self.current_project, selected_script_name) + '.py'

                    print ('selected_menu_path:', selected_menu_path)

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

                    try:

                        get_preset_info('One',
                                        None,
                                        self.edit_saved_presets_label_01,
                                        self.edit_saved_presets_label_01,
                                        self.edit_export_path_label_01,
                                        self.edit_export_path_lineedit_01,
                                        self.edit_top_layer_pushbutton_01,
                                        self.edit_foreground_pushbutton_01,
                                        self.edit_between_marks_pushbutton_01,
                                        self.edit_token_push_btn_01,
                                        self.edit_export_push_btn_01,
                                        self.edit_server_browse_btn_01,
                                        self.edit_saved_presets_push_btn_01)
                        preset_01_push_btn_text = self.edit_saved_presets_push_btn_01.text()
                    except:
                        pass

                    try:
                        get_preset_info('Two',
                                        self.edit_enable_preset_pushbutton_02,
                                        self.edit_saved_preset_type_label_02,
                                        self.edit_saved_presets_label_02,
                                        self.edit_export_path_label_02,
                                        self.edit_export_path_lineedit_02,
                                        self.edit_top_layer_pushbutton_02,
                                        self.edit_foreground_pushbutton_02,
                                        self.edit_between_marks_pushbutton_02,
                                        self.edit_token_push_btn_02,
                                        self.edit_export_push_btn_02,
                                        self.edit_server_browse_btn_02,
                                        self.edit_saved_presets_push_btn_02)
                        preset_02_push_btn_text = self.edit_saved_presets_push_btn_02.text()
                    except:

                        # Disable UI elements if nothing loaded for preset two

                        disable_ui_elements(self.edit_enable_preset_pushbutton_02,
                                            self.edit_saved_preset_type_label_02,
                                            self.edit_saved_presets_label_02,
                                            self.edit_export_path_label_02,
                                            self.edit_export_path_lineedit_02,
                                            self.edit_top_layer_pushbutton_02,
                                            self.edit_foreground_pushbutton_02,
                                            self.edit_between_marks_pushbutton_02,
                                            self.edit_token_push_btn_02,
                                            self.edit_export_push_btn_02,
                                            self.edit_server_browse_btn_02,
                                            self.edit_saved_presets_push_btn_02)

                    try:
                        get_preset_info('Three',
                                        self.edit_enable_preset_pushbutton_03,
                                        self.edit_saved_preset_type_label_03,
                                        self.edit_saved_presets_label_03,
                                        self.edit_export_path_label_03,
                                        self.edit_export_path_lineedit_03,
                                        self.edit_top_layer_pushbutton_03,
                                        self.edit_foreground_pushbutton_03,
                                        self.edit_between_marks_pushbutton_03,
                                        self.edit_token_push_btn_03,
                                        self.edit_export_push_btn_03,
                                        self.edit_server_browse_btn_03,
                                        self.edit_saved_presets_push_btn_03)
                        preset_03_push_btn_text = self.edit_saved_presets_push_btn_03.text()
                    except:

                        # Disable UI elements if nothing loaded for preset three

                        disable_ui_elements(self.edit_enable_preset_pushbutton_03,
                                            self.edit_saved_preset_type_label_03,
                                            self.edit_saved_presets_label_03,
                                            self.edit_export_path_label_03,
                                            self.edit_export_path_lineedit_03,
                                            self.edit_top_layer_pushbutton_03,
                                            self.edit_foreground_pushbutton_03,
                                            self.edit_between_marks_pushbutton_03,
                                            self.edit_token_push_btn_03,
                                            self.edit_export_push_btn_03,
                                            self.edit_server_browse_btn_03,
                                            self.edit_saved_presets_push_btn_03)

                    try:
                        get_preset_info('Four',
                                        self.edit_enable_preset_pushbutton_04,
                                        self.edit_saved_preset_type_label_04,
                                        self.edit_saved_presets_label_04,
                                        self.edit_export_path_label_04,
                                        self.edit_export_path_lineedit_04,
                                        self.edit_top_layer_pushbutton_04,
                                        self.edit_foreground_pushbutton_04,
                                        self.edit_between_marks_pushbutton_04,
                                        self.edit_token_push_btn_04,
                                        self.edit_export_push_btn_04,
                                        self.edit_server_browse_btn_04,
                                        self.edit_saved_presets_push_btn_04)
                        preset_04_push_btn_text = self.edit_saved_presets_push_btn_04.text()
                    except:

                        # Disable UI elements if nothing loaded for preset four

                        disable_ui_elements(self.edit_enable_preset_pushbutton_04,
                                            self.edit_saved_preset_type_label_04,
                                            self.edit_saved_presets_label_04,
                                            self.edit_export_path_label_04,
                                            self.edit_export_path_lineedit_04,
                                            self.edit_top_layer_pushbutton_04,
                                            self.edit_foreground_pushbutton_04,
                                            self.edit_between_marks_pushbutton_04,
                                            self.edit_token_push_btn_04,
                                            self.edit_export_push_btn_04,
                                            self.edit_server_browse_btn_04,
                                            self.edit_saved_presets_push_btn_04)

                    try:
                        get_preset_info('Five',
                                        self.edit_enable_preset_pushbutton_05,
                                        self.edit_saved_preset_type_label_05,
                                        self.edit_saved_presets_label_05,
                                        self.edit_export_path_label_05,
                                        self.edit_export_path_lineedit_05,
                                        self.edit_top_layer_pushbutton_05,
                                        self.edit_foreground_pushbutton_05,
                                        self.edit_between_marks_pushbutton_05,
                                        self.edit_token_push_btn_05,
                                        self.edit_export_push_btn_05,
                                        self.edit_server_browse_btn_05,
                                        self.edit_saved_presets_push_btn_05)
                        preset_05_push_btn_text = self.edit_saved_presets_push_btn_05.text()
                    except:

                        # Disable UI elements if nothing loaded for preset five

                        disable_ui_elements(self.edit_enable_preset_pushbutton_05,
                                            self.edit_saved_preset_type_label_05,
                                            self.edit_saved_presets_label_05,
                                            self.edit_export_path_label_05,
                                            self.edit_export_path_lineedit_05,
                                            self.edit_top_layer_pushbutton_05,
                                            self.edit_foreground_pushbutton_05,
                                            self.edit_between_marks_pushbutton_05,
                                            self.edit_token_push_btn_05,
                                            self.edit_export_push_btn_05,
                                            self.edit_server_browse_btn_05,
                                            self.edit_saved_presets_push_btn_05)

                    set_export_push_button(self.edit_export_push_btn_01, self.edit_saved_presets_push_btn_01, self.edit_saved_preset_menu_01)
                    set_export_push_button(self.edit_export_push_btn_02, self.edit_saved_presets_push_btn_02, self.edit_saved_preset_menu_02)
                    set_export_push_button(self.edit_export_push_btn_03, self.edit_saved_presets_push_btn_03, self.edit_saved_preset_menu_03)
                    set_export_push_button(self.edit_export_push_btn_04, self.edit_saved_presets_push_btn_04, self.edit_saved_preset_menu_04)
                    set_export_push_button(self.edit_export_push_btn_05, self.edit_saved_presets_push_btn_05, self.edit_saved_preset_menu_05)

                    self.edit_saved_presets_push_btn_01.setText(preset_01_push_btn_text)
                    try:
                        self.edit_saved_presets_push_btn_02.setText(preset_02_push_btn_text)
                    except:
                        pass
                    try:
                        self.edit_saved_presets_push_btn_03.setText(preset_03_push_btn_text)
                    except:
                        pass
                    try:
                        self.edit_saved_presets_push_btn_04.setText(preset_04_push_btn_text)
                    except:
                        pass
                    try:
                        self.edit_saved_presets_push_btn_05.setText(preset_05_push_btn_text)
                    except:
                        pass

                    print ('\n>>> existing export presets loaded <<<\n')

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
                    self.edit_export_push_btn_01.setEnabled(False)
                    self.edit_saved_presets_push_btn_01.setEnabled(False)
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
                    self.edit_export_push_btn_01.setText('')
                    self.edit_export_push_btn_02.setText('')
                    self.edit_export_push_btn_03.setText('')
                    self.edit_export_push_btn_04.setText('')
                    self.edit_export_push_btn_05.setText('')

                    print ('\n>>> no existing presets found <<<\n')

            def delete_preset():

                script_name = self.edit_menu_push_btn.text().split(' ', 1)[1]

                if 'Shared: ' in self.edit_menu_push_btn.text():
                    script_path = os.path.join(self.shared_menus_dir, script_name)
                else:
                    script_path = os.path.join(self.project_menus_dir, self.current_project, script_name)
                print ('\nscript_path:', script_path)

                os.remove(script_path + '.py')
                try:
                    os.remove(script_path + '.pyc')
                except:
                    pass

                print ('\n>>> deleted menu for %s <<<\n' % script_name)

                # Reload button menus

                build_main_menu_preset_menu(self.edit_menu_push_btn, self.edit_export_name_menu)
                load_preset()

                self.refresh_hooks()

            def build_main_menu_preset_menu(created_menu_btn, created_presets_menu):
                from functools import partial

                def add_menu(menu_name):
                    created_menu_btn.setText(menu_name)
                    load_preset()

                # Get list of created presets

                shared_menu_list = ['Shared: ' + menu[:-3] for menu in os.listdir(self.shared_menus_dir) if menu.endswith('.py')]
                shared_menu_list.sort()
                print ('shared_menu_list:', shared_menu_list)

                if os.path.isdir(self.current_project_created_presets_path):
                    project_menu_list = ['Project: ' + menu[:-3] for menu in os.listdir(self.current_project_created_presets_path) if menu.endswith('.py')]
                    print ('project_menu_list:', project_menu_list)
                else:
                    project_menu_list = []
                project_menu_list.sort()

                menu_list = shared_menu_list + project_menu_list
                print ('menu_list:', menu_list)

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

            def save_edited_menu():
                import flame
                import re

                def preset_check():

                    if self.edit_saved_presets_push_btn_01.text() == 'No Saved Presets Found':
                        return 'Export Preset One - Select a saved export preset'

                    if not self.edit_export_path_lineedit_01.text():
                        return 'Export Preset One - Add export path'

                    # Preset two field check

                    if self.edit_enable_preset_pushbutton_02.isChecked():

                        if self.edit_saved_presets_push_btn_02.text() == 'No Saved Export Presets':
                            return 'Export Preset Two - Select a saved export preset'

                        if self.edit_saved_presets_push_btn_02.text() == 'No Saved Presets Found':
                            return 'Export Preset Two - Select a saved export preset'

                        if not self.edit_export_path_lineedit_02.text():
                            return 'Export Preset Two - Add export path'

                    # Preset three field check

                    if self.edit_enable_preset_pushbutton_03.isChecked():

                        if self.edit_saved_presets_push_btn_03.text() == 'No Saved Export Presets':
                            return 'Export Preset Three - Select a saved export preset'

                        if self.edit_saved_presets_push_btn_03.text() == 'No Saved Presets Found':
                            return 'Export Preset Two - Select a saved export preset'

                        if not self.edit_export_path_lineedit_03.text():
                            return 'Export Preset Three - Add export path666'

                    # Preset four field check

                    if self.edit_enable_preset_pushbutton_04.isChecked():

                        if self.edit_saved_presets_push_btn_04.text() == 'No Saved Export Presets':
                            return 'Export Preset Four - Select a saved export preset'

                        if self.edit_saved_presets_push_btn_04.text() == 'No Saved Presets Found':
                            return 'Export Preset Two - Select a saved export preset'

                        if not self.edit_export_path_lineedit_04.text():
                            return 'Export Preset Four - Add export path'

                    # Preset five field check

                    if self.edit_enable_preset_pushbutton_05.isChecked():

                        if self.edit_saved_presets_push_btn_05.text() == 'No Saved Export Presets':
                            return 'Export Preset Five - Select a saved export preset'

                        if self.edit_saved_presets_push_btn_05.text() == 'No Saved Presets Found':
                            return 'Export Preset Two - Select a saved export preset'

                        if not self.edit_export_path_lineedit_05.text():
                            return 'Export Preset Five - Add export path'

                def set_menu_save_path():

                    # Set path for new menu file

                    if self.edit_menu_visibility_push_btn.text() == 'Project':
                        menu_save_dir = os.path.join(self.project_menus_dir, self.current_project)
                        self.script_project = self.current_project
                    else:
                        menu_save_dir = self.shared_menus_dir
                        self.script_project = 'None'

                    if not os.path.isdir(menu_save_dir):
                        os.makedirs(menu_save_dir)

                    self.menu_name = self.edit_menu_name_lineedit.text()
                    self.menu_name = self.menu_name.replace('.', '_')
                    self.menu_name = self.menu_name + '.py'

                    self.menu_save_file = os.path.join(menu_save_dir, self.menu_name)# + '.py'

                    print ('menu_save_file:', self.menu_save_file)

                def menu_template_replace_tokens():

                    # Replace tokens in menu template file

                    template_token_dict = {}

                    template_token_dict['<ScriptProject>'] = self.script_project
                    template_token_dict['<PresetName>'] = self.edit_menu_name_lineedit.text()
                    template_token_dict['<PresetType>'] = self.edit_menu_visibility_push_btn.text()

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

                    def get_preset_path(export_push_btn, saved_presets_push_btn):

                        # Get selected preset path

                        selected_export_menu = export_push_btn.text()

                        if 'Project' in selected_export_menu:
                            preset_path = self.project_preset_path
                        else:
                            preset_path = self.shared_preset_path

                        if 'Movie' in selected_export_menu:
                            preset_dir_path = preset_path + '/movie_file'
                        else:
                            preset_dir_path = preset_path + '/file_sequence'

                        preset_file_path = os.path.join(preset_dir_path, saved_presets_push_btn.text()) + '.xml'

                        print ('preset path:', preset_file_path, '\n')

                        return preset_file_path

                    def new_lines(export_preset_num, use_top_layer, export_in_foreground, export_between_marks, export_path, preset_file_path):

                        menu_lines.append("")
                        menu_lines.append("        # Export preset %s" % export_preset_num)
                        menu_lines.append("")
                        menu_lines.append("        # Export using top video track")
                        menu_lines.append("")
                        menu_lines.append("        clip_output.use_top_video_track = %s" % use_top_layer)
                        menu_lines.append("        print ('\\n>>> Export using top layer: %s <<<')" % use_top_layer)
                        menu_lines.append("")
                        menu_lines.append("        # Set export to foreground")
                        menu_lines.append("")
                        menu_lines.append("        clip_output.foreground = %s" % export_in_foreground)
                        menu_lines.append("        print ('>>> Export in foreground: %s <<<')" % export_in_foreground)
                        menu_lines.append("")
                        menu_lines.append("        # Export between markers")
                        menu_lines.append("")
                        menu_lines.append("        clip_output.export_between_marks = %s" % export_between_marks)
                        menu_lines.append("        print ('>>> Export between marks: %s <<<\\n\\n')" % export_between_marks)
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
                        menu_lines.append("        # Export preset %s END" % export_preset_num)
                        menu_lines.append("")

                    def switch_to_mediahub_lines():

                        menu_lines.append("")
                        menu_lines.append("        # Check flame version")
                        menu_lines.append("")
                        menu_lines.append("        flame_version = flame.get_version()")
                        menu_lines.append("")
                        menu_lines.append("        if 'pr' in flame_version:")
                        menu_lines.append("            flame_version = flame_version.rsplit('.pr', 1)[0]")
                        menu_lines.append("        if  flame_version.count('.') > 1:")
                        menu_lines.append("            flame_version = flame_version.rsplit('.', 1)[0]")
                        menu_lines.append("        flame_version = float(flame_version)")
                        menu_lines.append("        print ('flame_version:', flame_version)")
                        menu_lines.append("")
                        menu_lines.append("        # If flame version 2021.2 or higher switch to mediahub")
                        menu_lines.append("")
                        menu_lines.append("        if flame_version >= 2021.2:")
                        menu_lines.append("            flame.go_to('MediaHub')")
                        menu_lines.append("            flame.mediahub.files.set_path(new_export_path)")
                        menu_lines.append("            print ('\\n>>> Media Hub opened <<<\\n')")
                        menu_lines.append("")

                    # Build preset menus

                    # First preset tab

                    preset_file_path = get_preset_path(self.edit_export_push_btn_01, self.edit_saved_presets_push_btn_01)
                    print ('preset_file_path:', preset_file_path)
                    new_lines('One', str(self.edit_top_layer_pushbutton_01.isChecked()), str(self.edit_foreground_pushbutton_01.isChecked()), str(self.edit_between_marks_pushbutton_01.isChecked()), self.edit_export_path_lineedit_01.text(), preset_file_path)

                    if self.edit_enable_preset_pushbutton_02.isChecked():
                        preset_file_path = get_preset_path(self.edit_export_push_btn_02, self.edit_saved_presets_push_btn_02)
                        print ('preset_file_path:', preset_file_path)
                        new_lines('Two', str(self.edit_top_layer_pushbutton_02.isChecked()), str(self.edit_foreground_pushbutton_02.isChecked()), str(self.edit_between_marks_pushbutton_02.isChecked()), self.edit_export_path_lineedit_02.text(), preset_file_path)

                    if self.edit_enable_preset_pushbutton_03.isChecked():
                        preset_file_path = get_preset_path(self.edit_export_push_btn_03, self.edit_saved_presets_push_btn_03)
                        print ('preset_file_path:', preset_file_path)
                        new_lines('Three', str(self.edit_top_layer_pushbutton_03.isChecked()), str(self.edit_foreground_pushbutton_03.isChecked()), str(self.edit_between_marks_pushbutton_03.isChecked()), self.edit_export_path_lineedit_03.text(), preset_file_path)

                    if self.edit_enable_preset_pushbutton_04.isChecked():
                        preset_file_path = get_preset_path(self.edit_export_push_btn_04, self.edit_saved_presets_push_btn_04)
                        print ('preset_file_path:', preset_file_path)
                        new_lines('Four', str(self.edit_top_layer_pushbutton_04.isChecked()), str(self.edit_foreground_pushbutton_04.isChecked()), str(self.edit_between_marks_pushbutton_04.isChecked()), self.edit_export_path_lineedit_04.text(), preset_file_path)

                    if self.edit_enable_preset_pushbutton_05.isChecked():
                        preset_file_path = get_preset_path(self.edit_export_push_btn_05, self.edit_saved_presets_push_btn_05)
                        print ('preset_file_path:', preset_file_path)
                        new_lines('Five', str(self.edit_top_layer_pushbutton_05.isChecked()), str(self.edit_foreground_pushbutton_05.isChecked()), str(self.edit_between_marks_pushbutton_05.isChecked()), self.edit_export_path_lineedit_05.text(), preset_file_path)

                    # Add lines to switch to mediahub

                    switch_to_mediahub_lines()

                # Check fields for proper entries

                if not self.menu_name_lineedit.text():
                    return message_box('Add menu name')

                preset_error = preset_check()
                if preset_error:
                    return message_box(preset_error)

                # Get selected menu path

                selected_script_name = self.edit_menu_push_btn.text().rsplit(': ', 1)[1]
                print ('selected_script_name:', selected_script_name)

                if 'Shared: ' in self.edit_menu_push_btn.text():
                    selected_menu_path = os.path.join(self.shared_menus_dir, selected_script_name)
                elif 'Project: ' in self.edit_menu_push_btn.text():
                    selected_menu_path = os.path.join(self.project_menus_dir, self.current_project, selected_script_name)

                print ('selected_menu_path:', selected_menu_path)

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
                    overwrite = message_box_confirm('File already exists. Overwrite?')
                    if overwrite == False:
                        print ('\n>>> save cancelled <<<\n')
                        return

                # Check other folders for menu with same name

                menu_save_folder = self.menu_save_file.rsplit('/', 1)[0]
                print ('menu_save_folder:', menu_save_folder)

                for root, dirs, files in os.walk(SCRIPT_PATH):
                    if root != menu_save_folder:
                        for f in files:
                            if f == self.menu_name:
                                return message_box('Menu name already exists.<br>Change name to avoid conflict')

                # Save new menu

                out_file = open(self.menu_save_file, 'w')
                for line in self.template_lines:
                    print(line, file=out_file)
                out_file.close()

                # Delete old menu preset if name of preset has changed

                if self.edit_menu_push_btn.text().split(' ', 1)[1] != self.edit_menu_name_lineedit.text():
                    os.remove(selected_menu_path + '.py')
                    try:
                        os.remove(selected_menu_path + '.pyc')
                    except:
                        pass

                # Reload button menus

                build_main_menu_preset_menu(self.edit_menu_push_btn, self.edit_export_name_menu)
                load_preset()

                message_box('Edited Menu Saved')

                # Refresh python hooks

                flame.execute_shortcut('Rescan Python Hooks')

                print ('\n>>> python hooks refreshed <<<')

            # Labels

            self.edit_menu_visibility_label = QtWidgets.QLabel('Menu Visibility', self.window)
            self.edit_menu_visibility_label.setMinimumWidth(140)
            self.edit_menu_visibility_label.setMaximumWidth(150)
            self.edit_menu_visibility_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                          'QLabel:disabled {color: #6a6a6a}')

            self.edit_menu_label = QtWidgets.QLabel('Menu', self.window)
            self.edit_menu_label.setMinimumWidth(140)
            self.edit_menu_label.setMaximumWidth(150)
            self.edit_menu_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                               'QLabel:disabled {color: #6a6a6a}')

            self.edit_menu_name_label = QtWidgets.QLabel('Menu Name', self.window)
            self.edit_menu_name_label.setMinimumWidth(140)
            self.edit_menu_name_label.setMaximumWidth(150)
            self.edit_menu_name_label.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                                                    'QLabel:disabled {color: #6a6a6a}')

            # LineEdits

            self.edit_menu_name_lineedit = QtWidgets.QLineEdit('', self.window)
            self.edit_menu_name_lineedit.setMinimumSize(QtCore.QSize(200, 28))
            self.edit_menu_name_lineedit.setMaximumSize(QtCore.QSize(450, 28))
            self.edit_menu_name_lineedit.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                                       'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

            ## -------------------------------------------------------------

            ## Select Menu Push Button Menu

            self.edit_export_name_menu = QtWidgets.QMenu(self.window)
            self.edit_export_name_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            self.edit_menu_push_btn = QtWidgets.QPushButton('', self.window)
            self.edit_menu_push_btn.setMenu(self.edit_export_name_menu)
            self.edit_menu_push_btn.setMinimumSize(QtCore.QSize(450, 28))
            self.edit_menu_push_btn.setMaximumSize(QtCore.QSize(450, 28))
            self.edit_menu_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.edit_menu_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                  'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

            build_main_menu_preset_menu(self.edit_menu_push_btn, self.edit_export_name_menu)

            ## Menu Visibility Push Button Menu

            def project_preset_menu():
                self.edit_menu_visibility_push_btn.setText('Project')

            def shared_preset_menu():
                self.edit_menu_visibility_push_btn.setText('Shared')

            self.edit_export_type_menu = QtWidgets.QMenu(self.window)
            self.edit_export_type_menu.addAction('Project', project_preset_menu)
            self.edit_export_type_menu.addAction('Shared', shared_preset_menu)
            self.edit_export_type_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                                     'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

            self.edit_menu_visibility_push_btn = QtWidgets.QPushButton('Project', self.window)
            self.edit_menu_visibility_push_btn.setMenu(self.edit_export_type_menu)
            self.edit_menu_visibility_push_btn.setMinimumSize(QtCore.QSize(150, 28))
            self.edit_menu_visibility_push_btn.setMaximumSize(QtCore.QSize(150, 28))
            self.edit_menu_visibility_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.edit_menu_visibility_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                                             'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

            # -------------------------------------------------------------

            # Buttons

            self.edit_delete_btn = QtWidgets.QPushButton('Delete', self.window)
            self.edit_delete_btn.setMinimumSize(QtCore.QSize(110, 28))
            self.edit_delete_btn.setMaximumSize(QtCore.QSize(110, 28))
            self.edit_delete_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.edit_delete_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                               'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                                               'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
            self.edit_delete_btn.clicked.connect(delete_preset)

            self.edit_save_btn = QtWidgets.QPushButton('Save', self.window)
            self.edit_save_btn.setMinimumSize(QtCore.QSize(110, 28))
            self.edit_save_btn.setMaximumSize(QtCore.QSize(110, 28))
            self.edit_save_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.edit_save_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                             'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
            self.edit_save_btn.clicked.connect(save_edited_menu)

            self.edit_done_btn = QtWidgets.QPushButton('Done', self.window)
            self.edit_done_btn.setMinimumSize(QtCore.QSize(110, 28))
            self.edit_done_btn.setMaximumSize(QtCore.QSize(110, 28))
            self.edit_done_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.edit_done_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                             'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font:italic}')
            self.edit_done_btn.clicked.connect(self.window.close)

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
            edit_gridbox.addWidget(self.edit_menu_name_lineedit, 2, 1, 1, 2)

            edit_gridbox.addWidget(self.edit_preset_tabs, 4, 0, 1, 6)

            edit_gridbox.addWidget(self.edit_done_btn, 6, 4)
            edit_gridbox.addWidget(self.edit_save_btn, 6, 5)

            self.window.edit_tab.setLayout(edit_gridbox)

        create_tab()
        edit_tab()

        # Window Layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.addWidget(self.main_tabs)

        self.window.setLayout(gridbox)

        self.window.show()

    def server_path_browse(self, lineedit):
        from PySide2 import QtWidgets

        export_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.window, "Select Directory", lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

        if export_path != '':
            lineedit.setText(export_path)

    def create_menu(self):
        import flame
        import re

        def preset_check():

            if self.saved_presets_push_btn_01.text() == 'No Saved Presets Found':
                return 'Export Preset One - No saved preset selected'

            if not self.export_path_lineedit_01.text():
                return 'Export Preset One - Add export path'

            # Preset two field check

            if self.enable_preset_pushbutton_02.isChecked():

                if self.saved_presets_push_btn_02.text() == 'No Saved Presets Found':
                    return 'Export Preset Two - No saved preset selected'

                if not self.export_path_lineedit_02.text():
                    return 'Export Preset Two - Add export path'

            # Preset three field check

            if self.enable_preset_pushbutton_03.isChecked():

                if self.saved_presets_push_btn_03.text() == 'No Saved Presets Found':
                    return 'Export Preset Three - No saved preset selected'

                if not self.export_path_lineedit_03.text():
                    return 'Export Preset Three - Add export path'

            # Preset four field check

            if self.enable_preset_pushbutton_04.isChecked():

                if self.saved_presets_push_btn_04.text() == 'No Saved Presets Found':
                    return 'Export Preset Four - No saved preset selected'

                if not self.export_path_lineedit_04.text():
                    return 'Export Preset Four - Add export path'

            # Preset five field check

            if self.enable_preset_pushbutton_05.isChecked():

                if self.saved_presets_push_btn_05.text() == 'No Saved Presets Found':
                    return 'Export Preset Five - No saved preset selected'

                if not self.export_path_lineedit_05.text():
                    return 'Export Preset Five - Add export path'

        def set_menu_save_path():

            # Set path for new menu file

            if self.menu_visibility_push_btn.text() == 'Project':
                menu_save_dir = os.path.join(self.project_menus_dir, self.current_project)
                self.script_project = self.current_project
            else:
                menu_save_dir = self.shared_menus_dir
                self.script_project = 'None'

            if not os.path.isdir(menu_save_dir):
                os.makedirs(menu_save_dir)

            self.menu_name = self.menu_name_lineedit.text()
            self.menu_name = self.menu_name.replace('.', '_')
            self.menu_name = self.menu_name + '.py'

            self.menu_save_file = os.path.join(menu_save_dir, self.menu_name)# + '.py'

            print ('menu_save_file:', self.menu_save_file)

        def menu_template_replace_tokens():

            # Replace tokens in menu template file

            template_token_dict = {}

            template_token_dict['<ScriptProject>'] = self.script_project
            template_token_dict['<PresetName>'] = self.menu_name_lineedit.text()
            template_token_dict['<PresetType>'] = self.menu_visibility_push_btn.text()

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

            def get_preset_path(export_push_btn, saved_presets_push_btn):

                # Get selected preset path

                selected_export_menu = export_push_btn.text()

                if 'Project' in selected_export_menu:
                    preset_path = self.project_preset_path
                else:
                    preset_path = self.shared_preset_path

                if 'Movie' in selected_export_menu:
                    preset_dir_path = preset_path + '/movie_file'
                else:
                    preset_dir_path = preset_path + '/file_sequence'

                preset_file_path = os.path.join(preset_dir_path, saved_presets_push_btn.text()) + '.xml'

                print ('preset path:', preset_file_path, '\n')

                return preset_file_path

            def new_lines(export_preset_num, use_top_layer, export_in_foreground, export_between_marks, export_path, preset_file_path):

                menu_lines.append("")
                menu_lines.append("        # Export preset %s" % export_preset_num)
                menu_lines.append("")
                menu_lines.append("        # Export using top video track")
                menu_lines.append("")
                menu_lines.append("        clip_output.use_top_video_track = %s" % use_top_layer)
                menu_lines.append("        print ('\\n>>> Export using top layer: %s <<<')" % use_top_layer)
                menu_lines.append("")
                menu_lines.append("        # Set export to foreground")
                menu_lines.append("")
                menu_lines.append("        clip_output.foreground = %s" % export_in_foreground)
                menu_lines.append("        print ('>>> Export in foreground: %s <<<')" % export_in_foreground)
                menu_lines.append("")
                menu_lines.append("        # Export between markers")
                menu_lines.append("")
                menu_lines.append("        clip_output.export_between_marks = %s" % export_between_marks)
                menu_lines.append("        print ('>>> Export between marks: %s <<<\\n\\n')" % export_between_marks)
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
                menu_lines.append("        # Export preset %s END" % export_preset_num)
                menu_lines.append("")

            def switch_to_mediahub_lines():

                menu_lines.append("")
                menu_lines.append("        # Check flame version")
                menu_lines.append("")
                menu_lines.append("        flame_version = flame.get_version()")
                menu_lines.append("")
                menu_lines.append("        if 'pr' in flame_version:")
                menu_lines.append("            flame_version = flame_version.rsplit('.pr', 1)[0]")
                menu_lines.append("        if  flame_version.count('.') > 1:")
                menu_lines.append("            flame_version = flame_version.rsplit('.', 1)[0]")
                menu_lines.append("        flame_version = float(flame_version)")
                menu_lines.append("        print ('flame_version:', flame_version)")
                menu_lines.append("")
                menu_lines.append("        # If flame version 2021.2 or higher switch to mediahub")
                menu_lines.append("")
                menu_lines.append("        if flame_version >= 2021.2:")
                menu_lines.append("            flame.go_to('MediaHub')")
                menu_lines.append("            flame.mediahub.files.set_path(new_export_path)")
                menu_lines.append("            print ('\\n>>> Media Hub opened <<<\\n')")
                menu_lines.append("")

            # Build preset menus

            # First preset tab

            preset_file_path = get_preset_path(self.export_push_btn_01, self.saved_presets_push_btn_01)
            print ('preset_file_path:', preset_file_path)
            new_lines('One', str(self.top_layer_pushbutton_01.isChecked()), str(self.foreground_pushbutton_01.isChecked()), str(self.between_marks_pushbutton_01.isChecked()), self.export_path_lineedit_01.text(), preset_file_path)

            if self.enable_preset_pushbutton_02.isChecked():
                preset_file_path = get_preset_path(self.export_push_btn_02, self.saved_presets_push_btn_02)
                print ('preset_file_path:', preset_file_path)
                new_lines('Two', str(self.top_layer_pushbutton_02.isChecked()), str(self.foreground_pushbutton_02.isChecked()), str(self.between_marks_pushbutton_02.isChecked()), self.export_path_lineedit_02.text(), preset_file_path)

            if self.enable_preset_pushbutton_03.isChecked():
                preset_file_path = get_preset_path(self.export_push_btn_03, self.saved_presets_push_btn_03)
                print ('preset_file_path:', preset_file_path)
                new_lines('Three', str(self.top_layer_pushbutton_03.isChecked()), str(self.foreground_pushbutton_03.isChecked()), str(self.between_marks_pushbutton_03.isChecked()), self.export_path_lineedit_03.text(), preset_file_path)

            if self.enable_preset_pushbutton_04.isChecked():
                preset_file_path = get_preset_path(self.export_push_btn_04, self.saved_presets_push_btn_04)
                print ('preset_file_path:', preset_file_path)
                new_lines('Four', str(self.top_layer_pushbutton_04.isChecked()), str(self.foreground_pushbutton_04.isChecked()), str(self.between_marks_pushbutton_04.isChecked()), self.export_path_lineedit_04.text(), preset_file_path)

            if self.enable_preset_pushbutton_05.isChecked():
                preset_file_path = get_preset_path(self.export_push_btn_05, self.saved_presets_push_btn_05)
                print ('preset_file_path:', preset_file_path)
                new_lines('Five', str(self.top_layer_pushbutton_05.isChecked()), str(self.foreground_pushbutton_05.isChecked()), str(self.between_marks_pushbutton_05.isChecked()), self.export_path_lineedit_05.text(), preset_file_path)

            # Add lines to switch to mediahub

            switch_to_mediahub_lines()

        def save_config_file():

            # Save config file
            # ----------------

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame Create Export Menus script.')
            config_text.insert(1, 'Export Path')
            config_text.insert(2, self.export_path_lineedit_01.text())
            config_text.insert(3, 'Use Top Layer')
            config_text.insert(4, self.top_layer_pushbutton_01.isChecked())
            config_text.insert(5, 'Export in Foreground')
            config_text.insert(6, self.foreground_pushbutton_01.isChecked())
            config_text.insert(7, 'Export Between Marks')
            config_text.insert(8, self.between_marks_pushbutton_01.isChecked())

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

        # Check fields for proper entries

        if not self.menu_name_lineedit.text():
            return message_box('Add menu name')

        preset_error = preset_check()
        if preset_error:
            return message_box(preset_error)

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
            overwrite = message_box_confirm('File already exists. Overwrite?')
            if overwrite == False:
                print ('\n>>> save cancelled <<<\n')
                return

        # Check other folders for menu with same name

        menu_save_folder = self.menu_save_file.rsplit('/', 1)[0]
        print ('menu_save_folder:', menu_save_folder)

        for root, dirs, files in os.walk(SCRIPT_PATH):
            if root != menu_save_folder:
                for f in files:
                    if f == self.menu_name:
                        return message_box('Menu name already exists.<br>Change name to avoid conflict')

        save_config_file()

        # Save new menu

        out_file = open(self.menu_save_file, 'w')
        for line in self.template_lines:
            print(line, file=out_file)
        out_file.close()

        self.refresh_hooks()

        message_box('Export Menu Created: %s' % self.menu_name_lineedit.text())

        self.window.close()

    def refresh_hooks(self):
        import flame

        # Refresh python hooks

        flame.execute_shortcut('Rescan Python Hooks')

        print ('\n>>> python hooks refreshed <<<')

#-------------------------------------#

def message_box(message):
    from PySide2 import QtWidgets, QtCore

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
    from PySide2 import QtWidgets, QtCore

    msg_box = QtWidgets.QMessageBox()
    msg_box.setText('<b><center>%s' % message)
    msg_box_yes_button = msg_box.addButton(QtWidgets.QMessageBox.Yes)
    msg_box_yes_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_yes_button.setMinimumSize(QtCore.QSize(80, 24))
    msg_box_no_button = msg_box.addButton(QtWidgets.QMessageBox.No)
    msg_box_no_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_no_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14px "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14px "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

    message = message.replace('<br>', '-')

    print ('\n>>> %s <<<\n' % message)

    if msg_box.exec_() == QtWidgets.QMessageBox.Yes:
        return True
    return False

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Create Export Menus',
                    'execute': ExportSetup,
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]
