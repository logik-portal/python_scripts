'''
Script Name: Delete Folders
Script Version: 2.3
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 10.04.20
Update Date: 05.24.22

Custom Action Type: MediaHub - Files

Description:

    Delete one or more folders along with contents in the MediaHub Files view

    *** WARNING - THIS WILL DELETE ALL SELECTED FOLDERS/SUBFOLDERS - THIS IS NOT UNDOABLE***

Menu:

    Right-click with folders selected -> Delete... -> Delete Selected Folders

To install:

    Copy script into /opt/Autodesk/shared/python/delete_folders

Updates:

    v2.3 05.24.22

        Messages print to Flame message window - Flame 2023.1 and later

    v2.2 03.14.22

        Added delete confirmation

    v2.1 05.19.21

        Updated to be compatible with Flame 2022/Python 3.7
'''

from pyflame_lib_delete_folders import FlameMessageWindow, pyflame_print
import shutil

SCRIPT_NAME = 'Delete Folders'
VERSION = 'v2.3'

def delete_folders(selection):
    import flame

    print('\n')
    print('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

    if FlameMessageWindow('warning', 'Confirm Delete Operation', f'Delete selected folder(s)?<br><br>All files and sub-folders in selected folder(s) will be deleted.<br><br>This cannot be undone.'):
        for folder in selection:
            print('deleting:', folder.path[:-1])
            shutil.rmtree(folder.path)

        print('\n')

        flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

        pyflame_print(SCRIPT_NAME, 'Selected folders deleted.')

def scope_folder(selection):

    for item in selection:
        if 'FilesFolder' in str(item):
            return True
    return False

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Delete...',
            'actions': [
                {
                    'name': 'Delete Selected Folders',
                    'isVisible': scope_folder,
                    'execute': delete_folders,
                    'minimumVersion': '2022'
                },
            ]
        }
    ]
