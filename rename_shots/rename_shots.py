'''
Script Name: Rename Shots
Script Version: 1.2
Flame Version: 2023
Written by: Michael Vaglienty
Creation Date: 04.05.22
Update Date: 05.24.22

Custom Action Type: Media Panel/Timeline

Description:

    Save clip and/or shot name naming patterns with tokens, then apply both to segments in a timeline.

    <index> token does not work as expected in python. Use other tokens to rename shots.

Menus:

    Timeline:

        Right-click on selected segments -> Rename... -> Rename Shots

    Media Panel:

        Right-click on selected sequence -> Rename... -> Rename Shots

To install:

    Copy script into /opt/Autodesk/shared/python/rename_shots

Updates:

    v1.2 05.24.22

        Messages print to Flame message window - Flame 2023.1 and later

    v1.1 05.11.22

        Removed setup window and eliminated sequence entry to simplify UI.
'''

import xml.etree.ElementTree as ET
from PySide2 import QtWidgets
from pyflame_lib_rename_shots import FlameWindow, FlameLabel, FlameLineEdit, FlameTokenPushButton, FlameButton, FlameMessageWindow, pyflame_print
import os

SCRIPT_NAME = 'Rename Shots'
SCRIPT_PATH = '/opt/Autodesk/shared/python/rename_shots'
VERSION = 'v1.2'

class RenameShots():

    def __init__(self, selection):
        import flame

        print('\n')
        print('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

        # Make sure no cuts or transitions are selected

        self.selection = [s for s in selection if s.type == 'Video Segment' or isinstance(s, flame.PySequence)]

        # Load config

        self.config()

        self.rename_shots_main_window()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('rename_shots_settings'):
                self.clip_name = setting.find('clip_name').text
                self.shot_name = setting.find('shot_name').text

            pyflame_print(SCRIPT_NAME, 'Config loaded.')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', f'Unable to create folder: {self.config_path}<br><br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                pyflame_print(SCRIPT_NAME, 'Creating new config file.')

                config = """
<settings>
    <rename_shots_settings>
        <clip_name></clip_name>
        <shot_name></shot_name>
    </rename_shots_settings>
</settings>"""

                with open(self.config_xml, 'a') as config_file:
                    config_file.write(config)
                    config_file.close()

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        if os.path.isfile(self.config_xml):
            get_config_values()
        else:
            create_config_file()
            if os.path.isfile(self.config_xml):
                get_config_values()

    def rename_shots_main_window(self):

        def config_save():

            if not self.clip_name_entry.text() and not self.shot_name_entry.text():
                return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'At least one shot name field must be filled in')

            self.clip_name = self.clip_name_entry.text()
            self.shot_name = self.shot_name_entry.text()

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            clip_name = root.find('.//clip_name')
            clip_name.text = self.clip_name

            shot_name = root.find('.//shot_name')
            shot_name.text = self.shot_name

            xml_tree.write(self.config_xml)

            pyflame_print(SCRIPT_NAME, 'Config saved.')

            self.rename_shots_window.close()

            self.apply_name()

        # Create window

        vbox = QtWidgets.QVBoxLayout()
        self.rename_shots_window = FlameWindow(f'{SCRIPT_NAME} <small>{VERSION}', vbox, 700, 250)

        # Labels

        self.name_pattern_label = FlameLabel('Name Pattern', label_type='underline')
        self.clip_name_label = FlameLabel('Clip Name')
        self.shot_name_label = FlameLabel('Shot Name')

        # LineEdits

        self.clip_name_entry = FlameLineEdit(self.clip_name, width=300)
        self.shot_name_entry = FlameLineEdit(self.shot_name, width=300)

        # Token Push Buttons

        token_dict = {'Souce Name': '<source name>', 'Segment Index': '<segment>', 'Segment Name': '<segment name>', 'Shot Name': '<shot name>',
                      'Background Index': '<background segment>', 'Background Name': '<background name>', 'Background Shot Name': '<background shot name>',
                      'Track': '<track>', 'Track Name': '<track name>', 'Record Frame': '<record frame>',
                      'Event Number': '<event number>', 'Tape/Reel/Source': '<tape>', 'Resolution': '<resolution>', 'Width': '<width>', 'Height': '<height>',
                      'Depth': '<depth>', 'Colour Space': '<colour space>', 'Source Version Name': '<source version name>', 'Source Version ID': '<source version>',
                      'Clip Name': '<name>', 'Date': '<date>', 'Time': '<time>', 'Year YYYYY': '<YYYY>', 'Year YY': '<YY>', 'Month': '<MM>', 'Day': '<DD>',
                      'Hour': '<hh>', 'Minute': '<mm>', 'Second': '<ss>', 'Workstation': '<workstation>', 'User NickName': '<user nickname', 'User': '<user>',
                      'Project Nickname': '<project nickname>', 'Project': '<project>'}

        self.clip_name_token_button = FlameTokenPushButton('Tokens', token_dict, self.clip_name_entry)
        self.shot_name_token_button = FlameTokenPushButton('Tokens', token_dict, self.shot_name_entry)

        # Buttons

        self.apply_button = FlameButton('Apply', config_save, button_color='blue')
        self.cancel_button = FlameButton('Cancel', self.rename_shots_window.close)

        # UI Widgets Layout

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.cancel_button)
        hbox.addWidget(self.apply_button)

        grid = QtWidgets.QGridLayout()
        grid.setMargin(10)
        grid.addWidget(self.name_pattern_label, 0, 1)
        grid.addWidget(self.clip_name_label, 1, 0)
        grid.addWidget(self.clip_name_entry, 1, 1)
        grid.addWidget(self.clip_name_token_button, 1, 2)

        grid.addWidget(self.shot_name_label, 2, 0)
        grid.addWidget(self.shot_name_entry, 2, 1)
        grid.addWidget(self.shot_name_token_button, 2, 2)

        vbox.addLayout(grid)
        vbox.addLayout(hbox)

        self.rename_shots_window.show()

    def apply_name(self):
        import flame

        try:
            # If selection is segments, rename segments

            if isinstance(self.selection[0], flame.PySegment):
                for segment in self.selection:
                    self.rename_segment(segment)

            # If selection is sequence, rename segments in selected sequence

            elif isinstance(self.selection[0], flame.PySequence):
                for version in self.selection[0].versions:
                    for track in version.tracks:
                        for segment in track.segments:
                            self.rename_segment(segment)

            pyflame_print(SCRIPT_NAME, 'Shot renaming complete.')

        except RuntimeError:
            return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Clip is locked. Open the sequence or disable protect from editing in Flame preferences.')

    def rename_segment(self, segment):

        if self.clip_name:
            segment.tokenized_name = self.clip_name
            print('    clip name:', str(segment.name)[1:-1])
        if self.shot_name:
            segment.tokenized_shot_name = self.shot_name
            print('    shot name:', str(segment.shot_name)[1:-1])

        print('\n')

#-------------------------------------#

def scope_sequence(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PySequence):
            return True
    return False

def scope_segment(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PySegment):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Rename...',
            'actions': [
                {
                    'name': 'Rename Shots',
                    'isVisible': scope_sequence,
                    'execute': RenameShots,
                    'minimumVersion': '2023'
                }
            ]
        }
    ]

def get_timeline_custom_ui_actions():

    return [
        {
            'name': 'Rename...',
            'actions': [
                {
                    'name': 'Rename Shots',
                    'isVisible': scope_segment,
                    'execute': RenameShots,
                    'minimumVersion': '2023'
                }
            ]
        }
    ]
