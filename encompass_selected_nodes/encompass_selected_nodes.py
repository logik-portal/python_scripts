'''
Script Name: Encompass Selected Nodes
Script Version: 2.0
Flame Version: 2020.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 04.22.20
Update Date: 05.23.21

Custom Action Type: Batch

Description:

    Creates compass around selected nodes

    Select nodes to encompass -> Right-click on a selected node -> Compass... -> Encompass Selected Nodes

To install:

    Copy script into /opt/Autodesk/shared/python/encompass_selected_nodes

Updates:

v2.0 05.23.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.1 05.10.20

    Added ability to encompass selected action nodes
'''

from __future__ import print_function

VERSION = 'v2.0'

def encompass_action_nodes(selection):
    import flame

    print ('\n', '>' * 20, 'encompass selected nodes %s - action' % VERSION, '<' * 20, '\n')

    node_list = [node for node in selection]

    flame.batch.current_node.get_value().encompass_nodes(node_list)


def encompass_batch_nodes(selection):
    import flame

    print ('\n', '>' * 20, 'encompass selected nodes %s - batch' % VERSION, '<' * 20, '\n')

    node_list = [node for node in selection]

    flame.batch.encompass_nodes(node_list)

def scope_action_node(selection):
    import flame

    for n in selection:
        if isinstance(n, flame.PyCoNode):
            return True
        return False

def scope_node(selection):
    import flame

    for n in selection:
        if isinstance(n, flame.PyNode):
            return True
        return False

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Compass...',
            'actions': [
                {
                    'name': 'Encompass Selected Nodes',
                    'isVisible': scope_node,
                    'execute': encompass_batch_nodes,
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]

def get_action_custom_ui_actions():

    return [
        {
            'name': 'Compass...',
            'actions': [
                {
                    'name': 'Encompass Selected Nodes',
                    'isVisible': scope_action_node,
                    'execute': encompass_action_nodes,
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]
