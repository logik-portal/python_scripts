'''Script Name: Slate Desktop CopyScript Version: 1.1Flame Version: 2021Written by: John GeehrengCreation Date: 02.01.21Update Date: 02.03.21Description: If you put your slates on one reel and your sequences on another reel, this script allows you to select your Reel Group and Reelsto automatically insert your Slates to the corresponding Sequence.* Every Sequences needs a corresponding Slate and order is important. Slate 1 will go to Sequnece 1, 2 -> 2, 3 ->3...* Assumes your sequences start a 01:00:00:00.* It also automatically renames your sequences based on the slate names, but there's a Pop-Up Warning.'''
from __future__ import print_function

folder_name = "Slates"
action_name = "Desktop Copy Slates"
def getReelGroupList():    global rgList
    rgList = []
    for reel_group in reel_groups:
        rgName = str(reel_group.name)[1:-1]
        rgList.append(rgName)
        print ('Reel Group Name: ', rgName)
    print ('ReelGroupList: ', rgList)

def getReelGroupNumber():
    global selected_reel_group_num
    for i in [i for i, x in enumerate(rgList) if x == selected_reel_group_name]:
        selected_reel_group_num = int(i)
    print ('selected Reel Group Num: ', selected_reel_group_num)
    print ("*" * 10)

def getReelList():
    global reelList
    reelList = []
    for reel in reels:
        reelName = str(reel.name)[1:-1]
        reelList.append(reelName)
        print ('reelName: ', reelName)
    print ('reelList: ', reelList)

def updateReelList():
    # getReelGroupList()
    # getReelList()
    selected_reel_group_name = str(rgListCB.currentText())
    for i in [i for i, x in enumerate(rgList) if x == selected_reel_group_name]:
        selected_reel_group_num = int(i)
    print ("*" * 10)
    print ('selected Reel Group Num: ', selected_reel_group_num)
    reels = dsk.reel_groups[selected_reel_group_num].reels
    global reelList
    reelList = []
    for reel in reels:
        reelName = str(reel.name)[1:-1]
        reelList.append(reelName)
    print ('reelList: ', reelList)
    print ("*" * 10)
    reelListCB.clear()
    reelListCB.addItems(reelList)
    reelListCB.setCurrentIndex(2)
    seqListCB.clear()
    seqListCB.addItems(reelList)
    seqListCB.setCurrentIndex(3)

def main_window(selection):
    import flame
    import re
    from PySide2 import QtWidgets, QtCore

    global wks, dsk,selected_reel_group_num, reels, reel_groups
    wks = flame.project.current_project.current_workspace
    dsk = flame.project.current_project.current_workspace.desktop
    selected_reel_group_num = 0
    reels = dsk.reel_groups[selected_reel_group_num].reels
    reel_groups = dsk.reel_groups

    desktopWarning = QtWidgets.QMessageBox()
    desktopWarning.setText('<b><center>The # of Slates needs to match the # of Sequences.<br>And they need to be in the same order.<br>This will rename all sequences according to the slate name.')
    desktopWarning.setInformativeText('<center>Do you want to continue?</center>')
    desktopWarning.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    desktopWarning.setIcon(QtWidgets.QMessageBox.Warning)
    desktopWarning.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    desktopWarning.setStyleSheet('color: #9a9a9a; border-bottom: 1px inset #282828; font: 14pt "Discreet"')
    reply = desktopWarning.exec_()
    # exit if user clicks NO
    if reply != QtWidgets.QMessageBox.Yes:
        print ('abort')
        return

    if reply == QtWidgets.QMessageBox.Yes:
        print ('continue')

    getReelGroupList()
    # getReelGroupNumber()
    getReelList()

    def cancel_button():
        window.close()
    def ok_button():        # Get selected Reel Group
        selected_reel_group_name = str(rgListCB.currentText())
        print ("*" * 10)
        print ('Selected Reel Group Name: ', selected_reel_group_name)        # Get selected library number
        for i in [i for i, x in enumerate(rgList) if x == selected_reel_group_name]:
            selected_reel_group_num = int(i)
        print ('selected Reel Group Num: ', selected_reel_group_num)
        print ("*" * 10)

        # Get selected Slate Reel
        selected_slate_reel_name = str(reelListCB.currentText())
        print ('Selected Slate Reel Name: ', selected_slate_reel_name)
        # Get selected library number
        for i in [i for i, x in enumerate(reelList) if x == selected_slate_reel_name]:
            selected_slate_reel_num = i
        print ('selected Slate Reel Num: ', selected_slate_reel_num)
        print ("*" * 10)

        # Get selected Sequence Reel
        selected_seq_reel_name = str(seqListCB.currentText())
        print ('Selected Sequence Reel Name: ', selected_seq_reel_name)
        # Get selected library number
        for i in [i for i, x in enumerate(reelList) if x == selected_seq_reel_name]:
            selected_seq_reel_num = int(i)
        print ('Selected Sequence Reel Number: ', selected_seq_reel_num)        print ("*" * 10)
        clips = dsk.reel_groups[selected_reel_group_num].reels[selected_seq_reel_num].sequences
        status = -1
        for sequence in clips:
            print ("Sequence " + str(status))            status += 1
            seqName = sequence.name
            print ("Sequence Name: ",seqName)
            sequence.in_mark = None
            sequence.out_mark = None
            frameRate = sequence.frame_rate
            tc_OUT = flame.PyTime("00:59:58:00", frameRate)
            sequence.out_mark = tc_OUT
            sequence.open()
            print ("Status: ",status)            # slate = dsk.reel_groups[0].reels[selected_slate_reel_num].clips[status]
            slate = dsk.reel_groups[selected_reel_group_num].reels[selected_slate_reel_num].clips[status]
            slateName = slate.name
            tc_IN = flame.PyTime(1)
            slate.in_mark = tc_IN
            print ("Slate Name: ",slateName)
            slate.selected = True
            flame.execute_shortcut("Overwrite Edit")
            sequence.name = str(slateName)[1:-1] # + "_" + str(sequence.name)[1:-1]
            sequence.current_time = tc_IN

        slate_reel = dsk.reel_groups[selected_reel_group_num].reels[selected_slate_reel_num]
        slate_reel.selected = True
        flame.execute_shortcut("Clear Content")
        window.close()
    window = QtWidgets.QWidget()
    window.setMinimumSize(400, 130)
    window.setWindowTitle('Desktop Slates')
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    window.setStyleSheet('background-color: #272727')
    # Center window in linux
    resolution = QtWidgets.QDesktopWidget().screenGeometry()
    window.move((resolution.width() / 2) - (window.frameSize().width() / 2),                (resolution.height() / 2) - (window.frameSize().height() / 2))
    # Labels
    class FlameLabel(QtWidgets.QLabel):
        """        Custom Qt Flame Label Widget        Options for normal, label with background color, and label with background color and outline        """
        def __init__(self, label_name, parent, label_type='normal', *args, **kwargs):
            super(FlameLabel, self).__init__(*args, **kwargs)
            self.setText(label_name)
            self.setParent(parent)
            self.setMinimumSize(125, 28)
            self.setMaximumHeight(28)
            # Set label stylesheet based on label_type
            # For different label looks use: label_type='normal', label_type='background', or label_type='outline'
            if label_type == 'normal':
                self.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'                                   'QLabel:disabled {color: #6a6a6a}')            elif label_type == 'background':
                self.setAlignment(QtCore.Qt.AlignCenter)
                self.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')
            elif label_type == 'outline':
                self.setAlignment(QtCore.Qt.AlignCenter)
                self.setStyleSheet('color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"')
    select_reel_group_label = FlameLabel('Select Reel Group', window, label_type='normal')
    select_slate_reel_label = FlameLabel('Select Slates Reel', window, label_type='normal')
    select_sequence_reel_label = FlameLabel('Select Sequence Reel', window, label_type='normal')
    # Entries
    global rgListCB
    rgListCB = QtWidgets.QComboBox(window)
    rgListCB.addItems(rgList)
    rgListCB.setMinimumSize(QtCore.QSize(150, 26))
    rgListCB.setStyleSheet('background: #373e47; font: 14pt "Discreet"')
    rgListCB.currentTextChanged.connect(updateReelList)
    global reelListCB
    reelListCB = QtWidgets.QComboBox(window)
    reelListCB.addItems(reelList)
    reelListCB.setCurrentIndex(2)
    reelListCB.setMinimumSize(QtCore.QSize(150, 26))
    reelListCB.setStyleSheet('background: #373e47; font: 14pt "Discreet"')
    global seqListCB
    seqListCB = QtWidgets.QComboBox(window)
    seqListCB.addItems(reelList)
    seqListCB.setCurrentIndex(3)
    seqListCB.setMinimumSize(QtCore.QSize(150, 26))
    seqListCB.setStyleSheet('background: #373e47; font: 14pt "Discreet"')
    # Buttons
    class FlameButton(QtWidgets.QPushButton):
        """
        Custom Qt Flame Button Widget
        """
        def __init__(self, button_name, parent, connect, *args, **kwargs):
            super(FlameButton, self).__init__(*args, **kwargs)
            self.setText(button_name)
            self.setParent(parent)
            self.setMinimumSize(QtCore.QSize(110, 28))
            self.setMaximumSize(QtCore.QSize(110, 28))
            self.setFocusPolicy(QtCore.Qt.NoFocus)
            self.clicked.connect(connect)
            self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'                               'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'                               'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')
    ok_btn = FlameButton('Ok', window, ok_button)
    cancel_btn = FlameButton('Cancel', window, cancel_button)
    # Layout
    hbox00 = QtWidgets.QHBoxLayout()
    hbox00.addWidget(select_reel_group_label)
    hbox00.addWidget(rgListCB)
    hbox01 = QtWidgets.QHBoxLayout()
    hbox01.addWidget(select_slate_reel_label)
    hbox01.addWidget(reelListCB)
    hbox02 = QtWidgets.QHBoxLayout()
    hbox02.addWidget(select_sequence_reel_label)
    hbox02.addWidget(seqListCB)
    hbox03 = QtWidgets.QHBoxLayout()
    hbox03.addStretch(5)
    hbox03.addWidget(ok_btn)
    hbox03.addStretch(5)
    hbox03.addWidget(cancel_btn)
    hbox03.addStretch(5)
    vbox = QtWidgets.QVBoxLayout()
    vbox.setMargin(20)
    vbox.addLayout(hbox00)
    vbox.addLayout(hbox01)
    vbox.addLayout(hbox02)
    vbox.addLayout(hbox03)
    window.setLayout(vbox)
    window.show()
    return window
def scope_reel_group(item):
    import flame
    item = flame.project.current_project.current_workspace.desktop.reel_groups[0]
    if item != None:
        return True
    return False

def get_main_menu_custom_ui_actions():
    return [        {            'name': folder_name,            'actions': [                {                    'name': action_name,                    # 'isVisible': scope_reel_group,                    'execute': main_window,                    'minimumVersion': '2021'                }            ]        }    ]