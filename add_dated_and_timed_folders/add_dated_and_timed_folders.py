'''
Script Name: Add Dated and Timed Folders
Script Version: 1.1
Flame Version: 2020
Written by: John Geehreng
Creation Date: 07.04.20
Update Date: 03.02.21

Description: Add dated and/or timestamped folders to a selection which must be a library or a folder.
                3.2.21 - Updated to work with strftime
'''

folder_name = "Folders"

def date_time_folders(selection):
    import datetime
    import flame

    #set variables
    dateandtime = datetime.datetime.now()
    today = (dateandtime.strftime("%Y-%m-%d"))
    time = (dateandtime.strftime("%H%M"))

    for item in selection:
        item.create_folder(today).create_folder(time)

def dated_folders(selection):
    import datetime
    import flame

    #set variables
    dateandtime = datetime.datetime.now()
    today = (dateandtime.strftime("%Y-%m-%d"))

    for item in selection:
        item.create_folder(today)

def timed_folders(selection):
    import datetime
    import flame

    #set variables
    dateandtime = datetime.datetime.now()
    time = (dateandtime.strftime("%H%M"))

    for item in selection:
        item.create_folder(time)

                #Scopes
#-----------------------------------------#

def scope_library_or_folder(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PyLibrary, flame.PyFolder)):
            return True
    return False

def scope_folder(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyFolder):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': folder_name,
            'actions': [
                {
                    'name': "Add Dated and Timestamped Folders",
                    'isVisible': scope_library_or_folder,
                    'execute': date_time_folders,
                    'minimumVersion': '2020'
                }
            ]
        },
        {
            'name': folder_name,
            'actions': [
                {
                    'name': 'Add Dated Folder',
                    'isVisible': scope_library_or_folder,
                    'execute': dated_folders,
                    'minimumVersion': '2020'
                }
            ]
        },
        {
            'name': folder_name,
            'actions': [
                {
                    'name': 'Add Timestamped Folder',
                    'isVisible': scope_folder,
                    'execute': timed_folders,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
