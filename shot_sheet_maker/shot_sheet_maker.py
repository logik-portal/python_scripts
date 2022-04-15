'''
Script Name: Shot Sheet Maker
Script Version: 3.1
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 02.18.19
Update Date: 03.25.22

Custom Action Type: Media Panel

Description:

    Create excel shot sheet from selected sequence clip.

    *** First time script is run it will need to install xlsxWriter - System password required for this ***

    Sequence should have all clips on one track.

Menu:

    Right-click on sequence in media panel -> Shot Sheet Maker... -> Export Shot Sheet

To install:

    Copy script into /opt/Autodesk/shared/python/shot_sheet_maker

Updates:

    v3.1 03.25.22

        Updated UI for Flame 2023

        Moved UI widgets to external file

        Updated xlsxwriter module to 3.0.3

        Gaps in timeline no longer cause script to crash

        Misc improvements and bug fixes

        Config updated to XML

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

from subprocess import Popen, PIPE
import xml.etree.ElementTree as ET
import re, os, ast, shutil
from PySide2 import QtWidgets
from flame_widgets_shot_sheet_maker import FlameButton, FlameLabel, FlameLineEdit, FlamePushButton, FlamePushButtonMenu, FlameWindow, FlameMessageWindow, FlamePasswordWindow

VERSION = 'v3.1'

SCRIPT_PATH = '/opt/Autodesk/shared/python/shot_sheet_maker'

#-------------------------------------#

class ShotSheetMaker(object):

    def __init__(self, selection):
        from collections import OrderedDict
        import flame

        print ('\n', '>' * 20, f'shot sheet maker <small>{VERSION}', '<' * 20, '\n')

        self.selection = selection

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')
        self.preset_path = os.path.join(SCRIPT_PATH, 'export_presets')

        # Get Flame variables

        self.flame_project_name = flame.project.current_project.name
        # print ('flame_project_name:', self.flame_project_name)

        self.current_flame_version = flame.get_version()
        # print ('current_flame_version:', self.current_flame_version, '\n')

        # Load config file

        self.config()

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
                FlameMessageWindow('Error', 'error', 'Sequence can only have one version/track')
        for item in self.selection:
            if len(item.versions[0].tracks) > 1:
                return FlameMessageWindow('Error', 'error', 'Sequence can only have one track')

        # Check for xlsxWriter

        xlsxwriter_installed = self.xlsxwriter_check()

        if xlsxwriter_installed:
            return self.main_window()
        return self.install_xlsxwriter()

    def xlsxwriter_check(self):

        # Import xlsxWriter
        # Run setup if not found

        try:
            import xlsxwriter
            print ('--> xlsxWriter imported\n')
            return True
        except:
            print ('--> xlsxWriter not installed\n')
            return False

    def install_xlsxwriter(self):
        import flame

        def check_flame_version():

            # If Flame version less than 2022 use python 2.7, if 2022 or newer user python 3.7

            flame_version = self.current_flame_version

            if 'pr' in flame_version:
                flame_version = flame_version.rsplit('.pr', 1)[0]
            if '.' in flame_version:
                flame_version = flame_version.split('.', 1)[0]
            flame_version = int(flame_version)
            print ('flame_version:', flame_version)

            # If flame version 2021.2 or higher switch to mediahub

            if flame_version == 2022:
                return 'python3.7'
            elif flame_version == 2023:
                return 'python3.9'
            return 'python2.7'

        system_password = str(FlamePasswordWindow('Enter System Password', 'System password required to install python xlsxwriter module.<br>This is required for each new version of Flame.'))

        if system_password:
            python_version = check_flame_version()
            print ('python_version:', python_version)

            # Untar command

            python_install_dir = f'/opt/Autodesk/python/{self.current_flame_version}/lib/{python_version}/site-packages/'
            if not os.path.isdir(python_install_dir):
                return FlameMessageWindow('Error', 'error', 'Python version folder not found. Install Failed.')

            command = f'tar -xvf {SCRIPT_PATH}/xlsxwriter-3.0.3.tgz -C {python_install_dir}'
            command = command.split()

            p = Popen(['sudo', '-S'] + command, stdin=PIPE, stderr=PIPE, universal_newlines=True)
            sudo_prompt = p.communicate(system_password + '\n')[1]

            install_dir = f'/opt/Autodesk/python/{self.current_flame_version}/lib/{python_version}/site-packages/xlsxwriter'

            if os.path.isdir(install_dir):
                FlameMessageWindow('Operation Complete', 'message', 'Python xlsxWriter module installed.')
                flame.execute_shortcut('Rescan Python Hooks')
                self.main_window()
            else:
                FlameMessageWindow('Error', 'error', 'Python xlsxWriter module install failed.')

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Shot Sheet Maker Settings

            for setting in root.iter('shot_sheet_maker_settings'):
                self.export_path = setting.find('export_path').text
                self.thumbnail_size = setting.find('thumbnail_size').text
                self.reveal_in_finder = ast.literal_eval(setting.find('reveal_in_finder').text)
                self.add_source_name = ast.literal_eval(setting.find('add_source_name').text)
                self.add_source_path = ast.literal_eval(setting.find('add_source_path').text)
                self.add_source_tc = ast.literal_eval(setting.find('add_source_tc').text)
                self.add_record_tc = ast.literal_eval(setting.find('add_record_tc').text)
                self.add_shot_length = ast.literal_eval(setting.find('add_shot_length').text)
                self.add_source_length = ast.literal_eval(setting.find('add_source_length').text)

            print ('--> config loaded\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder:<br><br>{self.config_path}<br><br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file\n')

                config = """
<settings>
    <shot_sheet_maker_settings>
        <export_path></export_path>
        <thumbnail_size>Medium</thumbnail_size>
        <reveal_in_finder>True</reveal_in_finder>
        <add_source_name>False</add_source_name>
        <add_source_path>False</add_source_path>
        <add_source_tc>False</add_source_tc>
        <add_record_tc>False</add_record_tc>
        <add_shot_length>False</add_shot_length>
        <add_source_length>False</add_source_length>
    </shot_sheet_maker_settings>
    <column_names>
        <column_01_name>Internal Notes</column_01_name>
        <column_02_name>Client Notes</column_02_name>
        <column_03_name>Shot Description</column_03_name>
        <column_04_name>Task</column_04_name>
        <column_05_name></column_05_name>
        <column_06_name></column_06_name>
        <column_07_name></column_07_name>
        <column_08_name></column_08_name>
        <column_09_name></column_09_name>
        <column_10_name></column_10_name>
        <column_11_name></column_11_name>
        <column_12_name></column_12_name>
        <column_13_name></column_13_name>
        <column_14_name></column_14_name>
        <column_15_name></column_15_name>
        <column_16_name></column_16_name>
        <column_17_name></column_17_name>
        <column_18_name></column_18_name>
        <column_19_name></column_19_name>
        <column_20_name></column_20_name>
    </column_names>
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

    def load_column_names(self):

        xml_tree = ET.parse(self.config_xml)
        root = xml_tree.getroot()

        # Get spreadsheet column names

        for name in root.iter('column_names'):
            self.column_01_name = name.find('column_01_name').text
            self.column_02_name = name.find('column_02_name').text
            self.column_03_name = name.find('column_03_name').text
            self.column_04_name = name.find('column_04_name').text
            self.column_05_name = name.find('column_05_name').text
            self.column_06_name = name.find('column_06_name').text
            self.column_07_name = name.find('column_07_name').text
            self.column_08_name = name.find('column_08_name').text
            self.column_09_name = name.find('column_09_name').text
            self.column_10_name = name.find('column_10_name').text
            self.column_11_name = name.find('column_11_name').text
            self.column_12_name = name.find('column_12_name').text
            self.column_13_name = name.find('column_13_name').text
            self.column_14_name = name.find('column_14_name').text
            self.column_15_name = name.find('column_15_name').text
            self.column_16_name = name.find('column_16_name').text
            self.column_17_name = name.find('column_17_name').text
            self.column_18_name = name.find('column_18_name').text
            self.column_19_name = name.find('column_19_name').text
            self.column_20_name = name.find('column_20_name').text

        print ('--> column names loaded\n')

    #-------------------------------------#

    def main_window(self):

        vbox = QtWidgets.QVBoxLayout()
        self.window = FlameWindow(f'Shot Sheet Maker <small>{VERSION}', vbox, 700, 470)

        # Labels

        self.spread_sheet_settings_label = FlameLabel('Spreadsheet Settings', label_type='underline', label_width=130)
        self.export_path_label = FlameLabel('Export Path', label_width=130)
        self.spreadsheet_name_label = FlameLabel('Shot Sheet Name', label_width=130)
        self.thumbnail_size_label = FlameLabel('Thumbnail Size', label_width=130)
        self.add_clip_info_label = FlameLabel('Add Columns With Clip Info', label_type='underline', label_width=130)

        # Entries

        self.export_path_entry = FlameLineEdit(self.export_path)

        if self.export_type == 'seq':
            self.spreadsheet_name_entry = FlameLineEdit(self.seq_name)
        else:
            self.spreadsheet_name_entry = FlameLineEdit(self.flame_project_name)

        # Push Button Menu

        thumbnail_menu_options = ['Large', 'Medium', 'Small']
        self.thumbnail_push_button = FlamePushButtonMenu(self.thumbnail_size, thumbnail_menu_options)

        # Push buttons

        self.reveal_in_finder_push_button = FlamePushButton(' Reveal in Finder', True)
        self.source_name_push_button = FlamePushButton(' Add Source Name', self.add_source_name)
        self.source_path_push_button = FlamePushButton(' Add Source Path', self.add_source_path)
        self.source_tc_push_button = FlamePushButton(' Add Source Timecode', self.add_source_tc)
        self.record_tc_push_button = FlamePushButton(' Add Record Timecode', self.add_record_tc)
        self.shot_length_push_button = FlamePushButton(' Add Shot Length', self.add_shot_length)
        self.source_length_push_button = FlamePushButton(' Add Source Length', self.add_source_length)

        # Buttons

        self.export_path_browse_btn = FlameButton('Browse', self.export_path_browse)
        self.edit_column_names_btn = FlameButton('Edit Column Names', self.edit_column_names_window)
        self.create_btn = FlameButton('Create', self.check_entries)
        self.cancel_btn = FlameButton('Cancel', self.window.close)

        #------------------------------------#

        #  UI Widget Layout

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

        vbox.setMargin(15)
        vbox.addLayout(gridbox)
        vbox.addStretch(5)
        vbox.addLayout(hbox)
        vbox.addStretch(5)

        self.window.show()

    def edit_column_names_window(self):

        def save_config():

            # Save column name

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            column_01_name = root.find('.//column_01_name')
            column_01_name.text = self.column_01_entry.text()

            column_02_name = root.find('.//column_02_name')
            column_02_name.text = self.column_02_entry.text()

            column_03_name = root.find('.//column_03_name')
            column_03_name.text = self.column_03_entry.text()

            column_04_name = root.find('.//column_04_name')
            column_04_name.text = self.column_04_entry.text()

            column_05_name = root.find('.//column_05_name')
            column_05_name.text = self.column_05_entry.text()

            column_06_name = root.find('.//column_06_name')
            column_06_name.text = self.column_06_entry.text()

            column_07_name = root.find('.//column_07_name')
            column_07_name.text = self.column_07_entry.text()

            column_08_name = root.find('.//column_08_name')
            column_08_name.text = self.column_08_entry.text()

            column_09_name = root.find('.//column_09_name')
            column_09_name.text = self.column_09_entry.text()

            column_10_name = root.find('.//column_10_name')
            column_10_name.text = self.column_10_entry.text()

            column_11_name = root.find('.//column_11_name')
            column_11_name.text = self.column_11_entry.text()

            column_12_name = root.find('.//column_12_name')
            column_12_name.text = self.column_12_entry.text()

            column_13_name = root.find('.//column_13_name')
            column_13_name.text = self.column_13_entry.text()

            column_14_name = root.find('.//column_14_name')
            column_14_name.text = self.column_14_entry.text()

            column_15_name = root.find('.//column_15_name')
            column_15_name.text = self.column_15_entry.text()

            column_16_name = root.find('.//column_16_name')
            column_16_name.text = self.column_16_entry.text()

            column_17_name = root.find('.//column_17_name')
            column_17_name.text = self.column_17_entry.text()

            column_18_name = root.find('.//column_18_name')
            column_18_name.text = self.column_18_entry.text()

            column_19_name = root.find('.//column_19_name')
            column_19_name.text = self.column_19_entry.text()

            column_20_name = root.find('.//column_20_name')
            column_20_name.text = self.column_20_entry.text()

            xml_tree.write(self.config_xml)

            print ('--> column names saved\n')

            self.edit_window.close()

        self.load_column_names()

        vbox = QtWidgets.QVBoxLayout()
        self.edit_window = FlameWindow('Edit Column Names', vbox, 1000, 520)

        # Labels

        self.column_names_label = FlameLabel('Spreadsheet Column Names', label_type='underline')

        self.column_01_label = FlameLabel('Column 01')
        self.column_02_label = FlameLabel('Column 02')
        self.column_03_label = FlameLabel('Column 03')
        self.column_04_label = FlameLabel('Column 04')
        self.column_05_label = FlameLabel('Column 05')
        self.column_06_label = FlameLabel('Column 06')
        self.column_07_label = FlameLabel('Column 07')
        self.column_08_label = FlameLabel('Column 08')
        self.column_09_label = FlameLabel('Column 09')
        self.column_10_label = FlameLabel('Column 10')
        self.column_11_label = FlameLabel('Column 11')
        self.column_12_label = FlameLabel('Column 12')
        self.column_13_label = FlameLabel('Column 13')
        self.column_14_label = FlameLabel('Column 14')
        self.column_15_label = FlameLabel('Column 15')
        self.column_16_label = FlameLabel('Column 16')
        self.column_17_label = FlameLabel('Column 17')
        self.column_18_label = FlameLabel('Column 18')
        self.column_19_label = FlameLabel('Column 19')
        self.column_20_label = FlameLabel('Column 20')

        # LineEdits

        self.column_01_entry = FlameLineEdit(self.column_01_name)
        self.column_02_entry = FlameLineEdit(self.column_02_name)
        self.column_03_entry = FlameLineEdit(self.column_03_name)
        self.column_04_entry = FlameLineEdit(self.column_04_name)
        self.column_05_entry = FlameLineEdit(self.column_05_name)
        self.column_06_entry = FlameLineEdit(self.column_06_name)
        self.column_07_entry = FlameLineEdit(self.column_07_name)
        self.column_08_entry = FlameLineEdit(self.column_08_name)
        self.column_09_entry = FlameLineEdit(self.column_09_name)
        self.column_10_entry = FlameLineEdit(self.column_10_name)
        self.column_11_entry = FlameLineEdit(self.column_11_name)
        self.column_12_entry = FlameLineEdit(self.column_12_name)
        self.column_13_entry = FlameLineEdit(self.column_13_name)
        self.column_14_entry = FlameLineEdit(self.column_14_name)
        self.column_15_entry = FlameLineEdit(self.column_15_name)
        self.column_16_entry = FlameLineEdit(self.column_16_name)
        self.column_17_entry = FlameLineEdit(self.column_17_name)
        self.column_18_entry = FlameLineEdit(self.column_18_name)
        self.column_19_entry = FlameLineEdit(self.column_19_name)
        self.column_20_entry = FlameLineEdit(self.column_20_name)

        # Buttons

        self.save_columns_button = FlameButton('Save', save_config)
        self.edit_cancel_button = FlameButton('Cancel', self.edit_window.close)

        # UI Widget Layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setHorizontalSpacing(20)

        gridbox.addWidget(self.column_names_label, 0, 0, 1, 6)

        gridbox.addWidget(self.column_01_label, 1, 0)
        gridbox.addWidget(self.column_02_label, 2, 0)
        gridbox.addWidget(self.column_03_label, 3, 0)
        gridbox.addWidget(self.column_04_label, 4, 0)
        gridbox.addWidget(self.column_05_label, 5, 0)
        gridbox.addWidget(self.column_06_label, 6, 0)
        gridbox.addWidget(self.column_07_label, 7, 0)
        gridbox.addWidget(self.column_08_label, 8, 0)
        gridbox.addWidget(self.column_09_label, 9, 0)
        gridbox.addWidget(self.column_10_label, 10, 0)
        gridbox.addWidget(self.column_11_label, 1, 4)
        gridbox.addWidget(self.column_12_label, 2, 4)
        gridbox.addWidget(self.column_13_label, 3, 4)
        gridbox.addWidget(self.column_14_label, 4, 4)
        gridbox.addWidget(self.column_15_label, 5, 4)
        gridbox.addWidget(self.column_16_label, 6, 4)
        gridbox.addWidget(self.column_17_label, 7, 4)
        gridbox.addWidget(self.column_18_label, 8, 4)
        gridbox.addWidget(self.column_19_label, 9, 4)
        gridbox.addWidget(self.column_20_label, 10, 4)

        gridbox.addWidget(self.column_01_entry, 1, 1)
        gridbox.addWidget(self.column_02_entry, 2, 1)
        gridbox.addWidget(self.column_03_entry, 3, 1)
        gridbox.addWidget(self.column_04_entry, 4, 1)
        gridbox.addWidget(self.column_05_entry, 5, 1)
        gridbox.addWidget(self.column_06_entry, 6, 1)
        gridbox.addWidget(self.column_07_entry, 7, 1)
        gridbox.addWidget(self.column_08_entry, 8, 1)
        gridbox.addWidget(self.column_09_entry, 9, 1)
        gridbox.addWidget(self.column_10_entry, 10, 1)
        gridbox.addWidget(self.column_11_entry, 1, 5)
        gridbox.addWidget(self.column_12_entry, 2, 5)
        gridbox.addWidget(self.column_13_entry, 3, 5)
        gridbox.addWidget(self.column_14_entry, 4, 5)
        gridbox.addWidget(self.column_15_entry, 5, 5)
        gridbox.addWidget(self.column_16_entry, 6, 5)
        gridbox.addWidget(self.column_17_entry, 7, 5)
        gridbox.addWidget(self.column_18_entry, 8, 5)
        gridbox.addWidget(self.column_19_entry, 9, 5)
        gridbox.addWidget(self.column_20_entry, 10, 5)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(5)
        hbox.addWidget(self.save_columns_button)
        hbox.addStretch(5)
        hbox.addWidget(self.edit_cancel_button)
        hbox.addStretch(5)

        vbox.setMargin(15)
        vbox.addLayout(gridbox)
        vbox.addStretch(20)
        vbox.addLayout(hbox)
        vbox.addStretch(5)

        self.edit_window.show()

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

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            export_path = root.find('.//export_path')
            export_path.text = self.export_path

            thumbnail_size = root.find('.//thumbnail_size')
            thumbnail_size.text = self.thumbnail_size

            reveal_in_finder = root.find('.//reveal_in_finder')
            reveal_in_finder.text = str(self.reveal_in_finder)

            add_source_name = root.find('.//add_source_name')
            add_source_name.text = str(self.add_source_name)

            add_source_path = root.find('.//add_source_path')
            add_source_path.text = str(self.add_source_path)

            add_source_tc = root.find('.//add_source_tc')
            add_source_tc.text = str(self.add_source_tc)

            add_record_tc = root.find('.//add_record_tc')
            add_record_tc.text = str(self.add_record_tc)

            add_shot_length = root.find('.//add_shot_length')
            add_shot_length.text = str(self.add_shot_length)

            add_source_length = root.find('.//add_source_length')
            add_source_length.text = str(self.add_source_length)

            xml_tree.write(self.config_xml)

            print ('--> config saved\n')

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

            print ('\n--> finder opened\n')

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
                    if shot_name:
                        self.shot_list.append(shot_name)

                        self.clip_info_list = []

                        self.clip_info_list.append(f'Shot Name: {shot_name}')

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

                        print (seg.name)
                        #print (seg.current_time.relative_frame)

                        record_duration = str(seg.record_duration)[1:-1]
                        shot_length_frames = str(seg.record_duration.frame)
                        shot_length = 'Shot Length: ' + record_duration + ' - ' + shot_length_frames + ' Frames'
                        #print ('shot_length:', shot_length)
                        if self.add_shot_length:
                            self.clip_info_list.append(shot_length)

                        source_duration = str(seg.source_duration)[1:-1]
                        source_length_frames = str(seg.source_duration.frame)
                        source_length = 'Source Length: ' + source_duration + ' - ' + str(source_length_frames) + ' Frames'
                        #print ('source_length:', source_length)
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

        FlameMessageWindow('Operation Complete', 'message', f'Shot Sheet Exported: {self.spreadsheet_name_entry.text()}')

        if self.reveal_in_finder:
            open_finder()

        print ('done.\n')

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

        # Get saved column names

        self.load_column_names()

        column_name_entries = [self.column_01_name, self.column_02_name, self.column_03_name, self.column_04_name, self.column_05_name,
                               self.column_06_name, self.column_07_name, self.column_08_name, self.column_09_name, self.column_10_name,
                               self.column_11_name, self.column_12_name, self.column_13_name, self.column_14_name, self.column_15_name,
                               self.column_16_name, self.column_17_name, self.column_18_name, self.column_19_name, self.column_20_name,]

        column_names = [column for column in column_name_entries if column]

        # If clip info True add clip info column

        if clip_info:
            column_names.insert(0, 'Clip Info')
            # print ('column_names:', column_names)

        # Add sequence name to cell above first shot

        worksheet.write(1, 0, str(self.selection[0].name)[1:-1])

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

    def check_entries(self):

        # Check export path
        # If not found stop and give message

        if not os.path.isdir(self.export_path_entry.text()):
            return FlameMessageWindow('Error', 'error', 'Export path not found - Select new path')

        # Check spreadsheet name entry

        if self.spreadsheet_name_entry.text() == '':
            return FlameMessageWindow('Error', 'error', 'Enter spreadsheet name')

        if os.path.isfile(os.path.join(self.export_path_entry.text(), self.spreadsheet_name_entry.text() + '.xlsx')):
            if not FlameMessageWindow('Confirm Operation', 'warning', 'File already exists, overwrite?'):
                return

        if self.export_type == 'seq':
            self.create_seq_shot_sheet()

    def export_path_browse(self):

        export_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.window, "Select Directory", self.export_path_entry.text(), QtWidgets.QFileDialog.ShowDirsOnly))

        if os.path.isdir(export_path):
            self.export_path_entry.setText(export_path)

    def set_image_dir(self):

        # Set export image dir

        self.image_dir = os.path.join(str(self.export_path_entry.text()), str(self.spreadsheet_name_entry.text()))
        # print ('image_dir:', self.image_dir)

        if not os.path.isdir(self.image_dir):
            try:
                os.makedirs(self.image_dir)
            except:
                FlameMessageWindow('Error', 'error', 'Check export path.<br>Can not create export folder.')

    def export_thumbnail(self):
        import flame

        poster_frame_exporter = flame.PyExporter()
        poster_frame_exporter.foreground = True
        poster_frame_exporter.export(self.clip, self.temp_export_preset, self.image_dir)

#-------------------------------------#

def scope_sequence(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PySequence, flame.PyClip)):
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
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
