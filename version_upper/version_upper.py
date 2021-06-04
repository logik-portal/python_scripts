'''
Script Name: Version Upper
Script Version: 1.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 06.06.20
Update Date: 06.06.20

Custom Action Type: MediaPanel

Description:

    This will version up all of your selected clips/sequences as long as they end in "_v##"
'''

from __future__ import print_function

folder_name = "Renamers"
action_name = "Version Upper"

def version_upper(selection):
    import flame
    import re

    for item in selection:
        oldName = str(item.name)[(1):-(1)]
        baseName = re.split("_v"'(\d+)', oldName)[0]
        oldVersion = re.split("_v"'(\d+)', oldName)[1]
        newVersion = int(oldVersion)+int(1)
        print ("*" * 100)
        print ("oldName: ", oldName)
        print ("baseName: ", baseName)
        print ("oldVersion: ", oldVersion)
        print ("NewName: " + baseName + "_v" + '%02d' % newVersion)
        item.name = baseName + "_v" + '%02d' % newVersion
    print ("*" * 100)
    print ("\n" *2)

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def scope_not_desktop(selection):
    import flame

    for item in selection:
        if not isinstance(item, flame.PyDesktop):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': folder_name,
            'actions': [
                {
                    'name': action_name,
                    'isVisible': scope_not_desktop,
                    'execute': version_upper,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
