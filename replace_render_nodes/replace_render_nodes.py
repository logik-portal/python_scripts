'''
Script Name: Replace Render Nodes
Script Version: 2.0
Flame Version: 2020
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 02.22.20
Update Date: 06.03.21

Custom Action Type: Batch

Description:

    Use to replace all render nodes in comp when they fail to properly show up in render list

    Right-click in batch -> Render... -> Replace Render Nodes

To install:

    Copy script into /opt/Autodesk/shared/python/replace_render_nodes

Updates:

v2.0 06.03.21

    Updated to be compatible with Flame 2022/Python 3.7
'''

from __future__ import print_function

VERSION = 'v2.0'

def replace_render_nodes(selection):
    import flame

    print ('\n', '>' * 20, ' replace render nodes %s ' % VERSION, '<' * 20, '\n')

    # Duplicate render nodes

    for n in flame.batch.nodes:
        if n.type in ('Render', 'Write File'):
            new_node = n.duplicate(keep_node_connections=True)
            new_node.pos_x = n.pos_x
            new_node.pos_y = n.pos_y
            n.delete()

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Render...',
            'actions': [
                {
                    'name': 'Replace Render Nodes',
                    'execute': replace_render_nodes,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
