'''
Script Name: Find and Replace
Script Version: 1.0
Flame Version: 2019
Written by: John Geehreng
Creation Date: 01.01.19
Update Date: 01.01.19

Description:

    Find and replace names
'''

from __future__ import print_function

folder_name = "Renamers"
action_name = "Find and Replace"

# from PySide2 import QtWidgets, QtCore

def main_window(selection):
    from PySide2 import QtWidgets, QtCore

    def cancel_button():

        window.close()

    def ok_button():
        for item in selection:
            print ("*" * 10)

            seq_name = str(item.name)[(1):-(1)]
            print ('Start Name: ' + str(seq_name))

            find_me = str(find_entry.text())
            print ('Find Me: ' + str(find_me))

            replace_with_me = str(replace_entry.text())
            print ('Replace With Me: ' + str(replace_with_me))

            new_name = seq_name.replace(find_me,replace_with_me)
            item.name = new_name
            print ('New Name: ' + str(new_name))

            print ("*" * 10)
            print ("\n")

        window.close()

    window = QtWidgets.QWidget()
    window.setMinimumSize(600, 130)
    window.setWindowTitle('Find and Replace')
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    window.setStyleSheet('background-color: #272727')

    # Center window in linux

    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                (resolution.height() / 2) - (window.frameSize().height() / 2))

    # Labels

    find_label = QtWidgets.QLabel('Find ', window)
    find_label.setAlignment(QtCore.Qt.AlignVCenter)
    find_label.setMinimumWidth(50)
    find_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')
    replace_label = QtWidgets.QLabel('Replace ', window)
    replace_label.setAlignment(QtCore.Qt.AlignVCenter)
    replace_label.setMinimumWidth(50)
    replace_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')

    # Entries
    find_entry = QtWidgets.QLineEdit('', window)
    find_entry.setMinimumSize(QtCore.QSize(100, 26))
    find_entry.setStyleSheet('background: #373e47')

    replace_entry = QtWidgets.QLineEdit('', window)
    replace_entry.setMinimumSize(QtCore.QSize(100, 26))
    replace_entry.setStyleSheet('background: #373e47')

    # Buttons
    ok_btn = QtWidgets.QPushButton('Ok', window)
    ok_btn.setMinimumSize(QtCore.QSize(110, 24))
    ok_btn.setMinimumSize(QtCore.QSize(110, 26))
    ok_btn.setMaximumSize(QtCore.QSize(110, 26))
    ok_btn.setStyleSheet('background: #373737')
    ok_btn.clicked.connect(ok_button)

    cancel_btn = QtWidgets.QPushButton('Cancel', window)
    cancel_btn.setMinimumSize(QtCore.QSize(110, 26))
    cancel_btn.setMaximumSize(QtCore.QSize(110, 26))
    cancel_btn.setStyleSheet('background: #732020')
    cancel_btn.clicked.connect(cancel_button)

    # Layout
    gridbox01 = QtWidgets.QGridLayout()
    gridbox01.setVerticalSpacing(10)
    gridbox01.setHorizontalSpacing(10)

    gridbox01.addWidget(find_label, 0, 0)
    gridbox01.addWidget(find_entry, 0, 1)
    gridbox01.addWidget(replace_label, 1, 0)
    gridbox01.addWidget(replace_entry, 1, 1)

    hbox03 = QtWidgets.QHBoxLayout()
    hbox03.addStretch(5)
    hbox03.addWidget(ok_btn)
    hbox03.addStretch(5)
    hbox03.addWidget(cancel_btn)
    hbox03.addStretch(5)

    vbox = QtWidgets.QVBoxLayout()
    vbox.setMargin(5)
    vbox.addLayout(gridbox01)
    vbox.addLayout(hbox03)

    window.setLayout(vbox)

    window.show()

    return window

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
                    'execute': main_window,
                    'minimumVersion': '2019'
                }
            ]
        }
    ]
