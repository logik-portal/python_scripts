# Add Batch Nodes

Script Name: Add Batch Nodes
Script Version: 3.1
Flame Version: 2021
Written by: Michael Vaglienty
Creation Date: 04.18.20
Update Date: 10.26.21

Custom Action Type: Batch / Flame Main Menu

Description:

    Create menus that can add nodes to batch

    Works with standard batch nodes/matchboxes/ofx

    All created node menu scripts are saved in /opt/Autodesk/user/YOURUSER/python/batch_node_menus

    Menus:

        To create/rename/delete menus from node lists:
        Flame Main Menu -> pyFlame -> Add Batch Nodes Setup

        To create menus for nodes with settings applied in batch:
        Right-click on node in batch -> Add Batch Node Menu... -> Create Menu For Selected Node

        To create menus for ofx nodes:
        Right-click on node in batch -> Add Batch Node Menu... -> Create Menu Dor Selected Node

        To add node from menu to batch:
        Right-click in batch -> Add Batch Nodes... -> Select Node

        To add node from menu to batch connected to selected node:
        Right-click on node in batch -> Add Batch Nodes... -> Select Node

To install:

    Copy script into /opt/Autodesk/shared/python/add_batch_nodes

Updates:

    v3.1 10.26.21

        Updated config to xml

    v3.0 05.20.21

        Updated to be compatible with Flame 2022/Python 3.7

    v2.5 01.27.21:

        Updated UI

        Menus/Nodes can be renamed after they've been added

    v2.1 05.17.20:

        Misc code updates