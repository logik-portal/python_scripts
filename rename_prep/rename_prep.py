'''
Script Name: Rename Prep
Script Version: 1.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 01.01.20
Update Date: 01.01.20

Description:

    Rename AAF Prep
'''

from __future__ import print_function

folder_name = "Renamers"
action_name = "Rename Prep"

def rename_aaf_seq(selection):
    import flame

    for item in selection:
        print ("\n" *1)
        print ("*" * 10)
        seq_name = str(item.name)[(1):-(1)]
        print ("Start Name: ", seq_name)
        remove = ["_v1_", "_v2","_01_", "Copy", "_copy", ".Exported.01","_export_", "_exported_", "'","_CONFORM","CONFORM","_AAF","_XML","_Conform","_PREP","PREP","_PRE_CONFORM","PRE_CONFORM"]
        underscore = [" - "," ",]
        for items in underscore:
            if items in seq_name:
                seq_name = seq_name.replace(items, "_")
        for items in remove:
            if items in seq_name:
                seq_name = seq_name.replace(items, "")
        seq_name = seq_name.split("_Exported")[0]
        seq_name = seq_name.replace('v', "V")
        item.name = seq_name+"_CONFORM_v01"
        print ("New Name: ", seq_name + "_CONFORM_v01")
        print ("*" * 10)
        print ("\n" *1)

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
