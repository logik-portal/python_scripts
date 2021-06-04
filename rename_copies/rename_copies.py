'''
Script Name: Rename Copies
Script Version: 1.0
Flame Version: 2019
Written by: John Geehreng
Creation Date: 02.01.21
Update Date: 02.01.21

Description: If you make a bunch of copies and want to change their names so they don't say 'copy copy copy copy copy copy copy', use this script. Just enter a base name and hit ok.
'''

from __future__ import print_function

folder_name = "Renamers"
action_name = "Rename Copies"

from PySide2 import QtWidgets, QtCore

def main_window(selection):
    from PySide2 import QtWidgets, QtCore

    def cancel_button():

        window.close()

    def ok_button():
        status = 0

        for item in selection:
            print ("*" * 10)
            status += int(1)
            status_padded = '%02d' % status
            print (status)
            seq_name = str(item.name)[(1):-(1)]
            print ('Start Name: ' + seq_name)
            base_name = str(base_name_entry.text())
            print ('Base Name: ' + base_name)
            new_name = str(base_name) + str(status_padded)
            item.name = new_name
            print ('New Name: ' + new_name)

            print ("*" * 10)
            print ("\n")

        window.close()

    window = QtWidgets.QWidget()
    window.setMinimumSize(600, 130)
    window.setWindowTitle('Rename Copies')
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    window.setStyleSheet('background-color: #272727')

    # Center window in linux

    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                (resolution.height() / 2) - (window.frameSize().height() / 2))

    # Labels
    base_name_label = QtWidgets.QLabel('Base Name ', window)
    base_name_label.setAlignment(QtCore.Qt.AlignRight)
    base_name_label.setMinimumWidth(60)
    base_name_label.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')

    # Entries
    base_name_entry = QtWidgets.QLineEdit('', window)
    base_name_entry.setMinimumSize(QtCore.QSize(100, 26))
    base_name_entry.setStyleSheet('background: #373e47')

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
    hbox01 = QtWidgets.QHBoxLayout()
    hbox01.addWidget(base_name_label)
    hbox01.addWidget(base_name_entry)

    # hbox02 = QtWidgets.QHBoxLayout()
    # hbox02.addWidget(replace_label)
    # hbox02.addWidget(replace_entry)

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
