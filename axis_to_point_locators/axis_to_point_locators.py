'''
Script Name: Axis to Point Locators
Script Version: 1.0
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 11.12.21
Update Date: 11.12.21

Custom Action Type: Action

Description:

    Convert selected axis nodes to point locators

To install:

    Copy script into /opt/Autodesk/shared/python/axis_to_point_locators
'''

from __future__ import print_function
from random import randint
import os, shutil

VERSION = 'v1.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/axis_to_point_locators'

class AxisToPointLocators(object):

    def __init__(self, selection):
        import flame

        print ('''
               _  _______    _____      _       _   _                     _
    /\        (_)|__   __|  |  __ \    (_)     | | | |                   | |
   /  \  __  ___ ___| | ___ | |__) ___  _ _ __ | |_| |     ___   ___ __ _| |_ ___  _ __ ___
  / /\ \ \ \/ | / __| |/ _ \|  ___/ _ \| | '_ \| __| |    / _ \ / __/ _` | __/ _ \| '__/ __|
 / ____ \ >  <| \__ | | (_) | |  | (_) | | | | | |_| |___| (_) | (_| (_| | || (_) | |  \__ \\
/_/    \_/_/\_|_|___|_|\___/|_|   \___/|_|_| |_|\__|______\___/ \___\__,_|\__\___/|_|  |___/
        \n''')

        print ('>' * 32, 'axis to point locators %s' % VERSION, '<' * 32, '\n')

        self.selection = selection

        # Temp folder for saving action setup

        self.temp_folder = os.path.join(SCRIPT_PATH, 'temp_action')

        # Action variables

        self.action_node = self.get_action_node()

        self.action_node_name = str(self.action_node.name)[1:-1]
        self.save_action_path = os.path.join(self.temp_folder, self.action_node_name)
        self.action_filename = self.save_action_path + '.action'

        # Get list of axis nodes from selected nodes

        self.axis_list = [node for node in self.selection if node.type == 'Axis']

        # Get position of first selected axis

        self.first_axis = self.axis_list[0]
        self.first_axis_name = str(self.first_axis.name)[1:-1]

        # Set position of point locator in action schematic below first selected axis

        self.point_locator_pos_x = self.first_axis.pos_x
        self.point_locator_pos_y = self.first_axis.pos_y - 200

        # Create point locator from selected axis nodes

        self.convert_axis_to_point_locator()

    def convert_axis_to_point_locator(self):

        # Save current action node

        self.save_action_node()

        # Get ConcreteEnd line
        # Point locator node data to be inserted above this line

        item_line = self.find_line('ConcreteEnd')
        concrete_end_line = item_line - 1
        # print ('concrete_end_line:', concrete_end_line, '\n')

        # Get node number for point locator node

        node_number_line = self.find_line_before('Number', concrete_end_line)
        point_locator_node_number = str(int(self.get_line_value(node_number_line)) + 1)

        # Build point locator node

        point_locator_node = self.build_point_locator_insert(point_locator_node_number)

        # Read in saved action node

        edit_action = open(self.action_filename, 'r')
        contents = edit_action.read()
        edit_action.close()

        # Combine action lines with point locator insert lines

        contents_start = contents.rsplit('ConcreteEnd', 1)[0]
        contents_end = contents.rsplit('ConcreteEnd', 1)[1]

        new_action_script = contents_start + point_locator_node + '''
ConcreteEnd''' + contents_end

        # Save modified action file

        new_action = open(self.action_filename, 'w')
        new_action.write(new_action_script)
        new_action.close()

        # Reload saved action node

        self.reload_action_node()

        #
        # Connect point locator to parent axis if one exists
        #

        # Get updated action node

        self.action_node = self.get_action_node()

        # Find selected axis node number

        item_line = self.find_line(self.first_axis_name)
        line_number = self.find_line_after('Number', item_line)
        item_value = self.get_line_value(line_number)
        selected_axis_number = item_value

        # Find parent of selected axis

        item_line = self.find_line('Child %s' % selected_axis_number)
        line_number = self.find_line_before('Name', item_line)
        item_value = self.get_line_value(line_number)
        parent_axis_name = item_value[:-1]

        # Connect point locator node to parent if one exists

        parent_axis = [node for node in self.action_node.nodes if node.type == 'Axis' and node.name == parent_axis_name]
        # print ('parent_axis:', parent_axis)

        if parent_axis:
            self.action_node = self.get_action_node()
            point_locator = [node for node in self.action_node.nodes if node.name == self.point_locator_name]

            self.action_node.connect_nodes(parent_axis[0], point_locator[0])

        # Remove temp action folder

        self.remove_temp_folder()

        print ('>>> point locator created <<<\n')

        print ('done.\n')

    def build_point_locator_insert(self, point_locator_node_number):

        random_number = randint(10, 99)
        self.point_locator_name = 'PointLocators%s' % random_number

        point_locator_start = '''Node PointCloud
    Name %s
    Number %s
    MotionPath yes
    ShadowCaster no
    ShadowReceiver no
    ShadowOnly no
    PosX %s
    PosY %s
    IsLocked no
    IsSoftImported no
    OutputsSize 0
    Specifics
    {
            Colour 0.800000012 0.5 1
            DisplayMethod 1
            Radius 10
            Transparency 0
            TransformMode 0
            EnableSnap 1
            SnapTolerance 15
            Point''' % (self.point_locator_name, point_locator_node_number, self.point_locator_pos_x, self.point_locator_pos_y)

        point_locator_end = '''
        CoNodeFlags
        Collapsed no
        CoNodeFlagsEnd
    }
End'''

        point_locator_insert = ''

        for axis in self.axis_list:
            axis_insert = self.build_axis_insert(axis)
            point_locator_insert = point_locator_insert + axis_insert
        point_locator_insert = point_locator_insert[:-14]

        point_locator_node = point_locator_start + point_locator_insert + point_locator_end

        return point_locator_node

    def build_axis_insert(self, axis):

        axis_insert = '''
        Channel x
            Extrapolation constant
            Value %s
            End
        Channel y
            Extrapolation constant
            Value %s
            End
        Channel z
            Extrapolation constant
            Value %s
            End
        ChannelEnd
        Point''' % (eval(str(axis.position)))

        return axis_insert

    def get_action_node(self):
        import flame

        # Get action node from selected action node or selected media node

        node_type = str(flame.batch.current_node.get_value().type)[1:-1]

        if node_type == 'Action Media':
            node_value = flame.batch.current_node.get_value()
            node_sockets = node_value.sockets
            output_dict = node_sockets.get('output')
            action_node_name = output_dict.get('Result')[0]
            action_node = flame.batch.get_node(action_node_name)
        else:
            action_node_name = str(flame.batch.current_node.get_value().name)[1:-1]
            action_node = flame.batch.get_node(action_node_name)

        return action_node

    def save_action_node(self):
        import flame

        # Create temp action save dir

        try:
            os.makedirs(self.temp_folder)
        except:
            shutil.rmtree(self.temp_folder)
            os.makedirs(self.temp_folder)

        # Save action node

        action_node = self.get_action_node()
        action_node.save_node_setup(self.save_action_path)

    def reload_action_node(self):

        # Reload action setup

        self.action_node.load_node_setup(self.save_action_path)

    def remove_temp_folder(self):

        # Remove temp action folder

        shutil.rmtree(self.temp_folder)

    def find_line(self, item):

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if item in line:
                    item_line = num
                    return item_line

    def find_line_before(self, item, item_line_num):

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if num == item_line_num:
                    if item in line:
                        line_number = num
                        return line_number

            item_line_num = item_line_num - 1
            return self.find_line_before(item, item_line_num)

    def find_line_after(self, item, item_line_num):

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if num > item_line_num:
                    if item in line:
                        line_number = num
                        return line_number

    def get_line_value(self, line_number):

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if num == line_number:
                    item_value = line.rsplit(' ', 1)[1]
                    return item_value

#-------------------------------------#

def scope_axis(selection):
    import flame

    for item in selection:
        if item.type == 'Axis':
            return True
    return False

#-------------------------------------#

def get_action_custom_ui_actions():

    return [
        {
            'name': 'Axis...',
            'actions': [
                {
                    'name': 'Axis to Point Locator',
                    'isVisible': scope_axis,
                    'execute': AxisToPointLocators,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
