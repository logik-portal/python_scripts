'''
Script Name: Add System Folders
Script Version: 1.2
Flame Version: 2020
Written by: John Geehreng
Creation Date: 11.04.20
Updated: 03.02.21

Custom Action Type: MediaHub - Files

Description: Add dated or timestamped system folders in the media hub.
                3.2.21 - Updated to work with strftime
'''

from __future__ import print_function

def create_dated_folder(selection):
    import datetime
    import flame
    import os, sys
    from PySide2 import QtWidgets

    #set variables
    dateandtime = datetime.datetime.now()
    today = (dateandtime.strftime("%Y-%m-%d"))
    now = (dateandtime.strftime("%H%M"))
    shot_folder = os.path.join(flame.mediahub.files.get_path(), today)

    if not os.path.isdir(shot_folder):
        os.makedirs(shot_folder)

    else:
        return message_box('Cannot create Folder. Folder already exists.')

        print ('\n>>> %s shot folder created <<<\n' % today)

    flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

def create_timestamped_folder(selection):
    import datetime
    import flame
    import os, sys
    from PySide2 import QtWidgets

    #set variables
    dateandtime = datetime.datetime.now()
    today = (dateandtime.strftime("%Y-%m-%d"))
    now = (dateandtime.strftime("%H%M"))
    shot_folder = os.path.join(flame.mediahub.files.get_path(), now)

    if not os.path.isdir(shot_folder):
        os.makedirs(shot_folder)

    else:
        return message_box('Cannot create Folder. Folder already exists.')

        print ('\n>>> %s shot folder created <<<\n' % today)

    flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

def create_dated_folder_with_timestamped_subfolder(selection):
    import datetime
    import flame
    import os, sys
    from PySide2 import QtWidgets

    #set variables
    dateandtime = datetime.datetime.now()
    today = (dateandtime.strftime("%Y-%m-%d"))
    now = (dateandtime.strftime("%H%M"))
    dateandtime = str(today) + "/" + str(now)
    shot_folder = os.path.join(flame.mediahub.files.get_path(), dateandtime)

    if not os.path.isdir(shot_folder):
        os.makedirs(shot_folder)

    else:
        return message_box('Cannot create Folder. Folder already exists.')

        print ('\n>>> %s shot folder created <<<\n' % today)

    flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

def message_box(message):
    from PySide2 import QtWidgets

    message_box_window = QtWidgets.QMessageBox()
    message_box_window.setWindowTitle('Fail')
    message_box_window.setText('<b><center>%s' % message)
    message_box_window.setStandardButtons(QtWidgets.QMessageBox.Ok)
    message = message_box_window.exec_()

    return message

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Folders',
            'actions': [
                {
                    'name': 'Create Dated Folder',
                    'execute': create_dated_folder,
                    'minimumVersion': '2021.2'
                },
                                {
                    'name': 'Create Dated and Timestamped Folders',
                    'execute': create_dated_folder_with_timestamped_subfolder,
                    'minimumVersion': '2021.2'
                },
                {
                    'name': 'Create Timestamped Folder',
                    'execute': create_timestamped_folder,
                    'minimumVersion': '2021.2'
                },
            ]
        }
    ]
