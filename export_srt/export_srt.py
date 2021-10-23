'''
Script Name: Export SRT
Script Version: 1.1
Flame Version: 2020.3
Written by: Michael Vaglienty
Creation Date: 07.22.20
Update Date: 10.23.21

Custom Action Type: Timeline

Description:

    Export SRT file from timeline text fx.

    All text to be exported must be timeline text fx.

    When running the script a second time be sure to reselect all segments with text fx.
    Not doing so will can cause Flame to crash.

    Right-click on selected clips with timeline text fx -> SRT... -> Export SRT

To install:

    Copy script into /opt/Autodesk/shared/python/export_srt

    When creating this folder manually be sure Flame has full read/write permissions to it.

Updates:

    v1.1 10.23.21

        Updated to be compatible with Flame 2022/Python 3.7

'''

from __future__ import print_function
import os

VERSION = 'v1.1'

### config setup ###
CONFIG_PATH = '/opt/Autodesk/shared/python/export_srt/config'
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config')

class ExportSRT(object):

    def __init__(self, selection):

        self.selection = selection

        self.temp_save_path = '/opt/Autodesk/shared/python/export_srt/temp'
        if not os.path.isdir(self.temp_save_path):
            os.makedirs(self.temp_save_path)

        self.temp_text_file = os.path.join(self.temp_save_path, 'temp_text.ttg_node')

        # Get config file values
        #-----------------------

        get_config_values = open(CONFIG_FILE, 'r')
        values = get_config_values.read().splitlines()

        self.export_path = values[2]

        get_config_values.close()

        print ('>>> config loaded <<<\n')

        # Init variables

        self.seq_name = ''
        self.text_lines = []
        self.srt_block_list = []
        self.record_in = ''
        self.record_out = ''
        self.frame_rate = ''
        self.srt_timecode = ''

    def export_srt(self):
        import shutil
        import flame

        self.export_path = self.path_browse()

        if self.export_path:

            event_number = 1

            # Get sequence name and frame rate

            self.get_seqeunce_info()

            for seg in self.selection:
                if isinstance(seg, flame.PySegment):
                    for fx in seg.effects:
                        if fx.type == 'Text':

                            # Get segment in and out timecode

                            record_in = str(seg.record_in)[1:-1]
                            record_out = str(seg.record_out)[1:-1]

                            converted_record_in = self.convert_timecode(record_in, 'in')
                            converted_record_out = self.convert_timecode(record_out, 'out')

                            seg_timecode = converted_record_in + ' --> ' + converted_record_out

                            # Save text fx file

                            fx.save_setup(self.temp_text_file)

                            # Get segment text lines

                            self.read_text_file()

                            # Convert ascii to text

                            self.text_convert()

                            # Segment to list

                            self.srt_block_list.append(event_number)
                            self.srt_block_list.append(seg_timecode)
                            for line in self.line_list:
                                self.srt_block_list.append(line)
                            self.srt_block_list.append('')

                            event_number += 1

            self.export_file()

            # Remove temp folder

            shutil.rmtree(self.temp_save_path)

        else:
            print ('\n>>> exit - nothing exported <<<\n')

    def path_browse(self):
        from PySide2 import QtWidgets

        if not os.path.isdir(self.export_path):
            self.export_path = '/'

        window = QtWidgets.QWidget()

        path = str(QtWidgets.QFileDialog.getExistingDirectory(window, 'Select Directory', self.export_path, QtWidgets.QFileDialog.ShowDirsOnly))

        if os.path.isdir(path):
            self.export_path = path
            print ('export_path:', self.export_path)

            # Save Path

            config_text = []

            config_text.insert(0, 'Values for pyFlame Export SRT script.')
            config_text.insert(1, 'Export Path:')
            config_text.insert(2, self.export_path)

            out_file = open(CONFIG_FILE, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

            print ('\n>>> config file saved <<<\n')

        else:
            self.export_path = False

        return self.export_path

    def get_seqeunce_info(self):

        # Get name and frame rate of segment sequence

        for seg in self.selection:
            track = seg.parent
            version = track.parent
            sequence = version.parent
            self.seq_name = str(sequence.name)[1:-1]
            self.frame_rate = float(str(sequence.frame_rate)[:-4])
            break

        print ('sequence_name:', self.seq_name)
        print ('frame_rate:', self.frame_rate, '\n')

    def convert_timecode(self, timecode, in_out):

        if self.frame_rate == '50':
            self.frame_rate = '25'
        elif self.frame_rate == '59.94':
            self.frame_rate = '29.97'
        elif self.frame_rate == '60':
            self.frame_rate = '30'

        milliseconds_per_frame = 1000/float(self.frame_rate)

        hours_mins_secs = timecode[:-3]

        frames = timecode[-2:]

        # Add one extra frame to out timecode

        if in_out == 'out':
            frames = str(int(frames) + 1)

        milliseconds = str(int(round(float(frames)*milliseconds_per_frame)))

        if len(milliseconds) == 1:
            milliseconds = '00' + milliseconds
        elif len(milliseconds) == 2:
            milliseconds = '0' + milliseconds
        elif len(milliseconds) == 4:
            # Remove first number from milliseconds and add one to seconds
            milliseconds = milliseconds[1:]
            hours = hours_mins_secs[:2]
            print ('hours:', hours)
            mins = hours_mins_secs[3:-3]
            print ('mins:', mins)
            seconds = str(int(hours_mins_secs[-2:]) + 1)
            print ('seconds:', seconds)

            if len(seconds) == 1:
                seconds = '0' + seconds

            if seconds == '60':
                seconds = '00'
                mins = str(int(mins)) + 1
                if len(mins) == 1:
                    mins = '0' + mins

            if mins == '60':
                mins = '00'
                hours = str(int(hours)) + 1
                if len(hours) == 1:
                    hours = '0' + hours

            hours_mins_secs = hours + ':' + mins + ':' + seconds

        converted_timecode = hours_mins_secs + ',' + milliseconds

        return converted_timecode

    def read_text_file(self):

        # Get text lines from saved timeline text fx

        get_text_values = open(self.temp_text_file, 'r')
        lines = get_text_values.read()

        split_lines = lines.split('>')

        self.text_lines = [l.split('<', 1)[0] for l in split_lines if '</Text' in l]

        while '' in self.text_lines:
            self.text_lines.remove('')

        get_text_values.close()

    def text_convert(self):

        # Convert ascii to plain text

        self.line_list = []

        for line in self.text_lines:
            ascii_list = line.split()
            for i in range(0, len(ascii_list)):
                ascii_list[i] = int(ascii_list[i])
            result = ''.join(map(chr, ascii_list))
            self.line_list.append(result)

        print ('line_list:', self.line_list)

    def export_file(self):

        self.srt_export_file = os.path.join(self.export_path, self.seq_name) + '.srt'

        try:
            out_file = open(self.srt_export_file, 'w')
            for line in self.srt_block_list:
                print(line, file=out_file)
            out_file.close()

            message_box('SRT File Exported')

        except:
            message_box('SRT File Not Exported <br> Check File Path/Permissions')

# -------------------------------------- #

def config_file():

    # Check for and load config file
    #-------------------------------

    if not os.path.isdir(CONFIG_PATH):
        try:
            os.makedirs(CONFIG_PATH)
        except:
            message_box('Unable to create folder:<br>%s<br>Check folder permissions' % CONFIG_PATH)

    if not os.path.isfile(CONFIG_FILE):
        print ('>>> config file does not exist, creating new config file <<<')

        config_text = []

        config_text.insert(0, 'Values for pyFlame Export  SRT script.')
        config_text.insert(1, 'Export Path:')
        config_text.insert(2, '/')

        out_file = open(CONFIG_FILE, 'w')
        for line in config_text:
            print(line, file=out_file)
        out_file.close()

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

    code_list = ['<br>', '-']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

def export(selection):

    print ('\n', '>' * 20, 'export srt %s' % VERSION, '<' * 20, '\n')

    config_file()

    script = ExportSRT(selection)
    script.export_srt()

def scope_segment(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PySegment):
            return True
    return False

def get_timeline_custom_ui_actions():

    return [
        {
            'name': 'SRT...',
            'actions': [
                {
                    'name': 'Export SRT',
                    'isVisible': scope_segment,
                    'execute': export,
                    'minimumVersion': '2020.3'
                }
            ]
        }
    ]
