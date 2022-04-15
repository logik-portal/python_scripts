'''
Script Name: SRT to XML
Script Version: 3.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 05.01.20
Update Date: 03.15.22

Custom Action Type: Media Panel

Description:

    Convert SRT files to XML files that can be imported into Flame through MediaHub

Menu:

    Right-click on clip in Media Panel that subtitles will be added to -> SRT to XML... -> Convert SRT to XML

To install:

    Copy script into /opt/Autodesk/shared/python/srt_to_xml

Updates:

    v3.2 03.15.22

        Moved UI widgets to external file

    v3.1 03.05.22

        Updated UI for Flame 2023

        Config updated to XML

        Added option to open MediaHub to location of created XML

    v3.0 05.22.21

        Updated to be compatible with Flame 2022/Python 3.7

    v2.1 04.27.21

        Bug fixes

    v1.4 03.18.21:

        Added bottom align button - will align rows of text to bottom row

        Changed event detection from empty line to timecode line

    v1.3 02.17.21:

        Fixed problem that caused script not to work when right clicking on clip with ratio of 1.0

        UI Improvements

    v1.2 10.12.20:

        Updated UI

    v1.1 05.16.20:

        Fixed scoping so menu only shows when right-clicking on clips
'''

import xml.etree.ElementTree as ET
import os, re, ast, itertools
from PySide2 import QtWidgets
from flame_widgets_srt_to_xml import FlameButton, FlameLabel, FlamePushButton, FlameMessageWindow, FlameClickableLineEdit, FlameWindow

VERSION = 'v3.2'

SCRIPT_PATH = '/opt/Autodesk/shared/python/srt_to_xml'

class ConvertSRT(object):

    def __init__(self, selection):

        print ('\n', '>' * 20, f'srt to xml {VERSION}', '<' * 20, '\n')

        # Define paths

        self.xml_template_path = os.path.join(SCRIPT_PATH, 'xml_template.xml')
        self.xml_title_template_path = os.path.join(SCRIPT_PATH, 'xml_title_template.xml')
        self.default_template_path = os.path.join(SCRIPT_PATH, 'text_node_template.ttg')
        if not os.path.isfile(self.default_template_path):
            self.default_template_path = SCRIPT_PATH

        # Load config file

        self.config()

        #-----------------------------------------

        # Check SRT path. If file no longer exists. set to /

        if not (os.path.isfile(self.srt_path) or os.path.isdir(self.srt_path)):
            self.srt_path = '/'

        # Check default template path
        # If path is empty, set to default
        # If file doesn't exist, set to default

        if self.template_path == '/' or '':
            self.template_path = self.default_template_path
        elif not os.path.isfile(self.template_path):
            self.template_path = self.default_template_path

        #-----------------------------------------

        # Get sequence variables

        self.seq = selection[0]

        self.seq_name = str(self.seq.name)[1:-1]
        print ('seq_name:', self.seq_name)

        self.seq_frame_rate = self.seq.frame_rate.split(' ', 1)[0]
        print ('seq_frame_rate:', self.seq_frame_rate)

        self.seq_width = self.seq.width
        print ('seq_width:', self.seq_width)

        self.seq_height = self.seq.height
        print ('seq_height:', self.seq_height)

        self.seq_ratio = self.seq.ratio
        if len(str(self.seq_ratio)) > 5:
            self.seq_ratio = str(self.seq_ratio)[:5]
        print ('seq_ratio:', self.seq_ratio)

        self.seq_bit_depth = self.seq.bit_depth
        print ('seq_bit_depth:', self.seq_bit_depth, '\n')

        # Set XML label default values

        self.xml_name = 'None Selected'
        self.xml_start_timecode = '00:00:00:00'
        self.xml_end_timecode = '00:00:00:00'

        self.main_window()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get UI settings

            for setting in root.iter('srt_to_xml_settings'):
                self.srt_path = setting.find('srt_path').text
                self.template_path = setting.find('template_path').text
                self.bottom_align = ast.literal_eval(setting.find('bottom_align').text)
                self.reveal_in_mediahub = ast.literal_eval(setting.find('reveal_in_mediahub').text)

            if not os.path.isfile(self.srt_path):
                self.srt_path = SCRIPT_PATH

            if not os.path.isfile(self.template_path):
                self.template_path = SCRIPT_PATH

            print ('\n--> config loaded\n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder: {self.config_path}<br><br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file\n')

                config = '''
<settings>
    <srt_to_xml_settings>
        <srt_path>/</srt_path>
        <template_path>/</template_path>
        <bottom_align>False</bottom_align>
        <reveal_in_mediahub>False</reveal_in_mediahub>
    </srt_to_xml_settings>
</settings>'''

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

    def main_window(self):

        gridbox = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'SRT to XML <small>{VERSION}', gridbox, 770, 420)

        # Labels

        self.srt_path_label = FlameLabel('SRT File')
        self.template_path_label = FlameLabel('Text Node Template')

        self.xml_resolution_label = FlameLabel('XML Resolution', label_type='underline')
        self.xml_ratio_label = FlameLabel('XML Ratio', label_type='underline')
        self.xml_start_timecode_label = FlameLabel('XML Start Timecode', label_type='underline')
        self.xml_end_timecode_label = FlameLabel('XML End Timecode', label_type='underline')

        self.xml_resolution_label_02 = FlameLabel(f'{self.seq_width}x{self.seq_height}', label_type='background')
        self.xml_ratio_label_02 = FlameLabel(str(self.seq_ratio), label_type='background')
        self.xml_start_timecode_label_02 = FlameLabel(self.xml_start_timecode, label_type='background')
        self.xml_end_timecode_label_02 = FlameLabel(self.xml_end_timecode, label_type='background')

        #  Entries

        self.srt_path_entry = FlameClickableLineEdit(self.srt_path, self.srt_path_browse, max_width=600)
        self.template_path_entry = FlameClickableLineEdit(self.template_path, self.template_path_browse, max_width=600)

        # Push Button

        self.bottom_align_btn = FlamePushButton('Bottom Align', self.bottom_align)
        self.reveal_in_mediahub_btn = FlamePushButton('Reveal in MediaHub', self.reveal_in_mediahub)

        # Buttons

        self.convert_btn = FlameButton('Convert', self.confirm_entry_fields)
        self.cancel_btn = FlameButton('Cancel', self.window.close)

        # -------------------------------------------------------------

        # Widget layout

        gridbox.setMargin(30)

        gridbox.addWidget(self.srt_path_label, 1, 0)
        gridbox.addWidget(self.srt_path_entry, 1, 1, 1, 4)

        gridbox.addWidget(self.template_path_label, 2, 0)
        gridbox.addWidget(self.template_path_entry, 2, 1, 1, 4)

        gridbox.setColumnMinimumWidth(2, 50)
        gridbox.setRowMinimumHeight(3, 30)

        gridbox.addWidget(self.xml_resolution_label, 6, 0)
        gridbox.addWidget(self.xml_resolution_label_02, 7, 0)

        gridbox.addWidget(self.xml_ratio_label, 6, 1)
        gridbox.addWidget(self.xml_ratio_label_02, 7, 1)

        gridbox.addWidget(self.xml_start_timecode_label, 6, 3)
        gridbox.addWidget(self.xml_start_timecode_label_02, 7, 3)

        gridbox.addWidget(self.xml_end_timecode_label, 6, 4)
        gridbox.addWidget(self.xml_end_timecode_label_02, 7, 4)

        gridbox.setRowMinimumHeight(8, 28)

        gridbox.addWidget(self.bottom_align_btn, 9, 3)
        gridbox.addWidget(self.reveal_in_mediahub_btn, 9, 4)

        gridbox.setRowMinimumHeight(10, 28)

        gridbox.addWidget(self.cancel_btn, 11, 3)
        gridbox.addWidget(self.convert_btn, 11, 4)

        self.get_srt_info()

        self.window.show()

    def srt_path_browse(self):

        srt_path = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Select .srt File', self.srt_path_entry.text(), 'SRT Files (*.srt)')[0]

        if os.path.isfile(srt_path):
            self.srt_path = srt_path
            self.srt_path_entry.setText(srt_path)
            self.get_srt_info()

    def template_path_browse(self):

        template_path = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Select .ttg File', self.template_path_entry.text(), 'TTG Files (*.ttg)')[0]

        if os.path.isfile(template_path):
            self.template_path_entry.setText(template_path)

    def open_srt_file(self, srt_path):

        # Open srt file

        try:
            with open(srt_path, 'r') as srt_file:
                return srt_file.read().splitlines()
        except UnicodeDecodeError as error:
            FlameMessageWindow('SRT to XML - Error', 'error', f'Unable to load SRT: {error}.<br><br>Non standard characters or fancy quotes could be causing a problem.')
            return False

    def get_srt_info(self):

        print ('\n', 'srt_info', '\n')

        if os.path.isfile(self.srt_path):

            # Get xml name from name of srt file

            self.xml_name = str(self.srt_path.rsplit('/', 1)[1])[:-4]
            print ('xml_name:', self.xml_name)

            # Open srt file

            self.srt_lines = self.open_srt_file(self.srt_path)

            if self.srt_lines:

                # Get srt start timecode

                for line in self.srt_lines:
                    print ('line:', line)
                    start_timecode = re.match(r'\d\d:\d\d:\d\d,\d\d\d', line)
                    if start_timecode:
                        self.start_timecode = start_timecode.group(0)
                        print ('start_timecode:', self.start_timecode)
                        break

                # Convert start milliseconds to frames based on frame rate

                self.xml_start_timecode = self.calculate_frames(self.start_timecode)

                # Get srt end timecode

                for line in self.srt_lines:
                    end_timecode = re.findall(r'\d\d:\d\d:\d\d,\d\d\d', line)
                    if end_timecode:
                        self.end_timecode = end_timecode[1]

                print ('end_timecode:', self.end_timecode, '\n')

                # Convert end milliseconds to frames based on frame rate

                self.xml_end_timecode = self.calculate_frames(self.end_timecode)

                self.xml_start_timecode_label_02.setText(self.xml_start_timecode)
                self.xml_end_timecode_label_02.setText(self.xml_end_timecode)

    def calculate_frames(self, timecode):

        frame_rate = self.seq_frame_rate

        if self.seq_frame_rate == '50':
            frame_rate = '25'
        elif self.seq_frame_rate == '59.94':
            frame_rate = '29.97'
        elif self.seq_frame_rate == '60':
            frame_rate = '30'

        milliseconds_per_frame = 1000/float(frame_rate)

        timecode_split = timecode.rsplit(',', 1)

        milliseconds = timecode_split[1]

        hours_mins_secs = timecode_split[0]

        frames = str(int(round(float(milliseconds)/milliseconds_per_frame)))
        if len(frames) == 1:
            frames = '0' + frames

        if self.seq_frame_rate in ('23.976', '24'):
            resolved_timecode = hours_mins_secs + '+' + frames
        elif self.seq_frame_rate in ('25', '29.97', '30'):
            resolved_timecode = hours_mins_secs + ':' + frames
        elif self.seq_frame_rate in ('50', '59.94', '60'):
            resolved_timecode = hours_mins_secs + '#' + frames

        return resolved_timecode

    def confirm_entry_fields(self):

        # Confirm entry fields

        if not os.path.isfile(self.srt_path_entry.text()):
            return FlameMessageWindow('Error', 'error', 'Select SRT file to convert')

        elif not os.path.isfile(self.template_path_entry.text()):
            return FlameMessageWindow('Error', 'error', 'Select Text node template file')

        self.xml_save_file_path = self.srt_path_entry.text()[:-3] + 'xml'
        print ('xml_save_file_path:', self.xml_save_file_path)

        self.srt_lines = self.open_srt_file(self.srt_path_entry.text())
        if not self.srt_lines:
            return

        if os.path.isfile(self.xml_save_file_path):
            if not FlameMessageWindow('Confirm Operation', 'warning', 'File Exists, Overwrite?'):
                return
            return self.convert()
        return self.convert()

    def convert(self):

        def save_config():

            # Save path to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            srt_path = root.find('.//srt_path')
            srt_path.text = self.srt_path_entry.text()

            template_path = root.find('.//template_path')
            template_path.text = self.template_path_entry.text()

            bottom_align = root.find('.//bottom_align')
            bottom_align.text = str(self.bottom_align_btn.isChecked())

            reveal_in_mediahub = root.find('.//reveal_in_mediahub')
            reveal_in_mediahub.text = str(self.reveal_in_mediahub_btn.isChecked())

            xml_tree.write(self.config_xml)

            print ('--> config saved\n')

        def replace_xml_template_tokens():

            bit_depth = str(self.seq_bit_depth) + ' bit'
            if self.seq_bit_depth == 16:
                bit_depth = bit_depth + ' fp'

            frame_rate = self.seq_frame_rate
            if frame_rate == '29.97':
                frame_rate = '29.97 NDF'
            elif frame_rate == '59.94':
                frame_rate = '59.94 NDF'

            # Replace tokens in xml template file

            template_token_dict = {}

            template_token_dict['<XmlName>'] = self.srt_path_entry.text().rsplit('/', 1)[1][:-4]
            template_token_dict['<FrameRate>'] = frame_rate
            template_token_dict['<SeqWidth>'] = str(self.seq_width)
            template_token_dict['<SeqHeight>'] = str(self.seq_height)
            template_token_dict['<SeqBitDepth>'] = bit_depth
            template_token_dict['<SeqRatio>'] = str(self.seq_ratio)
            template_token_dict['<SeqTimecodeStart>'] = self.xml_start_timecode
            template_token_dict['<SeqTimecodeEnd>'] = self.xml_end_timecode

            # Open menu template

            xml_template = open(self.xml_template_path, 'r')
            self.xml_template_lines = xml_template.read().splitlines()

            # Replace tokens in menu template

            for key, value in template_token_dict.items():
                for line in self.xml_template_lines:
                    if key in line:
                        line_index = self.xml_template_lines.index(line)
                        new_line = re.sub(key, value, line)
                        self.xml_template_lines[line_index] = new_line

            xml_template.close()

        def create_srt_lists():

            # Create timecode and text line lists from srt
            # --------------------------------------------

            # Get timecode and text line numbers

            line_num = -1

            self.timecode_line_list = []

            for line in self.srt_lines:
                line_num += 1
                timecode_line = re.match('\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d', line)
                if timecode_line:
                    #print (str(line_num) + '   ' + timecode_line.group(0))
                    self.timecode_line_list.append(line_num)

        def open_media_hub(path):
            import flame

            flame.go_to('MediaHub')

            flame.mediahub.files.set_path(path)

        save_config()

        # Replace tokens in xml template with values from UI

        replace_xml_template_tokens()

        # Create timecode and text line lists from srt

        create_srt_lists()

        # loop through entries in srt to create xml titles
        # ------------------------------------------------

        # Line to start inserting titles into xml template

        self.xml_title_insert_line = 17

        # Get last line of text in srt file for end of last event

        with open(self.srt_path_entry.text(), 'r') as f:
            lines = f.read().splitlines()
            #print (lines, '\n')

        def get_last_line():
            last_line = lines[-1]
            if not last_line:
                lines.pop()
                get_last_line()
            return len(lines) + 2

        srt_end_line = get_last_line()
        #print ('srt_end_line:', srt_end_line)

        # Get max number of text lines in all events for bottom row align button

        text_line_num_list = []

        for item in self.timecode_line_list:
            next_item_index = self.timecode_line_list.index(item) + 1
            try:
                next_item = self.timecode_line_list[next_item_index]
            except:
                next_item = srt_end_line
            line_num_value = next_item - item - 1
            text_line_num_list.append(line_num_value)
        max_line_value = max(text_line_num_list) - 2
        #print ('max_line_value:', max_line_value)

        # Loop through events in timecode list to replace title tokens

        for item in self.timecode_line_list:
            item_index = self.timecode_line_list.index(item)

            # Convert start and end timecode from milliseconds to frames

            with open(self.srt_path_entry.text(), 'r') as srt_file:
                for srt_timecode_line in itertools.islice(srt_file, item, (item + 1)):
                    self.srt_start_timecode = self.calculate_frames(srt_timecode_line.split(' ', 1)[0])
                    self.srt_end_timecode = self.calculate_frames(srt_timecode_line.split('-> ', 1)[1])
                    # print ('srt_timecode_line:', srt_timecode_line)
                    # print ('srt_start_timecode:', self.srt_start_timecode)
                    # print ('srt_end_timecode:', self.srt_end_timecode, '\n')

            # Add text lines to list to be converted to string later

            self.srt_text_line_list = []

            # print ('item_index:', item_index)
            timecode_line_num = self.timecode_line_list[item_index]
            # print ('timecode_line_num:', timecode_line_num)
            first_line_num = timecode_line_num + 1
            # print ('first_line_num:', first_line_num)
            try:
                next_timecode_line_num = self.timecode_line_list[item_index + 1]
            except:
                next_timecode_line_num = srt_end_line
            # print ('next_timecode_line_num:', next_timecode_line_num)
            last_line_num = next_timecode_line_num - 2
            # print ('last_line_num:', last_line_num)


            with open(self.srt_path_entry.text(), 'r') as srt_file:
                for text_line in itertools.islice(srt_file, first_line_num, last_line_num):
                    text_line = text_line.strip()
                    self.srt_text_line_list.append(text_line)
            #print ('srt_text_line_list:', self.srt_text_line_list)

            # If bottom align button is selected insert empty lines to align rows of text

            if self.bottom_align_btn.isChecked():
                while len(self.srt_text_line_list) < max_line_value:
                    self.srt_text_line_list.insert(0, ' ')

            # Convert srt_text_line_list to string
            # Add return code if list has more than one item

            self.srt_line_text = ''

            if len(self.srt_text_line_list) == 1:
                self.srt_line_text = self.srt_text_line_list[0]
            else:
                for line in self.srt_text_line_list:
                    self.srt_line_text = self.srt_line_text + '&#13;' + line
                self.srt_line_text = self.srt_line_text[5:]

            # Create dict with value to replace tokens in xml title template

            title_template_token_dict = {}

            title_template_token_dict['<TitleStartTimecode>'] = self.srt_start_timecode
            title_template_token_dict['<TitleEndTimecode>'] = self.srt_end_timecode
            title_template_token_dict['<TitleText>'] = self.srt_line_text
            title_template_token_dict['<TextNodeTemplatePath>'] = self.template_path_entry.text()

            # Open xml title template

            xml_title_template = open(self.xml_title_template_path, 'r')
            self.title_template_lines = xml_title_template.read().splitlines()

            # Replace tokens in xml title template

            for key, value in title_template_token_dict.items():
                for line in self.title_template_lines:
                    if key in line:
                        line_index = self.title_template_lines.index(line)
                        new_line = re.sub(key, value, line)
                        self.title_template_lines[line_index] = new_line

            xml_title_template.close()

            # Insert new title template lines into xml template

            for line in self.title_template_lines:
                self.xml_template_lines.insert(self.xml_title_insert_line, line)
                self.xml_title_insert_line += 1

        # Save xml file

        out_file = open(self.xml_save_file_path, 'w')
        for line in self.xml_template_lines:
            print(line, file=out_file)
        out_file.close()

        self.window.close()

        FlameMessageWindow('Operation Complete', 'message', 'XML Exported')

        if self.reveal_in_mediahub_btn.isChecked():
            open_media_hub(self.xml_save_file_path.rsplit('/', 1)[0])

        print ('done.\n')

#-------------------------------------#

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'SRT to XML...',
            'actions': [
                {
                    'name': 'Convert SRT to XML',
                    'isVisible': scope_clip,
                    'execute': ConvertSRT,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
