'''
Script Name: Invert Axis
Script Version: 2.4
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 07.26.19
Update Date: 07.17.22

Custom Action Type: Action / GMask Tracer

Description:

    Create inverted axis at current frame or copy parent axis and invert at current frame.

    Works with axis nodes in GMask Tracer starting with Flame 2023

Menus:

    Action Axis Nodes:

        Right-click on axis node -> Axis... -> Create Inverted Axis At Current Frame
        Right-click on axis node -> Axis... -> Invert Parent Axis At Current Frame

    GMask Tracer Axis Nodes(Flame 2023 and later):

        Right-click on axis node -> Axis... -> GMask - Create Inverted Axis At Current Frame
        Right-click on axis node -> Axis... -> GMask - Invert Parent Axis At Current Frame

To install:

    Copy script into /opt/Autodesk/shared/python/invert_axis

Updates:

    v2.4 07.17.22

        Messages print to Flame message window - Flame 2023.1 and later

        Fixed: Right-clicking in Action or GMask Tracer with no axis selected causes error to show in shell.

    v2.3 03.25.22

        Now works with axis nodes in GMask Tracer in Flame 2023

    v2.2 11.12.21

        Changed menu name to Axis...

    v2.1 10.26.21

        Script now works when media layer is selected instead of action node.

    v2.0 05.23.21

        Updated to be compatible with Flame 2022/Python 3.7

        Fixed inverting axis not working when multiple axis parented to same axis

    v1.5 05.10.20

        Inverted axis is now added as child of selected axis

    v1.3 10.24.19

        Menu's now show up under Invert Axis... when right-clicking on axis node in action schematic

        Removed menu's from showing up in GMask Tracer. Action python commands do not work in GMask Tracer.
'''

import os, shutil
from pyflame_lib_invert_axis import pyflame_print

SCRIPT_NAME = 'Invert Axis'
SCRIPT_PATH = '/opt/Autodesk/shared/python/invert_axis'
VERSION = 'v2.4'

class InvertAxis():

    def __init__(self, selection):
        import flame

        self.current_frame = flame.batch.current_frame

        # Get selected axis

        self.selected_axis = selection[0]
        self.axis_name = str(selection[0].name)[1:-1]
        self.selected_axis_parent = self.selected_axis.parent
        self.selected_node_type = str(self.selected_axis_parent.type)[1:-1]

        # Temp folder for saving node setup

        self.temp_folder = os.path.join(SCRIPT_PATH, 'temp')

        # Selected node variables

        self.selected_node = self.get_selected_node()

        self.selected_node_name = str(self.selected_node.name)[1:-1]
        self.save_node_path = os.path.join(self.temp_folder, self.selected_node_name)

        if self.selected_node_type == 'Action':
            self.node_filename = self.save_node_path + '.action'
        else:
            self.node_filename = self.save_node_path + '.mask'

        # Init lists

        self.axis_child_list = []
        self.axis_child_lines_list = []

    def create_inverted_axis(self):
        import flame

        print ('\n')
        print ('>' * 10, f'{SCRIPT_NAME} {VERSION} - Create Inverted Axis', '<' * 10, '\n')

        # Create new axis node

        self.inverted_axis = self.selected_node.create_node('Axis')
        self.inverted_axis_name = self.name_axis()
        self.inverted_axis.name = self.inverted_axis_name

        # Copy axis values

        self.copy_axis_values(self.inverted_axis, self.selected_axis)

        # Connect nodes

        self.selected_node.connect_nodes(self.selected_axis, self.inverted_axis)

        # Save selected node

        self.save_selected_node()

        # Position/Invert New Inverted Axis Node
        # -------------------------------

        # Get selected axis position

        item_line = self.find_line(self.axis_name)
        line_number = self.find_line_after('PosX', item_line)
        item_value = self.get_line_value(line_number)
        selected_axis_pos_x = item_value

        next_line_num = line_number + 1
        item_value = self.get_line_value(next_line_num)
        selected_axis_pos_y = item_value

        # Find pos x and y lines for inverted axis

        item_line = self.find_line(self.inverted_axis_name)
        line_number = self.find_line_after('PosX', item_line)
        inverted_axis_pos_x_line = line_number - 1
        inverted_axis_pos_y_line = inverted_axis_pos_x_line + 1

        # Get axis invert mode line

        item_line = self.find_line(self.inverted_axis_name)
        line_number = self.find_line_after('InvertMode', item_line)
        invert_mode_line = line_number - 1

        # ---------------------------------------------------------------------

        # Reposition selected axis node
        # -----------------------------

        # Get y pos line for selected node

        selected_axis_new_pos_y = str(int(selected_axis_pos_y) + 150)

        # Get selected axis y position line for repo

        item_line = self.find_line(self.axis_name)
        line_number = self.find_line_after('PosX', item_line)
        selected_axis_pos_y_line = line_number + 1

        # ---------------------------------------------------------------------

        # Get selected axis connections to be removed

        item_line = self.find_line(self.axis_name)
        item_line_num = self.find_line_after('Child', item_line)
        self.find_child_lines('Child', item_line_num)

        # Put child lines into list to be inserted

        self.get_child_lines()

        # Get Inverted Axis line number to insert child lines to reconnect

        inverted_axis_line = self.find_line(self.inverted_axis_name)
        line_number = self.find_line_after('Number', inverted_axis_line)
        line_number = line_number - len(self.axis_child_list)
        insert_line_number = line_number + 1

        # ---------------------------------------------------------------------

        # Remove Inverted Axis from lists of Child nodes
        # Get inverted axis node number and set Child Name variable

        inverted_axis_node_num = self.get_line_value(inverted_axis_line + 1)
        inverted_axis_child_num = 'Child ' + str(inverted_axis_node_num)

        # Check child lists for Inverted Axis Child Number
        # If found remove from Inverted Axis from lists

        for axis in self.axis_child_lines_list:
            if inverted_axis_child_num in axis:
                axis_index = self.axis_child_lines_list.index(axis)
                self.axis_child_lines_list.pop(axis_index)
                self.axis_child_list.pop(axis_index)

        # Edit node lines

        edit_node = open(self.node_filename, 'r')
        contents = edit_node.readlines()
        edit_node.close()

        # Position New Inverted Axis in Selected Axis Position

        contents[inverted_axis_pos_x_line] = f'        PosX {selected_axis_pos_x}'
        contents[inverted_axis_pos_y_line] = f'        PosY {selected_axis_pos_y}'
        contents[invert_mode_line] = '                InvertMode yes'

        # Reposition Selected Axis above Inverted Axis

        contents[selected_axis_pos_y_line] = f'        PosY {selected_axis_new_pos_y}\n'

        # Remove child connections from Selected Axis

        for line_number in self.axis_child_list:
            contents[line_number] = ''

        # Insert lines for inverted axis child connections

        for child_line in self.axis_child_lines_list:
            contents.insert(insert_line_number, child_line)

        # Save modified action file

        edit_node = open(self.node_filename, 'w')
        contents = ''.join(contents)
        edit_node.write(contents)
        edit_node.close()

        # Reload saved node

        self.reload_selected_node()

        # Remove temp folder

        self.remove_temp_folder()

        pyflame_print(SCRIPT_NAME, 'Inverted axis created.')

    def invert_parent_axis(self):
        import flame

        print ('\n')
        print ('>' * 10, f'{SCRIPT_NAME} {VERSION} - Invert Parent Axis', '<' * 10, '\n')

        # Save selected node

        self.save_selected_node()

        # Get parent axis info
        # --------------------

        # Find selected axis node number

        item_line = self.find_line(self.axis_name)
        line_number = self.find_line_after('Number', item_line)
        item_value = self.get_line_value(line_number)
        axis_number = item_value

        # Find parent of selected axis

        item_line = self.find_line(f'Child {axis_number}')
        line_number = self.find_line_before('Name', item_line)
        item_value = self.get_line_value(line_number)
        parent_axis_name = item_value[:-1]

        # Check that parent node type is node type is axis

        node_type_line = line_number -1
        node_type_line_value = self.get_line_value(node_type_line)

        # If parent is axis, invert axis

        if node_type_line_value == 'Axis\n':

            # Rename selected axis to inverted axis

            selected_axis_name = self.name_axis()
            self.selected_axis.name = selected_axis_name
            axis_name = str(self.selected_axis.name)[1:-1]

            # Save selected node

            self.save_selected_node()

            # Get list of all nodes in selected node

            node_list = [node for node in self.selected_node.nodes]

            # Get parent axis

            for item in node_list:
                node_name = str(item.name)[1:-1]
                if node_name == parent_axis_name:
                    axis_node = item

            # Copy axis values

            self.copy_axis_values(self.selected_axis, axis_node)

            self.save_selected_node()

            # Invert axis
            # Get axis invert mode line

            item_line = self.find_line(axis_name)
            line_number = self.find_line_after('InvertMode', item_line)
            invert_mode_line = line_number - 1

            # Edit node lines to repo inverted axis above selected axis

            edit_node = open(self.node_filename, 'r')
            contents = edit_node.readlines()
            edit_node.close()

            contents[invert_mode_line] = '                InvertMode yes'

            edit_node = open(self.node_filename, 'w')
            contents = ''.join(contents)
            edit_node.write(contents)
            edit_node.close()

            # Reload node setup

            self.selected_node.load_node_setup(self.save_node_path)

            # Remove temp file

            self.remove_temp_folder()

            pyflame_print(SCRIPT_NAME, 'Inverted axis created.')

        else:
            # If no parent axis, remove temp file

            self.remove_temp_folder()

            pyflame_print(SCRIPT_NAME, 'No parent axis to invert.', message_type='error')

    #-------------------------------------#

    def find_line(self, item):

        with open(self.node_filename, 'r') as node_file:
            for num, line in enumerate(node_file, 1):
                if item in line:
                    item_line = num
                    return item_line

    def find_line_before(self, item, item_line_num):

        with open(self.node_filename, 'r') as node_file:
            for num, line in enumerate(node_file, 1):
                if num == item_line_num:
                    if item in line:
                        line_number = num
                        return line_number

            item_line_num = item_line_num - 1
            return self.find_line_before(item, item_line_num)

    def find_line_after(self, item, item_line_num):

        with open(self.node_filename, 'r') as node_file:
            for num, line in enumerate(node_file, 1):
                if num > item_line_num:
                    if item in line:
                        line_number = num
                        return line_number

    def find_child_lines(self, item, item_line_num):

        # Find all child lines for an axis

        with open(self.node_filename, 'r') as node_file:
            for num, line in enumerate(node_file, 1):
                if num >= item_line_num:
                    if item in line:
                        first_child_line = num - 1
                        self.axis_child_list.append(first_child_line)
                        for next_num, line in enumerate(node_file, first_child_line):
                            if next_num > first_child_line:
                                if item in line:
                                    self.axis_child_list.append(next_num)
                                else:
                                    return

    def get_child_lines(self):

        for line_num in self.axis_child_list:
            with open(self.node_filename, 'r') as node_file:
                for num, line in enumerate(node_file, 1):
                    if num == (line_num + 1):
                        self.axis_child_lines_list.append(line)

    def get_line_value(self, line_number):

        with open(self.node_filename, 'r') as node_file:
            for num, line in enumerate(node_file, 1):
                if num == line_number:
                    item_value = line.rsplit(' ', 1)[1]
                    return item_value

    #-------------------------------------#

    def get_selected_node(self):
        import flame

        # Get node from selected node or selected action media node

        node_type = str(flame.batch.current_node.get_value().type)[1:-1]

        if node_type == 'Action Media':
            node_value = flame.batch.current_node.get_value()
            node_sockets = node_value.sockets
            output_dict = node_sockets.get('output')
            action_node_name = output_dict.get('Result')[0]
            node = flame.batch.get_node(action_node_name)
        else:
            node_name = str(flame.batch.current_node.get_value().name)[1:-1]
            node = flame.batch.get_node(node_name)

        return node

    def name_axis(self, axis_num=0):
        import flame

        existing_nodes = [str(node.name)[1:-1] for node in self.selected_node.nodes]

        axis_name = 'inverted_axis_fr' + str(self.current_frame) + '_' + str(axis_num)

        if axis_name not in existing_nodes:
            inverted_axis_name = axis_name
            return inverted_axis_name
        axis_num = axis_num + 1

        return self.name_axis(axis_num)

    def copy_axis_values(self, axis_to_invert, axis_node):

        axis_to_invert.position = axis_node.position.get_value()
        axis_to_invert.rotation = axis_node.rotation.get_value()
        axis_to_invert.scale = axis_node.scale.get_value()
        axis_to_invert.shear = axis_node.shear.get_value()
        axis_to_invert.center = axis_node.center.get_value()

    def save_selected_node(self):
        import flame

        # Create temp save dir

        try:
            os.makedirs(self.temp_folder)
        except:
            shutil.rmtree(self.temp_folder)
            os.makedirs(self.temp_folder)

        # Save selected node

        self.selected_node.save_node_setup(self.save_node_path)

    def reload_selected_node(self):

        # Reload node setup

        self.selected_node.load_node_setup(self.save_node_path)

    def remove_temp_folder(self):

        # Remove temp folder

        shutil.rmtree(self.temp_folder)

#-------------------------------------#

def invert(selection):

    invert = InvertAxis(selection)
    invert.create_inverted_axis()

def invert_parent(selection):

    invert = InvertAxis(selection)
    invert.invert_parent_axis()

def scope_gmask_tracer_axis(selection):
    import flame

    if selection and selection[0].type == 'Axis' and selection[0].parent.type == 'GMask Tracer':
        return True
    return False

def scope_action_axis(selection):
    import flame

    if selection and selection[0].type == 'Axis' and selection[0].parent.type == 'Action':
        return True
    return False

#-------------------------------------#

def get_action_custom_ui_actions():

    return [
        {
            'name': 'Axis...',
            'actions': [
                {
                    'name': 'Create Inverted Axis At Current Frame',
                    'isVisible': scope_action_axis,
                    'execute': invert,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Invert Parent Axis At Current Frame',
                    'isVisible': scope_action_axis,
                    'execute': invert_parent,
                    'minimumVersion': '2022'
                },
                                {
                    'name': 'GMask - Create Inverted Axis At Current Frame',
                    'isVisible': scope_gmask_tracer_axis,
                    'execute': invert,
                    'minimumVersion': '2023'
                },
                {
                    'name': 'GMask - Invert Parent Axis At Current Frame',
                    'isVisible': scope_gmask_tracer_axis,
                    'execute': invert_parent,
                    'minimumVersion': '2023'
                }
            ]
        }
    ]
