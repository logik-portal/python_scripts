'''
Script Name: Save Shots to Plates Folder
Script Version: 2.0
Flame Version: 2019
Written by: John Geehreng
Creation Date: 01.01.19
Update Date:

Custom Action Type: Media Panel

Description:

    Save shots to shot folders
'''

from __future__ import print_function

folder_name = "Shots"
action_name = "Save Shots to Flame Shot Folder"

def getSelectLibrary():
    global libraryList

    libraryList = []
    for libraries in wks:
        libraryName = str(libraries.name)[1:-1]
        libraryList.append(libraryName)
        print ('libraryName: ', libraryName)
    print ('libraryList: ', libraryList)

def getShotFolders():
    global shotFolderList

    shotFolderList = []
    for folders in shotLibrary:
        folderName = str(folders.name)[1:-1]
        shotFolderList.append(folderName)
        print ('folderName: ', folderName)
    print ('shotFolderList: ', shotFolderList)

def main_window(selection):
    import flame
    import re
    from PySide2 import QtWidgets, QtCore

    global wks
    wks = flame.project.current_project.current_workspace.libraries

    getSelectLibrary()

    def cancel_button():
        window.close()

    def ok_button():
        print ("*" * 10)

        # Get selected Library name
        selectedLibraryName = str(libraryListCB.currentText())
        print ('selectedLibrayName: ', selectedLibraryName)
        # Get selected library number
        for i in [i for i, x in enumerate(libraryList) if x == selectedLibraryName]:
            selectedLibraryNum = i
        print ('selectedLibraryNum: ', selectedLibraryNum)
        global shotLibrary
        shotLibrary = flame.projects.current_project.current_workspace.libraries[selectedLibraryNum].folders
        getShotFolders()

        for item in selection:
            clipName = str(item.name)[(1):-(1)]
            sequenceName = re.split("_", clipName)[0]
            shotNumber = re.split("_", clipName)[1]
            shotName = str(sequenceName) + "_" + str(shotNumber)
            for f in [f for f, x in enumerate(shotFolderList) if x == shotName]:
                shotFolderNum = f
            print ('shotFolderNum: ', shotFolderNum)

            shotFolder = flame.projects.current_project.current_workspace.libraries[selectedLibraryNum].folders[shotFolderNum].folders[0]

            print ("*" * 10)
            print ("Shot Name = " + str(sequenceName) + "_" + str(shotNumber))
            print ("Clip Name = " + clipName)
            print ("*" * 10)
            flame.media_panel.copy(item, shotFolder)
        window.close()
        message_box('Shot(s) have been saved to shot folders.')

    window = QtWidgets.QWidget()
    window.setMinimumSize(400, 130)
    window.setWindowTitle('Select Library')
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    window.setStyleSheet('background-color: #272727')

    # Center window in linux

    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                (resolution.height() / 2) - (window.frameSize().height() / 2))

    # Labels

    select_lib_label = QtWidgets.QLabel('Select VFX Shot Library: ', window)
    select_lib_label.setAlignment(QtCore.Qt.AlignVCenter)
    select_lib_label.setMinimumWidth(50)
    select_lib_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')

    # Entries

    libraryListCB = QtWidgets.QComboBox(window)
    libraryListCB.addItems(libraryList)
    libraryListCB.setCurrentIndex(2)
    libraryListCB.setMinimumSize(QtCore.QSize(150, 26))
    libraryListCB.setStyleSheet('background: #373e47; font: 14pt "Discreet"')
    # Buttons

    ok_btn = QtWidgets.QPushButton('Ok', window)
    ok_btn.clicked.connect(ok_button)
    ok_btn.setMinimumSize(QtCore.QSize(100, 28))
    ok_btn.setMaximumSize(QtCore.QSize(100, 28))
    ok_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    ok_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                         'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                         'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    cancel_btn = QtWidgets.QPushButton('Cancel', window)
    cancel_btn.clicked.connect(cancel_button)
    cancel_btn.setMinimumSize(QtCore.QSize(100, 28))
    cancel_btn.setMaximumSize(QtCore.QSize(100, 28))
    cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
    cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                             'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                             'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

    # refresh_btn = QtWidgets.QPushButton('Refresh', window)
    # refresh_btn.setMinimumSize(QtCore.QSize(110, 24))
    # refresh_btn.clicked.connect(refresh_button)

    # Layout
    hbox01 = QtWidgets.QHBoxLayout()
    hbox01.addWidget(select_lib_label)
    hbox01.addWidget(libraryListCB)
    # hbox01.addStretch(5)

    # hbox02 = QtWidgets.QHBoxLayout()
    # hbox02.addStretch(5)
    # hbox02.addWidget(refresh_btn)
    # hbox02.addStretch(5)

    hbox03 = QtWidgets.QHBoxLayout()
    hbox03.addStretch(5)
    hbox03.addWidget(ok_btn)
    hbox03.addStretch(5)
    hbox03.addWidget(cancel_btn)
    hbox03.addStretch(5)

    vbox = QtWidgets.QVBoxLayout()
    vbox.setMargin(20)

    vbox.addLayout(hbox01)
    # vbox.addLayout(hbox02)
    vbox.addLayout(hbox03)

    window.setLayout(vbox)

    window.show()

    return window

def message_box(message):
    from PySide2 import QtWidgets

    message_box_window = QtWidgets.QMessageBox()
    message_box_window.setWindowTitle('Big Success')
    message_box_window.setText('<b><center>%s' % message)
    message_box_window.setStandardButtons(QtWidgets.QMessageBox.Ok)
    message = message_box_window.exec_()

    return message

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
                    'execute': main_window,
                    'minimumVersion': '2019'
                }
            ]
        }
    ]
