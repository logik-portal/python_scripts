"""
Script Name: version_upper
Script Version: 2.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 06.06.20
Update Date: 07.12.21

Description: This will version up all of your selected items as long as the names contains "_v##". Case sensitive.
If you like to use another letter, change "v" on lines 31, 33, and 37.

Update: 07.12.21 - Items do not need to end in "v##" anymore. "v##" can be anywhere in the item name. If it cannot find "v##" that item will be skipped, but you will see an
error message in the Flame UI and the script continues.

Menus:
    With a selection of clips, sequences, reels, or folders, right click and look for Renamers -> Version Upper.

"""

from __future__ import print_function

folder_name = "Renamers"
action_name = "Version Upper"

def version_upper(selection):
    import flame
    import re

    for item in selection:
        clip_name = str(item.name)[(1):-(1)]
        if re.search(r'v\d+', clip_name):
            print ("*" * 100)
            print ("Original Name: " + clip_name)
            version = str(re.findall(r'v\d+', clip_name))[(2):-(2)]
            print ("Version: ", version)
            version_number = re.split('v', version)[1]
            print ("Version Number: " + version_number)
            version_number = '%02d' % (int(version_number)+1)
            print ("New Version Number: " + str(version_number))
            new_version_name = re.sub('v\d+',"v" + str(version_number),clip_name)
            print ("New Version Name: ", new_version_name)
            item.name = new_version_name
        else:
            print ("Needs a version number like v01.")
            message = clip_name + str(" needs a version number like 'v01.'")
            show_confirm_dialog(message, "Needs Version")
            continue

    print ("*" * 100)
    print ("\n" *2)


def show_confirm_dialog(text, title):
    """
    Show a dialog box using PySide/QT.
    """
    from PySide2.QtWidgets import QMessageBox

    msg_box = QMessageBox()
    msg_box.setText(text)
    msg_box.setWindowTitle(title)
    msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg_box.setDefaultButton(QMessageBox.Ok)
    return msg_box.exec_() == QMessageBox.Ok

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
