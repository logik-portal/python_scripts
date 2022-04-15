'''
Script Name: Import ST Maps
Script Version: 2.3
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 04.30.21
Update Date: 03.15.22

Custom Action Type: Batch

Description:

    Imports ST Maps and builds ST Map setup

    Comp work is recomped over original plate at end of setup

Menu:

    Right-click in batch or on selected node -> Import... -> Import ST Maps

To install:

    Copy script into /opt/Autodesk/shared/python/import_st_map

Updates:

    v2.3 03.15.22

        Updated UI for Flame 2023

        Moved UI widgets to external file

    v2.2 02.17.22

        Updated config to XML

    v2.1 01.04.21

        Files starting with '.' are ignored when searching for undistort map after distort map is selected.

    v2.0 05.19.21

        Updated to be compatible with Flame 2022/Python 3.7
'''

import xml.etree.ElementTree as ET
import os, re, shutil
from PySide2 import QtWidgets
from flame_widgets_import_st_map import FlameMessageWindow

VERSION = 'v2.3'

SCRIPT_PATH = '/opt/Autodesk/shared/python/import_st_map'

class ImportSTMap(object):

    def __init__(self, selection):
        import flame

        print ('''
 _____                            _    _____ _______ __  __
|_   _|                          | |  / ____|__   __|  \/  |
  | |  _ __ ___  _ __   ___  _ __| |_| (___    | |  | \  / | __ _ _ __
  | | | '_ ` _ \| '_ \ / _ \| '__| __|\___ \   | |  | |\/| |/ _` | '_ \\
 _| |_| | | | | | |_) | (_) | |  | |_ ____) |  | |  | |  | | (_| | |_) |
|_____|_| |_| |_| .__/ \___/|_|   \__|_____/   |_|  |_|  |_|\__,_| .__/
                | |                                              | |
                |_|                                              |_|
        ''')

        print ('>' * 26, f'import st map {VERSION}', '<' * 26, '\n')

        # Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Load config file

        self.config()

        # Get current cursor position

        if selection != ():
            self.selection = selection[0]
            self.master_pos_x = self.selection.pos_x + 300
            self.master_pos_y = self.selection.pos_y
        else:
            self.selection = ''
            self.master_pos_x = flame.batch.cursor_position[0]
            self.master_pos_y = flame.batch.cursor_position[1]

        # Init variables

        self.undistort_map_path = ''
        self.redistort_map_path = ''
        self.redistort_map = ''
        self.undistort_map = ''

        # Create temp folder

        self.temp_folder = os.path.join(SCRIPT_PATH, 'temp')

        try:
            os.makedirs(self.temp_folder)
            print ('\n--> temp folder created \n')
        except:
            print ('temp folder already exists\n')

        self.create_st_map_setup()

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings from config XML

            for setting in root.iter('import_st_map_settings'):
                self.st_map_path = setting.find('st_map_path').text

            # Check st map path

            if not os.path.isdir(self.st_map_path):
                self.st_map_path = '/'

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
    <import_st_map_settings>
        <st_map_path>/</st_map_path>
    </import_st_map_settings>
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

    def create_st_map_setup(self):

        def config_save():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            st_map_path = root.find('.//st_map_path')
            st_map_path.text = self.undistort_map_path.rsplit('/', 1)[0]

            xml_tree.write(self.config_xml)

            print ('--> config saved \n')

        def get_st_maps():
            import flame

            # Browse for undistort map

            FlameMessageWindow('Import', 'message', 'Select File: ST Undistort Map')

            self.undistort_map_path = self.file_browse(self.st_map_path)

            print ('undistort_map_path:', self.undistort_map_path, '\n')

            if not self.undistort_map_path:
                return False

            config_save()

            # Search for undistort folder for redistort map

            for root, dirs, files in os.walk(self.undistort_map_path.rsplit('/', 1)[0]):
                for f in files:
                    if not f.startswith('.'):
                        if re.search('redistort', f, re.I):
                            self.redistort_map_path = os.path.join(root, f)
                            print ('--> st redistort map found \n')
                            break

            # If redistort map not found, browse for it

            if self.redistort_map_path == '':
                FlameMessageWindow('Import', 'message', 'Select File: ST Redistort Map')
                self.redistort_map_path = self.file_browse(self.undistort_map_path)

            # print ('redistort_map_path:', self.redistort_map_path, '\n')

            if not self.redistort_map_path:
                return False

            # create st maps schematic reel if it doesn't exist

            if 'st_maps' not in [reel.name for reel in flame.batch.reels]:
                flame.batch.create_reel('st_maps')

            # import maps

            self.redistort_map = flame.batch.import_clip(self.redistort_map_path, 'st_maps')
            self.undistort_map = flame.batch.import_clip(self.undistort_map_path, 'st_maps')

            print ('--> st maps imported \n')
            return True

        def build_st_map_setup():
            import flame

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

                # print ('new_node_names: ', new_node_names)

                return new_node_names

            def edit_resize_node():

                def get_st_map_res():

                    undistort_map_name = str(self.undistort_map.name)[1:-1]
                    # print ('undistort_map_name:', undistort_map_name)

                    # Get resolution of st map clips for resize node

                    st_map_reel = [reel for reel in flame.batch.reels if reel.name == 'st_maps'][0]

                    clip = [clip for clip in st_map_reel.clips if re.search(undistort_map_name, str(clip.name), re.I)][0]

                    undistort_clip_width = str(clip.width)
                    undistort_clip_height = str(clip.height)
                    undistort_clip_ratio = str(round(float(clip.ratio), 3))
                    # print ('undistort_clip_width:', undistort_clip_width)
                    # print ('undistort_clip_height:', undistort_clip_height)
                    # print ('undistort_clip_ratio:', undistort_clip_ratio, '\n')

                    return undistort_clip_width, undistort_clip_height, undistort_clip_ratio

                def save_resize_node():

                    # Save resize node

                    resize_node_name = str(undistort_plate_resize.name)[1:-1]
                    save_resize_path = os.path.join(self.temp_folder, resize_node_name)
                    # print ('save_resize_path:', save_resize_path)

                    undistort_plate_resize.save_node_setup(save_resize_path)

                    # Set Resize path and filename variable

                    resize_file_name = save_resize_path + '.resize_node'
                    # print ('resize_file_name:', resize_file_name)

                    # print ('--> resize node saved \n')

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
                edit_resize.close

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

                # print ('\n--> resize node set to st map resolution \n')

            # Set node names
            # --------------

            st_map_node_names = ['plate_undistort', 'plate_resize', 'st_map_undistort_in', 'comp_redistort_in', 'comp_redistort', 'st_map_redistort_in', 'mux_in', 'divide', 'regrain', 'comp_action']

            existing_node_names = [node.name for node in flame.batch.nodes]

            new_node_names = []

            new_node_names = name_nodes()

            # Create nodes
            # ------------

            # Create comp action node

            comp_action = flame.batch.create_node('Action')
            comp_action.name = new_node_names[9]
            comp_action.collapsed = False

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

            redistort_action = flame.batch.create_node('Action')
            redistort_action.name = new_node_names[4]
            redistort_action.collapsed = True

            redistort_action.pos_x = comp_redistort_in_mux.pos_x + 600
            redistort_action.pos_y = self.master_pos_y - 15

            # Create redistort action media layer 1

            comp_redistort_in_media = redistort_action.add_media()
            comp_redistort_in_media.pos_x = redistort_action.pos_x - 40
            comp_redistort_in_media.pos_y = redistort_action.pos_y - 525

            # Create UV Map

            comp_redistort_uv = redistort_action.create_node('UV Map')

            # Create redistort action media layer 2

            stmap_redistort_in_media = redistort_action.add_media()
            stmap_redistort_in_media.pos_x = redistort_action.pos_x - 40
            stmap_redistort_in_media.pos_y = redistort_action.pos_y - 940

            # Assign UV Map to media 2

            comp_redistort_uv.assign_media(2)

            # redistortAction nodes to delete

            axis_to_delete02 = redistort_action.get_node('axis3')
            image_to_delete02 = redistort_action.get_node('surface2')
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
            regrain_node.pos_x = redistort_action.pos_x + 300
            regrain_node.pos_y = redistort_action.pos_y

            # Move nodes
            # ----------

            self.undistort_map.pos_x = undistort_st_map_in_mux.pos_x - 400
            self.undistort_map.pos_y = undistort_st_map_in_mux.pos_y + 30

            self.redistort_map.pos_x = redistort_st_map_in_mux.pos_x - 400
            self.redistort_map.pos_y = redistort_st_map_in_mux.pos_y + 30

            comp_action.pos_x = plate_undistort_action.pos_x + 1000
            comp_action.pos_y = plate_undistort_action.pos_y - 80

            # Load saved redistort action setup

            redistort_action.load_node_setup(os.path.join(SCRIPT_PATH, 'action_nodes/comp_redistort.flare.action'))

            # Load saved comp action setup

            comp_action.load_node_setup(os.path.join(SCRIPT_PATH, 'action_nodes/comp_action.flare.action'))

            # Connect nodes
            #--------------

            if self.selection != '':
                flame.batch.connect_nodes(self.selection, 'Default', plate_in_mux, 'Input_0')

            flame.batch.connect_nodes(undistort_st_map_in_mux, 'Result', undistort_in_media, 'Front')
            flame.batch.connect_nodes(comp_action, 'Output [ Comp ]', comp_redistort_in_mux, 'Input_0')
            flame.batch.connect_nodes(comp_action, 'Output [ Matte ]', comp_redistort_in_mux, 'Matte_0')
            flame.batch.connect_nodes(comp_redistort_in_mux, 'Result', divide_comp, 'Front')
            flame.batch.connect_nodes(comp_redistort_in_mux, 'OutMatte', divide_comp, 'Back')
            flame.batch.connect_nodes(divide_comp, 'Result', comp_redistort_in_media, 'Front')
            flame.batch.connect_nodes(comp_redistort_in_mux, 'OutMatte', comp_redistort_in_media, 'Matte')
            flame.batch.connect_nodes(redistort_st_map_in_mux, 'Result', stmap_redistort_in_media, 'Front')
            flame.batch.connect_nodes(self.undistort_map, 'Default', undistort_st_map_in_mux, 'Input_0')
            flame.batch.connect_nodes(self.redistort_map, 'Default', redistort_st_map_in_mux, 'Input_0')
            flame.batch.connect_nodes(plate_in_mux, 'Result', redistort_action, 'Back')
            flame.batch.connect_nodes(redistort_action, 'Comp [ Comp ]', regrain_node, 'Front')
            flame.batch.connect_nodes(redistort_action, 'Comp [ Comp ]', regrain_node, 'Back')
            flame.batch.connect_nodes(redistort_action, 'Matte [ Matte ]', regrain_node, 'Matte')

            # Set resize node to match ST Map resolution

            edit_resize_node()

            # Load plate undistort action setup

            plate_undistort_action.load_node_setup(os.path.join(SCRIPT_PATH, 'action_nodes/plate_undistort.flare.action'))

            # Connect connect remaining nodes

            flame.batch.connect_nodes(undistort_plate_resize, 'Result', plate_undistort_action, 'Back')

            flame.batch.connect_nodes(plate_undistort_action, 'output1 [ Comp ]', comp_action, 'Back')

        st_maps_loaded = get_st_maps()

        if st_maps_loaded:
            config_save()
            build_st_map_setup()
            print ('--> st map setup created \n')
        else:
            print ('--> import cancelled \n')

        # Delete temp folder

        shutil.rmtree(self.temp_folder)

        print ('done.\n')

    def file_browse(self, path):

        file_browser = QtWidgets.QFileDialog()
        file_browser.setDirectory(path)
        file_browser.setNameFilter('EXR (*.exr)')
        file_browser.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if file_browser.exec_():
            return str(file_browser.selectedFiles()[0])
        return

#---------------------------#

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Import...',
            'actions': [
                {
                    'name': 'Import ST Map',
                    'execute': ImportSTMap,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
