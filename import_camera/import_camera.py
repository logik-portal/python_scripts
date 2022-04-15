'''
Script Name: Import Camera
Script Version: 4.3
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 06.02.18
Update Date: 03.15.22

Custom Action Type: Batch

Description:

    Creates a new Action node with selected FBX or Alembic file loaded.

    The Action camera will be automatically switched to the new FBX/Alembic camera.

    Options to load with simple re-comp or st-map setup.

Menus:

    Right-click in batch or on selected node -> Import... -> Import FBX

    Right-click in batch or on selected node -> Import... -> Import Alembic

To install:

    Copy script into /opt/Autodesk/shared/python/import_camera

Updates:

    v4.3 03.15.22

        Moved UI widgets to external file

    v4.2 02.25.22

        Updated UI for Flame 2023

        Updated config to XML

    v4.1 01.04.22

        Files starting with '.' are ignored when searching for undistort map after distort map is selected.

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

import xml.etree.ElementTree as ET
import os, re, ast, shutil
from PySide2 import QtWidgets
from flame_widgets_import_camera import FlameButton, FlameLabel, FlamePushButton, FlamePushButtonMenu, FlameMessageWindow, FlameSlider, FlameWindow

VERSION = 'v4.3'

SCRIPT_PATH = '/opt/Autodesk/shared/python/import_camera'

class Import(object):

    def __init__(self, selection, filter_type):
        import flame

        print ('''
 _____                            _    _____
|_   _|                          | |  / ____|
  | |  _ __ ___  _ __   ___  _ __| |_| |     __ _ _ __ ___   ___ _ __ __ _
  | | | '_ ` _ \| '_ \ / _ \| '__| __| |    / _` | '_ ` _ \ / _ \ '__/ _` |
 _| |_| | | | | | |_) | (_) | |  | |_| |___| (_| | | | | | |  __/ | | (_| |
|_____|_| |_| |_| .__/ \___/|_|   \__|\_____\__,_|_| |_| |_|\___|_|  \__,_|
                | |
                |_|
                ''')

        print ('>' * 28, f'import camera {VERSION}', '<' * 27, '\n')

        self.filter_type = filter_type

        # Define paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        self.batch_setup_path = os.path.join(SCRIPT_PATH, 'batch_setups')

        # Load config file

        self.config()

        # Get cursor position

        if selection != ():
            self.selection = selection[0]
            self.master_pos_x = self.selection.pos_x + 300
            self.master_pos_y = self.selection.pos_y
        else:
            self.selection = ''
            self.master_pos_x = flame.batch.cursor_position[0]
            self.master_pos_y = flame.batch.cursor_position[1]

        self.undistort_map_path = ''
        self.redistort_map_path = ''

        # Create temp folder

        self.temp_folder = os.path.join(SCRIPT_PATH, 'temp')

        try:
            os.makedirs(self.temp_folder)
            print ('--> temp folder created \n')
        except:
            print ('temp folder already exists\n')

        self.camera_file_path = self.file_browse(self.camera_path, self.filter_type)

        if self.camera_file_path:
            self.main_window()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings from config XML

            for setting in root.iter('import_camera_settings'):
                self.camera_path = setting.find('camera_path').text
                self.scene_scale = int(setting.find('scene_scale').text)
                self.import_type = setting.find('import_type').text
                self.st_map_setup = ast.literal_eval(setting.find('st_map_setup').text)
                self.patch_setup = ast.literal_eval(setting.find('patch_setup').text)

            if not os.path.isdir(self.camera_path):
                self.camera_path = self.camera_path.rsplit('/', 1)[0]

            print ('--> config loaded \n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder: {self.config_path}<br>Check folder permissions')

            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file \n')

                config = """
<settings>
    <import_camera_settings>
        <camera_path>/</camera_path>
        <scene_scale>100</scene_scale>
        <import_type>Action Objects</import_type>
        <st_map_setup>False</st_map_setup>
        <patch_setup>False</patch_setup>
    </import_camera_settings>
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

    # -------------------------------- #

    def create_camera_action(self):
        '''
        Create action and load FBX or Alembic camera scene
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

        print ('--> action created \n')

        # Import FBX camera

        if self.camera_file_path.endswith('.fbx'):
            if self.import_type == 'Action Objects':
                self.camera_action.import_fbx(f'{self.camera_file_path}', unit_to_pixels=int(self.scene_scale))
            else:
                self.camera_action.read_fbx(f'{self.camera_file_path}', unit_to_pixels=int(self.scene_scale))

        # Import Alembic camera

        else:
            if self.import_type == 'Action Objects':
                self.camera_action.import_abc(f'{self.camera_file_path}', unit_to_pixels=int(self.scene_scale))
            else:
                self.camera_action.read_abc(f'{self.camera_file_path}', unit_to_pixels=int(self.scene_scale))

        print ('--> camera imported \n')

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

            # print ('new_node_names: ', new_node_names)

            return new_node_names

        self.config_save()

        self.create_camera_action()

        st_map_node_names = ['mux_in', 'action_in', 'action_out', 'recomp', 'regrain', 'divide']

        existing_node_names = [node.name for node in flame.batch.nodes]
        # print ('existing_node_names:', existing_node_names)

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

        print ('--> camera imported with patch setup \n')

    def create_st_map_setup(self):
        '''
        Create setup with st map workflow with 3d camera. Recomps over original plate at end.
        '''

        import flame

        def get_st_maps():
            import flame

            # Browse for undistort map

            FlameMessageWindow('Import', 'message', 'Select ST undistort map')

            self.undistort_map_path = self.file_browse(self.camera_file_path.rsplit('/', 1)[0], 'EXR (*.exr)')

            print ('undistort_map_path:', self.undistort_map_path, '\n')

            if not self.undistort_map_path:
                return

            self.config_save()

            # Search for undistort folder for redistort map

            for root, dirs, files in os.walk(self.undistort_map_path.rsplit('/', 1)[0]):
                for f in files:
                    if not f.startswith('.'):
                        if re.search('redistort', f, re.I):
                            self.redistort_map_path = os.path.join(root, f)
                            print ('\n--> st redistort map found \n')
                            break

            # If redistort map not found, browse for it

            if self.redistort_map_path == '':

                FlameMessageWindow('Import', 'message', 'Select ST Redistort map')

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

            print ('\n--> st maps imported \n')
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

                    print ('\n--> resize node saved \n')

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

                new_ratio = f'<DestinationAspect>{undistort_clip_ratio}</DestinationAspect>'

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

                print ('\n--> resize node set to st map resolution \n')

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

            print ('\n--> camera imported with st map setup \n')

        # Load st maps

        st_maps_loaded = get_st_maps()

        if st_maps_loaded:
            self.create_camera_action()
            build_st_map_setup()
        else:
            print ('--> import cancelled \n')

    def config_save(self):

        #  Save settings

        self.scene_scale = self.scale_slider.text()
        self.import_type = self.import_type_btn.text()

        # Save settings to config file

        xml_tree = ET.parse(self.config_xml)
        root = xml_tree.getroot()

        camera_path = root.find('.//camera_path')
        camera_path.text = self.camera_file_path

        scene_scale = root.find('.//scene_scale')
        scene_scale.text = str(self.scene_scale)

        import_type = root.find('.//import_type')
        import_type.text = self.import_type

        st_map_setup = root.find('.//st_map_setup')
        st_map_setup.text = str(self.st_map_setup_button.isChecked())

        patch_setup = root.find('.//patch_setup')
        patch_setup.text = str(self.patch_setup_button.isChecked())

        xml_tree.write(self.config_xml)

        print ('--> config saved \n')

    # -------------------------------- #

    def main_window(self):

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
            print ('--> temp folder deleted \n')

            print ('done.\n')

        def cancel():

            shutil.rmtree(self.temp_folder)

            self.window.close()

        vbox = QtWidgets.QVBoxLayout()
        self.window = FlameWindow(f'Import Camera <small>{VERSION}', vbox, 500, 230)

        # Labels

        self.scene_scale_label = FlameLabel('Scene Scale', 'normal', 110)
        self.import_type_label = FlameLabel('Import Type', 'normal', 110)

        # Slider

        self.scale_slider = FlameSlider(self.scene_scale, 1, 1000, False, 150)

        # Menu Pushbutton

        import_menu_options = ['Action Objects', 'Read File']
        self.import_type_btn = FlamePushButtonMenu(self.import_type, import_menu_options)

        #  Pushbuttons

        def st_map_setup_toggle():
            if self.st_map_setup_button.isChecked():
                self.patch_setup_button.setChecked(False)

        def patch_setup_toggle():
            if self.patch_setup_button.isChecked():
                self.st_map_setup_button.setChecked(False)

        self.st_map_setup_button = FlamePushButton('ST Map Setup', self.st_map_setup)
        self.st_map_setup_button.clicked.connect(st_map_setup_toggle)

        self.patch_setup_button = FlamePushButton('Patch Setup', self.patch_setup)
        self.patch_setup_button.clicked.connect(patch_setup_toggle)

        # Buttons

        self.load_btn = FlameButton('Load', load)
        self.cancel_btn = FlameButton('Cancel', cancel)

        # Window Layout

        # Gridbox

        gridbox = QtWidgets.QGridLayout()
        gridbox.setHorizontalSpacing(5)
        gridbox.setColumnMinimumWidth(2, 50)

        gridbox.addWidget(self.scene_scale_label, 0, 0)
        gridbox.addWidget(self.scale_slider, 0, 1)
        gridbox.addWidget(self.st_map_setup_button, 0, 3)

        gridbox.addWidget(self.import_type_label, 1, 0)
        gridbox.addWidget(self.import_type_btn, 1, 1)
        gridbox.addWidget(self.patch_setup_button, 1, 3)

        # Hbox01

        hbox01 = QtWidgets.QHBoxLayout()
        hbox01.addWidget(self.cancel_btn)
        hbox01.addWidget(self.load_btn)

        # Main VBox

        vbox.setMargin(20)
        vbox.addStretch(5)
        vbox.addLayout(gridbox)
        vbox.addSpacing(40)
        vbox.addLayout(hbox01)
        vbox.addStretch(5)

        self.window.show()

    def file_browse(self, path, filter_type):

        file_browser = QtWidgets.QFileDialog()
        file_browser.setDirectory(path)
        file_browser.setNameFilter(filter_type)
        file_browser.setFileMode(QtWidgets.QFileDialog.ExistingFile) # Change to ExistingFiles to capture many files
        if file_browser.exec_():
            return str(file_browser.selectedFiles()[0])

        print ('\n--> import cancelled \n')
        return

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
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Import Alembic',
                    'execute': import_abc,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
