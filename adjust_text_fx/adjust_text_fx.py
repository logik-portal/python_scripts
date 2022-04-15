'''
Script Name: Adjust Text FX
Script Version: 2.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 05.08.20
Update Date: 03.18.22

Custom Action Type: Timeline

Description:

    Interactively adjust timeline text fx settings that can then be applied to all selected timeline text fx

Menu:

    Right-click on selected clips on timeline with text fx -> Text FX... -> Adjust Text FX

To install:

    Copy script into /opt/Autodesk/shared/python/adjust_text_fx

Updates:

    v2.2 03.18.22

        Moved UI widgets to external file

    v2.1 02.25.22

        Updated UI for Flame 2023

    v2.0 05.22.21

        Updated to be compatible with Flame 2022/Python 3.7

    v1.4 02.17.21

        Multiple text layers can now be repositioned properly

        Fixes to slider calculator

    v1.3 02.06.21

        Misc slider calculator fixes

        Converted UI elements to classes
'''

import xml.etree.cElementTree as ET
from functools import partial
import os, ast, shutil
from PySide2 import QtWidgets
from flame_widgets_adjust_text_fx import FlameButton, FlameLabel, FlameClickableLineEdit, FlamePushButton, FlamePushButtonMenu, FlameSlider, FlameWindow, FlameMessageWindow

VERSION = 'v2.2'

SCRIPT_PATH = '/opt/Autodesk/shared/python/adjust_text_fx'

class AdjustFX(object):

    def __init__(self, selection):
        import xml.etree.cElementTree as ET

        print ('\n')
        print ('>' * 20, f'adjust text fx {VERSION}', '<' * 20, '\n')

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
            return FlameMessageWindow('Error', 'error', 'Segment text fx contains no text layers')

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
                item_value = elem.text
            return item_value
        except:
            return False

    def get_text_fx_values(self):

        def get_line_value(line_name, value):
            # Get values from lines that contain multiple values
            # Such as Font Style of Colour Fill

            for elem in self.root.iter(line_name):
                elem_dict = elem.attrib
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

    def regen_align(self):

        self.regen_text_fx(True)

    def main_window(self):

        gridbox = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'Adjust Text FX <small>{VERSION}', gridbox, 1150, 445)

        # Labels

        self.font_label = FlameLabel('Font', label_type='underline', label_width=110)
        self.position_offset_label = FlameLabel('Position Offset', label_type='underline',  label_width=110)
        self.shadow_label = FlameLabel('Shadow', label_type='underline',  label_width=110)

        self.font_path_label = FlameLabel('Font', label_width=110)
        self.font_size_label = FlameLabel('Font Size', label_width=110)
        self.italic_angle_label = FlameLabel('Italic Angle', label_width=110)
        self.kern_label = FlameLabel('Kern', label_width=110)
        self.align_label = FlameLabel('Align', label_width=110)
        self.fill_trans_label = FlameLabel('Transparency', label_width=110)
        self.softness_label = FlameLabel('Softness', label_width=110)
        self.separation_label = FlameLabel('Separation', label_width=110)
        self.offset_x_pos_label = FlameLabel('Offset X Pos', label_width=110)
        self.offset_y_pos_label = FlameLabel('Offset Y Pos', label_width=110)
        self.shadow_transp_label = FlameLabel('Transparency', label_width=110)
        self.shadow_softness_label = FlameLabel('Softness', label_width=110)
        self.shadow_x_pos_label = FlameLabel('X Pos', label_width=110)
        self.shadow_y_pos_label = FlameLabel('Y Pos', label_width=110)
        self.shadow_blur_label = FlameLabel('Blur', label_width=110)

        # Font Line Edit

        self.font_path_entry = FlameClickableLineEdit(self.font, self.font_browse)
        self.font_path_entry.clicked.connect(partial(self.regen_text_fx, self.align_changed))

        # Sliders

        if self.font_size_anim:
            minimum_value = 0
        else:
            minimum_value = 1

        self.font_size_slider = FlameSlider(int(self.font_size), minimum_value, 2000)
        self.font_size_slider.textChanged.connect(self.regen_text_fx)

        self.italic_angle_slider = FlameSlider(self.italic_angle, -60, 60)
        self.italic_angle_slider.textChanged.connect(self.regen_text_fx)

        self.kern_slider = FlameSlider(self.kern, -100, 100)
        self.kern_slider.textChanged.connect(self.regen_text_fx)

        self.fill_transp_slider = FlameSlider(self.fill_transp, 0, 100)
        self.fill_transp_slider.textChanged.connect(self.regen_text_fx)

        self.softness_slider = FlameSlider(self.char_soft, -100, 100, value_is_float=True)
        self.softness_slider.textChanged.connect(self.regen_text_fx)

        self.offset_x_pos_slider = FlameSlider(0, -99999, 99999, value_is_float=True)
        self.offset_x_pos_slider.textChanged.connect(self.regen_text_fx)

        self.offset_y_pos_slider = FlameSlider(0, -99999, 99999, value_is_float=True)
        self.offset_y_pos_slider.textChanged.connect(self.regen_text_fx)

        self.separation_slider = FlameSlider(self.separation, 0, 999)
        self.separation_slider.textChanged.connect(self.regen_text_fx)

        self.shadow_transp_slider = FlameSlider(self.shadow_transp, 0, 100)
        self.shadow_transp_slider.textChanged.connect(self.regen_text_fx)

        self.shadow_softness_slider = FlameSlider(self.shadow_softness, -100, 100, value_is_float=True)
        self.shadow_softness_slider.textChanged.connect(self.regen_text_fx)

        self.shadow_x_pos_slider = FlameSlider(self.all_shadows_translation_x, -9999, 9999, value_is_float=True)
        self.shadow_x_pos_slider.textChanged.connect(self.regen_text_fx)

        self.shadow_y_pos_slider = FlameSlider(self.all_shadows_translation_y, -9999, 9999, value_is_float=True)
        self.shadow_y_pos_slider.textChanged.connect(self.regen_text_fx)

        self.shadow_blur_slider = FlameSlider(self.shadow_blur_level, 0, 200)
        self.shadow_blur_slider.textChanged.connect(self.regen_text_fx)

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
                self.shadow_softness_label.setEnabled(True)
                self.shadow_softness_slider.setEnabled(True)
                self.shadow_x_pos_label.setEnabled(True)
                self.shadow_x_pos_slider.setEnabled(True)
                self.shadow_y_pos_label.setEnabled(True)
                self.shadow_y_pos_slider.setEnabled(True)

                self.shadow_blur_pushbutton.setEnabled(True)
                if self.shadow_blur_pushbutton.isChecked():
                    self.shadow_blur_label.setEnabled(True)
                    self.shadow_blur_slider.setEnabled(True)
            else:
                self.shadow_transp_label.setEnabled(False)
                self.shadow_transp_slider.setEnabled(False)
                self.shadow_softness_label.setEnabled(False)
                self.shadow_softness_slider.setEnabled(False)
                self.shadow_x_pos_label.setEnabled(False)
                self.shadow_x_pos_slider.setEnabled(False)
                self.shadow_y_pos_label.setEnabled(False)
                self.shadow_y_pos_slider.setEnabled(False)

                self.shadow_blur_pushbutton.setEnabled(False)
                self.shadow_blur_label.setEnabled(False)
                self.shadow_blur_slider.setEnabled(False)

        def shadow_blur_options_toggle(shadow_blur_checked):

            if shadow_blur_checked:
                self.shadow_blur_label.setEnabled(True)
                self.shadow_blur_slider.setEnabled(True)
            else:
                self.shadow_blur_label.setEnabled(False)
                self.shadow_blur_slider.setEnabled(False)

        self.shadow_pushbutton = FlamePushButton('Shadow', self.drop_shadow, button_width=110)
        self.shadow_pushbutton.clicked.connect(shadow_options)

        self.shadow_blur_pushbutton = FlamePushButton('Shadow Blur', self.shadow_blur, button_width=110)
        self.shadow_blur_pushbutton.clicked.connect(shadow_blur_options)

        if self.shadow_pushbutton.isChecked():
            shadow_options_toggle(True)
        else:
            shadow_options_toggle(False)
            shadow_blur_options_toggle(False)

        if not self.shadow_blur_pushbutton.isChecked():
            self.shadow_blur_label.setEnabled(False)
            self.shadow_blur_slider.setEnabled(False)

        # Align Pushbutton Menu

        align_menu_options = ['Left', 'Centre', 'Right']
        self.align_push_btn = FlamePushButtonMenu(self.alignment, align_menu_options, 110, menu_action=self.regen_align)

        # Buttons

        self.cancel_btn = FlameButton('Cancel', self.cancel, button_width=110)
        self.apply_btn = FlameButton('Apply', self.apply_text_fx, button_width=110)

        # -------------------------------------------------------------

        # Window Layout

        gridbox.setHorizontalSpacing(10)
        gridbox.setMargin(20)

        gridbox.addWidget(self.font_label, 0, 0, 1, 6)

        gridbox.addWidget(self.font_path_label, 1, 0)
        gridbox.addWidget(self.font_path_entry, 1, 1, 1, 3)
        gridbox.addWidget(self.font_size_label, 1, 4)
        gridbox.addWidget(self.font_size_slider, 1, 5)

        gridbox.addWidget(self.fill_trans_label, 2, 0)
        gridbox.addWidget(self.fill_transp_slider, 2, 1)
        gridbox.addWidget(self.italic_angle_label, 2, 2)
        gridbox.addWidget(self.italic_angle_slider, 2, 3)

        gridbox.addWidget(self.softness_label, 3, 0)
        gridbox.addWidget(self.softness_slider, 3, 1)
        gridbox.addWidget(self.kern_label, 3, 2)
        gridbox.addWidget(self.kern_slider, 3, 3)

        gridbox.addWidget(self.align_label, 4, 0)
        gridbox.addWidget(self.align_push_btn, 4, 1)
        gridbox.addWidget(self.separation_label, 4, 2)
        gridbox.addWidget(self.separation_slider, 4, 3)

        gridbox.addWidget(self.shadow_label, 0, 7, 1, 3)

        gridbox.addWidget(self.shadow_pushbutton, 1, 7)
        gridbox.addWidget(self.shadow_transp_label, 1, 8)
        gridbox.addWidget(self.shadow_transp_slider, 1, 9)
        gridbox.addWidget(self.shadow_softness_label, 2, 8)
        gridbox.addWidget(self.shadow_softness_slider, 2, 9)
        gridbox.addWidget(self.shadow_x_pos_label, 3, 8)
        gridbox.addWidget(self.shadow_x_pos_slider, 3, 9)
        gridbox.addWidget(self.shadow_y_pos_label, 4, 8)
        gridbox.addWidget(self.shadow_y_pos_slider, 4, 9)

        gridbox.addWidget(self.shadow_blur_pushbutton, 7, 7)
        gridbox.addWidget(self.shadow_blur_label, 7, 8)
        gridbox.addWidget(self.shadow_blur_slider, 7, 9)

        gridbox.setColumnMinimumWidth(6, 25)
        gridbox.setRowMinimumHeight(6, 28)

        gridbox.addWidget(self.position_offset_label, 7, 0, 1, 4)

        gridbox.addWidget(self.offset_x_pos_label, 8, 0)
        gridbox.addWidget(self.offset_x_pos_slider, 8, 1)
        gridbox.addWidget(self.offset_y_pos_label, 8, 2)
        gridbox.addWidget(self.offset_y_pos_slider, 8, 3)

        gridbox.setRowMinimumHeight(11, 28)

        gridbox.addWidget(self.cancel_btn, 12, 8)
        gridbox.addWidget(self.apply_btn, 12, 9)

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

        print ('\n--> Changes applied to all selected timeline seqments \n')

        # Remove temp files

        shutil.rmtree(self.temp_save_path)

        print ('\n--> Temp files removed \n')

        # Restore playhead position

        self.seq.current_time = self.playhead_position

        self.window.close()

        print ('\ndone.\n')

    def regen_text_fx(self, align_changed):

        self.playhead_position = self.seq.current_time.get_value()
        #print ('playhead_position:', self.playhead_position, '\n')

        if align_changed:
            self.align_changed = True

        for fx in self.selected_segment.effects:
            if fx.type == 'Text':
                self.save_text_fx(fx, self.selected_segment, align_changed)

        # Restore playhead position

        self.seq.current_time = self.playhead_position

        print ('-' * 30, '\n\n\n')

    def save_text_fx(self, fx, seg, align_changed):
        import flame

        def get_ui_values():

            print ('\nnew text values', '\n------------------------------------------\n')

            # If channel has animation use spinbox value to offset current channel value
            # If channel has no animation use spinbox value as new channel value
            # Offset X and Y Position spinbox value is always used to offset current value

            if self.font_size_anim:
                self.new_font_size = str(int(self.font_size_slider.text()) + self.font_size)
            else:
                self.new_font_size = self.font_size_slider.text()
            print ('new_font_size:', self.new_font_size)

            if self.italic_angle_anim:
                self.new_italic_angle = str(int(self.italic_angle_slider.text()) + self.italic_angle)
            else:
                self.new_italic_angle = self.italic_angle_slider.text()
            print ('new_italic_angle:', self.new_italic_angle)

            if self.kern_anim:
                self.new_kern = str(int(self.kern_slider.text()) + self.kern)
            else:
                self.new_kern = self.kern_slider.text()
            print ('new_kern:', self.new_kern)

            self.new_align = 'Justify_' + self.align_push_btn.text()
            print ('new_align:', self.new_align)

            if self.fill_transp_anim:
                self.new_fill_transp = str(int(self.fill_transp_slider.text()) + self.fill_transp)
            else:
                self.new_fill_transp = str(self.fill_transp_slider.text())
            print ('new_fill_transp:', self.new_fill_transp)

            if self.char_soft_anim:
                self.new_char_soft = str(float(self.softness_slider.text()) + self.char_soft)
            else:
                self.new_char_soft = str(self.softness_slider.text())
            print ('new_char_soft:', self.new_char_soft)

            # self.new_offset_x = str(float(self.offset_x_pos_lineedit.text()) + self.translation_x)
            # print 'new_offset_x:', self.new_offset_x

            self.new_translation_x_list = [str(x + float(self.offset_x_pos_slider.text())) for x in self.translation_x_list]
            print ('new_translation_x_list:', self.new_translation_x_list)

            # self.new_offset_y = str(float(self.offset_y_pos_lineedit.text()) + self.translation_y)
            # print 'new_offset_y:', self.new_offset_y

            self.new_translation_y_list = [str(y + float(self.offset_y_pos_slider.text())) for y in self.translation_y_list]
            print ('new_translation_y_list:', self.new_translation_y_list)

            if self.separation_anim:
                self.new_separation = str(self.separation_slider.text() + self.separation)
            else:
                self.new_separation = str(self.separation_slider.text())
            print ('new_separation:', self.new_separation)

            # Shadow

            if self.shadow_pushbutton.isChecked():
                self.new_shadow = '1'
            else:
                self.new_shadow = '0'
            print ('new_shadow:', self.new_shadow)

            if self.shadow_transp_anim:
                self.new_shadow_transp = str(self.shadow_transp_slider.text() + self.shadow_transp)
            else:
                self.new_shadow_transp = str(self.shadow_transp_slider.text())
            print ('new_shadow_transp:', self.new_shadow_transp)

            if self.shad_soft_anim:
                self.new_shad_softness = str(float(self.shadow_softness_slider.text()) + self.shad_soft)
            else:
                self.new_shad_softness = str(self.shadow_softness_slider.text())
            print ('new_shad_softness:', self.new_shad_softness)

            if self.all_shadows_translation_x_anim:
                self.new_all_shadows_translation_x = str(float(self.shadow_x_pos_slider.text()) + self.all_shadows_translation_x)
            else:
                self.new_all_shadows_translation_x = str(self.shadow_x_pos_slider.text())
            print ('new_all_shadows_translation_x:', self.new_all_shadows_translation_x)

            if self.all_shadows_translation_y_anim:
                self.new_all_shadows_translation_y = str(float(self.shadow_y_pos_slider.text()) + self.all_shadows_translation_y)
            else:
                self.new_all_shadows_translation_y = str(self.shadow_y_pos_slider.text())
            print ('new_all_shadows_translation_y:', self.new_all_shadows_translation_y)

            # Shadow Blur

            self.new_shadow_blur = str(self.shadow_blur_pushbutton.isChecked())
            print ('new_shadow_blur:', self.new_shadow_blur)

            self.new_shadow_blur_level = str(self.shadow_blur_slider.text())
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

        # Shadow values

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
        import flame

        print ('\n--> Apply Text FX Cancelled - Restoring original text fx \n')

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
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
