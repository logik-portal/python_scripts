'''
Script Name: Add GMask
Script Version: 2.1
Flame Version: 2020
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 01.05.20
Update Date: 05.19.21

Custom Action Type: Batch

Description:

    Add GMask or GMask Tracer node in batch or connected to any node with matte input

    Right click anywhere in batch or on any node with a matte input -> Add GMask... -> Add GMask Tracer Node

    Right click anywhere in batch or on any node with a matte input -> Add GMask... -> Add GMask Node

To install:

    Copy script into /opt/Autodesk/shared/python/add_gmask

Updates:

v2.1 05.19.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.1 05.08.21

    Gmask nodes can now be added loose in batch at cursor position
'''

from __future__ import print_function

VERSION = 'v2.1'

def create_gmask_node(selection, gmask_type):
    import flame

    def add_to_selected_node():
        '''
        Add gmask node to matte output of selected node
        '''

        selected_node = selection[0]

        # Get selected node socket dict

        selected_node_sockets = flame.batch.current_node.get_value().sockets

        # Find node connected to front socket

        connected_node_pos_x = ''

        for n in selected_node_sockets.values():
            if isinstance(n, dict):
                for k, v in n.items():
                    if 'Front' in k:
                        try:
                            connected_node_name = str(v)[2:-2]

                            # Match socket value to node in batch

                            for node in flame.batch.nodes:
                                if str(node.name)[1:-1] == connected_node_name:
                                    connected_node = node
                                    connected_node_pos_x = int(str(connected_node.pos_x))
                                    break
                        except:
                            pass

        # Create gmask tracer node

        gmask_node = flame.batch.create_node(gmask_type)

        if connected_node_pos_x != '':
            gmask_node.pos_x = (connected_node_pos_x - selected_node.pos_x)/2 + selected_node.pos_x
        else:
            gmask_node.pos_x = selected_node.pos_x - 250

        gmask_node.pos_y = selected_node.pos_y - 100

        # Get selected node matte input socket name

        for socket in selected_node.input_sockets:
            if 'Matte' in socket:
                selected_node_socket = socket

        # Connect gmask tracer node

        flame.batch.connect_nodes(gmask_node, 'Default', selected_node, selected_node_socket)

        # Connect gmask tracer front if node connected to selected node

        try:
            flame.batch.connect_nodes(connected_node, 'Default', gmask_node, 'Default')
        except:
            pass

    def add_loose():
        '''
        Add gmask node loose in batch at cursor position
        '''
        gmask_node = flame.batch.create_node(gmask_type)

        cursor_pos = flame.batch.cursor_position

        gmask_node.pos_x = cursor_pos[0]
        gmask_node.pos_y = cursor_pos[1]

    if selection:
        add_to_selected_node()
    else:
        add_loose()

    print ('done.\n')

def add_gmask_tracer(selection):

    gmask_type = 'GMask Tracer'

    print ('\n', '>' * 20, 'add gmask %s - %s' % (VERSION, gmask_type), '<' * 20, '\n')

    create_gmask_node(selection, gmask_type)

def add_gmask(selection):

    gmask_type = 'GMask'

    print ('\n', '>' * 20, 'add gmask %s - %s' % (VERSION, gmask_type), '<' * 20, '\n')

    create_gmask_node(selection, gmask_type)

def scope(selection):
    import flame

    if selection == ():
        return True

    for item in selection:
        if isinstance(item, flame.PyNode):
            for node in selection:
                for socket in node.input_sockets:
                    if 'Matte' in socket:
                        return True

    return False

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Add GMask...',
            'actions': [
                {
                    'name': 'Add GMask Tracer Node',
                    'isVisible': scope,
                    'execute': add_gmask_tracer,
                    'minimumVersion': '2020'
                },
                {
                    'name': 'Add GMask Node',
                    'isVisible': scope,
                    'execute': add_gmask,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
