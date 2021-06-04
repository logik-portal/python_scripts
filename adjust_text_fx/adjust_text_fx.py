'''
Script Name: Adjust Timeline Text FX
Script Version: 2.0
Flame Version: 2020
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 05.08.20
Update Date: 05.22.21

Custom Action Type: Timeline

Description:

    Interactively adjust timeline text fx settings that can then be applied to all selected timeline text fx

    Right-click on selected clips on timeline with text fx -> Text FX... -> Adjust Text FX

To install:

    Copy script into /opt/Autodesk/shared/python/adjust_text_fx

Updates:

v2.0 05.22.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.4 02.17.21

    Multiple text layers can now be repositioned properly

    Fixes to calculator

v1.3 02.06.21

    Misc calculator fixes

    Converted UI elements to classes
'''

from __future__ import print_function
from functools import partial
import os
from PySide2 import QtCore, QtWidgets

VERSION = 'v2.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/adjust_text_fx'

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

    def __init__(self, text, parent, *args, **kwargs):
        super(FlameClickableLineEdit, self).__init__(*args, **kwargs)

        self.setText(text)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setReadOnly(True)
        self.setStyleSheet('QLineEdit {color: #898989; background-color: #373e47; font: 14px "Discreet"}'
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

    def __init__(self, name, parent, checked, connect, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(name)
        self.setParent(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.clicked.connect(connect)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setMinimumSize(110, 28)
        self.setMaximumSize(110, 28)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #424142, stop: .91 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #4f4f4f, stop: .91 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

class FlamePushButtonMenu(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Menu Widget
    """

    def __init__(self, button_name, menu_options, regen_text_fx, parent, *args, **kwargs):
        super(FlamePushButtonMenu, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        def create_menu(option):

            self.setText(option)
            justify_changed = True
            regen_text_fx(justify_changed)

        pushbutton_menu = QtWidgets.QMenu(parent)
        pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        pushbutton_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        for option in menu_options:
            pushbutton_menu.addAction(option, partial(create_menu, option))

        self.setMenu(pushbutton_menu)

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget
    """

    def __init__(self, name, parent, connect, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setParent(parent)
        self.setText(name)
        self.setMinimumSize(QtCore.QSize(110, 28))
        self.setMaximumSize(QtCore.QSize(110, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

# ---------------------------------------- #

class AdjustFX(object):

    def __init__(self, selection):
        import xml.etree.cElementTree as ET

        print ('\n', '>' * 20, 'adjust text fx %s' % VERSION, '<' * 20, '\n')

        self.selection = selection

        self.selection_count = len(selection)
        print ('selection_count:', self.selection_count)

        self.selected_segment = selection[0]

        self.temp_save_path = os.path.join(SCRIPT_PATH, 'temp')
        if not os.path.isdir(self.temp_save_path):
            os.makedirs(self.temp_save_path)

        self.temp_text_file = os.path.join(self.temp_save_path, 'temp_text.ttg_node')
        print ('temp_text_file:', self.temp_text_file)

        self.backup_temp_text_file = os.path.join(self.temp_save_path, 'backup_temp_text.ttg_node')
        print ('backup_temp_text_file:', self.backup_temp_text_file)

        self.temp_xml_path = os.path.join(self.temp_save_path, 'temp_text.xml')
        print ('temp_xml_path:', self.temp_xml_path, '\n')

        self.default_font_path = '/opt/Autodesk/font'

        self.font_size_anim = False
        self.italic_angle_anim = False
        self.kern_anim = False
        self.fill_transp_anim = False
        self.char_soft_anim = False
        self.translation_x_anim = False
        self.translation_y_anim = False
        self.separation_anim = False
        self.shadow_transp_anim = False
        self.shad_soft_anim = False
        self.all_shadows_translation_x_anim = False
        self.all_shadows_translation_y_anim = False

        # Init variables

        self.channel_anim = ''
        self.text_fx_setup = ''

        self.align_changed = False

        self.get_initial_text_fx()

        # Import text node setup xml

        tree = ET.ElementTree(file=self.temp_text_file)
        self.root = tree.getroot()

        # Check text fx for text layers

        if not self.get_value('FontName'):
            return message_box('Segment text fx contains no text layers')

        # Check number of fx on segment. If only one add additional fx
        # Needed for gap fx. Script deletes gap fx later. If no additional gap fx
        # is added, gap will be deleted.

        if len(self.selected_segment.effects) < 2:
            self.create_temp_timeline_fx = True
            print ('temp fx needed')
        else:
            self.create_temp_timeline_fx = False
            print ('temp fx not needed')

        # Get text fx values

        self.get_text_fx_values()

        self.new_font_path = self.font_path

        self.main_window()

    def get_initial_text_fx(self):
        # import shutil
        # import flame

        def load_text_setup():

            # Get text lines from saved timeline text fx

            get_text_values = open(self.temp_text_file, 'r')
            self.text_fx_setup = get_text_values.read()
            get_text_values.close()

        def insert_lines():

            # Insert missing <Extrap> and <Value> lines if x/y translation is set to 0

            load_text_setup()

            line = '<Extrap>constant</Extrap><Value>0</Value>'

            if '<Channel Name="translation/x"/><Channel' in self.text_fx_setup:

                translate_x_split = self.text_fx_setup.split('<Channel Name="translation/x"/>', 1)
                self.text_fx_setup = translate_x_split[0] + '<Channel Name="translation/x">' + line + '</Channel>' + translate_x_split[1]

            if '<Channel Name="translation/y"/><Channel' in self.text_fx_setup:

                translate_y_split = self.text_fx_setup.split('<Channel Name="translation/y"/>', 1)
                self.text_fx_setup = translate_y_split[0] + '<Channel Name="translation/y">' + line + '</Channel>' + translate_y_split[1]

        # Get playhead position on timeline

        track = self.selected_segment.parent
        version = track.parent
        self.seq = version.parent
        print ('seq name:', self.seq.name)

        self.playhead_position = self.seq.current_time.get_value()
        print ('playhead_position:', self.playhead_position, '\n')

        # Save text fx setup as xml
        # for seg in self.selected_seqment:

        for fx in self.selected_segment.effects:
            if fx.type == 'Text':

                #  Save text node to be modified

                fx.save_setup(self.temp_text_file)

                # Save backup text node to be restored if script cancelled

                fx.save_setup(self.backup_temp_text_file)

                # Insert missing lines if x/y translation is set to 0

                insert_lines()

                # Save out new text node and xml files

                text_node_file = open(self.temp_text_file, "w")
                text_node_file.write(self.text_fx_setup)
                text_node_file.close()

                xml_file = open(self.temp_xml_path, "w")
                xml_file.write(self.text_fx_setup)
                xml_file.close()

    def get_value(self, value):

        # Get value from saved xml file

        try:
            for elem in self.root.iter(value):
                # print elem.attrib
                # print elem.tag
                item_value = elem.text
            # print value, ':', elem.text
            return item_value
        except:
            return False

    def get_text_fx_values(self):
        import ast

        def get_line_value(line_name, value):
            # Get values from lines that contain multiple values
            # Such as Font Style of Colour Fill

            for elem in self.root.iter(line_name):
                elem_dict = elem.attrib
            # print '\n', 'elem_dict:', elem_dict

            result = elem_dict.get(value)

            return result

        def parse_xml(channel):

            # Reset channel anim to False as default

            self.channel_anim = False

            child_names = [child.tag for child in channel]
            # print 'child_names:', child_names

            child_objects = [child for child in channel]
            # print 'child_objects:', child_objects

            if 'KFrames' not in child_names:
                # print 'No Key Frames Found'
                self.channel_anim = False
                #try:
                    #value_index = child_names.index('Value')
                    #print value_index
                    #value = child_objects[value_index].text
                    #print 'Value:', value
                #except:
                   # value = 0

                for child in channel:
                    # print 'CHILD:', child
                    if 'Value' in str(child):
                        # print child.tag
                        # print child.text
                        value = child.text
                # print 'value:', value
                # print 'channel_name:', channel_name

            else:
                # print ('Key Frames Found')
                self.channel_anim = True
                kframe_index = child_names.index('KFrames')
                kframe_object = child_objects[kframe_index]
                # print kframe_object.tag

                # Only get first key frame value

                for key in kframe_object:
                    # print key.tag
                    key_names = [k.tag for k in key]
                    # print key_names
                    key_objects = [k for k in key]
                    key_value_index = key_names.index('Value')
                    value = key_objects[key_value_index].text
                    # print 'Value:', value
                    break

            # print 'value:', value

            result = float(value)

            # Convert float to int if float has .0 at end

            if str(result).endswith('.0'):
                result = int(result)

            return result

        # Get text file values

        self.font_path = self.get_value('FontName')
        if self.font_path == 'Discreet':
            self.font_path = '/opt/Autodesk/font/Discreet.font'

        # Extract font name from font path

        self.get_font_name(self.font_path)

        self.font_size = int(self.get_value('FontSize'))
        self.italic_angle = float(self.get_value('ItalicAngle'))
        self.kern = float(self.get_value('Kern'))
        self.alignment = (self.get_value('Justification')).rsplit('_', 1)[1]
        self.char_soft = float(self.get_value('CharSoftness'))
        self.shadow_softness = float(self.get_value('ShadowSoftness'))
        self.all_shadows_translation_x = float(self.get_value('RulerStaticTranslationX'))
        self.all_shadows_translation_y = float(self.get_value('RulerStaticTranslationY'))
        self.separation = 0

        self.drop_shadow = get_line_value('FontStyle', 'DropShadow')
        if self.drop_shadow == '1':
            self.drop_shadow = True
        else:
            self.drop_shadow = False
        # print 'drop_shadow:', self.drop_shadow, '\n'

        self.fill_transp = int(round(float(get_line_value('ColourFill', 'a'))))
        # print 'fill_transp:', self.fill_transp

        self.shadow_transp = int(round(float(get_line_value('ColourDrop', 'a'))))
        # print 'shadow_transp:', self.shadow_transp

        self.shadow_blur = ast.literal_eval(self.get_value('BlurOn'))
        # print 'shadow_blur:', self.shadow_blur

        self.shadow_blur_level = int(self.get_value('BlurLevel'))
        # print 'shadow_blur_level', self.shadow_blur_level, '\n'

        # Create lists for layer x/y offsets

        self.translation_x_list = []
        self.translation_y_list = []

        # Check for Channel/Key Frame values
        # Overwrite values from above if Channel/Key Frame values exist

        for channel in self.root.iter('Channel'):
            channel_name = str(channel.attrib).rsplit("'", 2)[1]
            # print 'channel_name:', channel_name

            # Get values from xml
            # If channel has animation set channel value to 0 - slider will act as offset

            if 'size' in channel_name:
                self.font_size = parse_xml(channel)
                if self.channel_anim:
                    self.font_size_anim = True
                    self.font_size = 0
                # print 'font_size:', self.font_size, '\n'

            elif 'italic' in channel_name:
                self.italic_angle = parse_xml(channel)
                if self.channel_anim:
                    self.italic_angle_anim = True
                    self.italic_angle = 0
                # print 'italic_angle:', self.italic_angle, '\n'

            elif 'kern' in channel_name:
                self.kern = parse_xml(channel)
                if self.channel_anim:
                    self.kern_anim = True
                    self.kern = 0
                # print 'kern:', self.kern, '\n'

            elif 'fill_colour/transp' in channel_name:
                self.fill_transp = parse_xml(channel)
                if self.channel_anim:
                    self.fill_transp_anim = True
                    self.fill_transp = 0
                # print 'fill_transp:', self.fill_transp, '\n'

            elif 'char_soft' in channel_name:
                self.char_soft = parse_xml(channel)
                if self.channel_anim:
                    self.char_soft_anim = True
                    self.char_soft = 0
                # print 'char_soft:', self.char_soft, '\n'

            elif channel_name == 'translation/x':
                self.translation_x = parse_xml(channel)
                self.translation_x_list.append(self.translation_x)
                #if self.channel_anim:
                    # print 'translation/x animated!'
                    #self.translation_x_anim = True
                # print 'translation_x:', self.translation_x, '\n'

            elif channel_name == 'translation/y':
                self.translation_y = parse_xml(channel)
                self.translation_y_list.append(self.translation_y)
                #if self.channel_anim:
                    #self.translation_y_anim = True
                # print 'translation_y:', self.translation_y, '\n'

            elif 'separation' in channel_name:
                self.separation = parse_xml(channel)
                #if self.channel_anim:
                    #self.separation_anim = True
                    #self.separation = 0
                # print 'separation:', self.separation, '\n'

            elif 'drop_colour/transp' in channel_name:
                self.shadow_transp = parse_xml(channel)
                #if self.channel_anim:
                    #self.shadow_transp_anim = True
                    #self.shadow_transp = 0
                # print 'shadow_transp:', self.shadow_transp, '\n'

            elif 'shad_soft' in channel_name:
                self.shad_soft = parse_xml(channel)
                #if self.channel_anim:
                    #self.shad_soft_anim = True
                    #self.shad_soft = 0
                # print 'shad_soft:', self.shad_soft, '\n'

            elif 'all_shadows/translation/x' in channel_name:
                self.all_shadows_translation_x = parse_xml(channel)
                #if self.channel_anim:
                    #self.all_shadows_translation_x_anim = True
                    #self.all_shadows_translation_x = 0
                # print 'all_shadows_translation_x:', self.all_shadows_translation_x, '\n'

            elif 'all_shadows/translation/y' in channel_name:
                self.all_shadows_translation_y = parse_xml(channel)

    def main_window(self):

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(1150, 375))
        self.window.setMaximumSize(QtCore.QSize(1150, 375))
        self.window.setWindowTitle('Adjust Timeline Text FX %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.font_label = FlameLabel('Font', 'background', self.window)
        self.position_offset_label = FlameLabel('Position Offset', 'background', self.window)
        self.shadow_label = FlameLabel('Shadow', 'background', self.window)

        self.font_path_label = FlameLabel('Font', 'normal', self.window)
        self.font_size_label = FlameLabel('Font Size', 'normal', self.window)
        self.italic_angle_label = FlameLabel('Italic Angle', 'normal', self.window)
        self.kern_label = FlameLabel('Kern', 'normal', self.window)
        self.align_label = FlameLabel('Align', 'normal', self.window)
        self.fill_trans_label = FlameLabel('Transparency', 'normal', self.window)
        self.softness_label = FlameLabel('Softness', 'normal', self.window)
        self.separation_label = FlameLabel('Separation', 'normal', self.window)
        self.offset_x_pos_label = FlameLabel('Offset X Pos', 'normal', self.window)
        self.offset_y_pos_label = FlameLabel('Offset Y Pos', 'normal', self.window)
        self.shadow_transp_label = FlameLabel('Transparency', 'normal', self.window)
        self.shadow_softness_label = FlameLabel('Softness', 'normal', self.window)
        self.shadow_x_pos_label = FlameLabel('X Pos', 'normal', self.window)
        self.shadow_y_pos_label = FlameLabel('Y Pos', 'normal', self.window)
        self.shadow_blur_label = FlameLabel('Blur', 'normal', self.window)

        # Font Line Edit

        self.font_path_entry = FlameClickableLineEdit(self.font, self.window)
        self.font_path_entry.clicked.connect(self.font_browse)
        self.font_path_entry.clicked.connect(partial(self.regen_text_fx, self.align_changed))

        # Sliders

        class FlameSliderLineEdit(QtWidgets.QLineEdit):
            from PySide2 import QtWidgets, QtCore, QtGui

            IntSpinBox = 0
            DoubleSpinBox = 1

            def __init__(self, spinbox_type, value, parent=None):
                from PySide2 import QtGui

                super(FlameSliderLineEdit, self).__init__(parent)

                self.setAlignment(QtCore.Qt.AlignCenter)
                self.setMinimumHeight(28)
                self.setMinimumWidth(110)
                self.setMaximumWidth(110)

                if spinbox_type == FlameSliderLineEdit.IntSpinBox:
                    self.setValidator(QtGui.QIntValidator(parent=self))
                else:
                    self.setValidator(QtGui.QDoubleValidator(parent=self))

                self.spinbox_type = spinbox_type
                self.min = None
                self.max = None
                self.steps = 1
                self.value_at_press = None
                self.pos_at_press = None

                self.setValue(value)
                self.setReadOnly(True)
                self.textChanged.connect(self.value_changed)
                self.setFocusPolicy(QtCore.Qt.NoFocus)
                self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                                   'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}'
                                   'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')
                self.clearFocus()

            def calculator(self):
                from PySide2 import QtCore, QtWidgets, QtGui
                from functools import partial

                def clear():
                    calc_lineedit.setText('')

                def button_press(key):

                    if self.clean_line == True:
                        calc_lineedit.setText('')

                    calc_lineedit.insert(key)

                    self.clean_line = False

                def plus_minus():

                    if calc_lineedit.text():
                        calc_lineedit.setText(str(float(calc_lineedit.text()) * -1))

                def add_sub(key):

                    if calc_lineedit.text() == '':
                        calc_lineedit.setText('0')

                    if '**' not in calc_lineedit.text():
                        try:
                            calc_num = eval(calc_lineedit.text().lstrip('0'))

                            calc_lineedit.setText(str(calc_num))

                            calc_num = float(calc_lineedit.text())

                            if calc_num == 0:
                                calc_num = 1
                            if key == 'add':
                                self.setValue(float(self.text()) + float(calc_num))
                            else:
                                self.setValue(float(self.text()) - float(calc_num))

                            self.clean_line = True
                        except:
                            pass

                def enter():

                    if self.clean_line == True:
                        return calc_window.close()

                    if calc_lineedit.text():
                        try:

                            # If only single number set slider value to that number

                            self.setValue(float(calc_lineedit.text()))
                        except:

                            # Do math

                            new_value = calculate_entry()
                            self.setValue(float(new_value))

                    close_calc()

                def equals():

                    if calc_lineedit.text() == '':
                        calc_lineedit.setText('0')

                    if calc_lineedit.text() != '0':

                        calc_line = calc_lineedit.text().lstrip('0')
                    else:
                        calc_line = calc_lineedit.text()

                    if '**' not in calc_lineedit.text():
                        try:
                            calc = eval(calc_line)
                        except:
                            calc = 0

                        calc_lineedit.setText(str(calc))
                    else:
                        calc_lineedit.setText('1')

                def calculate_entry():

                    calc_line = calc_lineedit.text().lstrip('0')
                    print ('calc_line:', calc_line)
                    if '**' not in calc_lineedit.text():
                        try:
                            if calc_line.startswith('+'):
                                calc = float(self.text()) + eval(calc_line[-1:])
                            elif calc_line.startswith('-'):
                                try:
                                    if float(calc_lineedit.text()):
                                        calc = float(self.text()) - eval(calc_line[-1:])
                                except:
                                    calc = eval(calc_line)
                            elif calc_line.startswith('*'):
                                calc = float(self.text()) * eval(calc_line[-1:])
                            elif calc_line.startswith('/'):
                                calc = float(self.text()) / eval(calc_line[-1:])
                            else:
                                calc = eval(calc_line)
                        except:
                            calc = 0
                    else:
                        calc = 1

                    calc_lineedit.setText(str(float(calc)))

                    return calc

                def close_calc():
                    calc_window.close()
                    self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"')

                def revert_color():
                    self.setStyleSheet('color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"')

                calc_version = '1.1'
                self.clean_line = False

                calc_window = QtWidgets.QWidget()
                calc_window.setMinimumSize(QtCore.QSize(210, 280))
                calc_window.setMaximumSize(QtCore.QSize(210, 280))
                calc_window.setWindowTitle('pyFlame Calc %s' % calc_version)
                calc_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
                calc_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                calc_window.destroyed.connect(revert_color)
                calc_window.move(QtGui.QCursor.pos().x() - 110, QtGui.QCursor.pos().y() - 290)
                calc_window.setStyleSheet('background-color: #282828')

                # Labels

                calc_label = QtWidgets.QLabel('Calculator', calc_window)
                calc_label.setAlignment(QtCore.Qt.AlignCenter)
                calc_label.setMinimumHeight(28)
                calc_label.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')

                #  LineEdit

                calc_lineedit = QtWidgets.QLineEdit('', calc_window)
                calc_lineedit.setMinimumHeight(28)
                calc_lineedit.setFocus()
                calc_lineedit.returnPressed.connect(enter)
                calc_lineedit.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}')

                # Limit characters that can be entered into lineedit

                regex = QtCore.QRegExp('[0-9_,=,/,*,+,\-,.]+')
                validator = QtGui.QRegExpValidator(regex)
                calc_lineedit.setValidator(validator)

                # Buttons

                def calc_null():
                    # For blank button - this does nothing
                    pass

                class FlameCalcButton(QtWidgets.QPushButton):
                    """
                    Custom Qt Flame Button Widget
                    """

                    def __init__(self, button_name, size_x, size_y, connect, parent, *args, **kwargs):
                        super(FlameCalcButton, self).__init__(*args, **kwargs)

                        self.setText(button_name)
                        self.setParent(parent)
                        self.setMinimumSize(size_x, size_y)
                        self.setMaximumSize(size_x, size_y)
                        self.setFocusPolicy(QtCore.Qt.NoFocus)
                        self.clicked.connect(connect)
                        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

                blank_btn = FlameCalcButton('', 40, 28, calc_null, calc_window)
                blank_btn.setDisabled(True)
                plus_minus_btn = FlameCalcButton('+/-', 40, 28, plus_minus, calc_window)
                plus_minus_btn.setStyleSheet('color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"')
                add_btn = FlameCalcButton('Add', 40, 28, (partial(add_sub, 'add')), calc_window)
                sub_btn = FlameCalcButton('Sub', 40, 28, (partial(add_sub, 'sub')), calc_window)

                #  --------------------------------------- #

                clear_btn = FlameCalcButton('C', 40, 28, clear, calc_window)
                equal_btn = FlameCalcButton('=', 40, 28, equals, calc_window)
                div_btn = FlameCalcButton('/', 40, 28, (partial(button_press, '/')), calc_window)
                mult_btn = FlameCalcButton('/', 40, 28, (partial(button_press, '*')), calc_window)

                #  --------------------------------------- #

                _7_btn = FlameCalcButton('7', 40, 28, (partial(button_press, '7')), calc_window)
                _8_btn = FlameCalcButton('8', 40, 28, (partial(button_press, '8')), calc_window)
                _9_btn = FlameCalcButton('9', 40, 28, (partial(button_press, '9')), calc_window)
                minus_btn = FlameCalcButton('-', 40, 28, (partial(button_press, '-')), calc_window)

                #  --------------------------------------- #

                _4_btn = FlameCalcButton('4', 40, 28, (partial(button_press, '4')), calc_window)
                _5_btn = FlameCalcButton('5', 40, 28, (partial(button_press, '5')), calc_window)
                _6_btn = FlameCalcButton('6', 40, 28, (partial(button_press, '6')), calc_window)
                plus_btn = FlameCalcButton('+', 40, 28, (partial(button_press, '+')), calc_window)

                #  --------------------------------------- #

                _1_btn = FlameCalcButton('1', 40, 28, (partial(button_press, '1')), calc_window)
                _2_btn = FlameCalcButton('2', 40, 28, (partial(button_press, '2')), calc_window)
                _3_btn = FlameCalcButton('3', 40, 28, (partial(button_press, '3')), calc_window)
                enter_btn = FlameCalcButton('Enter', 40, 61, enter, calc_window)

                #  --------------------------------------- #

                _0_btn = FlameCalcButton('0', 86, 28, (partial(button_press, '0')), calc_window)
                point_btn = FlameCalcButton('.', 40, 28, (partial(button_press, '.')), calc_window)

                gridbox = QtWidgets.QGridLayout()
                gridbox.setVerticalSpacing(5)
                gridbox.setHorizontalSpacing(5)

                gridbox.addWidget(calc_label, 0, 0, 1, 4)

                gridbox.addWidget(calc_lineedit, 1, 0, 1, 4)

                gridbox.addWidget(blank_btn, 2, 0)
                gridbox.addWidget(plus_minus_btn, 2, 1)
                gridbox.addWidget(add_btn, 2, 2)
                gridbox.addWidget(sub_btn, 2, 3)

                gridbox.addWidget(clear_btn, 3, 0)
                gridbox.addWidget(equal_btn, 3, 1)
                gridbox.addWidget(div_btn, 3, 2)
                gridbox.addWidget(mult_btn, 3, 3)

                gridbox.addWidget(_7_btn, 4, 0)
                gridbox.addWidget(_8_btn, 4, 1)
                gridbox.addWidget(_9_btn, 4, 2)
                gridbox.addWidget(minus_btn, 4, 3)

                gridbox.addWidget(_4_btn, 5, 0)
                gridbox.addWidget(_5_btn, 5, 1)
                gridbox.addWidget(_6_btn, 5, 2)
                gridbox.addWidget(plus_btn, 5, 3)

                gridbox.addWidget(_1_btn, 6, 0)
                gridbox.addWidget(_2_btn, 6, 1)
                gridbox.addWidget(_3_btn, 6, 2)
                gridbox.addWidget(enter_btn, 6, 3, 2, 1)

                gridbox.addWidget(_0_btn, 7, 0, 1, 2)
                gridbox.addWidget(point_btn, 7, 2)

                calc_window.setLayout(gridbox)

                calc_window.show()

            def value_changed(self):

                # If value is greater or less than min/max values set values to min/max

                if int(self.value()) < self.min:
                    self.setText(str(self.min))
                if int(self.value()) > self.max:
                    self.setText(str(self.max))

            def mousePressEvent(self, event):
                from PySide2 import QtGui

                if event.buttons() == QtCore.Qt.LeftButton:
                    self.value_at_press = self.value()
                    self.pos_at_press = event.pos()
                    self.setCursor(QtGui.QCursor(QtCore.Qt.SizeHorCursor))
                    self.setStyleSheet('QLineEdit {color: #d9d9d9; background-color: #474e58; selection-color: #d9d9d9; selection-background-color: #474e58; font: 14px "Discreet"}'
                                       'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}'
                                       'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

            def mouseReleaseEvent(self, event):
                from PySide2 import QtGui

                if event.button() == QtCore.Qt.LeftButton:

                    # Open calculator if button is released within 10 pixels of button click

                    if event.pos().x() in range((self.pos_at_press.x() - 10), (self.pos_at_press.x() + 10)) and event.pos().y() in range((self.pos_at_press.y() - 10), (self.pos_at_press.y() + 10)):
                        self.calculator()
                    else:
                        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #9a9a9a; selection-background-color: #373e47; font: 14px "Discreet"}'
                                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}'
                                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

                    self.value_at_press = None
                    self.pos_at_press = None
                    self.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
                    return

                super(FlameSliderLineEdit, self).mouseReleaseEvent(event)

            def mouseMoveEvent(self, event):

                if event.buttons() != QtCore.Qt.LeftButton:
                    return

                if self.pos_at_press is None:
                    return

                steps_mult = self.getStepsMultiplier(event)

                delta = event.pos().x() - self.pos_at_press.x()
                delta /= 5  # Make movement less sensitive.
                delta *= self.steps * steps_mult

                value = self.value_at_press + delta
                self.setValue(value)

                super(FlameSliderLineEdit, self).mouseMoveEvent(event)

            def getStepsMultiplier(self, event):

                steps_mult = 1

                if event.modifiers() == QtCore.Qt.CTRL:
                    steps_mult = 10
                elif event.modifiers() == QtCore.Qt.SHIFT:
                    steps_mult = 0.10

                return steps_mult

            def setMinimum(self, value):

                self.min = value

            def setMaximum(self, value):

                self.max = value

            def setSteps(self, steps):

                if self.spinbox_type == FlameSliderLineEdit.IntSpinBox:
                    self.steps = max(steps, 1)
                else:
                    self.steps = steps

            def value(self):

                if self.spinbox_type == FlameSliderLineEdit.IntSpinBox:
                    return int(self.text())
                else:
                    return float(self.text())

            def setValue(self, value):

                if self.min is not None:
                    value = max(value, self.min)

                if self.max is not None:
                    value = min(value, self.max)

                if self.spinbox_type == FlameSliderLineEdit.IntSpinBox:
                    self.setText(str(int(value)))
                else:
                    # Keep float values to two decimal places

                    value_string = str(float(value))

                    if len(value_string.rsplit('.', 1)[1]) < 2:
                        value_string = value_string + '0'

                    if len(value_string.rsplit('.', 1)[1]) > 2:
                        value_string = value_string[:-1]

                    self.setText(value_string)

        def slider(min_value, max_value, start_value, slider, lineedit):

            def set_slider():
                slider.setValue(float(lineedit.text()))
                justify_changed = False
                self.regen_text_fx(justify_changed)

            slider.setMaximumHeight(3)
            slider.setMinimumWidth(110)
            slider.setMaximumWidth(110)
            slider.setMinimum(min_value)
            slider.setMaximum(max_value)
            slider.setValue(start_value)
            slider.setStyleSheet('QSlider {color: #111111}'
                                 'QSlider::groove:horizontal {background-color: #111111}'
                                 'QSlider::handle:horizontal {background-color: #626467; width: 3px}')
            slider.setDisabled(True)

            lineedit.setMinimum(min_value)
            lineedit.setMaximum(max_value)
            lineedit.textChanged.connect(set_slider)
            slider.raise_()

        self.font_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        if self.font_size_anim:
            minimum_value = 0
        else:
            minimum_value = 1
        self.font_size_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, self.font_size, parent=self.window)
        slider(minimum_value, 2000, int(self.font_size), self.font_size_slider, self.font_size_lineedit)

        self.italic_angle_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.italic_angle_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, self.italic_angle, parent=self.window)
        slider(-60, 60, self.italic_angle, self.italic_angle_slider, self.italic_angle_lineedit)

        self.kern_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.kern_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, self.kern, parent=self.window)
        slider(-100, 100, self.kern, self.kern_slider, self.kern_lineedit)

        self.fill_transp_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.fill_transp_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, self.fill_transp, parent=self.window)
        slider(0, 100, self.fill_transp, self.fill_transp_slider, self.fill_transp_lineedit)

        self.softness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.softness_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.DoubleSpinBox, self.char_soft, parent=self.window)
        slider(-100, 100, self.char_soft, self.softness_slider, self.softness_lineedit)

        self.offset_x_pos_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.offset_x_pos_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.DoubleSpinBox, 0, parent=self.window)
        slider(-99999, 99999, 0, self.offset_x_pos_slider, self.offset_x_pos_lineedit)

        self.offset_y_pos_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.offset_y_pos_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.DoubleSpinBox, 0, parent=self.window)
        slider(-99999, 99999, 0, self.offset_y_pos_slider, self.offset_y_pos_lineedit)

        self.separation_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.separation_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, self.separation, parent=self.window)
        slider(0, 999, self.separation, self.separation_slider, self.separation_lineedit)

        self.shadow_transp_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.shadow_transp_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, self.shadow_transp, parent=self.window)
        slider(0, 100, self.shadow_transp, self.shadow_transp_slider, self.shadow_transp_lineedit)

        self.shadow_softness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.shadow_softness_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.DoubleSpinBox, self.shadow_softness, parent=self.window)
        slider(-100, 100, self.shadow_softness, self.shadow_softness_slider, self.shadow_softness_lineedit)

        self.shadow_x_pos_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.shadow_x_pos_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.DoubleSpinBox, self.all_shadows_translation_x, parent=self.window)
        slider(-9999, 9999, self.all_shadows_translation_x, self.shadow_x_pos_slider, self.shadow_x_pos_lineedit)

        self.shadow_y_pos_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.shadow_y_pos_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.DoubleSpinBox, self.all_shadows_translation_y, parent=self.window)
        slider(-9999, 9999, self.all_shadows_translation_y, self.shadow_y_pos_slider, self.shadow_y_pos_lineedit)

        self.shadow_blur_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.shadow_blur_lineedit = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, self.shadow_blur_level, parent=self.window)
        slider(0, 200, self.shadow_blur_level, self.shadow_blur_slider, self.shadow_blur_lineedit)

        # Shadow Pushbuttons

        def shadow_options():

            shadow_checked = self.shadow_pushbutton.isChecked()
            shadow_options_toggle(shadow_checked)
            self.regen_text_fx(self.align_changed)

        def shadow_blur_options():

            shadow_blur_checked = self.shadow_blur_pushbutton.isChecked()
            shadow_blur_options_toggle(shadow_blur_checked)
            self.regen_text_fx(self.align_changed)

        def shadow_options_toggle(shadow_checked):

            if shadow_checked:
                self.shadow_transp_label.setEnabled(True)
                self.shadow_transp_slider.setEnabled(True)
                self.shadow_transp_lineedit.setEnabled(True)
                self.shadow_softness_label.setEnabled(True)
                self.shadow_softness_slider.setEnabled(True)
                self.shadow_softness_lineedit.setEnabled(True)
                self.shadow_x_pos_label.setEnabled(True)
                self.shadow_x_pos_slider.setEnabled(True)
                self.shadow_x_pos_lineedit.setEnabled(True)
                self.shadow_y_pos_label.setEnabled(True)
                self.shadow_y_pos_slider.setEnabled(True)
                self.shadow_y_pos_lineedit.setEnabled(True)

                self.shadow_blur_pushbutton.setEnabled(True)
                if self.shadow_blur_pushbutton.isChecked():
                    self.shadow_blur_label.setEnabled(True)
                    self.shadow_blur_slider.setEnabled(True)
                    self.shadow_blur_lineedit.setEnabled(True)
            else:
                self.shadow_transp_label.setEnabled(False)
                self.shadow_transp_slider.setEnabled(False)
                self.shadow_transp_lineedit.setEnabled(False)
                self.shadow_softness_label.setEnabled(False)
                self.shadow_softness_slider.setEnabled(False)
                self.shadow_softness_lineedit.setEnabled(False)
                self.shadow_x_pos_label.setEnabled(False)
                self.shadow_x_pos_slider.setEnabled(False)
                self.shadow_x_pos_lineedit.setEnabled(False)
                self.shadow_y_pos_label.setEnabled(False)
                self.shadow_y_pos_slider.setEnabled(False)
                self.shadow_y_pos_lineedit.setEnabled(False)

                self.shadow_blur_pushbutton.setEnabled(False)
                self.shadow_blur_label.setEnabled(False)
                self.shadow_blur_slider.setEnabled(False)
                self.shadow_blur_lineedit.setEnabled(False)

        def shadow_blur_options_toggle(shadow_blur_checked):

            if shadow_blur_checked:
                self.shadow_blur_label.setEnabled(True)
                self.shadow_blur_slider.setEnabled(True)
                self.shadow_blur_lineedit.setEnabled(True)
            else:
                self.shadow_blur_label.setEnabled(False)
                self.shadow_blur_slider.setEnabled(False)
                self.shadow_blur_lineedit.setEnabled(False)

        self.shadow_pushbutton = FlamePushButton(' Shadow', self.window, self.drop_shadow, shadow_options)
        self.shadow_blur_pushbutton = FlamePushButton(' Shadow Blur', self.window, self.shadow_blur, shadow_blur_options)

        if self.shadow_pushbutton.isChecked():
            shadow_options_toggle(True)
        else:
            shadow_options_toggle(False)
            shadow_blur_options_toggle(False)

        if not self.shadow_blur_pushbutton.isChecked():
            self.shadow_blur_label.setEnabled(False)
            self.shadow_blur_lineedit.setEnabled(False)

        # Align Pushbutton Menu

        menu_options = ['Left', 'Centre', 'Right']
        self.align_push_btn = FlamePushButtonMenu(self.alignment, menu_options, self.regen_text_fx, self.window)

        # Buttons

        self.cancel_btn = FlameButton('Cancel', self.window, self.cancel)
        self.apply_btn = FlameButton('Apply', self.window, self.apply_text_fx)

        # -------------------------------------------------------------

        # Window Layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setHorizontalSpacing(10)
        gridbox.setMargin(20)

        gridbox.addWidget(self.font_label, 0, 0, 1, 6)

        gridbox.addWidget(self.font_path_label, 1, 0)
        gridbox.addWidget(self.font_path_entry, 1, 1, 1, 3)
        gridbox.addWidget(self.font_size_label, 1, 4)
        gridbox.addWidget(self.font_size_slider, 1, 5, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.font_size_lineedit, 1, 5)

        gridbox.addWidget(self.fill_trans_label, 2, 0)
        gridbox.addWidget(self.fill_transp_slider, 2, 1, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.fill_transp_lineedit, 2, 1)
        gridbox.addWidget(self.italic_angle_label, 2, 2)
        gridbox.addWidget(self.italic_angle_slider, 2, 3, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.italic_angle_lineedit, 2, 3)

        gridbox.addWidget(self.softness_label, 3, 0)
        gridbox.addWidget(self.softness_slider, 3, 1, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.softness_lineedit, 3, 1)
        gridbox.addWidget(self.kern_label, 3, 2)
        gridbox.addWidget(self.kern_slider, 3, 3, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.kern_lineedit, 3, 3)

        gridbox.addWidget(self.align_label, 4, 0)
        gridbox.addWidget(self.align_push_btn, 4, 1)
        gridbox.addWidget(self.separation_label, 4, 2)
        gridbox.addWidget(self.separation_slider, 4, 3, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.separation_lineedit, 4, 3)

        gridbox.addWidget(self.shadow_label, 0, 7, 1, 3)

        gridbox.addWidget(self.shadow_pushbutton, 1, 7)
        gridbox.addWidget(self.shadow_transp_label, 1, 8)
        gridbox.addWidget(self.shadow_transp_slider, 1, 9, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.shadow_transp_lineedit, 1, 9)
        gridbox.addWidget(self.shadow_softness_label, 2, 8)
        gridbox.addWidget(self.shadow_softness_slider, 2, 9, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.shadow_softness_lineedit, 2, 9)
        gridbox.addWidget(self.shadow_x_pos_label, 3, 8)
        gridbox.addWidget(self.shadow_x_pos_slider, 3, 9, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.shadow_x_pos_lineedit, 3, 9)
        gridbox.addWidget(self.shadow_y_pos_label, 4, 8)
        gridbox.addWidget(self.shadow_y_pos_slider, 4, 9, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.shadow_y_pos_lineedit, 4, 9)

        gridbox.addWidget(self.shadow_blur_pushbutton, 7, 7)
        gridbox.addWidget(self.shadow_blur_label, 7, 8)
        gridbox.addWidget(self.shadow_blur_slider, 7, 9, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.shadow_blur_lineedit, 7, 9)

        gridbox.setColumnMinimumWidth(6, 25)
        gridbox.setRowMinimumHeight(6, 28)

        gridbox.addWidget(self.position_offset_label, 7, 0, 1, 4)

        gridbox.addWidget(self.offset_x_pos_label, 8, 0)
        gridbox.addWidget(self.offset_x_pos_slider, 8, 1, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.offset_x_pos_lineedit, 8, 1)
        gridbox.addWidget(self.offset_y_pos_label, 8, 2)
        gridbox.addWidget(self.offset_y_pos_slider, 8, 3, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.offset_y_pos_lineedit, 8, 3)

        gridbox.setRowMinimumHeight(11, 28)

        gridbox.addWidget(self.cancel_btn, 12, 8)
        gridbox.addWidget(self.apply_btn, 12, 9)

        self.window.setLayout(gridbox)

        self.window.show()

        self.seq.current_time = self.playhead_position

    def font_browse(self):

        font_open_path = self.new_font_path.rsplit('/', 1)[0]

        file_browser = QtWidgets.QFileDialog()
        file_browser.setDirectory(font_open_path)
        file_browser.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        file_browser.setNameFilter('Fonts (*.afm *.font *.pfa *.ttf *.ttc *.otf *.dfont *.TMM)')
        file_browser.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if file_browser.exec_():
            self.new_font_path = file_browser.selectedFiles()[0]
            self.get_font_name(self.new_font_path)
            self.font_path_entry.setText(self.font)

    def get_font_name(self, path):

        self.font = path.rsplit('/', 1)[1]
        self.font = self.font.rsplit('.', 1)[0]

    def apply_text_fx(self):
        import shutil
        import flame

        print ('\n', '>' * 20, 'applying changes', '<' * 20, '\n')

        # Apply changes to all selected timeline segments with text fx

        self.selection_processed = 1

        for seg in self.selection:

            print ('\nProcessing Text FX %d of %d ...\n' % (self.selection_processed, self.selection_count))

            if isinstance(seg, flame.PySegment):
                for fx in seg.effects:
                    if fx.type == 'Text':
                        self.selection_processed += 1
                        fx.save_setup(self.temp_text_file)
                        self.save_text_fx(fx, seg, self.align_changed)

        print ('\n>>> Changes applied to all selected timeline seqments <<<\n')

        # Remove temp files

        shutil.rmtree(self.temp_save_path)

        print ('\n>>> Temp files removed <<<\n')

        # Restore playhead position

        self.seq.current_time = self.playhead_position

        self.window.close()

        print ('\ndone.\n')

    def regen_text_fx(self, align_changed):

        self.playhead_position = self.seq.current_time.get_value()
        print ('playhead_position:', self.playhead_position, '\n')

        if align_changed:
            self.align_changed = True

        for fx in self.selected_segment.effects:
            if fx.type == 'Text':
                self.save_text_fx(fx, self.selected_segment, align_changed)

        # Restore playhead position

        self.seq.current_time = self.playhead_position

        print ('-' * 30, '\n\n\n')

    def save_text_fx(self, fx, seg, align_changed):
        import xml.etree.cElementTree as ET
        import shutil
        import flame

        def get_ui_values():

            print ('\n', 'new text values', '\n------------------------------------------\n')

            # If channel has animation use spinbox value to offset current channel value
            # If channel has no animation use spinbox value as new channel value
            # Offset X and Y Position spinbox value is always used to offset current value

            if self.font_size_anim:
                self.new_font_size = str(int(self.font_size_lineedit.text()) + self.font_size)
            else:
                self.new_font_size = self.font_size_lineedit.text()
            print ('new_font_size:', self.new_font_size)

            if self.italic_angle_anim:
                self.new_italic_angle = str(int(self.italic_angle_lineedit.text()) + self.italic_angle)
            else:
                self.new_italic_angle = self.italic_angle_lineedit.text()
            print ('new_italic_angle:', self.new_italic_angle)

            if self.kern_anim:
                self.new_kern = str(int(self.kern_lineedit.text()) + self.kern)
            else:
                self.new_kern = self.kern_lineedit.text()
            print ('new_kern:', self.new_kern)

            self.new_align = 'Justify_' + self.align_push_btn.text()
            print ('new_align:', self.new_align)

            if self.fill_transp_anim:
                self.new_fill_transp = str(int(self.fill_transp_lineedit.text()) + self.fill_transp)
            else:
                self.new_fill_transp = str(self.fill_transp_lineedit.text())
            print ('new_fill_transp:', self.new_fill_transp)

            if self.char_soft_anim:
                self.new_char_soft = str(float(self.softness_lineedit.text()) + self.char_soft)
            else:
                self.new_char_soft = str(self.softness_lineedit.text())
            print ('new_char_soft:', self.new_char_soft)

            # self.new_offset_x = str(float(self.offset_x_pos_lineedit.text()) + self.translation_x)
            # print 'new_offset_x:', self.new_offset_x

            self.new_translation_x_list = [str(x + float(self.offset_x_pos_lineedit.text())) for x in self.translation_x_list]
            print ('new_translation_x_list:', self.new_translation_x_list)

            # self.new_offset_y = str(float(self.offset_y_pos_lineedit.text()) + self.translation_y)
            # print 'new_offset_y:', self.new_offset_y

            self.new_translation_y_list = [str(y + float(self.offset_y_pos_lineedit.text())) for y in self.translation_y_list]
            print ('new_translation_y_list:', self.new_translation_y_list)

            if self.separation_anim:
                self.new_separation = str(self.separation_lineedit.text() + self.separation)
            else:
                self.new_separation = str(self.separation_lineedit.text())
            print ('new_separation:', self.new_separation)

            # Shadow

            if self.shadow_pushbutton.isChecked():
                self.new_shadow = '1'
            else:
                self.new_shadow = '0'
            print ('new_shadow:', self.new_shadow)

            if self.shadow_transp_anim:
                self.new_shadow_transp = str(self.shadow_transp_lineedit.text() + self.shadow_transp)
            else:
                self.new_shadow_transp = str(self.shadow_transp_lineedit.text())
            print ('new_shadow_transp:', self.new_shadow_transp)

            if self.shad_soft_anim:
                self.new_shad_softness = str(float(self.shadow_softness_lineedit.text()) + self.shad_soft)
            else:
                self.new_shad_softness = str(self.shadow_softness_lineedit.text())
            print ('new_shad_softness:', self.new_shad_softness)

            if self.all_shadows_translation_x_anim:
                self.new_all_shadows_translation_x = str(float(self.shadow_x_pos_lineedit.text()) + self.all_shadows_translation_x)
            else:
                self.new_all_shadows_translation_x = str(self.shadow_x_pos_lineedit.text())
            print ('new_all_shadows_translation_x:', self.new_all_shadows_translation_x)

            if self.all_shadows_translation_y_anim:
                self.new_all_shadows_translation_y = str(float(self.shadow_y_pos_lineedit.text()) + self.all_shadows_translation_y)
            else:
                self.new_all_shadows_translation_y = str(self.shadow_y_pos_lineedit.text())
            print ('new_all_shadows_translation_y:', self.new_all_shadows_translation_y)

            # Shadow Blur

            self.new_shadow_blur = str(self.shadow_blur_pushbutton.isChecked())
            print ('new_shadow_blur:', self.new_shadow_blur)

            self.new_shadow_blur_level = str(self.shadow_blur_lineedit.text())
            print ('new_shadow_blur_level:', self.new_shadow_blur_level)

        def replace_value(elem_name, new_value):

            for elem in root.iter(elem_name):
                elem.text = new_value

        def replace_channel_value(channel_name, translation_list):

            # print 'channel name:', channel_name

            index = 0

            for elem in root.iter('Channel'):

                # Get list of channel values for desired channel

                child_objects = [child for child in elem if elem.get('Name') == channel_name]
                # print 'child_objects:', child_objects

                if child_objects:

                    # Get channel object for 'Value'

                    for child in child_objects:
                        # print child.tag
                        if child.tag == 'Value':
                            # print 'translation_list_value:', translation_list[index]
                            child.text = translation_list[index]
                    index += 1

        def replace_equals_value(name, value_name, new_value, *args):

            #  Use for fill transparency and turning dropshadows off and on

            for elem in root.iter(name):
                elem.set(value_name, new_value)

        self.get_text_fx_values()

        # Import text node setup

        tree = ET.ElementTree(file=self.temp_text_file)
        root = tree.getroot()

        # Get values from GUI

        get_ui_values()

        # Replace values in xml with values from UI

        if str(self.new_font_path) != str(self.font_path):
            replace_value('FontName', self.new_font_path)

        if int(self.new_font_size) != int(self.font_size):
            replace_value('FontSize', self.new_font_size)

        if int(self.new_italic_angle) != int(self.italic_angle):
            replace_value('ItalicAngle', self.new_italic_angle)

        if int(self.new_kern) != int(self.kern):
            replace_value('Kern', self.new_kern)

        if align_changed:
            replace_value('Justification', self.new_align)

        if int(self.new_fill_transp) != int(self.fill_transp):
            replace_equals_value('ColourFill', 'a', self.new_fill_transp)

        if float(self.new_char_soft) != float(self.char_soft):
            replace_value('CharSoftness', self.new_char_soft)

        if float(self.new_translation_x_list[0]) != float(self.translation_x_list[0]):
            replace_channel_value('translation/x', self.new_translation_x_list)

        if float(self.new_translation_y_list[0]) != float(self.translation_y_list[0]):
            replace_channel_value('translation/y', self.new_translation_y_list)

        if int(self.new_separation) != int(self.separation):
            replace_value('Separation', self.new_separation)

        # Shadow values #### NOT WORKING

        replace_equals_value('FontStyle', 'DropShadow', self.new_shadow)

        if int(self.new_shadow_transp) != int(self.shadow_transp):
            replace_equals_value('ColourDrop', 'a', self.new_shadow_transp)

        if float(self.new_shad_softness) != float(self.shadow_softness):
            replace_value('ShadowSoftness', self.new_shad_softness)

        if float(self.new_all_shadows_translation_x) != float(self.all_shadows_translation_x):
            replace_value('RulerStaticTranslationX', self.new_all_shadows_translation_x)

        if float(self.new_all_shadows_translation_y) != float(self.all_shadows_translation_y):
            replace_value('RulerStaticTranslationY', self.new_all_shadows_translation_y)

        # Shadow Blur

        replace_value('BlurOn', self.new_shadow_blur)

        if int(self.new_shadow_blur_level) != int(self.shadow_blur_level):
            replace_value('BlurLevel', self.new_shadow_blur_level)

        # Save new text node setup

        tree.write(self.temp_text_file)

        # Add aditional timeline fx to prevent timeline gap from being deleted

        if self.create_temp_timeline_fx:
            tempfx = seg.create_effect('blur')

        # Clear old text fx

        flame.delete(fx)
        fx = seg.create_effect('Text')

        # Delete temp timeline fx if one was added

        if self.create_temp_timeline_fx:
            flame.delete(tempfx)

        # Load temp text setup back to timeline

        fx.load_setup(self.temp_text_file)

        # Copy temp text file to xml
        # Only for testing

        shutil.copy(self.temp_text_file, self.temp_xml_path)

    def cancel(self):
        import shutil
        import flame

        print ('\n>>> Apply Text FX Cancelled - Restoring original text fx <<<\n')

        # Add aditional timeline fx to prevent timeline gap from being deleted

        if self.create_temp_timeline_fx:
            tempfx = self.selected_segment.create_effect('blur')

        # Restore original text fx

        for fx in self.selected_segment.effects:
            if fx.type == 'Text':
                flame.delete(fx)
                fx = self.selected_segment.create_effect('Text')
                fx.load_setup(self.backup_temp_text_file)

        # Delete temp timeline fx if one was added

        if self.create_temp_timeline_fx:
            flame.delete(tempfx)

        # Remove temp files

        shutil.rmtree(self.temp_save_path)

        # Close window

        self.window.close()

# -------------------------------------- #

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

def scope_segment(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PySegment):
            for fx in item.effects:
                if fx.type == 'Text':
                    return True
    return False

def get_timeline_custom_ui_actions():

    return [
        {
            'name': 'Text FX...',
            'actions': [
                {
                    'name': 'Adjust Text FX',
                    'isVisible': scope_segment,
                    'execute': AdjustFX,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
