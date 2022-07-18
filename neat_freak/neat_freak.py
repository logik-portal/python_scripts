'''
Script Name: Neat Freak
Script Version: 1.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 10.22.21
Update Date: 07.14.22

Custom Action Type: Batch

Description:

    Add Neat/Render/Write nodes to selected clips in batch or select multiple clips in the media panel to build a new
    batch group with Neat/Render/Write nodes for all selected clips.

    Only works with Neat v5

    Render/Write node outputs are set to match each clip(name, duration, timecode, fps, bit-depth).

    Write node options can be set in Setup.

    Menus:

        Setup:

            Flame Main Menu -> PyFlame -> Neat Freak Setup

        Batch:

            Right-click on any clip in batch -> Neat... -> Denoise Selected Clips

        Media Panel:

            Right-click on any clip in media panel -> Neat... -> Denoise Selected Clips

To install:

    Copy script into /opt/Autodesk/shared/python/pyFlame/neat_freak

Updates:

    v1.2 07.14.22

        Neat/render nodes can now be added to selected clips in batch.

        Write nodes can now be used instead of render nodes.

        Added Setup options for setting up Write nodes. Flame Main Menu -> PyFlame -> Neat Freak Setup

    v1.1 10.26.21

        Script now attempts to add shot name to render node
'''

from functools import partial
import xml.etree.ElementTree as ET
import os, ast
from PySide2 import QtWidgets, QtCore
from pyflame_lib_neat_freak import FlameMessageWindow, FlameWindow, FlameButton, FlameLabel, FlameLineEdit, FlameSlider, FlameTokenPushButton, FlamePushButton, FlamePushButtonMenu, pyflame_print, pyflame_file_browser, pyflame_get_shot_name

SCRIPT_NAME = 'Neat Freak'
SCRIPT_PATH = '/opt/Autodesk/shared/python/neat_freak'
VERSION = 'v1.2'

class NeatFreak():

    def __init__(self, selection):

        print('\n')
        print('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

        self.selection = selection

        # Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Load config file

        self.config()

        # Init Variables

        self.y_position = 0
        self.x_position = 0
        self.batch_duration = 1

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings from config XML

            for setting in root.iter('neat_freak_settings'):
                self.write_file_render_node_type = setting.find('write_file_render_node_type').text
                self.write_file_media_path = setting.find('write_file_media_path').text
                self.write_file_pattern = setting.find('write_file_pattern').text
                self.write_file_create_open_clip = ast.literal_eval(setting.find('write_file_create_open_clip').text)
                self.write_file_include_setup = ast.literal_eval(setting.find('write_file_include_setup').text)
                self.write_file_create_open_clip_value = setting.find('write_file_create_open_clip_value').text
                self.write_file_include_setup_value = setting.find('write_file_include_setup_value').text
                self.write_file_image_format = setting.find('write_file_image_format').text
                self.write_file_compression = setting.find('write_file_compression').text
                self.write_file_padding = setting.find('write_file_padding').text
                self.write_file_frame_index = setting.find('write_file_frame_index').text
                self.write_file_iteration_padding = setting.find('write_file_iteration_padding').text
                self.write_file_version_name = setting.find('write_file_version_name').text

            pyflame_print(SCRIPT_NAME, 'Config loaded.')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', f'Unable to create folder: {self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                pyflame_print(SCRIPT_NAME, 'Config file does not exist. Creating new config file.')

                config = """
<settings>
    <neat_freak_settings>
        <write_file_render_node_type>Render Node</write_file_render_node_type>
        <write_file_media_path>/opt/Autodesk</write_file_media_path>
        <write_file_pattern>&lt;Name&gt;</write_file_pattern>
        <write_file_create_open_clip>True</write_file_create_open_clip>
        <write_file_include_setup>True</write_file_include_setup>
        <write_file_create_open_clip_value>&lt;Name&gt;</write_file_create_open_clip_value>
        <write_file_include_setup_value>&lt;Name&gt;</write_file_include_setup_value>
        <write_file_image_format>Dpx 10-bit</write_file_image_format>
        <write_file_compression>Uncompressed</write_file_compression>
        <write_file_padding>4</write_file_padding>
        <write_file_frame_index>Use Start Frame</write_file_frame_index>
        <write_file_iteration_padding>2</write_file_iteration_padding>
        <write_file_version_name>v&lt;version&gt;</write_file_version_name>
    </neat_freak_settings>
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

    # ---------------------------------------- #

    def batch_neat_clips(self):
        import flame

        # Get current batch

        self.batch_group = flame.batch

        for clip in self.selection:
            self.x_position = clip.pos_x
            self.y_position = clip.pos_y

            self.get_clip_info(clip)

            self.create_batch_nodes(clip)

        self.batch_group.frame_all()

        pyflame_print(SCRIPT_NAME, 'Neat/Render nodes added.')

    def media_panel_neat_clips(self):
        import flame

        flame.go_to('Batch')

        # Create batch group

        batch_group = flame.batch.create_batch_group('Neat', reels=['plates'])

        plates_reel = batch_group.reels[0]

        batch_group.expanded = False

        # Copy all clips in selection to batch

        for clip in self.selection:
            flame.media_panel.copy(clip, plates_reel)

        # Create new selection of all clips in batch

        self.selection = flame.batch.nodes
        self.selection.reverse()

        # Repo clips in batch to spread them out

        clip_pos_y = 200

        for clip in self.selection:
                clip_pos_y += 200
                clip.pos_y = clip_pos_y

        # Set batch duration if duration of current clip is longer than last or Default

        for clip in flame.batch.nodes:
            if int(str(clip.duration)) > int(str(batch_group.duration)):
                batch_group.duration = int(str(clip.duration))

        # Run batch neat clips on all clips in batch

        self.batch_neat_clips()

        batch_group.frame_all()

    def get_clip_info(self, clip):
        import flame

        # Get clip values

        self.clip_name = str(clip.name)[1:-1]
        #print('clip_name: ', self.clip_name)

        self.clip_duration = clip.duration
        #print('clip_duration:', self.clip_duration)

        self.clip_frame_rate = clip.clip.frame_rate
        #print('clip_frame_rate:', self.clip_frame_rate)

        self.clip_timecode = clip.clip.start_time
        #print('clip_timecode:', self.clip_timecode)

        self.clip_shot_name = pyflame_get_shot_name(clip)

    def create_batch_nodes(self, clip):
        import flame

        def add_render_node():

            # Create render node

            self.render_node = self.batch_group.create_node('Render')
            self.render_node.range_end = self.clip_duration
            self.render_node.frame_rate = self.clip_frame_rate
            self.render_node.source_timecode = self.clip_timecode
            self.render_node.record_timecode = self.clip_timecode
            self.render_node.name = self.clip_name + '_dnz'

            if self.clip_shot_name:
                self.render_node.shot_name = self.clip_shot_name

        def add_write_node():

            # Create write node

            self.render_node = flame.batch.create_node('Write File')

            self.render_node.name = self.clip_name + '_dnz'

            self.render_node.media_path = self.write_file_media_path
            self.render_node.media_path_pattern = self.write_file_pattern
            self.render_node.create_clip = self.write_file_create_open_clip
            self.render_node.include_setup = self.write_file_include_setup
            self.render_node.create_clip_path = self.write_file_create_open_clip_value
            self.render_node.include_setup_path = self.write_file_include_setup_value

            image_format = self.write_file_image_format.split(' ', 1)[0]
            bit_depth = self.write_file_image_format.split(' ', 1)[1]

            self.render_node.file_type = image_format
            self.render_node.bit_depth = bit_depth

            if self.write_file_compression:
                self.render_node.compress = True
                self.render_node.compress_mode = self.write_file_compression
            if image_format == 'Jpeg':
                self.render_node.quality = 100

            self.render_node.frame_index_mode = self.write_file_frame_index
            self.render_node.frame_padding = int(self.write_file_padding)
            self.render_node.frame_rate = self.clip_frame_rate
            self.render_node.range_end = self.clip_duration
            self.render_node.source_timecode = self.clip_timecode
            self.render_node.record_timecode = self.clip_timecode
            self.render_node.shot_name = self.clip_shot_name
            self.render_node.range_start = int(str(flame.batch.start_frame))
            self.render_node.range_end = self.clip_duration

            if self.write_file_create_open_clip:
                self.render_node.version_mode = 'Follow Iteration'
                self.render_node.version_name = self.write_file_version_name
                self.render_node.version_padding = int(self.write_file_iteration_padding)

        # Add neat node

        self.neat_node = self.batch_group.create_node('OpenFX')
        self.neat_node.change_plugin('Reduce Noise v5')
        self.neat_node.pos_x = self.x_position + 300
        self.neat_node.pos_y = self.y_position - 25

        # Add Render Node or Write File Node

        if self.write_file_render_node_type == 'Render Node':
            add_render_node()
        else:
            add_write_node()

        self.render_node.pos_x = self.neat_node.pos_x + 300
        self.render_node.pos_y = self.y_position - 25

        # Connect nodes

        flame.batch.connect_nodes(clip, 'Default', self.neat_node, 'Default')
        flame.batch.connect_nodes(self.neat_node, 'Default', self.render_node, 'Default')

        self.y_position = self.y_position - 200

    # ---------------------------------------- #

    def write_node_setup(self):

        def save_config():

            if not self.write_file_media_path_lineedit.text():
                FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Write Node Setup: Enter Media Path.')
            elif not self.write_file_pattern_lineedit.text():
                FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Write Node Setup: Enter Pattern for image files.')
            elif not self.write_file_create_open_clip_lineedit.text():
                FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Write Node Setup: Enter Create Open Clip Naming.')
            elif not self.write_file_include_setup_lineedit.text():
                FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Write Node Setup: Enter Include Setup Naming.')
            elif not self.write_file_version_name_lineedit.text():
                FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Write Node Setup: Enter Version Naming.')
            else:

                # Save settings to config file

                xml_tree = ET.parse(self.config_xml)
                root = xml_tree.getroot()

                write_file_render_node_type = root.find('.//write_file_render_node_type')
                write_file_render_node_type.text = self.write_file_render_node_type_push_btn.text()

                write_file_media_path = root.find('.//write_file_media_path')
                write_file_media_path.text = self.write_file_media_path_lineedit.text()

                write_file_pattern = root.find('.//write_file_pattern')
                write_file_pattern.text = self.write_file_pattern_lineedit.text() + '.'

                write_file_create_open_clip = root.find('.//write_file_create_open_clip')
                write_file_create_open_clip.text = str(self.write_file_create_open_clip_btn.isChecked())

                write_file_include_setup = root.find('.//write_file_include_setup')
                write_file_include_setup.text = str(self.write_file_include_setup_btn.isChecked())

                write_file_create_open_clip_value = root.find('.//write_file_create_open_clip_value')
                write_file_create_open_clip_value.text = self.write_file_create_open_clip_lineedit.text()

                write_file_include_setup_value = root.find('.//write_file_include_setup_value')
                write_file_include_setup_value.text = self.write_file_include_setup_lineedit.text()

                write_file_image_format = root.find('.//write_file_image_format')
                write_file_image_format.text = self.write_file_image_format_push_btn.text()

                write_file_compression = root.find('.//write_file_compression')
                write_file_compression.text = self.write_file_compression_push_btn.text()

                write_file_padding = root.find('.//write_file_padding')
                write_file_padding.text = self.write_file_padding_slider.text()

                write_file_frame_index = root.find('.//write_file_frame_index')
                write_file_frame_index.text = self.write_file_frame_index_push_btn.text()

                write_file_iteration_padding = root.find('.//write_file_iteration_padding')
                write_file_iteration_padding.text = self.write_file_iteration_padding_slider.text()

                write_file_version_name = root.find('.//write_file_version_name')
                write_file_version_name.text = self.write_file_version_name_lineedit.text()

                xml_tree.write(self.config_xml)

                pyflame_print(SCRIPT_NAME, 'Config saved.')

                self.setup_window.close()

        def write_file_create_open_clip_btn_check():
            if self.write_file_create_open_clip_btn.isChecked():
                self.write_file_create_open_clip_lineedit.setDisabled(False)
                self.write_file_open_clip_token_btn.setDisabled(False)
            else:
                self.write_file_create_open_clip_lineedit.setDisabled(True)
                self.write_file_open_clip_token_btn.setDisabled(True)

        def write_file_include_setup_btn_check():
            if self.write_file_include_setup_btn.isChecked():
                self.write_file_include_setup_lineedit.setDisabled(False)
                self.write_file_include_setup_token_btn.setDisabled(False)
            else:
                self.write_file_include_setup_lineedit.setDisabled(True)
                self.write_file_include_setup_token_btn.setDisabled(True)

        def render_node_type_toggle():

            if self.write_file_render_node_type_push_btn.text() == 'Render Node':
                self.write_file_setup_label.setDisabled(True)
                self.write_file_media_path_label.setDisabled(True)
                self.write_file_pattern_label.setDisabled(True)
                self.write_file_type_label.setDisabled(True)
                self.write_file_frame_index_label.setDisabled(True)
                self.write_file_padding_label.setDisabled(True)
                self.write_file_compression_label.setDisabled(True)
                self.write_file_settings_label.setDisabled(True)
                self.write_file_iteration_padding_label.setDisabled(True)
                self.write_file_version_name_label.setDisabled(True)
                self.write_file_media_path_lineedit.setDisabled(True)
                self.write_file_pattern_lineedit.setDisabled(True)
                self.write_file_create_open_clip_lineedit.setDisabled(True)
                self.write_file_include_setup_lineedit.setDisabled(True)
                self.write_file_version_name_lineedit.setDisabled(True)
                self.write_file_padding_slider.setDisabled(True)
                self.write_file_iteration_padding_slider.setDisabled(True)
                self.write_file_image_format_push_btn.setDisabled(True)
                self.write_file_compression_push_btn.setDisabled(True)
                self.write_file_frame_index_push_btn.setDisabled(True)
                self.write_file_pattern_token_btn.setDisabled(True)
                self.write_file_browse_btn.setDisabled(True)
                self.write_file_include_setup_btn.setDisabled(True)
                self.write_file_create_open_clip_btn.setDisabled(True)
                self.write_file_open_clip_token_btn.setDisabled(True)
                self.write_file_include_setup_token_btn.setDisabled(True)
            else:
                self.write_file_setup_label.setDisabled(False)
                self.write_file_media_path_label.setDisabled(False)
                self.write_file_pattern_label.setDisabled(False)
                self.write_file_type_label.setDisabled(False)
                self.write_file_frame_index_label.setDisabled(False)
                self.write_file_padding_label.setDisabled(False)
                self.write_file_compression_label.setDisabled(False)
                self.write_file_settings_label.setDisabled(False)
                self.write_file_iteration_padding_label.setDisabled(False)
                self.write_file_version_name_label.setDisabled(False)
                self.write_file_media_path_lineedit.setDisabled(False)
                self.write_file_pattern_lineedit.setDisabled(False)
                self.write_file_create_open_clip_lineedit.setDisabled(False)
                self.write_file_include_setup_lineedit.setDisabled(False)
                self.write_file_version_name_lineedit.setDisabled(False)
                self.write_file_padding_slider.setDisabled(False)
                self.write_file_iteration_padding_slider.setDisabled(False)
                self.write_file_image_format_push_btn.setDisabled(False)
                self.write_file_compression_push_btn.setDisabled(False)
                self.write_file_frame_index_push_btn.setDisabled(False)
                self.write_file_pattern_token_btn.setDisabled(False)
                self.write_file_browse_btn.setDisabled(False)
                self.write_file_include_setup_btn.setDisabled(False)
                self.write_file_create_open_clip_btn.setDisabled(False)
                self.write_file_open_clip_token_btn.setDisabled(False)
                self.write_file_include_setup_token_btn.setDisabled(False)

                write_file_create_open_clip_btn_check()

                write_file_include_setup_btn_check()

        def media_path_browse():

            file_path = pyflame_file_browser('Select Directory', [''], self.write_file_media_path_lineedit.text(), select_directory=True, window_to_hide=[self.setup_window])

            if file_path:
                self.write_file_media_path_lineedit.setText(file_path)

        gridbox = QtWidgets.QGridLayout()
        self.setup_window = FlameWindow(f'{SCRIPT_NAME}: Render/Write Node Setup <small>{VERSION}', gridbox, 1000, 570)

        # Labels

        self.write_file_render_node_type_label = FlameLabel('Render Node Type')
        self.write_file_setup_label = FlameLabel('Write File Node Setup', label_type='underline')
        self.write_file_media_path_label = FlameLabel('Media Path')
        self.write_file_pattern_label = FlameLabel('Pattern')
        self.write_file_type_label = FlameLabel('File Type')
        self.write_file_frame_index_label = FlameLabel('Frame Index')
        self.write_file_padding_label = FlameLabel('Padding')
        self.write_file_compression_label = FlameLabel('Compression')
        self.write_file_settings_label = FlameLabel('Settings', label_type='underline')
        self.write_file_iteration_padding_label = FlameLabel('Iteration Padding')
        self.write_file_version_name_label = FlameLabel('Version Name')

        # LineEdits

        self.write_file_media_path_lineedit = FlameLineEdit(self.write_file_media_path)
        self.write_file_pattern_lineedit = FlameLineEdit(self.write_file_pattern)
        self.write_file_create_open_clip_lineedit = FlameLineEdit(self.write_file_create_open_clip_value)
        self.write_file_include_setup_lineedit = FlameLineEdit(self.write_file_include_setup_value)
        self.write_file_version_name_lineedit = FlameLineEdit(self.write_file_version_name, max_width=150)

        # Sliders

        self.write_file_padding_slider = FlameSlider(int(self.write_file_padding), 1, 20, value_is_float=False, slider_width=150)
        self.write_file_iteration_padding_slider = FlameSlider(int(self.write_file_iteration_padding), 1, 10, value_is_float=False, slider_width=150)

        # Image format pushbutton

        image_format_menu = QtWidgets.QMenu(self.setup_window)
        image_format_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#2d3744; border: none; font: 14px "Discreet"}'
                                        'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.write_file_image_format_push_btn = QtWidgets.QPushButton(self.write_file_image_format)
        self.write_file_image_format_push_btn.setMenu(image_format_menu)
        self.write_file_image_format_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.write_file_image_format_push_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.write_file_image_format_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.write_file_image_format_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #2d3744; border: none; font: 14px "Discreet"}'
                                                            'QPushButton:hover {border: 1px solid #5a5a5a}'
                                                            'QPushButton:disabled {color: #747474; background-color: #2d3744; border: none}'
                                                            'QPushButton::menu-indicator { image: none; }')

        # -------------------------------------------------------------

        def compression(file_format):

            def create_menu(option):
                self.write_file_compression_push_btn.setText(option)

            compression_menu.clear()
            # compression_list = []

            self.write_file_image_format_push_btn.setText(file_format)

            if 'Dpx' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'Pixspan', 'Packed']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Jpeg' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'OpenEXR' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'Scanline', 'Multi_Scanline', 'RLE', 'PXR24', 'PIZ', 'DWAB', 'DWAA', 'B44A', 'B44']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Png' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'Sgi' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'RLE']
                self.write_file_compression_push_btn.setEnabled(True)

            elif 'Targa' in file_format:
                self.write_file_compression_push_btn.setText('')
                compression_list = []
                self.write_file_compression_push_btn.setEnabled(False)

            elif 'Tiff' in file_format:
                self.write_file_compression_push_btn.setText('Uncompressed')
                compression_list = ['Uncompressed', 'RLE', 'LZW']
                self.write_file_compression_push_btn.setEnabled(True)

            for option in compression_list:
                compression_menu.addAction(option, partial(create_menu, option))

        image_format_menu.addAction('Dpx 8-bit', partial(compression, 'Dpx 8-bit'))
        image_format_menu.addAction('Dpx 10-bit', partial(compression, 'Dpx 10-bit'))
        image_format_menu.addAction('Dpx 12-bit', partial(compression, 'Dpx 12-bit'))
        image_format_menu.addAction('Dpx 16-bit', partial(compression, 'Dpx 16-bit'))
        image_format_menu.addAction('Jpeg 8-bit', partial(compression, 'Jpeg 8-bit'))
        image_format_menu.addAction('OpenEXR 16-bit fp', partial(compression, 'OpenEXR 16-bit fp'))
        image_format_menu.addAction('OpenEXR 32-bit fp', partial(compression, 'OpenEXR 32-bit fp'))
        image_format_menu.addAction('Png 8-bit', partial(compression, 'Png 8-bit'))
        image_format_menu.addAction('Png 16-bit', partial(compression, 'Png 16-bit'))
        image_format_menu.addAction('Sgi 8-bit', partial(compression, 'Sgi 8-bit'))
        image_format_menu.addAction('Sgi 16-bit', partial(compression, 'Sgi 16-bit'))
        image_format_menu.addAction('Targa 8-bit', partial(compression, 'Targa 8-bit'))
        image_format_menu.addAction('Tiff 8-bit', partial(compression, 'Tiff 8-bit'))
        image_format_menu.addAction('Tiff 16-bit', partial(compression, 'Tiff 16-bit'))

        compression_menu = QtWidgets.QMenu(self.setup_window)
        compression_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#2d3744; border: none; font: 14px "Discreet"}'
                                    'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.write_file_compression_push_btn = QtWidgets.QPushButton(self.write_file_compression)
        self.write_file_compression_push_btn.setMenu(compression_menu)
        self.write_file_compression_push_btn.setMinimumSize(QtCore.QSize(150, 28))
        self.write_file_compression_push_btn.setMaximumSize(QtCore.QSize(150, 28))
        self.write_file_compression_push_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.write_file_compression_push_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #2d3744; border: none; font: 14px "Discreet"}'
                                                        'QPushButton:hover {border: 1px solid #5a5a5a}'
                                                        'QPushButton:disabled {color: #747474; background-color: #2d3744; border: none}'
                                                        'QPushButton::menu-indicator { image: none; }')
        self.write_file_compression_push_btn.setText(self.write_file_compression)

        # Render Type Pushbutton Menu

        render_node_options = ['Render Node', 'Write File Node']
        self.write_file_render_node_type_push_btn = FlamePushButtonMenu(self.write_file_render_node_type, render_node_options, menu_action=render_node_type_toggle)

        # Frame Index Pushbutton Menu

        frame_index = ['Use Start Frame', 'Use Timecode']
        self.write_file_frame_index_push_btn = FlamePushButtonMenu(self.write_file_frame_index, frame_index)

        # Token Push Buttons

        write_file_token_dict = {'Batch Name': '<batch name>', 'Batch Iteration': '<batch iteration>', 'Iteration': '<iteration>',
                                'Project': '<project>', 'Project Nickname': '<project nickname>', 'Shot Name': '<shot name>', 'Clip Height': '<height>',
                                'Clip Width': '<width>', 'Clip Name': '<name>', }

        self.write_file_pattern_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_pattern_lineedit)
        self.write_file_open_clip_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_create_open_clip_lineedit)
        self.write_file_include_setup_token_btn = FlameTokenPushButton('Add Token', write_file_token_dict, self.write_file_include_setup_lineedit)

        # Pushbuttons



        self.write_file_create_open_clip_btn = FlamePushButton('Create Open Clip', self.write_file_create_open_clip)
        self.write_file_create_open_clip_btn.clicked.connect(write_file_create_open_clip_btn_check)
        write_file_create_open_clip_btn_check()

        self.write_file_include_setup_btn = FlamePushButton('Include Setup', self.write_file_include_setup)
        self.write_file_include_setup_btn.clicked.connect(write_file_include_setup_btn_check)
        write_file_include_setup_btn_check()

        # Buttons

        self.write_file_browse_btn = FlameButton('Browse', media_path_browse)
        self.write_file_save_btn = FlameButton('Save', save_config)
        self.write_file_cancel_btn = FlameButton('Cancel', self.setup_window.close)

        # ------------------------------------------------------------- #

        compression(self.write_file_image_format_push_btn.text())
        self.write_file_compression_push_btn.setText(self.write_file_compression)

        render_node_type_toggle()

        # UI Widget layout

        gridbox.setMargin(20)
        gridbox.setVerticalSpacing(5)
        gridbox.setHorizontalSpacing(5)
        gridbox.setRowStretch(3, 2)
        gridbox.setRowStretch(6, 2)
        gridbox.setRowStretch(9, 2)

        gridbox.addWidget(self.write_file_render_node_type_label, 0, 0)
        gridbox.addWidget(self.write_file_render_node_type_push_btn, 0, 1)

        gridbox.addWidget(self.write_file_setup_label, 1, 0, 1, 6)

        gridbox.addWidget(self.write_file_media_path_label, 2, 0)
        gridbox.addWidget(self.write_file_media_path_lineedit, 2, 1, 1, 4)
        gridbox.addWidget(self.write_file_browse_btn, 2, 5)

        gridbox.addWidget(self.write_file_pattern_label, 3, 0)
        gridbox.addWidget(self.write_file_pattern_lineedit, 3, 1, 1, 4)
        gridbox.addWidget(self.write_file_pattern_token_btn, 3, 5)

        gridbox.setRowMinimumHeight(4, 28)

        gridbox.addWidget(self.write_file_create_open_clip_btn, 5, 0)
        gridbox.addWidget(self.write_file_create_open_clip_lineedit, 5, 1, 1, 4)
        gridbox.addWidget(self.write_file_open_clip_token_btn, 5, 5)

        gridbox.addWidget(self.write_file_include_setup_btn, 6, 0)
        gridbox.addWidget(self.write_file_include_setup_lineedit, 6, 1, 1, 4)
        gridbox.addWidget(self.write_file_include_setup_token_btn, 6, 5)

        gridbox.setRowMinimumHeight(7, 28)

        gridbox.addWidget(self.write_file_settings_label, 8, 0, 1, 5)
        gridbox.addWidget(self.write_file_frame_index_label, 9, 0)
        gridbox.addWidget(self.write_file_frame_index_push_btn, 9, 1)
        gridbox.addWidget(self.write_file_type_label, 10, 0)
        gridbox.addWidget(self.write_file_image_format_push_btn, 10, 1)
        gridbox.addWidget(self.write_file_compression_label, 11, 0)
        gridbox.addWidget(self.write_file_compression_push_btn, 11, 1)

        gridbox.addWidget(self.write_file_padding_label, 9, 2)
        gridbox.addWidget(self.write_file_padding_slider, 9, 3)
        gridbox.addWidget(self.write_file_iteration_padding_label, 10, 2)
        gridbox.addWidget(self.write_file_iteration_padding_slider, 10, 3)
        gridbox.addWidget(self.write_file_version_name_label, 11, 2)
        gridbox.addWidget(self.write_file_version_name_lineedit, 11, 3)

        gridbox.addWidget(self.write_file_save_btn, 13, 5)
        gridbox.addWidget(self.write_file_cancel_btn, 14, 5)

        self.setup_window.show()

# ---------------------------------------- #

def neat_media_panel_clips(selection):

    script = NeatFreak(selection)
    script.media_panel_neat_clips()

def neat_batch_clips(selection):

    script = NeatFreak(selection)
    script.batch_neat_clips()

def setup(selection):

    script = NeatFreak(selection)
    script.write_node_setup()

# ---------------------------------------- #

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PyClip, flame.PyClipNode)):
            return True
    return False

# ---------------------------------------- #

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Neat Freak Setup',
                    'execute': setup,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Neat...',
            'actions': [
                {
                    'name': 'Denoise Selected Clips',
                    'isVisible': scope_clip,
                    'execute': neat_batch_clips,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Neat...',
            'actions': [
                {
                    'name': 'Denoise Selected Clips',
                    'isVisible': scope_clip,
                    'execute': neat_media_panel_clips,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
