'''
Script Name: Invert Axis
Script Version: 2.0
Flame Version: 2021.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 07.26.19
Update Date: 05.23.21

Custom Action Type: Action

Description:

    Create inverted axis at current frame or copy parent axis and invert at current frame

    Right-click on axis node -> Invert Axis... -> Create Inverted Axis
    Right-click on axis node -> Invert Axis... -> Copy Parent Axis Values and Invert

To install:

    Copy script into /opt/Autodesk/shared/python/invert_axis

Updates:

v2.0 05.23.21

    Updated to be compatible with Flame 2022/Python 3.7

    Fixed inverting axis not working when multiple axis parented to same axis

v1.5 05.10.20

    Inverted axis is now added as child of selected axis

v1.3 10.24.19

    Menu's now show up under Invert Axis... when right-clicking on axis node in action schematic
    Removed menu's from showing up in GMask Tracer. Action python commands do not work in GMask Tracer.
'''

from __future__ import print_function

VERSION = 'v2.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/invert_axis'

class InvertAxis(object):

    def __init__(self, selection):
        import flame
        import os

        self.current_frame = flame.batch.current_frame

        # Get selected axis

        for selected_axis in selection:
            self.selected_axis = selected_axis
            self.axis_name = str(selected_axis.name)[1:-1]

        # Temp folder for saving action setup

        self.temp_folder = os.path.join(SCRIPT_PATH, 'temp_action')

        # Action variables

        self.action_node = flame.batch.current_node.get_value()
        self.action_node_name = str(self.action_node.name)[1:-1]
        self.save_action_path = os.path.join(self.temp_folder, self.action_node_name)
        self.action_filename = self.save_action_path + '.action'

        # Init lists

        self.axis_child_list = []
        self.axis_child_lines_list = []

    def create_inverted_axis(self):
        import flame

        print ('\n', '>' * 20, 'invert axis %s - create inverted axis' % VERSION, '<' * 20, '\n')

        # Create new axis node

        self.inverted_axis = self.action_node.create_node('Axis')
        self.inverted_axis_name = self.name_axis()
        self.inverted_axis.name = self.inverted_axis_name

        # Copy axis values

        self.copy_axis_values(self.inverted_axis, self.selected_axis)

        # Connect nodes

        self.action_node.connect_nodes(self.selected_axis, self.inverted_axis)

        # Save action node

        self.save_action_node()

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

        # Edit action lines

        edit_action = open(self.action_filename, 'r')
        contents = edit_action.readlines()
        edit_action.close()

        # Position New Inverted Axis in Selected Axis Position

        contents[inverted_axis_pos_x_line] = '        PosX %s' % selected_axis_pos_x
        contents[inverted_axis_pos_y_line] = '        PosY %s' % selected_axis_pos_y
        contents[invert_mode_line] = '                InvertMode yes'

        # Reposition Selected Axis above Inverted Axis

        contents[selected_axis_pos_y_line] = '        PosY %s\n' % selected_axis_new_pos_y

        ## Remove child connections from Selected Axis

        for line_number in self.axis_child_list:

            contents[line_number] = ''

        # Insert lines for inverted axis child connections

        for child_line in self.axis_child_lines_list:
            contents.insert(insert_line_number, child_line)

        # Save modified action file

        edit_action = open(self.action_filename, 'w')
        contents = ''.join(contents)
        edit_action.write(contents)
        edit_action.close()

        # Reload saved action node

        self.reload_action_node()

        # Remove temp action folder

        self.remove_temp_folder()

        print ('>>> inverted axis created <<<')

    def invert_parent_axis(self):
        import flame

        print ('\n', '>' * 20, 'invert axis %s - invert parent axis' % VERSION, '<' * 20, '\n')

        # Save action node

        self.save_action_node()

        # Get parent axis info
        # --------------------

        # Find selected axis node number

        item_line = self.find_line(self.axis_name)
        line_number = self.find_line_after('Number', item_line)
        item_value = self.get_line_value(line_number)
        axis_number = item_value

        # Find parent of selected axis

        item_line = self.find_line('Child %s' % axis_number)
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

            # Save action node

            self.save_action_node()

            # Get list of all nodes in action node

            action_node_list = []

            action_node = flame.batch.current_node.get_value()

            for item in action_node.nodes:
                action_node_list.append(item)

            # Get parent axis

            for item in action_node_list:
                node_name = str(item.name)[1:-1]
                if node_name == parent_axis_name:
                    axis_node = item

            # Copy axis values

            self.copy_axis_values(self.selected_axis, axis_node)

            self.save_action_node()

            # Invert axis
            # Get axis invert mode line

            item_line = self.find_line(axis_name)
            line_number = self.find_line_after('InvertMode', item_line)
            invert_mode_line = line_number - 1

            # Edit action lines to repo inverted axis above selected axis

            edit_action = open(self.action_filename, 'r')
            contents = edit_action.readlines()
            edit_action.close()

            contents[invert_mode_line] = '                InvertMode yes'

            edit_action = open(self.action_filename, 'w')
            contents = ''.join(contents)
            edit_action.write(contents)
            edit_action.close()

            # Reload action setup

            action_node.load_node_setup(self.save_action_path)

            # Remove temp action file

            self.remove_temp_folder()

            print ('\n', '>>> inverted axis created <<<', '\n')

        else:
            # If no parent axis, remove temp action file

            self.remove_temp_folder()

            print ('\n', '>>> no parent axis to invert <<<', '\n')

    #-------------------------------------#

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

    def find_child_lines(self, item, item_line_num):

        # Find all child lines for an axis

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if num >= item_line_num:
                    if item in line:
                        first_child_line = num - 1
                        self.axis_child_list.append(first_child_line)
                        for next_num, line in enumerate(action_file, first_child_line):
                            if next_num > first_child_line:
                                if item in line:
                                    self.axis_child_list.append(next_num)
                                else:
                                    return

    def get_child_lines(self):

        for line_num in self.axis_child_list:
            with open(self.action_filename, 'r') as action_file:
                for num, line in enumerate(action_file, 1):
                    if num == (line_num + 1):
                        self.axis_child_lines_list.append(line)

    def get_line_value(self, line_number):

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if num == line_number:
                    item_value = line.rsplit(' ', 1)[1]
                    return item_value

    def save_action_node(self):
        import shutil
        import flame
        import os

        # Create temp action save dir

        try:
            os.makedirs(self.temp_folder)
        except:
            shutil.rmtree(self.temp_folder)
            os.makedirs(self.temp_folder)

        # Save action node

        action_node = flame.batch.get_node(self.action_node_name)
        action_node.save_node_setup(self.save_action_path)

    def reload_action_node(self):

        # Reload action setup

        self.action_node.load_node_setup(self.save_action_path)

    def remove_temp_folder(self):
        import shutil

        # Remove temp action folder

        shutil.rmtree(self.temp_folder)

    def name_axis(self, axis_num=0):
        import flame

        existing_nodes = []

        for node in flame.batch.current_node.get_value().nodes:
            node_name = str(node.name)[1:-1]
            existing_nodes.append(node_name)

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

#-------------------------------------#

def invert(selection):

    invert = InvertAxis(selection)
    invert.create_inverted_axis()

def invert_parent(selection):

    invert = InvertAxis(selection)
    invert.invert_parent_axis()

def scope_axis(selection):
    import flame

    for item in selection:
        print (item)
        print (item.type)
        # if flame.batch.current_node.get_value().type == 'Action':
        if item.type == 'Axis':
            return True
    return False

#-------------------------------------#

def get_action_custom_ui_actions():

    return [
        {
            'name': 'Invert Axis...',
            'actions': [
                {
                    'name': 'Create Inverted Axis At Current Frame',
                    'isVisible': scope_axis,
                    'execute': invert,
                    'minimumVersion': '2021.1'
                },
                {
                    'name': 'Invert Parent Axis At Current Frame',
                    'isVisible': scope_axis,
                    'execute': invert_parent,
                    'minimumVersion': '2021.1'
                }
            ]
        }
    ]
