'''
Script Name: save_and_export_mp4
Script Version: 1.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 07.28.21
Update Date: 07.28.21

Description: This will save your selection into the FROM_FLAME Shared Library under Dated and Timestamped folers. Then it will export into a dated and timestamped folder in the FROM_FLAME folder in your job.
It works with a selection of clips, sequences, folders, or reels. Basically anything but a Desktop. Then it changes the extension from .mov to .mp4.

To change for your facility modify the paths in lines: 48, 58, 142 & 143

'''

from __future__ import print_function

folder_name = "Export"

def export_and_copy_path(selection):
    import flame
    import os, sys
    from PySide2 import QtWidgets
    import datetime

    global export_path

    wks = flame.project.current_project.current_workspace
    dsk = flame.project.current_project.current_workspace.desktop
    project_nickname = flame.project.current_project.nickname
    project_name = flame.project.current_project.name

    dateandtime = datetime.datetime.now()
    today = (dateandtime.strftime("%Y-%m-%d"))
    time = (dateandtime.strftime("%H%M"))

    #Check for FROM_FLAME Shared Library if missing create one
    get_shared_library_list()

    if type(from_flame_library_number) == int:
        print ('FROM_FLAME: ', from_flame_library_number)
        sharedlib = flame.projects.current_project.shared_libraries[from_flame_library_number]
    else:
        print ('Cannot Find FROM_FLAME Shared Libray.')
        sharedlib = flame.project.current_project.create_shared_library('FROM_FLAME')

    #Define Export Path & Check for Preset
    job_folder = os.path.join("/Volumes/vfx/UC_Jobs")
    preset_path_ProResHQ = "/opt/Autodesk/shared/python/save_and_export_mp4/presets/H264_8Mbits.xml"
    preset_check = (str(os.path.isfile(preset_path_ProResHQ)))
    if preset_check == 'True':
        print ("Export Preset Found")
    else:
        print ('Export Preset Not Found.')
        show_confirm_dialog("Cannot find Export Preset.", "Missing Export Preset")
        return

    export_dir = str(job_folder)+ "/" + str(project_nickname) + "/FROM_FLAME" + "/" + str(today)

    #Define Exporter
    exporter = flame.PyExporter()
    exporter.foreground = True
    exporter.export_between_marks = True
    exporter.use_top_video_track = True

    #Get SubFolder Names
    # folder_names = [f.name for f in sharedlib.folders]
    folder_list = []
    for folders in sharedlib.folders:
        folder_name = str(folders.name)[1:-1]
        folder_list.append(folder_name)
        print ("folder_list: ", folder_list)

    #  Look for Today's folder and then copy and export
    today_folder_number = 'TEST'
    for i in [i for i, x in enumerate(folder_list) if x == today]:
        today_folder_number = i
    if type(today_folder_number) == int:
        print ("Today's Folder # is: ", today_folder_number)
        sharedlib.acquire_exclusive_access()
        postingfolder = sharedlib.folders[today_folder_number].create_folder(time)
        tab = flame.get_current_tab()
        if tab == 'MediaHub':
            flame.set_current_tab("Timeline")
        for item in selection:
            flame.media_panel.copy(item, postingfolder)
        exporter.export(postingfolder, preset_path_ProResHQ, export_dir)
        sharedlib.expanded = False
        sharedlib.release_exclusive_access()
        posted_folder = postingfolder.name
        export_path = str(export_dir) + "/" + str(posted_folder)[1:-1]
        qt_app_instance = QtWidgets.QApplication.instance()
        qt_app_instance.clipboard().setText(export_path)
        rename_to_mp4(export_path)
        message_box('Export Path has been copied to Clipboard.')
    else:
        print ("Today's Folder Not Found")
        sharedlib.acquire_exclusive_access()
        postingfolder = sharedlib.create_folder(today).create_folder(time)
        tab = flame.get_current_tab()
        if tab == 'MediaHub':
            flame.set_current_tab("Timeline")
        for item in selection:
            flame.media_panel.copy(item, postingfolder)
        exporter.export(postingfolder, preset_path_ProResHQ, export_dir)
        sharedlib.expanded = False
        sharedlib.release_exclusive_access()
        posted_folder = postingfolder.name
        export_path = str(export_dir) + "/" + str(posted_folder)[1:-1]
        qt_app_instance = QtWidgets.QApplication.instance()
        qt_app_instance.clipboard().setText(export_path)
        rename_to_mp4(export_path)
        message_box('Export Path has been copied to Clipboard.')

def export_and_copy_path_manual(selection):
    import flame
    import os, sys
    from PySide2 import QtWidgets
    import datetime

    global export_path

    wks = flame.project.current_project.current_workspace
    dsk = flame.project.current_project.current_workspace.desktop
    project_nickname = flame.project.current_project.nickname
    project_name = flame.project.current_project.name

    dateandtime = datetime.datetime.now()
    today = (dateandtime.strftime("%Y-%m-%d"))
    time = (dateandtime.strftime("%H%M"))

    #Check for FROM_FLAME Shared Library if missing create one
    get_shared_library_list()
    if type(from_flame_library_number) == int:
        print ('FROM_FLAME: ', from_flame_library_number)
        sharedlib = flame.projects.current_project.shared_libraries[from_flame_library_number]
    else:
        print ('Cannot Find FROM_FLAME Shared Libray.')
        sharedlib = flame.project.current_project.create_shared_library('FROM_FLAME')

    #Define Export Path
    jobs_folder = os.path.join("/Volumes/vfx/UC_Jobs")
    export_dir = str(jobs_folder)+ "/" + str(project_nickname) + "/FROM_FLAME" + "/" + str(today)
    preset_path = "/opt/Autodesk/shared/python/save_and_export_mp4/presets"
    my_preset = QtWidgets.QFileDialog.getOpenFileName(None, "Select Preset", preset_path, "XML Files (*.xml)")[0]
    preset_path_ProResHQ = str(my_preset)

    #Define Exporter
    exporter = flame.PyExporter()
    exporter.foreground = True
    exporter.export_between_marks = True
    exporter.use_top_video_track = True

    #Get SubFolder Names
    # folder_names = [f.name for f in sharedlib.folders]
    folder_list = []
    for folders in sharedlib.folders:
        folder_name = str(folders.name)[1:-1]
        folder_list.append(folder_name)
        print ("folder_list: ", folder_list)

    #  Look for Today's folder and then copy and export
    today_folder_number = 'TEST'
    for i in [i for i, x in enumerate(folder_list) if x == today]:
        today_folder_number = i
    if type(today_folder_number) == int:
        print ("Today's Folder # is: ", today_folder_number)
        sharedlib.acquire_exclusive_access()
        postingfolder = sharedlib.folders[today_folder_number].create_folder(time)
        tab = flame.get_current_tab()
        if tab == 'MediaHub':
            flame.set_current_tab("Timeline")
        for item in selection:
            flame.media_panel.copy(item, postingfolder)
        exporter.export(postingfolder, preset_path_ProResHQ, export_dir)
        sharedlib.expanded = False
        sharedlib.release_exclusive_access()
        posted_folder = postingfolder.name
        export_path = str(export_dir) + "/" + str(posted_folder)[1:-1]
        qt_app_instance = QtWidgets.QApplication.instance()
        qt_app_instance.clipboard().setText(export_path)
        rename_to_mp4(export_path)
        message_box('Export Path has been copied to Clipboard.')
    else:
        print ("Today's Folder Not Found")
        sharedlib.acquire_exclusive_access()
        postingfolder = sharedlib.create_folder(today).create_folder(time)
        tab = flame.get_current_tab()
        if tab == 'MediaHub':
            flame.set_current_tab("Timeline")
        for item in selection:
            flame.media_panel.copy(item, postingfolder)
        exporter.export(postingfolder, preset_path_ProResHQ, export_dir)
        sharedlib.expanded = False
        sharedlib.release_exclusive_access()
        posted_folder = postingfolder.name
        export_path = str(export_dir) + "/" + str(posted_folder)[1:-1]
        qt_app_instance = QtWidgets.QApplication.instance()
        qt_app_instance.clipboard().setText(export_path)
        rename_to_mp4(export_path)
        message_box('Export Path has been copied to Clipboard.')

def export_and_open_finder(selection):
    export_and_copy_path(selection)
    openFinder(export_path)

def export_and_open_finder_manual(selection):
    export_and_copy_path_manual(selection)
    openFinder(export_path)

def get_shared_library_list():
    import flame
    global from_flame_library_number
    #Find the "FROM_FLAME" Shared Library - If not, create one.
    shared_libs = flame.projects.current_project.shared_libraries
    shared_library_list = []
    for libraries in shared_libs:
        shared_library_name = str(libraries.name)[1:-1]
        shared_library_list.append(shared_library_name)

    from_flame_library_number = 'TEST'
    for i in [i for i, x in enumerate(shared_library_list) if x == 'FROM_FLAME']:
        from_flame_library_number = i

def rename_to_mp4(clipPath):
    import os
    import glob

    export_path = clipPath + '/**/*'
    files = glob.glob(export_path, recursive=True)
    print (files)
    for filename in files:
        if os.path.splitext(filename)[1] == ".mov":
            os.rename(filename, filename[:-4] + '.mp4')

def openFinder(clipPath):
    import platform
    import subprocess
    if platform.system() == 'Darwin':
        subprocess.Popen(['open', clipPath])
    else:
        subprocess.Popen(['xdg-open', clipPath])

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

def message_box(message):
    from PySide2 import QtWidgets

    message_box_window = QtWidgets.QMessageBox()
    message_box_window.setWindowTitle('Big Success')
    message_box_window.setText('<b><center>%s' % message)
    message_box_window.setStandardButtons(QtWidgets.QMessageBox.Ok)
    message = message_box_window.exec_()

    return message

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
                    'name': "Export H264 and Copy Path - Automatic",
                    'isVisible': scope_not_desktop,
                    'execute': export_and_copy_path,
                    'minimumVersion': '2021'
                },
                {
                    'name': "Export H264 and Copy Path - Manual",
                    'isVisible': scope_not_desktop,
                    'execute': export_and_copy_path_manual,
                    'minimumVersion': '2021'
                },
                {
                    "name": "Export H264 and Reveal in Finder - Automatic",
                    "isVisible": scope_not_desktop,
                    "execute": export_and_open_finder,
                    'minimumVersion': '2021'
                },
                {
                    "name": "Export H264 and Reveal in Finder - Manual",
                    "isVisible": scope_not_desktop,
                    "execute": export_and_open_finder_manual,
                    'minimumVersion': '2021'
                },

            ]
        }
    ]
