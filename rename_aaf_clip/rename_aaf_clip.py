'''
Script Name: Rename AAF Clip
Script Version: 2.0
Flame Version: 2020
Written by: John Fegan
Creation Date: 10.07.19
Update Date: 06.04.21

Custom Action Type: MediaPanel

Description:

    Removes all the extra bull shit that comes across in the file name when importing an aaf from avid.

To install:

    Copy script into /opt/Autodesk/shared/python/rename_aaf_clip

Updates:

v2.0 06.04.21

    Updated to be compatible with Flame 2022/Python 3.7
'''

from __future__ import print_function

folder_name = "Python: Conform"
action_name = "Rename AAF"

def rename_aaf_seq(selection):
    import flame

    for item in selection:
        seq_name = str(item.name)
        print (seq_name)
        remove = ["_v1_", "_v2","_01_", "Copy", "_copy", "_export_", "_exported_", "'"]
        underscore = [" ", "."]
        for items in underscore:
            if items in seq_name:
                seq_name = seq_name.replace(items, "_")
        print (seq_name)
        for items in remove:
            if items in seq_name:
                seq_name = seq_name.replace(items, "").replace('"', "")
        seq_name = seq_name.split("_Exported")[0]
        print (seq_name)
        item.name = seq_name

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': folder_name,
            'actions': [
                {
                    'name': action_name,
                    'isVisible': scope_clip,
                    'execute': rename_aaf_seq,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
