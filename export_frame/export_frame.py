'''
Script Name: Export Frame
Script Version: 1.4
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 10.11.21
Update Date: 04.07.22

Custom Action Type: Media Panel/Player

Description:

    Export current frame or frames at markers from selected clips/sequences.
    Based in part from the Autodesk Export Current Frame example script.

    Frames can be exported from player view.

    One or more clips can be selected in the Media Panel to export frames from.

    When exporting multiple frames using markers, the export preset should use frame padding
    or timecode in the file name to avoid overwriting frames.

    The default export preset used is the default Autodesk Jpeg preset. To use custom presets,
    save them as shared presets and then select it in the script setup.

    Custom export paths using tokens can be set in the script setup.

    Openning the MediaHub or a Finder window after the export is completed can be set in the script setup.

Menus:

    Setup:

        Flame Main Menu -> pyFlame -> Export Current Frame Setup

    To Export:

        Right-click on clip, sequence, or player view -> Export... -> Export Current Frame
        Right-click on clip, sequence, or player view -> Export... -> Export Marker Frames

To install:

    Copy script into /opt/Autodesk/shared/python/export_frame

Updates:

    v1.4 04.07.22

        Updated UI for Flame 2023

        UI Widgets moved to external file

    v1.3 11.02.21

        Fixed shot name token compatibility to work with python 3.7

    v1.2 10.24.21

        Removed custom path menus. Custom export paths can be turned on in Setup.

        Known bug - right clicking on clip in schematic reel will cause Flame to crash.

    v1.1 10.12.21

        Fixed SEQNAME token
'''

from PySide2 import QtWidgets
import xml.etree.ElementTree as ET
import re, os, ast, datetime, platform, subprocess
from flame_widgets_export_frame import FlameLabel, FlameButton, FlameLineEdit, FlamePushButton, FlamePushButtonMenu, FlameTokenPushButton, FlameMessageWindow, FlameWindow

VERSION = 'v1.4'

SCRIPT_PATH = '/opt/Autodesk/shared/python/export_frame'

class ExportFrame(object):

    def __init__(self, selection):
        import flame

        print ('''
 ______                       _    ______
|  ____|                     | |  |  ____|
| |__  __  ___ __   ___  _ __| |_ | |__ _ __ __ _ _ __ ___   ___
|  __| \ \/ / '_ \ / _ \| '__| __||  __| '__/ _` | '_ ` _ \ / _ \\
| |____ >  <| |_) | (_) | |  | |_ | |  | | | (_| | | | | | |  __/
|______/_/\_\ .__/ \___/|_|   \__||_|  |_|  \__,_|_| |_| |_|\___|
            | |
            |_|
        ''')

        print ('>' * 24, f'export frame {VERSION}', '<' * 24, '\n')

        self.selection = selection

        # Set paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Get list of export presets in shared export folder

        self.shared_presets_path = '/opt/Autodesk/shared/export/presets/file_sequence'
        self.shared_presets = ['Default Jpeg'] + [preset[:-4] for preset in os.listdir(self.shared_presets_path)]

        # Load config file

        self.config()

        print ('selected export preset:', self.export_preset, '\n')

        # Get current date/time for token conversion

        self.date = datetime.datetime.now()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings

            for setting in root.iter('export_frame_settings'):
                self.saved_browse_path = setting.find('saved_browse_path').text
                self.custom_export_path = setting.find('custom_export_path').text
                self.export_preset = setting.find('export_preset').text
                self.reveal_in_finder = ast.literal_eval(setting.find('reveal_in_finder').text)
                self.reveal_in_mediahub = ast.literal_eval(setting.find('reveal_in_mediahub').text)
                self.export_destination = setting.find('export_destination').text

            print ('>>> config loaded <<<\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder: {self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('>>> config file does not exist, creating new config file <<<')

                config = """
<settings>
    <export_frame_settings>
        <saved_browse_path>/</saved_browse_path>
        <custom_export_path>/</custom_export_path>
        <export_preset>Default Jpeg</export_preset>
        <reveal_in_finder>False</reveal_in_finder>
        <reveal_in_mediahub>False</reveal_in_mediahub>
        <export_destination>Browse to Path</export_destination>
    </export_frame_settings>
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

#-------------------------------------#

    def setup(self):

        def export_dest_toggle():

            if self.export_dest_menu_push_button.text() == 'Browse to Path':
                self.custom_path_settings_label.setEnabled(False)
                self.custom_export_path_label.setEnabled(False)
                self.custom_export_path_lineedit.setEnabled(False)
                self.custom_token_push_btn.setEnabled(False)
                self.browse_btn.setEnabled(False)
            else:
                self.custom_path_settings_label.setEnabled(True)
                self.custom_export_path_label.setEnabled(True)
                self.custom_export_path_lineedit.setEnabled(True)
                self.custom_token_push_btn.setEnabled(True)
                self.browse_btn.setEnabled(True)

        def custom_path_browse():

            file_path = str(QtWidgets.QFileDialog.getExistingDirectory(self.setup_window, 'Select Directory', self.custom_export_path_lineedit.text(), QtWidgets.QFileDialog.ShowDirsOnly))

            if os.path.isdir(file_path):
                self.custom_export_path_lineedit.setText(file_path)

        def save_config():

            if self.custom_export_path_lineedit.text() == '':
                self.custom_export_path_lineedit.setText('/')
            else:

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                custom_export_path = root.find('.//custom_export_path')
                custom_export_path.text = self.custom_export_path_lineedit.text()

                export_preset = root.find('.//export_preset')
                export_preset.text = self.export_preset_menu_push_button.text()

                reveal_in_finder = root.find('.//reveal_in_finder')
                reveal_in_finder.text = str(self.reveal_finder_push_button.isChecked())

                reveal_in_mediahub = root.find('.//reveal_in_mediahub')
                reveal_in_mediahub.text = str(self.reveal_mediahub_push_button.isChecked())

                export_destination = root.find('.//export_destination')
                export_destination.text = self.export_dest_menu_push_button.text()

                xml_tree.write(self.config_xml)

                print ('>>> Config saved <<<\n')

                self.setup_window.close()

                print ('Done.\n')

        gridbox = QtWidgets.QGridLayout()
        self.setup_window = FlameWindow(f'Export Frame - Setup <small>{VERSION}', gridbox, 900, 490)

        # Labels

        self.export_settings_label = FlameLabel('Export Settings', label_type='underline')
        self.after_export_label = FlameLabel('After Export')
        self.export_dest_label = FlameLabel('Export Destination')
        self.custom_path_settings_label = FlameLabel('Custom Path Settings', label_type='underline')
        self.custom_export_path_label = FlameLabel('Custom Export Path')
        self.export_preset_label = FlameLabel('Export Preset')

        # LineEdits

        self.custom_export_path_lineedit = FlameLineEdit(self.custom_export_path)

        # Batch Path Token Pushbutton Menu

        custom_token_dict = {'Project Name': '<ProjectName>', 'Project Nickname': '<ProjectNickName>', 'Shot Name': '<ShotName>',
                             'Sequence Name': '<SeqName>', 'SEQUENCE NAME': '<SEQNAME>', 'Clip Name': '<ClipName>',
                             'User Name': '<UserName>', 'User Nickname': '<UserNickName>', 'Clip Resolution': '<Resolution>',
                             'Clip Height': '<ClipHeight>', 'Clip Width': '<ClipWidth>', 'Year (YYYY)': '<YYYY>',
                             'Year (YY)': '<YY>', 'Month': '<MM>', 'Day': '<DD>', 'Hour': '<Hour>', 'Minute': '<Minute>',
                             'AM/PM': '<AMPM>', 'am/pm': '<ampm>'}

        self.custom_token_push_btn = FlameTokenPushButton('Add Token', custom_token_dict, self.custom_export_path_lineedit)

        # Menu Push Buttons

        self.export_preset_menu_push_button = FlamePushButtonMenu(self.export_preset, self.shared_presets)

        # Export Destination Menu Push Button

        export_menu_options = ['Browse to Path', 'Use Custom Path']
        self.export_dest_menu_push_button = FlamePushButtonMenu(self.export_destination, export_menu_options, menu_action=export_dest_toggle)

        # Push buttons

        self.reveal_finder_push_button = FlamePushButton(' Reveal in Finder', self.reveal_in_finder)
        self.reveal_mediahub_push_button = FlamePushButton(' Reveal in MediaHub', self.reveal_in_mediahub)

        #  Buttons

        self.browse_btn = FlameButton('Browse', custom_path_browse)
        self.save_btn = FlameButton('Save', save_config)
        self.cancel_btn = FlameButton('Cancel', self.setup_window.close)

        export_dest_toggle()

        # UI Widget Layout

        gridbox.setMargin(20)

        gridbox.setRowMinimumHeight(1, 30)
        gridbox.setRowMinimumHeight(4, 30)
        gridbox.setRowMinimumHeight(8, 30)
        gridbox.setRowMinimumHeight(11, 30)

        gridbox.setColumnMinimumWidth(2, 75)

        gridbox.addWidget(self.export_settings_label, 0 ,0, 1, 6)

        gridbox.addWidget(self.export_preset_label, 3 ,0)
        gridbox.addWidget(self.export_preset_menu_push_button, 3, 1, 1, 3)

        gridbox.addWidget(self.export_dest_label, 5 ,0)
        gridbox.addWidget(self.export_dest_menu_push_button, 5 ,1)

        gridbox.addWidget(self.after_export_label, 5 ,3)
        gridbox.addWidget(self.reveal_finder_push_button, 5 ,4)
        gridbox.addWidget(self.reveal_mediahub_push_button, 6 ,4)

        gridbox.addWidget(self.custom_path_settings_label, 9 ,0, 1, 6)

        gridbox.addWidget(self.custom_export_path_label, 10 ,0)
        gridbox.addWidget(self.custom_export_path_lineedit, 10 ,1, 1, 3)
        gridbox.addWidget(self.custom_token_push_btn, 10 ,4)
        gridbox.addWidget(self.browse_btn, 10 ,5)

        gridbox.addWidget(self.save_btn, 12, 5)
        gridbox.addWidget(self.cancel_btn, 13, 5)

        self.setup_window.show()

        return self.setup_window

    def export_current_frame(self):
        import flame

        marker = ''

        if self.export_destination == 'Browse to Path':

            export_path = self.folder_browser()

            # Export current frame from selected clips

            if os.path.isdir(export_path):
                for clip in self.selection:
                    self.export(export_path, marker, clip)
                print ('\n')
                self.post_export(export_path)
            else:
                print ('--> Export cancelled\n')

        else:
            # Check path in config file

            if self.custom_export_path == '/':
                return FlameMessageWindow('Error', 'error', 'Add export path in script setup.<br><br>Flame Main Menu -> pyFlame -> Export Frame Setup')

            # Export frames

            for clip in self.selection:

                # Translate custom path

                export_path = self.translate_path(clip)

                # Export

                self.export(export_path, marker, clip)

            print ('\n')

            self.post_export(export_path)

    def export_marker_frame(self):

        if self.export_destination == 'Browse to Path':

            export_path = self.folder_browser()

            # Export current frame from selected clips

            if os.path.isdir(export_path):
                for clip in self.selection:
                    for marker in clip.markers:
                        self.export(export_path, marker, clip)
                print ('\n')
                self.post_export(export_path)
            else:
                print ('--> Export cancelled\n')

        else:
            # Check saved settings

            if self.custom_export_path == '/':
                return FlameMessageWindow('Error', 'error', 'Add custom path in script setup. <br><br>Flame Main Menu -> pyFlame -> Export Frame Setup')

            for clip in self.selection:
                for marker in clip.markers:

                    # Translate custom path

                    export_path = self.translate_path(clip)

                    # Export

                    self.export(export_path, marker, clip)

                    print ('\n')

            print ('\n')

            self.post_export(export_path)

#-------------------------------------#

    def export(self, export_path, marker, clip):
        import flame

        # Set exporter

        exporter = flame.PyExporter()
        exporter.foreground = True
        exporter.export_between_marks = True

        # Duplicate the clip to avoid modifying the original clip

        duplicate_clip = flame.duplicate(clip)

        # Set export preset path

        if self.export_preset == 'Default Jpeg':

            # Get default export preset path

            preset_dir = flame.PyExporter.get_presets_dir(
                flame.PyExporter.PresetVisibility.Autodesk,
                flame.PyExporter.PresetType.Image_Sequence)
            export_preset_path = os.path.join(preset_dir, "Jpeg", "Jpeg (8-bit).xml")

        else:
            export_preset_path = os.path.join(self.shared_presets_path, self.export_preset + '.xml')

        try:
            if marker:
                duplicate_clip.in_mark = marker.location.get_value()
                duplicate_clip.out_mark = marker.location.get_value() + 1
            else:
                duplicate_clip.in_mark = clip.current_time.get_value()
                duplicate_clip.out_mark = clip.current_time.get_value() + 1
            exporter.export(duplicate_clip, export_preset_path, export_path)
        finally:
            print ('    Exported:', str(clip.name)[1:-1], f'at {duplicate_clip.in_mark}')
            flame.delete(duplicate_clip)

#-------------------------------------#

    def folder_browser(self):

        def save_config():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            saved_browse_path = root.find('.//saved_browse_path')
            saved_browse_path.text = export_path

            xml_tree.write(self.config_xml)

            print ('--> config saved\n')

        # Select export folder

        FlameMessageWindow('Select Path', 'message', 'Select still image export path')

        # Open folder browse window

        window = QtWidgets.QWidget()
        export_path = str(QtWidgets.QFileDialog.getExistingDirectory(window, 'Select Directory', self.saved_browse_path, QtWidgets.QFileDialog.ShowDirsOnly))

        # Save config if path is good

        if os.path.isdir(export_path):
            save_config()
            print ('Export path:', export_path, '\n')

        return export_path

    def translate_path(self, clip):
        import flame

        def get_shot_name(name):

            shot_name_split = re.split(r'(\d+)', name)

            if len(shot_name_split) > 1:
                if shot_name_split[1].isalnum():
                    shot_name = shot_name_split[0] + shot_name_split[1]
                else:
                    shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]
            else:
                shot_name = name

            return shot_name

        def get_seq_name(name):

            # Get sequence name abreviation from shot name

            seq_name = re.split('[^a-zA-Z]', name)[0]

            return seq_name

        clip_name = str(clip.name)[1:-1]

        # Get shot name

        try:
            if clip.versions[0].tracks[0].segments[0].shot_name != '':
                shot_name = str(clip.versions[0].tracks[0].segments[0].shot_name)[1:-1]
            else:
                shot_name = get_shot_name(clip_name)
        except:
            shot_name = ''

        # Get Seq Name

        seq_name = get_seq_name(shot_name)

        # Get time values for tokens

        yyyy = self.date.strftime('%Y')
        yy = self.date.strftime('%y')
        mm = self.date.strftime('%m')
        dd = self.date.strftime('%d')
        hour = self.date.strftime('%I')
        if hour.startswith('0'):
            hour = hour[1:]
        minute = self.date.strftime('%M')
        ampm_caps = self.date.strftime('%p')
        ampm = str(self.date.strftime('%p')).lower()

        # Replace tokens in path

        new_export_path = re.sub('<ProjectName>', flame.project.current_project.name, self.custom_export_path)
        new_export_path = re.sub('<ProjectNickName>', flame.project.current_project.nickname, new_export_path)
        new_export_path = re.sub('<ShotName>',shot_name, new_export_path)
        new_export_path = re.sub('<SEQNAME>', seq_name.upper(), new_export_path)
        new_export_path = re.sub('<SeqName>', seq_name, new_export_path)
        new_export_path = re.sub('<UserName>', flame.users.current_user.name, new_export_path)
        new_export_path = re.sub('<UserNickName>', flame.users.current_user.nickname, new_export_path)
        new_export_path = re.sub('<ClipName>', str(clip.name)[1:-1], new_export_path)
        new_export_path = re.sub('<Resolution>', str(clip.width) + 'x' + str(clip.height), new_export_path)
        new_export_path = re.sub('<ClipHeight>', str(clip.height), new_export_path)
        new_export_path = re.sub('<ClipWidth>', str(clip.width), new_export_path)
        new_export_path = re.sub('<YYYY>', yyyy, new_export_path)
        new_export_path = re.sub('<YY>', yy, new_export_path)
        new_export_path = re.sub('<MM>', mm, new_export_path)
        new_export_path = re.sub('<DD>', dd, new_export_path)
        new_export_path = re.sub('<Hour>', hour, new_export_path)
        new_export_path = re.sub('<Minute>', minute, new_export_path)
        new_export_path = re.sub('<AMPM>', ampm_caps, new_export_path)
        new_export_path = re.sub('<ampm>', ampm, new_export_path)

        # print ('custom_export_path:', self.custom_export_path)
        print ('    Export path:', new_export_path)

        if not os.path.isdir(new_export_path):
            os.makedirs(new_export_path)

        return new_export_path

    def post_export(self, export_path):

        if self.reveal_in_finder:
            self.open_finder(export_path)

        if self.reveal_in_mediahub:
            self.open_mediahub(export_path)

        FlameMessageWindow('Operation Complete', 'message', f'Frame(s) exported: {export_path}')

    def open_mediahub(self, export_path):
        import flame

        flame.go_to('MediaHub')
        flame.mediahub.files.set_path(export_path)
        print ('--> Media Hub opened\n')

    def open_finder(self, export_path):

        if platform.system() == 'Darwin':
            subprocess.Popen(['open', export_path])
        else:
            subprocess.Popen(['xdg-open', export_path])

#-------------------------------------#

def export_frame(selection):

    export = ExportFrame(selection)
    return export.export_current_frame()

def export_markers(selection):

    export = ExportFrame(selection)
    return export.export_marker_frame()

def script_setup(selection):

    open_setup = ExportFrame(selection)
    return open_setup.setup()

#-------------------------------------#

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PyClip, flame.PySequence)):
            return True
    return False

def scope_markers(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PySequence, flame.PyClip)):
            if not isinstance(item.parent, flame.PyReel):
                if item.markers:
                    return True
    return False

#-------------------------------------#

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Export...',
            'actions': [
                {
                    'name': 'Export Current Frame',
                    'isVisible': scope_clip,
                    'execute': export_frame,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Export Marker Frames',
                    'isVisible': scope_markers,
                    'execute': export_markers,
                    'minimumVersion': '2022'
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
                    'name': 'Export Frame Setup',
                    'execute': script_setup,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
