'''
Script Name: SRT to XML
Script Version: 3.0
Flame Version: 2020
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 05.01.20
Update Date: 05.22.21

Custom Action Type: Media Panel

Description:

    Convert SRT files to XML files that can be imported into Flame

    Right-click on clip in Media Panel that subtitles will be added to -> SRT to XML... -> Convert SRT to XML

To install:

    Copy script into /opt/Autodesk/shared/python/srt_to_xml

Updates:

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

from __future__ import print_function
import os
from PySide2 import QtCore, QtWidgets

VERSION = 'v3.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/srt_to_xml'

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
        self.setMinimumSize(110, 28)
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

class FlameClickableLineEdit(QtWidgets.QLineEdit):
    """
    Custom Qt Flame Clickable Line Edit Widget
    """

    clicked = QtCore.Signal()

    def __init__(self, text, connect, parent, *args, **kwargs):
        super(FlameClickableLineEdit, self).__init__(*args, **kwargs)

        self.setText(text)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setReadOnly(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; font: 14px "Discreet"}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.setStyleSheet('QLineEdit {color: #bbbbbb; background-color: #474e58; font: 14px "Discreet"}'
                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
            self.clicked.emit()
            self.setStyleSheet('QLineEdit {color: #898989; background-color: #373e47; font: 14px "Discreet"}'
                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
        else:
            super().mousePressEvent(event)

class FlamePushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Widget
    """

    def __init__(self, button_name, checked, parent, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setMinimumSize(150, 28)
        self.setMaximumSize(150, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #424142, stop: .91 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #4f4f4f, stop: .91 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #383838, stop: .91 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget
    """

    def __init__(self, button_name, connect, parent, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumSize(QtCore.QSize(150, 28))
        self.setMaximumSize(QtCore.QSize(150, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

# ------------------------------------- #

class ConvertSRT(object):

    def __init__(self, selection):
        from ast import literal_eval

        print ('\n', '>' * 20, 'srt to xml %s' % VERSION, '<' * 20, '\n')

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')
        self.xml_template_path = os.path.join(SCRIPT_PATH, 'xml_template.xml')
        self.xml_title_template_path = os.path.join(SCRIPT_PATH, 'xml_title_template.xml')
        self.default_template_path = os.path.join(SCRIPT_PATH, 'text_node_template.ttg')
        if not os.path.isfile(self.default_template_path):
            self.default_template_path = SCRIPT_PATH

        # Check for config file, if none, create

        self.check_config_file()

        # Get config file values

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.srt_path = values[2]
        self.template_path = values[4]
        self.bottom_align = literal_eval(values[6])

        if not os.path.isfile(self.srt_path):
            self.srt_path = SCRIPT_PATH

        if not os.path.isfile(self.template_path):
            self.template_path = SCRIPT_PATH

        get_config_values.close()

        print ('>>> config loaded <<<\n')

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

            config_text.insert(0, 'Values for pyFlame SRT to XML script.')
            config_text.insert(1, 'SRT Path:')
            config_text.insert(2, '/opt/Autodesk')
            config_text.insert(3, 'Text Node Template Path:')
            config_text.insert(4, '/opt/Autodesk')
            config_text.insert(5, 'Bottom Align Button:')
            config_text.insert(6, 'False')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

    def main_window(self):

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(800, 300))
        self.window.setMaximumSize(QtCore.QSize(800, 300))
        self.window.setWindowTitle('pyFlame SRT to XML %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #282828')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.srt_path_label = FlameLabel('SRT File', 'normal', self.window)
        self.template_path_label = FlameLabel('Text Node Template', 'normal', self.window)

        self.xml_resolution_label = FlameLabel('XML Resolution', 'background', self.window)
        self.xml_ratio_label = FlameLabel('XML Ratio', 'background', self.window)
        self.xml_start_timecode_label = FlameLabel('XML Start Timecode', 'background', self.window)
        self.xml_end_timecode_label = FlameLabel('XML End Timecode', 'background', self.window)

        self.xml_resolution_label_02 = FlameLabel('%sx%s' % (self.seq_width, self.seq_height), 'outline', self.window)
        self.xml_ratio_label_02 = FlameLabel(str(self.seq_ratio), 'outline', self.window)
        self.xml_start_timecode_label_02 = FlameLabel(self.xml_start_timecode, 'outline', self.window)
        self.xml_end_timecode_label_02 = FlameLabel(self.xml_end_timecode, 'outline', self.window)

        #  Entries

        self.srt_path_entry = FlameClickableLineEdit(self.srt_path, self.srt_path_browse, self.window)
        self.template_path_entry = FlameClickableLineEdit(self.template_path, self.template_path_browse, self.window)

        # Push Button

        self.bottom_align_btn = FlamePushButton(' Bottom Align', self.bottom_align, self.window)

        # Buttons

        self.convert_btn = FlameButton('Convert', self.confirm_entry_fields, self.window)
        self.cancel_btn = FlameButton('Cancel', self.window.close, self.window)

        # -------------------------------------------------------------

        # Window layout

        # Gridbox01

        gridbox = QtWidgets.QGridLayout()
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

        gridbox.addWidget(self.bottom_align_btn, 9, 0)
        gridbox.addWidget(self.cancel_btn, 9, 3)
        gridbox.addWidget(self.convert_btn, 9, 4)

        self.get_srt_info()

        self.window.setLayout(gridbox)

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

    def get_srt_info(self):
        import re

        print ('\n', 'srt_info', '\n')

        if os.path.isfile(self.srt_path):

            # Get xml name from name of srt file

            self.xml_name = str(self.srt_path.rsplit('/', 1)[1])[:-4]
            print ('xml_name:', self.xml_name)

            # Open srt file
            print ('srt_path:', self.srt_path_entry.text())

            srt_file = open(self.srt_path_entry.text(), 'r')
            srt_lines = srt_file.read().splitlines()

            # Get srt start timecode

            for line in srt_lines:
                print ('line:', line)
                start_timecode = re.match(r'\d\d:\d\d:\d\d,\d\d\d', line)
                if start_timecode:
                    self.start_timecode = start_timecode.group(0)
                    print ('start_timecode:', self.start_timecode)
                    break

            # Convert start milliseconds to frames based on frame rate

            self.xml_start_timecode = self.calculate_frames(self.start_timecode)

            # Get srt end timecode

            for line in srt_lines:
                end_timecode = re.findall(r'\d\d:\d\d:\d\d,\d\d\d', line)
                if end_timecode:
                    self.end_timecode = end_timecode[1]

            print ('end_timecode:', self.end_timecode, '\n')

            # Convert end milliseconds to frames based on frame rate

            self.xml_end_timecode = self.calculate_frames(self.end_timecode)

            # Close srt file

            srt_file.close()

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
            return message_box('Select SRT File to Convert')

        elif not os.path.isfile(self.template_path_entry.text()):
            return message_box('Select Text Node Template File')

        self.xml_save_file_path = self.srt_path_entry.text()[:-3] + 'xml'
        print ('xml_save_file_path:', self.xml_save_file_path)

        if os.path.isfile(self.xml_save_file_path):
            message_box_confirm('File Exists, Overwrite?')
            if not message_box_confirm:
                return
            return self.convert()
        return self.convert()

    def convert(self):
        import itertools
        import re

        def save_settings():

            config_text = []

            config_text.insert(0, 'Values for pyFlame SRT to XML script.')
            config_text.insert(1, 'SRT Path:')
            config_text.insert(2, self.srt_path_entry.text())
            config_text.insert(3, 'Text Node Template Path:')
            config_text.insert(4, self.template_path_entry.text())
            config_text.insert(5, 'Bottom Align Button:')
            config_text.insert(6, self.bottom_align_btn.isChecked())

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

            print ('\n>>> config file saved <<<\n')

        def replace_xml_template_tokens():
            import re

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

            # Open srt file

            srt_file = open(self.srt_path_entry.text(), 'r')
            self.srt_lines = srt_file.read().splitlines()
            srt_file.close()

            # Get timecode and text line numbers

            line_num = -1

            self.timecode_line_list = []

            for line in self.srt_lines:
                line_num += 1
                timecode_line = re.match('\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d', line)
                if timecode_line:
                    print (str(line_num) + '   ' + timecode_line.group(0))
                    self.timecode_line_list.append(line_num)

            # print ('timecode_line_list:', self.timecode_line_list, '\n')

        save_settings()

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
            print (lines, '\n')

        def get_last_line():
            last_line = lines[-1]
            if not last_line:
                lines.pop()
                get_last_line()
            return len(lines) + 2

        srt_end_line = get_last_line()
        print ('srt_end_line:', srt_end_line)

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
        print ('max_line_value:', max_line_value)

        # Loop through events in timecode list to replace title tokens

        for item in self.timecode_line_list:
            item_index = self.timecode_line_list.index(item)

            # Convert start and end timecode from milliseconds to frames

            with open(self.srt_path_entry.text(), 'r') as srt_file:

                for srt_timecode_line in itertools.islice(srt_file, item, (item + 1)):

                    self.srt_start_timecode = self.calculate_frames(srt_timecode_line.split(' ', 1)[0])
                    self.srt_end_timecode = self.calculate_frames(srt_timecode_line.split('-> ', 1)[1])
                    print ('srt_timecode_line:', srt_timecode_line)
                    print ('srt_start_timecode:', self.srt_start_timecode)
                    print ('srt_end_timecode:', self.srt_end_timecode, '\n')

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
                # for text_line in itertools.islice(srt_file, self.first_line_list[item_index], self.last_line_list[item_index]):
                for text_line in itertools.islice(srt_file, first_line_num, last_line_num):
                    text_line = text_line.strip()
                    self.srt_text_line_list.append(text_line)
            print ('srt_text_line_list:', self.srt_text_line_list)

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

        message_box('XML Exported')

        print ('\ndone.\n')

#-------------------------------------#

def message_box(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setMinimumSize(400, 100)
    msg_box.setText(message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14pt "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14pt "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

def message_box_confirm(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setText('<b><center>%s' % message)
    msg_box_yes_button = msg_box.addButton(QtWidgets.QMessageBox.Yes)
    msg_box_yes_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_yes_button.setMinimumSize(QtCore.QSize(80, 24))
    msg_box_no_button = msg_box.addButton(QtWidgets.QMessageBox.No)
    msg_box_no_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_no_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14pt "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14pt "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')

    message = message.replace('<br>', '-')

    print ('\n>>> %s <<<\n' % message)

    if msg_box.exec_() == QtWidgets.QMessageBox.Yes:
        return True
    return False

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
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
