'''
Script Name: Add Mux
Script Version: 2.1
Flame Version: 2021
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 07.31.19
Update Date: 05.19.21

Custom Action Type: Batch

Description:

    Add regular mux node or frame locked mux to batch

    Right-click in batch -> Add Mux... -> Add MUX / Add Freeze Frame MUX
    Right-click on node in batch -> Add Mux -> Add MUX / Add Freeze Frame MUX
    Right-click on Mux node in batch -> Add Mux... -> Freeze Selected MUX

To install:

    Copy script into /opt/Autodesk/shared/python/add_mux

Updates:

v2.1 05.19.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.6 05.12.21

    Mux node can now be added at cursor position

    Regular MUX can now be added

v1.5 02.10.20

    Freeze existing mux at current frame
'''

from __future__ import print_function

VERSION = 'v2.1'

def add_mux(selection):
    import flame

    print ('\n', '>' * 10, 'Add MUX %s' % VERSION, '<' * 10, '\n')

    mux_node = flame.batch.create_node('MUX')
    mux_node.name = name_node('mux')

    position_mux(mux_node, selection)

def add_mux_freeze(selection):
    import flame

    print ('\n', '>' * 10, 'Add MUX %s - Add MUX Freeze Frame' % VERSION, '<' * 10, '\n')

    current_frame = flame.batch.current_frame

    mux_node = flame.batch.create_node('MUX')
    mux_node.name = name_node('freeze_frame')
    mux_node.range_active = True
    mux_node.range_start = current_frame
    mux_node.range_end = current_frame
    mux_node.before_range = 'Repeat First'
    mux_node.after_range = 'Repeat Last'

    position_mux(mux_node, selection)

def name_node(node_type, node_num=0):
    import flame

    existing_node_list = []

    for item in flame.batch.nodes:
        existing_node = item.name
        existing_node_list.append(existing_node)

    node_name = 'freeze_frame' + str(node_num)
    node_name = node_type + str(node_num)

    if node_name.endswith('e0'):
        node_name = node_name[:-1]

    if node_name not in existing_node_list:
        node_name = node_name
        return node_name
    else:
        node_num = node_num + 1
        return name_node(node_type, node_num)

def position_mux(mux_node, selection):
    import flame

    # If node is selected, connect mux node

    if selection:
        for item in selection:
            mux_node.pos_x = item.pos_x + 300
            mux_node.pos_y = item.pos_y
            flame.batch.connect_nodes(item, 'Default', mux_node, 'Default')

    # If no node is selected, add mux at cursor position

    else:
        cursor_pos = flame.batch.cursor_position

        mux_node.pos_x = cursor_pos[0]
        mux_node.pos_y = cursor_pos[1]

def freeze_existing_mux(selection):
    import flame

    print ('\n', '>' * 10, 'Add MUX %s - Freeze exisiting MUX node' % VERSION, '<' * 10, '\n')

    current_frame = flame.batch.current_frame

    for mux_node in selection:
        mux_node.range_active = True
        mux_node.range_start = current_frame
        mux_node.range_end = current_frame
        mux_node.before_range = 'Repeat First'
        mux_node.after_range = 'Repeat Last'

def scope_mux_node(selection):

    for item in selection:
        if item.type == 'MUX':
            return True
    return False

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Add Mux...',
            'actions': [
                {
                    'name': 'Add MUX',
                    'execute': add_mux,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Add Freeze Frame MUX',
                    'execute': add_mux_freeze,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Freeze Selected MUX',
                    'isVisible': scope_mux_node,
                    'execute': freeze_existing_mux,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
