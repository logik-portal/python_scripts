'''
Script Name: Delete Folders
Script Version: 2.1
Flame Version: 2022
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 10.04.20
Update Date: 05.19.21

Custom Action Type: MediaHub - Files

Description:

    Delete one or more folders along with contents in the MediaHub Files view

    *** WARNING - THIS WILL DELETE ALL SELECTED FOLDERS/SUBFOLDERS WITHOUT CONFIRMATION ***

    Right-click with folders selected -> Delete... -> Delete Selected Folders

To install:

    Copy script into /opt/Autodesk/shared/python/delete_folders

Updates:

v2.1 05.19.21

    Updated to be compatible with Flame 2022/Python 3.7
'''

from __future__ import print_function

VERSION = 'v2.1'

def delete_folders(selection):
    import shutil
    import flame

    print ('\n', '>' * 20, 'delete folders %s' % VERSION, '<' * 20, '\n')

    for folder in selection:
        print ('deleting:', folder.path[:-1])
        shutil.rmtree(folder.path)

    flame.execute_shortcut("Refresh the MediaHub's Folders and Files")

    print ('\ndone.\n')

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
