'''
Script Name: Rename Shots
Script Version: 1.0
Flame Version: 2023
Written by: Michael Vaglienty
Creation Date: 04.05.22
Update Date: 04.05.22

Custom Action Type: Media Panel/Timeline

Description:

    Save clip and/or shot name naming patterns with tokens, then apply them to segments in a timeline.

    Go to Rename Shots Setup to set up pattern naming with tokens. By default shots will only be named
    to whatever is entered into the Sequence Name field.

Menus:

    Setup:

        Flame Main Menu -> pyFlame -> Rename Shots Setup

    Timeline:

        Right-click on selected segments -> Rename... -> Rename Shots

    Media Panel:

        Right-click on selected sequence -> Rename... -> Rename Shots

To install:

    Copy script into /opt/Autodesk/shared/python/rename_shots
'''

import xml.etree.ElementTree as ET
from PySide2 import QtWidgets
from flame_widgets_rename_shots import FlameButton, FlameLabel, FlameMessageWindow, FlameWindow, FlameLineEdit, FlameTokenPushButton
import os

VERSION = 'v1.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/rename_shots'

class RenameShots(object):

    def __init__(self, selection):

        print ('>' * 21, f'rename shots {VERSION}', '<' * 21, '\n')

        self.selection = selection

        # Load config

        self.config()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('rename_shots_settings'):
                self.clip_name = setting.find('clip_name').text
                self.shot_name = setting.find('shot_name').text

            print ('--> config loaded\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder: {self.config_path}<br><br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file\n')

                config = """
<settings>
    <rename_shots_settings>
        <clip_name>&lt;sequence name&gt;</clip_name>
        <shot_name>&lt;sequence name&gt;</shot_name>
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

    def setup_main_window(self):

        def config_save():

            if not self.clip_name_entry.text() and not self.shot_name_entry.text():
                return FlameMessageWindow('Rename Shots - Error', 'error', 'At least one name field must be filled in')

            sequence_error = '<br><br>The <b>Sequence Name</b> token is replaced by the sequence name given when the sequence shots are named'

            if self.clip_name_entry.text() and '<sequence name>' not in self.clip_name_entry.text():
                return FlameMessageWindow('Rename Shots - Error', 'error', f'<b>Sequence Name</b> (&lt;sequence name&gt;) token must be in the Clip Name field.{sequence_error}')

            if self.shot_name_entry.text() and '<sequence name>' not in self.shot_name_entry.text():
                return FlameMessageWindow('Rename Shots - Error', 'error', f'<b>Sequence Name</b> (&lt;sequence name&gt;) token must be in the Shot Name field.{sequence_error}')

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            clip_name = root.find('.//clip_name')
            clip_name.text = self.clip_name_entry.text()

            shot_name = root.find('.//shot_name')
            shot_name.text = self.shot_name_entry.text()

            xml_tree.write(self.config_xml)

            print ('--> config saved\n')

            self.setup_window.close()

        # Create main window

        vbox = QtWidgets.QVBoxLayout()
        self.setup_window = FlameWindow(f'Rename Shots - Setup <small>{VERSION}', vbox, 700, 230)

        # Labels

        self.name_pattern_label = FlameLabel('Name Pattern', label_type='underline')
        self.clip_name_label = FlameLabel('Clip Name')
        self.shot_name_label = FlameLabel('Shot Name')

        # LineEdits

        self.clip_name_entry = FlameLineEdit(self.clip_name, width=300)
        self.shot_name_entry = FlameLineEdit(self.shot_name, width=300)

        # Token Push Buttons

        token_dict = {'Sequence Name': '<sequence name>', 'Souce Name': '<source name>', 'Segment Index': '<segment>', 'Segment Name': '<segment name>', 'Shot Name': '<shot name>',
                      'Background Index': '<background segment>', 'Background Name': '<background name>', 'Background Shot Name': '<background shot name>',
                      'Custom Index': '<index##@1+1>', 'Track': '<track>', 'Track Name': '<track name>', 'Record Frame': '<record frame>',
                      'Event Number': '<event number>', 'Tape/Reel/Source': '<tape>', 'Resolution': '<resolution>', 'Width': '<width>', 'Height': '<height>',
                      'Depth': '<depth>', 'Colour Space': '<colour space>', 'Source Version Name': '<source version name>', 'Source Version ID': '<source version>',
                      'Clip Name': '<name>', 'Date': '<date>', 'Time': '<time>', 'Year YYYYY': '<YYYY>', 'Year YY': '<YY>', 'Month': '<MM>', 'Day': '<DD>',
                      'Hour': '<hh>', 'Minute': '<mm>', 'Second': '<ss>', 'Workstation': '<workstation>', 'User NickName': '<user nickname', 'User': '<user>',
                      'Project Nickname': '<project nickname>', 'Project': '<project>'}

        self.clip_name_token_button = FlameTokenPushButton('Tokens', token_dict, self.clip_name_entry)
        self.shot_name_token_button = FlameTokenPushButton('Tokens', token_dict, self.shot_name_entry)

        # Buttons

        self.save_button = FlameButton('Save', config_save)
        self.cancel_button = FlameButton('Cancel', self.setup_window.close)

        # UI Widgets Layout

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.save_button)
        hbox.addWidget(self.cancel_button)

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

        self.setup_window.show()

    def rename_shots_main_window(self):

        # Create window

        vbox = QtWidgets.QVBoxLayout()
        self.rename_shots_window = FlameWindow(f'Rename Shots <small>{VERSION}', vbox, 450, 200)

        # Labels

        self.sequence_name_label = FlameLabel('Sequence Name')

        # LineEdits

        self.sequence_name_entry = FlameLineEdit('')

        # Buttons

        self.apply_button = FlameButton('Apply', self.apply_name, button_color='blue')
        self.cancel_button = FlameButton('Cancel', self.rename_shots_window.close)

        # UI Widgets Layout

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self.sequence_name_label)
        hbox1.addWidget(self.sequence_name_entry)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(self.cancel_button)
        hbox2.addWidget(self.apply_button)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.rename_shots_window.show()

    def apply_name(self):
        import flame

        if not self.sequence_name_entry.text():
            return FlameMessageWindow('Rename Shots - Error', 'error', '<b>Sequence Name</b> field cannot be empty')

        print ('--> naming shots:\n')

        # If selection is segments, rename segments

        if isinstance(self.selection[0], flame.PySegment):
            for segment in self.selection:
                self.rename_segment(segment)

        # If selection is sequence, rename segments in selected sequence

        elif isinstance(self.selection[0], flame.PySequence):
            print (f'--> {str(self.selection[0].name)[1:-1]}\n')
            for v in self.selection[0].versions:
                for t in v.tracks:
                    for s in t.segments:
                        self.rename_segment(s)

        self.rename_shots_window.close()

        print ('\ndone.\n')

    def rename_segment(self, segment):

        if self.clip_name:
            clip_name = self.clip_name.replace('<sequence name>', self.sequence_name_entry.text())
            segment.tokenized_name = clip_name
            print ('    clip name:', str(segment.name)[1:-1])
        if self.shot_name:
            shot_name = self.shot_name.replace('<sequence name>', self.sequence_name_entry.text())
            segment.tokenized_shot_name = shot_name
            print ('    shot name:', str(segment.shot_name)[1:-1])

#-------------------------------------#

def setup(selection):

    rename = RenameShots(selection)
    rename.setup_main_window()

def rename_shots(selection):

    rename = RenameShots(selection)
    rename.rename_shots_main_window()
    return rename

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
                    'execute': rename_shots,
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
                    'execute': rename_shots,
                    'minimumVersion': '2023'
                }
            ]
        }
    ]

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Rename Shots Setup',
                    'execute': setup,
                    'minimumVersion': '2023'
                }
            ]
        }
    ]
