'''
Script Name: Rename Keep AD-ID Only
Script Version: 1.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 01.01.20
Update Date: 01.01.20

Description:

    Rename keeping only AD-ID
'''

from __future__ import print_function

folder_name = "Renamers"
action_name = "Keep AD-ID Only"

def keep_ad_id_only(selection):
    import flame
    import re

    for item in selection:
        print ("\n" *1)
        print ("*" * 10)
        seq_name = str(item.name)[(1):-(1)]
        print ("Original Name: ", seq_name)
        ad_id = seq_name[0:12]
        item.name = ad_id
        print ("Truncated Name: ", ad_id)
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
                    'execute': keep_ad_id_only,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
