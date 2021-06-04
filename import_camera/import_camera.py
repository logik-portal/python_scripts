'''
Script Name: Import Camera
Script Version: 4.0
Flame Version: 2021
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 06.02.18
Update Date: 05.22.21

Custom Action Type: Batch

Description:

    Creates a new Action node with selected FBX or Alembic file loaded.
    Action camera switched to new FBX/Alembic camera

    Options to load with simple recomp or st map setup

    Right-click in batch or on selected node -> Import... -> Import FBX
    Right-click in batch or on selected node -> Import... -> Import Alembic

To install:

    Copy script into /opt/Autodesk/shared/python/import_camera

Updates:

v4.0 05.22.21

    Updated to be compatible with Flame 2022/Python 3.7

    Redistort map will automatically be found if in the same folder as undistort map

    Speed improvements

v3.6 02.21.21

    Updated UI

    Improved calculator

    Plate resize node in ST Map Setup now takes ratio from st map

v3.5 01.25.21

    Added ability to import Alembic(ABC) files

    Fixed UI font size for Linux

v3.4 11.05.20

    Updates to paths and description for Logik Portal

v3.3 10.18.20

    ST Map search no longer case sensitive

    If ST Map not found, file browser will open to manually select

v3.2 10.12.20

    Improved spinbox with calculator

v3.1 09.26.20

    Updated UI

    Import FBX with Patch Setup - Will import FBX into an Action node and also create
    other nodes to re-comp work done in FBX Action over original background

    Import FBX with ST map Setup - Will import FBX into an Action node and also build
    a undistort/redistort setup using the ST maps. ST maps must be in the same folder or sub-folder of
    FBX camera for this to work. ST Maps should also contain 'undistort' or 'redistort' in their file
    names.

v3.0 06.06.20

    Code re-write

    Add FBX Action under cursor position

    Fixed UI in Linux
'''

from __future__ import print_function
import os
from PySide2 import QtCore, QtWidgets

VERSION = 'v4.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/import_camera'

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

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget
    Options for normal, label with background color, and label with background color and outline
    """

    def __init__(self, label_name, label_type, parent, *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent)
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

class FlamePushButtonMenu(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Menu Widget
    """

    def __init__(self, button_name, menu_options, parent, *args, **kwargs):
        super(FlamePushButtonMenu, self).__init__(*args, **kwargs)
        from functools import partial

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        def create_menu(option):
            self.setText(option)

        pushbutton_menu = QtWidgets.QMenu(parent)
        pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        pushbutton_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        for option in menu_options:
            pushbutton_menu.addAction(option, partial(create_menu, option))

        self.setMenu(pushbutton_menu)

class FlamePushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Widget
    """

    def __init__(self, button_name, parent, checked, connect, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setMinimumSize(150, 28)
        self.setMaximumSize(150, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #424142, stop: .91 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #4f4f4f, stop: .91 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}')

# -------------------------------- #

class Import(object):

    def __init__(self, selection, filter_type):
        import flame
        import ast

        print ('\n', '>' * 20, 'import fbx %s' % VERSION, '<' * 20, '\n')

        self.filter_type = filter_type

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')
        self.batch_setup_path = os.path.join(SCRIPT_PATH, 'batch_setups')

        self.check_config_file()

        if selection != ():
            self.selection = selection[0]
            self.master_pos_x = self.selection.pos_x + 300
            self.master_pos_y = self.selection.pos_y
        else:
            self.selection = ''
            self.master_pos_x = flame.batch.cursor_position[0]
            self.master_pos_y = flame.batch.cursor_position[1]

        # get values from config file

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.camera_path = values[2]
        self.scene_scale = values[4]
        self.import_type = values[6]
        self.st_map_setup = ast.literal_eval(values[8])
        self.patch_setup = ast.literal_eval(values[10])

        get_config_values.close()

        if not os.path.isdir(self.camera_path):
            self.camera_path = self.camera_path.rsplit('/', 1)[0]

        self.undistort_map_path = ''
        self.redistort_map_path = ''

        # Create temp folder

        self.temp_folder = os.path.join(SCRIPT_PATH, 'temp')

        try:
            os.makedirs(self.temp_folder)
            print ('\n>>> temp folder created <<<\n')
        except:
            print ('temp folder already exists')

        self.camera_file_path = self.file_browse(self.camera_path, self.filter_type)

        if self.camera_file_path:
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

            config_text.insert(0, 'Setup values for pyFlame Import Camera script.')
            config_text.insert(1, 'Camera Path:')
            config_text.insert(2, '/')
            config_text.insert(3, 'Scene Scale:')
            config_text.insert(4, '10')
            config_text.insert(5, 'Import Type:')
            config_text.insert(6, 'Action Objects')
            config_text.insert(7, 'Add ST Map Setup')
            config_text.insert(8, 'False')
            config_text.insert(9, 'Add Patch Setup')
            config_text.insert(10, 'False')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

    # -------------------------------- #

    def create_camera_action(self):
        '''
        Create action and load FBX or ABC camera scene
        '''

        import flame

        def name_node(node_name, node_num=0):
            import flame

            # Create list of existing node names

            existing_node_names = [node.name for node in flame.batch.nodes]

            # New Node Name

            new_node_name = node_name + '_' + str(node_num)

            if new_node_name.endswith('0'):
                new_node_name = new_node_name[:-2]

            # If new_node_name already exists, add 1 to end of file name and try again

            if new_node_name in existing_node_names:
                node_num += 1
                return name_node(node_name, node_num)
            return new_node_name

        self.config_save()

        # Set Action node name

        self.camera_action_node_name = name_node('camera_action')

        # Create Action node

        self.camera_action = flame.batch.create_node('Action')
        self.camera_action.name = self.camera_action_node_name
        self.camera_action.collapsed = False

        # Load saved action setup for extra outputs

        self.camera_action.load_node_setup(os.path.join(SCRIPT_PATH, 'action_nodes/camera_action/camera_action.flare.action'))

        # Position Action node
        # If exisiting node selected position Action node next to node and connect to node
        # If nothing selected, position Action node under cursor

        if self.selection != '':
            self.camera_action.pos_x = self.master_pos_x
            self.camera_action.pos_y = self.master_pos_y - 70
            flame.batch.connect_nodes(self.selection, 'Default', self.camera_action, 'Default')
        else:
            self.camera_action.pos_x = self.master_pos_x
            self.camera_action.pos_y = self.master_pos_y

        print ('\n>>> action created <<<')

        # Import FBX camera

        if self.camera_file_path.endswith('.fbx'):
            if self.import_type == 'Action Objects':
                self.camera_action.import_fbx('%s' % self.camera_file_path, unit_to_pixels=int(self.scene_scale))
            else:
                self.camera_action.read_fbx('%s' % self.camera_file_path, unit_to_pixels=int(self.scene_scale))

        # Import Alembic camera

        else:
            if self.import_type == 'Action Objects':
                self.camera_action.import_abc('%s' % self.camera_file_path, unit_to_pixels=int(self.scene_scale))
            else:
                self.camera_action.read_abc('%s' % self.camera_file_path, unit_to_pixels=int(self.scene_scale))

        print ('\n>>> camera imported <<<\n')

    def create_patch_setup(self):
        '''
        Create setup for doing simple patching with 3d camera
        '''

        import flame

        def name_nodes(node_num=0):

            # Compare nodes to be crated against existing nodes. Remove 0 if first time

            for node in st_map_node_names:
                node = node + str(node_num)
                if node.endswith('0'):
                    node = node[:-1]

                # If node name not already existing, add as is to new_node_name list

                if node not in existing_node_names:
                    new_node_names.append(node)

                # If node name exists add 1 to node name and try again

                else:
                    node_num += 1
                    name_nodes(node_num)

            print ('new_node_names: ', new_node_names)

            return new_node_names

        self.config_save()

        self.create_camera_action()

        st_map_node_names = ['mux_in', 'action_in', 'action_out', 'recomp', 'regrain', 'divide']

        existing_node_names = [node.name for node in flame.batch.nodes]
        print ('existing_node_names:', existing_node_names)

        new_node_names = []

        new_node_names = name_nodes()

        # Create nodes
        # ------------

        plate_in_mux = flame.batch.create_node('MUX')
        plate_in_mux.name = new_node_names[0]

        action_in_mux = flame.batch.create_node('MUX')
        action_in_mux.name = new_node_names[1]

        action_out_mux = flame.batch.create_node('MUX')
        action_out_mux.name = new_node_names[2]

        divide_comp = flame.batch.create_node('Comp')
        divide_comp.name = new_node_names[5]
        divide_comp.flame_blend_mode = 'Divide'
        divide_comp.swap_inputs = True

        recomp_action = flame.batch.create_node('Action')
        recomp_action.collapsed = True

        recomp_action.name = new_node_names[3]
        recomp_action_media = recomp_action.add_media()

        regrain = flame.batch.create_node('Regrain')
        regrain.name = new_node_names[4]

        # Move nodes
        # ----------

        plate_in_mux.pos_x = self.master_pos_x
        plate_in_mux.pos_y = self.master_pos_y- 25

        action_in_mux.pos_x = plate_in_mux.pos_x + 450
        action_in_mux.pos_y = plate_in_mux.pos_y - 300

        self.camera_action.pos_x = action_in_mux.pos_x + 600
        self.camera_action.pos_y = action_in_mux.pos_y - 60

        action_out_mux.pos_x = self.camera_action.pos_x + 600
        action_out_mux.pos_y = self.camera_action.pos_y - 70

        divide_comp.pos_x = action_out_mux.pos_x + 220
        divide_comp.pos_y = action_out_mux.pos_y + 70

        recomp_action.pos_x = plate_in_mux.pos_x + 2150
        recomp_action.pos_y = plate_in_mux.pos_y + 20

        recomp_action_media.pos_x = recomp_action.pos_x - 30
        recomp_action_media.pos_y = recomp_action.pos_y - 440

        regrain.pos_x = recomp_action.pos_x + 300
        regrain.pos_y = recomp_action.pos_y

        # Load recomp action node setup

        recomp_action.load_node_setup(os.path.join(SCRIPT_PATH, 'action_nodes/patch_import/recomp.flare.action'))

        # Connect nodes
        # -------------

        if self.selection != '':
            flame.batch.connect_nodes(self.selection, 'Default', plate_in_mux, 'Input_0')

        flame.batch.connect_nodes(plate_in_mux, 'Result', action_in_mux, 'Input_0')
        flame.batch.connect_nodes(plate_in_mux, 'Result', recomp_action, 'Back')
        flame.batch.connect_nodes(action_in_mux, 'Result', self.camera_action, 'Back')
        flame.batch.connect_nodes(self.camera_action, 'Output [ Comp ]', action_out_mux, 'Input_0')
        flame.batch.connect_nodes(self.camera_action, 'Output [ Matte ]', action_out_mux, 'Matte_0')
        flame.batch.connect_nodes(recomp_action, 'Comp [ Comp ]', regrain, 'Front')
        flame.batch.connect_nodes(recomp_action, 'Comp [ Comp ]', regrain, 'Back')
        flame.batch.connect_nodes(recomp_action, 'Matte [ Matte ]', regrain, 'Matte')
        flame.batch.connect_nodes(action_out_mux, 'Result', divide_comp, 'Front')
        flame.batch.connect_nodes(action_out_mux, 'OutMatte', divide_comp, 'Back')
        flame.batch.connect_nodes(action_out_mux, 'OutMatte', recomp_action_media, 'Matte')
        flame.batch.connect_nodes(divide_comp, 'Result', recomp_action_media, 'Front')

        print ('\n>>> camera imported with patch setup <<<\n')

    def create_st_map_setup(self):
        '''
        Create setup with st map workflow with 3d camera. Recomps over original plate at end.
        '''
        import flame

        def get_st_maps():
            import flame
            import re

            # Browse for undistort map

            message_box('Select Undistort Map')
            self.undistort_map_path = self.file_browse(self.camera_file_path.rsplit('/', 1)[0], 'EXR (*.exr)')

            print ('undistort_map_path:', self.undistort_map_path, '\n')

            if not self.undistort_map_path:
                return

            self.config_save()

            # Search for undistort folder for redistort map

            for root, dirs, files in os.walk(self.undistort_map_path.rsplit('/', 1)[0]):
                for f in files:
                    if re.search('redistort', f, re.I):
                        self.redistort_map_path = os.path.join(root, f)
                        print ('\n>>> st redistort map found <<<\n')
                        break

            # If redistort map not found, browse for it

            if self.redistort_map_path == '':
                message_box('Select Redistort Map')
                self.redistort_map_path = self.file_browse(self.undistort_map_path, 'EXR (*.exr)')

            print ('redistort_map_path:', self.redistort_map_path, '\n')

            if not self.redistort_map_path:
                return

            # create st maps schematic reel if it doesn't exist

            if 'st_maps' not in [reel.name for reel in flame.batch.reels]:
                flame.batch.create_reel('st_maps')

            # import maps

            self.redistort_map = flame.batch.import_clip(self.redistort_map_path, 'st_maps')
            self.undistort_map = flame.batch.import_clip(self.undistort_map_path, 'st_maps')

            print ('\n>>> st maps imported <<<\n')
            return True

        def build_st_map_setup():

            def name_nodes(node_num=0):

                # Compare nodes to be crated against existing nodes. Remove 0 if first time

                for node in st_map_node_names:
                    node = node + str(node_num)
                    if node.endswith('0'):
                        node = node[:-1]

                    # If node name not already existing, add as is to newNodeName list

                    if node not in existing_node_names:
                        new_node_names.append(node)

                    # If node name exists add 1 to node name and try again

                    else:
                        node_num += 1
                        name_nodes(node_num)

                print ('new_node_names: ', new_node_names)

                return new_node_names

            def edit_resize_node():

                def get_st_map_res():
                    import re

                    # Get resolution of st map clips for resize node

                    st_map_reel = [reel for reel in flame.batch.reels if reel.name == 'st_maps'][0]

                    clip = [clip for clip in st_map_reel.clips if re.search('undistort', str(clip.name), re.I)][0]

                    undistort_clip_width = str(clip.width)
                    undistort_clip_height = str(clip.height)
                    undistort_clip_ratio = str(round(float(clip.ratio), 3))
                    print ('undistort_clip_width:', undistort_clip_width)
                    print ('undistort_clip_height:', undistort_clip_height)
                    print ('undistort_clip_ratio:', undistort_clip_ratio)

                    return undistort_clip_width, undistort_clip_height, undistort_clip_ratio

                def save_resize_node():

                    # Save resize node

                    resize_node_name = str(undistort_plate_resize.name)[1:-1]
                    save_resize_path = os.path.join(self.temp_folder, resize_node_name)
                    print ('save_resize_path:', save_resize_path)

                    undistort_plate_resize.save_node_setup(save_resize_path)

                    # Set Resize path and filename variable

                    resize_file_name = save_resize_path + '.resize_node'
                    print ('resize_file_name:', resize_file_name)

                    print ('\n>>> resize node saved <<<\n')

                    return resize_file_name

                # Get resolution of undistort plate

                undistort_clip_width, undistort_clip_height, undistort_clip_ratio = get_st_map_res()

                # Save plate_resize node

                resize_file_name = save_resize_node()

                # Edit resize node to match resolution of ST Map
                # ----------------------------------------------

                # Load resize node

                edit_resize = open(resize_file_name, 'r')
                contents = edit_resize.readlines()
                edit_resize.close()

                # Convert to string

                contents = str(contents)

                # Change destination width to match st map width

                dest_width_split01 = contents.split('<DestinationWidth>', 1)[0]
                dest_width_split02 = contents.split('</DestinationWidth>', 1)[1]

                new_dest_width = '<DestinationWidth>' + undistort_clip_width + '</DestinationWidth>'

                contents = dest_width_split01 + new_dest_width + dest_width_split02

                # Change destination height to match st map height

                dest_height_split01 = contents.split('<DestinationHeight>', 1)[0]
                dest_height_split02 = contents.split('</DestinationHeight>', 1)[1]

                new_dest_height = '<DestinationHeight>' + undistort_clip_height + '</DestinationHeight>'

                contents = dest_height_split01 + new_dest_height + dest_height_split02

                # Change resize to fill

                resize_type_split01 = contents.split('<ResizeType>', 1)[0]
                resize_type_split02 = contents.split('</ResizeType>', 1)[1]

                new_resize_type = '<ResizeType>3</ResizeType>'

                contents = resize_type_split01 + new_resize_type + resize_type_split02

                # Change ratio to match st map ratio

                ratio_split01 = contents.split('<DestinationAspect>', 1)[0]
                ratio_split02 = contents.split('</DestinationAspect>', 1)[1]

                new_ratio = '<DestinationAspect>%s</DestinationAspect>' % undistort_clip_ratio

                contents = ratio_split01 + new_ratio + ratio_split02

                # Convert contents back to list

                contents = contents[2:-2]
                contents = [contents]

                # ----------------------------------------------

                # Save edited resize node

                edit_resize = open(resize_file_name, 'w')
                contents = ''.join(contents)
                edit_resize.write(contents)
                edit_resize.close()

                # Reload resize node file

                undistort_plate_resize.load_node_setup(resize_file_name)

                # Connect resize node after edit
                # Resize can only be edited without being connected

                flame.batch.connect_nodes(undistort_plate_resize, 'Result', plate_undistort_action, 'Back')
                flame.batch.connect_nodes(undistort_plate_resize, 'Result', plate_resize_media, 'Front')
                flame.batch.connect_nodes(plate_in_mux, 'Result', undistort_plate_resize, 'Front')

                print ('\n>>> resize node set to st map resolution <<<\n')

            # Set node names
            # --------------

            st_map_node_names = ['plate_undistort', 'plate_resize', 'st_map_undistort_in', 'comp_redistort_in', 'comp_redistort', 'st_map_redistort_in', 'mux_in', 'divide', 'regrain']

            existing_node_names = [node.name for node in flame.batch.nodes]
            print ('existing_node_names:', existing_node_names)

            new_node_names = []

            new_node_names = name_nodes()

            # Create nodes
            # ------------

            # Create undistort action node

            plate_undistort_action = flame.batch.create_node('Action')
            plate_undistort_action.name = new_node_names[0]
            plate_undistort_action.collapsed = True

            plate_undistort_action.pos_x = self.master_pos_x + 1400
            plate_undistort_action.pos_y = self.master_pos_y - 400

            # Create undistort action media layer 1

            plate_resize_media = plate_undistort_action.add_media()
            plate_resize_media.pos_x = plate_undistort_action.pos_x - 40
            plate_resize_media.pos_y = plate_undistort_action.pos_y - 200

            # Create UV Map

            plate_undistort_uv = plate_undistort_action.create_node('UV Map')

            # Create undistort action media layer 2

            undistort_in_media = plate_undistort_action.add_media()
            undistort_in_media.pos_x = plate_undistort_action.pos_x - 40
            undistort_in_media.pos_y = plate_undistort_action.pos_y - 415

            # Assign UV Map to media 2

            plate_undistort_uv.assign_media(2)

            # undistortAction nodes to delete

            axis_to_delete01 = plate_undistort_action.get_node('axis3')
            image_to_delete01 = plate_undistort_action.get_node('surface2')
            flame.delete(axis_to_delete01)
            flame.delete(image_to_delete01)

            # Create undistort plate resize node

            undistort_plate_resize = flame.batch.create_node('Resize')
            undistort_plate_resize.name = new_node_names[1]
            undistort_plate_resize.pos_x = plate_undistort_action.pos_x - 600
            undistort_plate_resize.pos_y = self.master_pos_y -410

            # Create Plate IN mux

            plate_in_mux = flame.batch.create_node('MUX')
            plate_in_mux.name = new_node_names[6]
            plate_in_mux.pos_x = undistort_plate_resize.pos_x - 600
            plate_in_mux.pos_y = self.master_pos_y - 25

            # Create mux for stmap undistort input

            undistort_st_map_in_mux = flame.batch.create_node('MUX')
            undistort_st_map_in_mux.name = new_node_names[2]
            undistort_st_map_in_mux.pos_x = plate_undistort_action.pos_x - 600
            undistort_st_map_in_mux.pos_y = undistort_plate_resize.pos_y - 400

            # Create mux for plate redistort input

            comp_redistort_in_mux = flame.batch.create_node('MUX')
            comp_redistort_in_mux.name = new_node_names[3]
            comp_redistort_in_mux.pos_x = plate_undistort_action.pos_x + 2000
            comp_redistort_in_mux.pos_y = plate_undistort_action.pos_y - 145

            # Create redistort action node

            recomp_action = flame.batch.create_node('Action')
            recomp_action.name = new_node_names[4]
            recomp_action.collapsed = True
            ####recomp_action.load_node_setup(os.path.join(SCRIPT_PATH, 'action_nodes/st_map_import/comp_redistort.flare.action'))
            #### save_action_path, action_filename = self.save_action_node(recomp_action, new_node_names[4])

            recomp_action.pos_x = comp_redistort_in_mux.pos_x + 600
            recomp_action.pos_y = self.master_pos_y - 15

            # Create redistort action media layer 1

            comp_redistort_in_media = recomp_action.add_media()
            comp_redistort_in_media.pos_x = recomp_action.pos_x - 40
            comp_redistort_in_media.pos_y = recomp_action.pos_y - 525

            # Create UV Map

            comp_redistort_uv = recomp_action.create_node('UV Map')

            # Create redistort action media layer 2

            stmap_redistort_in_media = recomp_action.add_media()
            stmap_redistort_in_media.pos_x = recomp_action.pos_x - 40
            stmap_redistort_in_media.pos_y = recomp_action.pos_y - 940

            # Assign UV Map to media 2

            comp_redistort_uv.assign_media(2)

            # redistortAction nodes to delete

            axis_to_delete02 = recomp_action.get_node('axis3')
            image_to_delete02 = recomp_action.get_node('surface2')
            flame.delete(axis_to_delete02)
            flame.delete(image_to_delete02)

            # Create mux for redistort stmap input

            redistort_st_map_in_mux = flame.batch.create_node('MUX')
            redistort_st_map_in_mux.name = new_node_names[5]
            redistort_st_map_in_mux.pos_x = comp_redistort_in_mux.pos_x
            redistort_st_map_in_mux.pos_y = comp_redistort_in_mux.pos_y - 400

            # Create comp divide node

            divide_comp = flame.batch.create_node('Comp')
            divide_comp.name = new_node_names[7]
            divide_comp.flame_blend_mode = 'Divide'
            divide_comp.swap_inputs = True
            divide_comp.pos_x = comp_redistort_in_mux.pos_x + 300
            divide_comp.pos_y = comp_redistort_in_mux.pos_y + 150

            # Create regrain node

            regrain_node = flame.batch.create_node('Regrain')
            regrain_node.name = new_node_names[8]
            regrain_node.pos_x = recomp_action.pos_x + 300
            regrain_node.pos_y = recomp_action.pos_y

            # Move nodes
            # ----------

            self.undistort_map.pos_x = undistort_st_map_in_mux.pos_x - 400
            self.undistort_map.pos_y = undistort_st_map_in_mux.pos_y + 30

            self.redistort_map.pos_x = redistort_st_map_in_mux.pos_x - 400
            self.redistort_map.pos_y = redistort_st_map_in_mux.pos_y + 30

            self.camera_action.pos_x = plate_undistort_action.pos_x + 1000
            self.camera_action.pos_y = plate_undistort_action.pos_y - 80

            # Edit recomp action node
            # -----------------------

            recomp_action.load_node_setup(os.path.join(SCRIPT_PATH, 'action_nodes/st_map_import/comp_redistort.flare.action'))

            # self.edit_recomp_action_node(recomp_action, save_action_path, action_filename)

            # Connect nodes
            #--------------

            if self.selection != '':
                flame.batch.connect_nodes(self.selection, 'Default', plate_in_mux, 'Input_0')

            flame.batch.connect_nodes(undistort_st_map_in_mux, 'Result', undistort_in_media, 'Front')
            flame.batch.connect_nodes(plate_undistort_action, 'output1 [ Comp ]', self.camera_action, 'Back')
            flame.batch.connect_nodes(self.camera_action, 'Output [ Comp ]', comp_redistort_in_mux, 'Input_0')
            flame.batch.connect_nodes(self.camera_action, 'Output [ Matte ]', comp_redistort_in_mux, 'Matte_0')
            flame.batch.connect_nodes(comp_redistort_in_mux, 'Result', divide_comp, 'Front')
            flame.batch.connect_nodes(comp_redistort_in_mux, 'OutMatte', divide_comp, 'Back')
            flame.batch.connect_nodes(divide_comp, 'Result', comp_redistort_in_media, 'Front')
            flame.batch.connect_nodes(comp_redistort_in_mux, 'OutMatte', comp_redistort_in_media, 'Matte')
            flame.batch.connect_nodes(redistort_st_map_in_mux, 'Result', stmap_redistort_in_media, 'Front')
            flame.batch.connect_nodes(self.undistort_map, 'Default', undistort_st_map_in_mux, 'Input_0')
            flame.batch.connect_nodes(self.redistort_map, 'Default', redistort_st_map_in_mux, 'Input_0')
            flame.batch.connect_nodes(plate_in_mux, 'Result', recomp_action, 'Back')
            flame.batch.connect_nodes(recomp_action, 'Comp [ Comp ]', regrain_node, 'Front')
            flame.batch.connect_nodes(recomp_action, 'Comp [ Comp ]', regrain_node, 'Back')
            flame.batch.connect_nodes(recomp_action, 'Matte [ Matte ]', regrain_node, 'Matte')

            # Set resize node to match ST Map resolution
            # ------------------------------------------

            edit_resize_node()

            # Edit plate_undistort action node to turn back off
            # -------------------------------------------------

            ###### edit_plate_undistort_action_node()

            print ('\n>>> camera imported with st map setup <<<\n')

        # Load st maps

        st_maps_loaded = get_st_maps()

        if st_maps_loaded:
            self.create_camera_action()
            build_st_map_setup()
        else:
            print ('\n>>> import cancelled <<<\n')

    def config_save(self):

        #  Save settings

        self.scene_scale = self.scale_spinbox.value()
        self.import_type = self.import_type_btn.text()

        print ('scene_scale:', self.scene_scale)
        print ('import_type:', self.import_type)

        config_text = []

        config_text.insert(0, 'Setup values for pyFlame Import Camera script.')
        config_text.insert(1, 'Camera Path:')
        config_text.insert(2, self.camera_file_path)
        config_text.insert(3, 'Scene Scale:')
        config_text.insert(4, self.scene_scale)
        config_text.insert(5, 'Import Type:')
        config_text.insert(6, self.import_type)
        config_text.insert(7, 'Add ST Map Setup')
        config_text.insert(8, self.st_map_setup_button.isChecked())
        config_text.insert(9, 'Add Patch Setup')
        config_text.insert(10, self.patch_setup_button.isChecked())

        out_file = open(self.config_file, 'w')
        for line in config_text:
            print(line, file=out_file)
        out_file.close()

        print ('\n>>> config saved <<<\n')

    # -------------------------------- #

    def main_window(self):
        import shutil

        def load():

            self.window.close()

            if self.st_map_setup_button.isChecked():
                self.create_st_map_setup()
            elif self.patch_setup_button.isChecked():
                self.create_patch_setup()
            else:
                self.create_camera_action()

            # Delete temp folder

            shutil.rmtree(self.temp_folder)
            print ('\n>>> temp folder deleted <<<\n')

            print ('done.')

        def cancel():
            import shutil

            shutil.rmtree(self.temp_folder)

            self.window.close()

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(QtCore.QSize(300, 150))
        self.window.setMaximumSize(QtCore.QSize(500, 300))
        self.window.setWindowTitle('pyFlame Import FBX/Alembic %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #313131')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.scene_scale_label = FlameLabel('Scene Scale', 'normal', self.window)
        self.import_type_label = FlameLabel('Import Type', 'normal', self.window)

        # Scale Slider

        class FlameSliderLineEdit(QtWidgets.QLineEdit):
            from PySide2 import QtGui

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
                from functools import partial
                from PySide2 import QtGui

                def clear():
                    calc_lineedit.setText('')

                def button_press(key):

                    if self.clean_line:
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

        self.scale_spinbox_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.window)
        self.scale_spinbox = FlameSliderLineEdit(FlameSliderLineEdit.IntSpinBox, 10, parent=self.window)
        slider(1, 1000, 10, self.scale_spinbox_slider, self.scale_spinbox)

        # Menu Pushbutton

        import_menu_options = ['Action Objects', 'Read File']
        self.import_type_btn = FlamePushButtonMenu(self.import_type, import_menu_options, self.window)

        #  Pushbuttons

        def st_map_setup_toggle():
            if self.st_map_setup_button.isChecked():
                self.patch_setup_button.setChecked(False)

        def patch_setup_toggle():
            if self.patch_setup_button.isChecked():
                self.st_map_setup_button.setChecked(False)

        self.st_map_setup_button = FlamePushButton(' ST Map Setup', self.window, self.st_map_setup, st_map_setup_toggle)
        self.patch_setup_button = FlamePushButton(' Patch Setup', self.window, self.patch_setup, patch_setup_toggle)

        # Buttons

        self.load_btn = FlameButton('Load', load, self.window)
        self.cancel_btn = FlameButton('Cancel', cancel, self.window)

        # Window Layout

        # Gridbox

        gridbox = QtWidgets.QGridLayout()
        gridbox.setHorizontalSpacing(5)
        gridbox.setColumnMinimumWidth(2, 50)

        gridbox.addWidget(self.scene_scale_label, 0, 0)
        gridbox.addWidget(self.scale_spinbox_slider, 0, 1, QtCore.Qt.AlignBottom)
        gridbox.addWidget(self.scale_spinbox, 0, 1)
        gridbox.addWidget(self.st_map_setup_button, 0, 3)

        gridbox.addWidget(self.import_type_label, 1, 0)
        gridbox.addWidget(self.import_type_btn, 1, 1)
        gridbox.addWidget(self.patch_setup_button, 1, 3)

        # Hbox01

        hbox01 = QtWidgets.QHBoxLayout()
        hbox01.addWidget(self.cancel_btn)
        hbox01.addWidget(self.load_btn)

        # Main VBox

        vbox = QtWidgets.QVBoxLayout()
        vbox.setMargin(20)
        vbox.addStretch(5)
        vbox.addLayout(gridbox)
        vbox.addSpacing(40)
        vbox.addLayout(hbox01)
        vbox.addStretch(5)

        self.window.setLayout(vbox)

        self.window.show()

    def file_browse(self, path, filter_type):

        file_browser = QtWidgets.QFileDialog()
        file_browser.setDirectory(path)
        file_browser.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        file_browser.setNameFilter(filter_type)
        file_browser.setFileMode(QtWidgets.QFileDialog.ExistingFile) # Change to ExistingFiles to capture many files
        if file_browser.exec_():
            return str(file_browser.selectedFiles()[0])

        print ('\n>>> import cancelled <<<\n')
        return

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

# -------------------------------- #

def import_fbx(selection):

    filter_type = 'FBX (*.fbx)'

    Import(selection, filter_type)

def import_abc(selection):

    filter_type = 'Alembic (*.abc)'

    Import(selection, filter_type)

#---------------------------#

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Import...',
            'actions': [
                {
                    'name': 'Import FBX',
                    'execute': import_fbx,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Import Alembic',
                    'execute': import_abc,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
