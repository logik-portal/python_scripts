'''
Script Name: Shot Sheet Maker
Script Version: 3.0
Flame Version: 2020
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 02.18.19
Update Date: 05.28.21

Custom Action Type: Media Panel

Description:

    Create excel shot sheet from selected sequence clip.

    *** First time script is run it will need to install xlsxWriter - System password required for this ***

    Sequence should have all clips on one track with no gap at start.

    Right-click on sequence in media panel -> Shot Sheet Maker... -> Export Shot Sheet

To install:

    Copy script into /opt/Autodesk/shared/python/shot_sheet_maker

    If installing this script manually make sure Flame has full permissions to the
    shot_sheet_maker folder, otherwise the script may fail to run properly.

Updates:

v3.0 05.28.21

    Updated to be compatible with Flame 2022/Python 3.7

    Updated UI

    Added check to make sure sequence has only one version/track

    Added button to reveal spreadsheet in finder when done

v2.2 07.15.20

    Script setup now in Flame Main Menu: Flame Main Menu -> pyFlame -> Shot Sheet Maker Setup

    Window now closes before overwrite warning appears so overwrite warning is not behind window.

    The following information can be added to the spreadsheet for each shot:
        Source Clip Name
        Source Clip Path
        Source Timecode
        Record Timecode
        Shot Length - Length of shot minus handles
        Source Length - Length of shot plus handles

    Better sizing of image column to match size/ratio of sequence images

v2.1 04.05.20

    Fixed UI issues in Linux

v2.0 12.26.19

    Up to 20 columns can now be added through the Edit Column Names button

    Thumbnail images used in the shot sheet can be saved if desired

    Misc. bug fixes
'''

from __future__ import print_function
import re
import os
import ast
import shutil
from PySide2 import QtCore, QtWidgets

VERSION = 'v3.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/shot_sheet_maker'

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
        self.setMinimumSize(130, 28)
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
        self.setMinimumSize(QtCore.QSize(155, 28))
        self.setMaximumSize(QtCore.QSize(155, 28))
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

    pushbutton = FlamePushButton(' Button Name', True_or_False, window)
    """

    def __init__(self, button_name, button_checked, parent_window, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setCheckable(True)
        self.setChecked(button_checked)
        self.setMinimumSize(155, 28)
        self.setMaximumSize(155, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #424142, stop: .94 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #4f4f4f, stop: .94 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlamePushButtonMenu(QtWidgets.QPushButton):
    """
    Custom Qt Flame Menu Push Button Widget

    To use:

    push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
    menu_push_button = FlamePushButtonMenu('push_button_name', push_button_menu_options, window)

    or

    push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
    menu_push_button = FlamePushButtonMenu(push_button_menu_options[0], push_button_menu_options, window)
    """

    def __init__(self, button_name, menu_options, parent_window, *args, **kwargs):
        super(FlamePushButtonMenu, self).__init__(*args, **kwargs)
        from functools import partial

        self.setText(button_name)
        self.setParent(parent_window)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        def create_menu(option):
            self.setText(option)

        pushbutton_menu = QtWidgets.QMenu(parent_window)
        pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        pushbutton_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        for option in menu_options:
            pushbutton_menu.addAction(option, partial(create_menu, option))

        self.setMenu(pushbutton_menu)

#-------------------------------------#

class ShotSheetMaker(object):

    def __init__(self, selection):
        from collections import OrderedDict
        import flame

        print ('\n', '>' * 20, ' shot sheet maker %s ' % VERSION, '<' * 20, '\n')

        self.selection = selection

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')
        self.column_file = os.path.join(self.config_path, 'column_names')
        self.preset_path = os.path.join(SCRIPT_PATH, 'export_presets')

        # Get Flame variables

        self.flame_project_name = flame.project.current_project.name
        # print ('flame_project_name:', self.flame_project_name)

        self.current_flame_version = flame.get_version()
        # print ('current_flame_version:', self.current_flame_version, '\n')

        # Get config variables
        # --------------------

        self.config_file_check()

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.export_path = values[2]
        self.thumbnail_size = values[4]
        self.reveal_in_finder = ast.literal_eval(values[6])
        self.add_source_name = ast.literal_eval(values[8])
        self.add_source_path = ast.literal_eval(values[10])
        self.add_source_tc = ast.literal_eval(values[12])
        self.add_record_tc = ast.literal_eval(values[14])
        self.add_shot_length = ast.literal_eval(values[16])
        self.add_source_length = ast.literal_eval(values[18])

        get_config_values.close()

        print ('>>> shot sheet maker config loaded <<<\n')

        # Seq info variables

        for select in self.selection:
            self.seq_name = str(select.name)[1:-1]
            self.seq_height = select.height
            self.seq_width = select.width
            self.seq_ratio = float(self.seq_width) / float(self.seq_height)
            break

        self.thumb_nail_height = ''
        self.thumb_nail_width = ''
        self.x_offset = ''
        self.y_offset = ''
        self.column_width = ''
        self.row_height = ''
        self.temp_export_preset = ''
        self.image_dir = ''
        self.workbook_name = ''

        self.shot_dict = OrderedDict()

        # List for order of shots in edit - Used later to load shots into spreadsheet

        self.shot_list = []

        # Is export a seq or collection of clips

        if len(self.selection) == 1:
            self.export_type = 'seq'
        else:
            self.export_type = 'clip'

        # Check that sequence only has one version/track

        for item in self.selection:
            if len(item.versions) > 1:
                return message_box('Sequence can only have one version/track')
        for item in self.selection:
            if len(item.versions[0].tracks) > 1:
                return message_box('Sequence can only have one track')

        # Check for xlsxWriter

        xlsxwriter_installed = self.xlsxwriter_check()

        if xlsxwriter_installed:
            return self.main_window()
        return self.setup()

    def xlsxwriter_check(self):

        # Import xlsxWriter
        # Run setup if not found

        try:
            import xlsxwriter
            print ('>>> xlsxWriter imported <<<\n')
            return True
        except:
            print ('\n>>> xlsxWriter not installed <<<\n')
            return False

    def config_file_check(self):

        if not os.path.isdir(self.config_path):
            print ('config folder does not exist, creating folder and config file.\n')
            os.makedirs(self.config_path)
            if not os.path.isdir(self.config_path):
                message_box('Unable to create folder:<br>%s<br>Check folder permissions' % self.config_path)

        if not os.path.isfile(self.config_file):
            print ('config file does not exist, creating new config file.\n')

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame Shot Sheet Maker script.')
            config_text.insert(1, 'Export Path')
            config_text.insert(2, '')
            config_text.insert(3, 'Thumbnail Size')
            config_text.insert(4, 'Medium')
            config_text.insert(5, 'Reveal in Finder')
            config_text.insert(6, 'True')
            config_text.insert(7, 'Add Source name:')
            config_text.insert(8, 'False')
            config_text.insert(9, 'Add Source Path:')
            config_text.insert(10, 'False')
            config_text.insert(11, 'Add Source Timecode:')
            config_text.insert(12, 'False')
            config_text.insert(13, 'Add Record Timecode:')
            config_text.insert(14, 'False')
            config_text.insert(15, 'Add Shot Lenth:')
            config_text.insert(16, 'False')
            config_text.insert(17, 'Add Source Length:')
            config_text.insert(18, 'False')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

            config_text = []

            config_text.insert(0, 'Column names for pyFlame Shot Sheet Maker script.')
            config_text.insert(1, 'Internal Notes')
            config_text.insert(2, 'Client Notes')
            config_text.insert(3, 'Shot Description')
            config_text.insert(4, 'Task')

            out_file = open(self.column_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

    def main_window(self):

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(700, 400))
        self.window.setMaximumSize(QtCore.QSize(700, 400))
        self.window.setWindowTitle('Shot Sheet Maker %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.spread_sheet_settings_label = FlameLabel('Spreadsheet Settings', 'background', self.window)
        self.export_path_label = FlameLabel('Export Path', 'normal', self.window)
        self.spreadsheet_name_label = FlameLabel('Shot Sheet Name', 'normal', self.window)
        self.thumbnail_size_label = FlameLabel('Thumbnail Size', 'normal', self.window)
        self.add_clip_info_label = FlameLabel('Add Columns With Clip Info', 'background', self.window)

        # Entries

        self.export_path_entry = FlameLineEdit(self.export_path, self.window)

        if self.export_type == 'seq':
            self.spreadsheet_name_entry = FlameLineEdit(self.seq_name, self.window)
        else:
            self.spreadsheet_name_entry = FlameLineEdit(self.flame_project_name, self.window)

        # Push Button Menu

        thumbnail_menu_options = ['Large', 'Medium', 'Small']
        self.thumbnail_push_button = FlamePushButtonMenu(self.thumbnail_size, thumbnail_menu_options, self.window)

        # Push buttons

        self.reveal_in_finder_push_button = FlamePushButton(' Reveal in Finder', True, self.window)

        self.source_name_push_button = FlamePushButton(' Add Source Name', self.add_source_name, self.window)
        self.source_path_push_button = FlamePushButton(' Add Source Path', self.add_source_path, self.window)
        self.source_tc_push_button = FlamePushButton(' Add Source Timecode', self.add_source_tc, self.window)
        self.record_tc_push_button = FlamePushButton(' Add Record Timecode', self.add_record_tc, self.window)
        self.shot_length_push_button = FlamePushButton(' Add Shot Length', self.add_shot_length, self.window)
        self.source_length_push_button = FlamePushButton(' Add Source Length', self.add_source_length, self.window)

        # Buttons

        self.export_path_browse_btn = FlameButton('Browse', self.export_path_browse, self.window)
        self.edit_column_names_btn = FlameButton('Edit Column Names', self.edit_column_names, self.window)
        self.create_btn = FlameButton('Create', self.check_entries, self.window)
        self.cancel_btn = FlameButton('Cancel', self.window.close, self.window)

        #------------------------------------#

        #  Window Layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setHorizontalSpacing(20)

        gridbox.addWidget(self.export_path_label, 0, 0)
        gridbox.addWidget(self.export_path_entry, 0, 1, 1, 2)
        gridbox.addWidget(self.export_path_browse_btn, 0, 3)

        gridbox.addWidget(self.spreadsheet_name_label, 1, 0)
        gridbox.addWidget(self.spreadsheet_name_entry, 1, 1, 1, 2)

        gridbox.setRowMinimumHeight(2, 28)

        gridbox.addWidget(self.spread_sheet_settings_label, 3, 0, 1, 4)
        gridbox.addWidget(self.thumbnail_size_label, 4, 0)
        gridbox.addWidget(self.thumbnail_push_button, 4, 1)
        gridbox.addWidget(self.reveal_in_finder_push_button, 4, 3)

        gridbox.setRowMinimumHeight(5, 28)

        gridbox.addWidget(self.add_clip_info_label, 6, 0, 1, 3)
        gridbox.addWidget(self.edit_column_names_btn, 6, 3)

        gridbox.addWidget(self.source_name_push_button, 7, 0)
        gridbox.addWidget(self.source_path_push_button, 7, 1)
        gridbox.addWidget(self.source_tc_push_button, 7, 2)
        gridbox.addWidget(self.record_tc_push_button, 8, 0)
        gridbox.addWidget(self.shot_length_push_button, 8, 1)
        gridbox.addWidget(self.source_length_push_button, 8, 2)

        # HBox

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(5)
        hbox.addWidget(self.cancel_btn)
        hbox.addStretch(5)
        hbox.addWidget(self.create_btn)
        hbox.addStretch(5)

        # Main VBox

        vbox = QtWidgets.QVBoxLayout()
        vbox.setMargin(15)
        vbox.addLayout(gridbox)
        vbox.addStretch(5)
        vbox.addLayout(hbox)
        vbox.addStretch(5)

        self.window.setLayout(vbox)

        self.window.show()

    def check_entries(self):

        # Check export path
        # If not found stop and give message

        if not os.path.isdir(self.export_path_entry.text()):
            message_box('Export path not found - Select new path')
            return

        # Check spreadsheet name entry

        if self.spreadsheet_name_entry.text() == '':
            message_box('Enter spreadsheet name')
            return

        if self.export_type == 'seq':
            self.create_seq_shot_sheet()

    def export_path_browse(self):

        export_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.window, "Select Directory", self.export_path_entry.text(), QtWidgets.QFileDialog.ShowDirsOnly))

        if os.path.isdir(export_path):
            self.export_path_entry.setText(export_path)

    def edit_column_names(self):

        def column_file_check():

            def create_default_column_name_file():

                config_text = []

                config_text.insert(0, 'Column names for Shot Sheet Maker script.')
                config_text.insert(1, 'Internal Notes')
                config_text.insert(2, 'Client Notes')
                config_text.insert(3, 'Shot Description')
                config_text.insert(4, 'Task')

                out_file = open(self.column_file, 'w')
                for line in config_text:
                    print(line, file=out_file)
                out_file.close()

            if not os.path.isfile(self.column_file):
                print ('>>> column name file does not exist, creating new file <<<')
                create_default_column_name_file()

        def build_entry_fields():

            # Create list of entries

            entry_list = []

            for num in range(20):
                num = num + 1
                entry_list.append('column_entry' + str(num))
            #print 'entry_list:', entry_list

            # Create dict for dynamic variables

            self.entry_dict = {}
            for x in range(len(entry_list)):
                self.entry_dict[x] = entry_list[x]

            # Add entry fields

            n = 0
            m = 0

            for num in range(20):
                n = n + 1
                if n > 10:
                    m = 500
                    o = n - 10
                else:
                    o = n

                self.column_label_name = FlameLabel('Column %s' % n, 'normal', self.edit_window)
                self.column_label_name.setMinimumSize(100, 28)
                self.column_label_name.move((20 + m), 35 * o)

                self.entry_dict[n] = FlameLineEdit(self.entry_value_dict[n], self.edit_window)
                self.entry_dict[n].move((130 + m), 35 * o)
                self.entry_dict[n].resize(370, 28)

        def load_column_file():

            # Get config variables
            # --------------------

            get_config_values = open(self.column_file, 'r')
            values = get_config_values.read().splitlines()

            # Add blank values to empty fields

            if len(values) < 21:
                short_values = 21 - len(values)
                for x in range(short_values):
                    values.append('')

            # Create variables for all fields

            entry_value_list = []

            for num in range(21):
                num = num + 1
                entry_value_list.append('entry_value' + str(num))
            #print 'entry_value_list:', entry_value_list

            # Create dict for dynamic variables

            self.entry_value_dict = {}
            for x in range(21):
                self.entry_value_dict[x] = entry_value_list[x]

            # Assign values to all variables

            for n in range(21):
                self.entry_value_dict[n] = values[n]
                #print 'value:', self.entry_value_dict[n]

            get_config_values.close()

            print ('>>> shot sheet maker column names loaded <<<\n')

        def save_column_names():

            config_text = []

            config_text.insert(0, 'Column names for pyFlame Shot Sheet Maker script.')

            # Dynamically add entry values

            for x in range(20):
                x = x + 1
                if self.entry_dict[x].text() != '':
                    config_text.insert(x, self.entry_dict[x].text())

            out_file = open(self.column_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

            self.edit_window.close()

            print ('>>> column names saved <<<')

        column_file_check()

        self.edit_window = QtWidgets.QWidget()
        self.edit_window.setFixedSize(1020, 470)
        self.edit_window.setWindowTitle('Edit Column Names')
        self.edit_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.edit_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.edit_window.setStyleSheet('background-color: #272727')

        load_column_file()

        build_entry_fields()

        self.save_columns_button = FlameButton('Save', save_column_names, self.edit_window)
        self.save_columns_button.move(515, 410)

        self.edit_cancel_button = FlameButton('Cancel', self.edit_window.close, self.edit_window)
        self.edit_cancel_button.move(345, 410)

        self.edit_window.show()

    def set_image_dir(self):

        # Set export image dir

        self.image_dir = os.path.join(str(self.export_path_entry.text()), str(self.spreadsheet_name_entry.text()))
        # print ('image_dir:', self.image_dir)

        if not os.path.isdir(self.image_dir):
            try:
                os.makedirs(self.image_dir)
            except:
                message_box('Check export path.<br>Can not create export folder.')

    def export_thumbnail(self):
        import flame

        poster_frame_exporter = flame.PyExporter()
        poster_frame_exporter.foreground = True
        poster_frame_exporter.export(self.clip, self.temp_export_preset, self.image_dir)

    def timecode_to_frames(self, clip_timecode, framerate):

        def _seconds(value):
            # print ('Value:', value)
            if isinstance(value, str):
                _zip_ft = zip((3600, 60, 1, 1/framerate), value.split(':'))
                return sum(f * float(t) for f, t in _zip_ft)
            elif isinstance(value, (int, float)):
                return value / framerate
            return 0

        def _timecode(seconds):
            return '{h:02d}:{m:02d}:{s:02d}:{f:02d}' \
                    .format(h=int(seconds/3600),
                            m=int(seconds/60%60),
                            s=int(seconds%60),
                            f=round((seconds-int(seconds))*framerate))

        def _frames(seconds):
            return seconds * framerate

        def timecode_to_frames(_timecode, start=None):
            return _frames(_seconds(_timecode) - _seconds(start))
        # print ('clip_timecode:', clip_timecode)
        if '+' in clip_timecode:
            clip_timecode = clip_timecode.replace('+', ':')
        elif '#' in clip_timecode:
            clip_timecode = clip_timecode.replace('#', ':')
        # print ('clip_timecode:', clip_timecode)
        frames = int(round(timecode_to_frames(clip_timecode, start='00:00:00:00')))

        return frames

    def create_spreadsheet(self):
        import xlsxwriter

        # Are any clip info buttons selected

        if self.source_name_push_button.isChecked():
            clip_info = True
        elif self.source_path_push_button.isChecked():
            clip_info = True
        elif self.source_tc_push_button.isChecked():
            clip_info = True
        elif self.record_tc_push_button.isChecked():
            clip_info = True
        elif self.shot_length_push_button.isChecked():
            clip_info = True
        elif self.source_length_push_button.isChecked():
            clip_info = True
        else:
            clip_info = False

        # print ('clip_info:', clip_info)

        # Set image export directory and workbook name

        self.workbook_name = str(self.export_path_entry.text()) + '/' +  str(self.spreadsheet_name_entry.text()) + '.xlsx'
        # print ('workbook_name:', self.workbook_name)

        # Create workbook

        workbook = xlsxwriter.Workbook(self.workbook_name)
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', self.column_width)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 25)
        cell_format = workbook.add_format({'font_name': 'Helvetica', 'bg_color': '#d6d6d6', 'bold': True, 'font_color': 'black'})
        cell_format02 = workbook.add_format({'font_name': 'Helvetica', 'bg_color': '#adadad', 'align': 'top', 'text_wrap': True})
        cell_format03 = workbook.add_format({'font_name': 'Helvetica', 'align': 'top', 'text_wrap': True})

        worksheet.set_row(0, cell_format=cell_format02)
        worksheet.set_row(1, cell_format=cell_format02)

        shot_name_insert_row = 3
        image_insert_row = 4

        if clip_info:
            line_height = (len(self.clip_info_list) * 13) + 26
            if line_height > self.row_height:
                self.row_height = line_height
                self.y_offset = ((line_height * 1.333) - self.thumb_nail_height) / 2

        shot_name_row_list = []

        for image in self.shot_dict:
            image_path = os.path.join(self.image_dir, image) + '.jpg'
            worksheet.set_row(shot_name_insert_row, self.row_height, cell_format=cell_format03)
            shot_name_row = 'A' + str(shot_name_insert_row)
            image_row = 'A' + str(image_insert_row)
            shot_name_row_list.append(shot_name_row)
            worksheet.write(shot_name_row, image, cell_format)
            worksheet.insert_image(image_row, image_path, {'x_offset': self.x_offset, 'y_offset': self.y_offset})
            shot_name_insert_row = shot_name_insert_row + 2
            image_insert_row = image_insert_row + 2

        # Load saved column names

        get_config_values = open(self.column_file, 'r')
        column_names = get_config_values.read().splitlines()
        column_names.pop(0)

        get_config_values.close()

        # If clip info True add clip info column

        if clip_info:
            column_names.insert(0, 'Clip Info')
            # print ('column_names:', column_names)

        # List to hold column codes

        column_code_list = []

        # Set column letter iteration

        column_letter = 'A'

        # Iterate through alphabet to create column codes

        for n in column_names:
            column_letter = chr(ord(column_letter) + 1)
            column_code = column_letter + '2'
            column_code_list.append(column_code)

        # Add column names and set column width

        for (code, val) in zip(column_code_list, column_names):
            column_letter = re.split(r'(\d+)', code)[0]
            column_width_code = column_letter + ':' + column_letter
            worksheet.write(code, val, cell_format02)
            worksheet.set_column(column_width_code, 25)

        # If clip info True fill in clip info

        if clip_info:
            worksheet.set_column('B:B', 50)

            clip_info_row = 3

            for key in self.shot_dict:
                clip_info = ''
                for x in range(len(self.clip_info_list)):
                    clip_info = clip_info + '\n' + str(self.shot_dict[key][x])

                worksheet.write(clip_info_row, 1, clip_info)
                clip_info_row += 2

        workbook.close()

    #-------------------------------------#

    def create_seq_shot_sheet(self):
        import flame

        def get_settings():

            self.export_path = self.export_path_entry.text()
            self.thumbnail_size = self.thumbnail_push_button.text()

            self.reveal_in_finder = self.reveal_in_finder_push_button.isChecked()

            self.add_source_name = self.source_name_push_button.isChecked()
            self.add_source_path = self.source_path_push_button.isChecked()
            self.add_source_tc = self.source_tc_push_button.isChecked()
            self.add_record_tc = self.record_tc_push_button.isChecked()
            self.add_shot_length = self.shot_length_push_button.isChecked()
            self.add_source_length = self.source_length_push_button.isChecked()

        def save_config_file():

            config_text = []

            config_text.insert(0, 'This text files saves setup values for pyFlame Shot Sheet Maker script.')
            config_text.insert(1, 'Export Path:')
            config_text.insert(2, self.export_path)
            config_text.insert(3, 'Thumbnail Size:')
            config_text.insert(4, self.thumbnail_size)
            config_text.insert(5, 'Reveal in Finder')
            config_text.insert(6, self.reveal_in_finder)
            config_text.insert(7, 'Add Source name:')
            config_text.insert(8, self.add_source_name)
            config_text.insert(9, 'Add Source Path:')
            config_text.insert(10, self.add_source_path)
            config_text.insert(11, 'Add Source Timecode:')
            config_text.insert(12, self.add_source_tc)
            config_text.insert(13, 'Add Record Timecode:')
            config_text.insert(14, self.add_record_tc)
            config_text.insert(15, 'Add Shot Lenth:')
            config_text.insert(16, self.add_shot_length)
            config_text.insert(17, 'Add Source Length:')
            config_text.insert(18, self.add_source_length)

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

        def thumbnail_res():

            thumbnail_size = self.thumbnail_push_button.text()

            if thumbnail_size == 'Small':
                self.thumb_nail_height = 50
                self.thumb_nail_width = int(self.thumb_nail_height * self.seq_ratio)
                self.x_offset = 20

            elif thumbnail_size == 'Medium':
                self.thumb_nail_height = 100
                self.thumb_nail_width = int(self.thumb_nail_height * self.seq_ratio)
                self.x_offset = 30

            elif thumbnail_size == 'Large':
                self.thumb_nail_height = 150
                self.thumb_nail_width = int(self.thumb_nail_height * self.seq_ratio)
                self.x_offset = 31

            self.row_height = self.thumb_nail_height + (self.thumb_nail_height * .2)
            self.column_width = (self.thumb_nail_width + (self.x_offset * 2)) / 7.83
            self.y_offset = ((self.row_height * 1.333) - self.thumb_nail_height) / 2

        def modify_preset():

            if self.export_type == 'seq':
                export_preset = os.path.join(self.preset_path, 'Poster_Frame_Preset_Seq.xml')
            else:
                export_preset = os.path.join(self.preset_path, 'Poster_Frame_Preset_Clip.xml')

            self.temp_export_preset = os.path.join(self.preset_path, 'Poster_Frame_Preset_Temp.xml')

            shutil.copy(export_preset, self.temp_export_preset)

            width_line = '            <width>{}</width>\n'.format(self.thumb_nail_width)
            height_line = '            <height>{}</height>\n'.format(self.thumb_nail_height)

            edit_preset = open(self.temp_export_preset, 'r')
            contents = edit_preset.readlines()
            edit_preset.close()

            if self.export_type == 'seq':
                contents[42] = width_line
                contents[43] = height_line
            else:
                contents[19] = width_line
                contents[20] = height_line

            edit_preset = open(self.temp_export_preset, 'w')
            contents = ''.join(contents)
            edit_preset.write(contents)
            edit_preset.close()

        def open_finder():
            import platform
            import subprocess

            path = self.workbook_name.rsplit('/', 1)[0]

            if platform.system() == 'Darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])

            print ('\n>>> finder opened <<<\n')

        self.window.close()

        # Get settings from main window

        get_settings()

        # Save setting from main window to config file

        save_config_file()

        # Set image dir

        self.set_image_dir()

        # Set thumbnail size

        thumbnail_res()

        # Modify export preset with selected resolution

        modify_preset()

        # Get seq object and name from selection

        for seq in self.selection:
            self.clip = seq
            self.clip_name = str(self.clip.name)[1:-1]
            self.clip_frame_rate = float(str(self.clip.frame_rate)[:-4])
            # print ('clip_name:', self.clip_name)
            # print ('clip_frame_rate:', self.clip_frame_rate)
            break

        # Export thumbnails of shots in sequence

        self.export_thumbnail()

        # Add names of clips to shot list

        for version in self.clip.versions:
            for track in version.tracks:
                for seg in track.segments:
                    self.shot_list.append(str(seg.name)[1:-1])
                break

        # Create dictionary for all shots

        for version in self.clip.versions:
            for track in version.tracks:
                for seg in track.segments:
                    shot_name = str(seg.name)[1:-1]
                    self.shot_list.append(shot_name)

                    self.clip_info_list = []

                    self.clip_info_list.append('Shot Name: %s' % shot_name)

                    source_name = 'Source Name: ' + str(seg.source_name)
                    # print ('source_name:', source_name)
                    if self.add_source_name:
                        self.clip_info_list.append(source_name)

                    source_path = 'Source Path: ' + seg.file_path
                    # print ('source_path:', source_path)
                    if self.add_source_path:
                        self.clip_info_list.append(source_path)

                    source_tc = 'Source TC: ' + str(seg.source_in)[1:-1] + ' - ' + str(seg.source_out)[1:-1]
                    # print ('source_tc:', source_tc)
                    if self.add_source_tc:
                        self.clip_info_list.append(source_tc)

                    record_tc = 'Record TC: ' + str(seg.record_in)[1:-1] + ' - ' + str(seg.record_out)[1:-1]
                    # print ('record_tc:', record_tc)
                    if self.add_record_tc:
                        self.clip_info_list.append(record_tc)

                    record_duration = str(seg.record_duration)[1:-1]
                    shot_length_frames = self.timecode_to_frames(record_duration, self.clip_frame_rate)
                    shot_length = 'Shot Length: ' + record_duration + ' - ' + str(shot_length_frames) + ' Frames'
                    # print ('shot_length:', shot_length)
                    if self.add_shot_length:
                        self.clip_info_list.append(shot_length)

                    source_duration = str(seg.source_duration)[1:-1]
                    source_length_frames = self.timecode_to_frames(source_duration, self.clip_frame_rate)
                    source_length = 'Source Length: ' + source_duration + ' - ' + str(source_length_frames) + ' Frames'
                    # print ('source_length:', source_length)
                    if self.add_source_length:
                        self.clip_info_list.append(source_length)

                    # print ('\nclip_info_list:', self.clip_info_list, '\n')
                    self.shot_dict.update({shot_name : self.clip_info_list})
                break

        # print ('shot_dict:', self.shot_dict, '\n')
        # print ('shot_list:', self.shot_list)

        # Create spreadsheet

        self.create_spreadsheet()

        # Delete shot still images

        shutil.rmtree(self.image_dir)

        # Delete temp export preset

        os.remove(self.temp_export_preset)

        # Close window

        self.window.close()

        # Show message window

        message_box('%s Shot Sheet Exported' % self.spreadsheet_name_entry.text())

        if self.reveal_in_finder:
            open_finder()

        print ('done.\n')

    def setup(self):

        def install_button():

            def install_xls_writer():
                import flame
                from subprocess import Popen, PIPE

                def check_flame_version():

                    # If Flame version less than 2022 use python 2.7, if 2022 or newer user python 3.7

                    flame_version = self.current_flame_version

                    if 'pr' in flame_version:
                        flame_version = flame_version.rsplit('.pr', 1)[0]
                    if  flame_version.count('.') > 1:
                        flame_version = flame_version.rsplit('.', 1)[0]
                    flame_version = float(flame_version)
                    print ('flame_version:', flame_version)

                    # If flame version 2021.2 or higher switch to mediahub

                    if flame_version >= 2022:
                        return 'python3.7'
                    return 'python2.7'

                python_version = check_flame_version()
                print ('python_version:', python_version)

                # Untar command

                command = 'tar -xvf %s/xlsxwriter.tar.gz -C /opt/Autodesk/python/%s/lib/%s/site-packages/' % (SCRIPT_PATH, self.current_flame_version, python_version)
                command = command.split()

                p = Popen(['sudo', '-S'] + command, stdin=PIPE, stderr=PIPE, universal_newlines=True)
                sudo_prompt = p.communicate(self.password + '\n')[1]

                install_dir = '/opt/Autodesk/python/%s/lib/%s/site-packages/xlsxwriter' % (self.current_flame_version, python_version)

                if os.path.isdir(install_dir):
                    message_box('xlsxWriter Installed')
                    print ('\n>>> xlsxWriter Installed <<<\n')
                    self.password = ''
                    self.setup_window.close()
                else:
                    message_box('xlsxWriter Install Failed')
                    print ('\n>>> xlsxWriter Install Failed <<<\n')

            if self.password_entry.text() == '':
                message_box('Enter Root Password')
            else:
                self.password = self.password_entry.text()
                install_xls_writer()

        self.setup_window = QtWidgets.QWidget()
        self.setup_window.setMinimumSize(QtCore.QSize(400, 175))
        self.setup_window.setMaximumSize(QtCore.QSize(400, 175))
        self.setup_window.setWindowTitle('Shot Sheet Maker - Install xlsxWriter')
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                               (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        #  Labels

        self.install_label = FlameLabel('System Password', 'normal', self.setup_window)

        #  Entries

        self.password_entry = FlameLineEdit('', self.setup_window)
        self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)

        #  Buttons

        self.install_btn = FlameButton('Install', install_button, self.setup_window)
        self.cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window)

        #------------------------------------#

        #  Window Layout

        # Gridbox

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(10)

        grid.addWidget(self.install_label, 0, 0)
        grid.addWidget(self.password_entry, 0, 1)

        # Buttons HBox

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.cancel_btn)
        hbox.addWidget(self.install_btn)

        # Main VBox

        vbox = QtWidgets.QVBoxLayout()
        vbox.setMargin(15)
        vbox.addStretch(5)
        vbox.addLayout(grid)
        vbox.addStretch(10)
        vbox.addLayout(hbox)
        vbox.addStretch(5)

        self.setup_window.setLayout(vbox)

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
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14px "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14px "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

#-------------------------------------#

def scope_sequence(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PySequence)):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Shot Sheet Maker...',
            'actions': [
                {
                    'name': 'Export Shot Sheet',
                    'isVisible': scope_sequence,
                    'execute': ShotSheetMaker,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
