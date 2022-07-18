'''

Script Name: slate_desktop_copy

Script Version: 1.2
Flame Version: 2022

Written by: John Geehreng

Creation Date: 02.01.21

Update Date: 04.19.22




Description: If you put your slates on one reel and your sequences on another reel, this script allows you to select your Reel Group and Reels

to automatically insert your Slates to the corresponding Sequence.

* Every Sequences needs a corresponding Slate and order is important. Slate 1 will go to Sequnece 1, 2 -> 2, 3 ->3...

* Assumes your sequences start a 01:00:00:00.

* It also automatically renames your sequences based on the slate names, but there's a Pop-Up Warning.


04.19.22 - Updated for 2023 UI

'''


from __future__ import print_function
from flame_widgets import FlameButton, FlameLabel, FlameLineEdit, FlamePushButtonMenu, FlameWindow, FlameMessageWindow

folder_name = "UC Slates"

action_name = "Desktop Copy Slates"

VERSION = '1.2'

def getReelGroupList():
    global rgList
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

    reel_group_text = reel_group_list_push_button.text()
    print ('Reel Group Text666: ', reel_group_text)

    for i in [i for i, x in enumerate(rgList) if x == reel_group_text]:
        selected_reel_group_num = int(i)
    print ("*" * 10)
    print ('selected Reel Group Num666: ', selected_reel_group_num)
    reels = dsk.reel_groups[selected_reel_group_num].reels
    global reelList
    reelList = []
    for reel in reels:
        reelName = str(reel.name)[1:-1]
        reelList.append(reelName)
    print ('reelList: ', reelList)
    print ("*" * 10)
    print ('666')
    # slate_reel_list_push_button.clear()
    # slate_reel_list_push_button.addItems(reelList)
    # slate_reel_list_push_button.setCurrentIndex(2)
    # select_sequence_reel_label.clear()
    # select_sequence_reel_label.addItems(reelList)
    # select_sequence_reel_label.setCurrentIndex(3)

    # reelListCB.clear()
    # reelListCB.addItems(reelList)
    # reelListCB.setCurrentIndex(2)
    # seqListCB.clear()
    # seqListCB.addItems(reelList)
    # seqListCB.setCurrentIndex(3)



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

    if FlameMessageWindow('Confirm Operation', 'confirm', '<b><center>The # of Slates needs to match the # of Sequences.<br>And they need to be in the same order.<br>This will rename all sequences according to the slate name.'):
        print ('continue')
    else:
        return

    getReelGroupList()
    # getReelGroupNumber()
    getReelList()

    def ok_button():

        # Get selected Reel Group
        selected_reel_group_name = str(rgListCB.currentText())
        print ("*" * 10)
        print ('Selected Reel Group Name: ', selected_reel_group_name)
        # Get selected library number
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
        print ('Selected Sequence Reel Number: ', selected_seq_reel_num)
        print ("*" * 10)
        clips = dsk.reel_groups[selected_reel_group_num].reels[selected_seq_reel_num].sequences
        status = -1
        for sequence in clips:
            print ("Sequence " + str(status))
            status += 1
            seqName = sequence.name
            print ("Sequence Name: ",seqName)
            sequence.in_mark = None
            sequence.out_mark = None
            frameRate = sequence.frame_rate
            tc_OUT = flame.PyTime("00:59:58:00", frameRate)
            sequence.out_mark = tc_OUT
            sequence.open()
            print ("Status: ",status)

            # slate = dsk.reel_groups[0].reels[selected_slate_reel_num].clips[status]
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

    def test():
        reel_group_text = reel_group_list_push_button.text()
        print ('Reel Group Text: ', reel_group_text)

    grid_layout = QtWidgets.QGridLayout()
    window = FlameWindow(f'Desktop Copy Slates <small>{VERSION}', grid_layout, 450, 200)



    # Labels

    select_reel_group_label = FlameLabel('Select Reel Group', label_type='underline')

    select_slate_reel_label = FlameLabel('Select Slates Reel', label_type='underline')

    select_sequence_reel_label = FlameLabel('Select Sequence Reel', label_type='underline')


    # Entries
    # global rgListCB
    # rgListCB = QtWidgets.QComboBox(window)
    # rgListCB.addItems(rgList)
    # rgListCB.setMinimumSize(QtCore.QSize(150, 26))
    # rgListCB.setStyleSheet('background: #373e47; font: 14pt "Discreet"')
    # rgListCB.currentTextChanged.connect(updateReelList)
    #
    # global reelListCB
    # reelListCB = QtWidgets.QComboBox(window)
    # reelListCB.addItems(reelList)
    # reelListCB.setCurrentIndex(2)
    # reelListCB.setMinimumSize(QtCore.QSize(150, 26))
    # reelListCB.setStyleSheet('background: #373e47; font: 14pt "Discreet"')
    #
    # global seqListCB
    # seqListCB = QtWidgets.QComboBox(window)
    # seqListCB.addItems(reelList)
    # seqListCB.setCurrentIndex(3)
    # seqListCB.setMinimumSize(QtCore.QSize(150, 26))
    # seqListCB.setStyleSheet('background: #373e47; font: 14pt "Discreet"')

    # PushButtons

    global reel_group_list_push_button, slate_reel_list_push_button, sequence_reel_list_push_button

    reel_group_list_push_button = FlamePushButtonMenu(rgList[0], rgList, menu_action=updateReelList)
    slate_reel_list_push_button = FlamePushButtonMenu(reelList[0], reelList)
    sequence_reel_list_push_button = FlamePushButtonMenu(reelList[3], reelList)

    # Buttons

    ok_btn = FlameButton('Copy',ok_button, button_color='blue',button_width=100, button_max_width=110)
    cancel_btn = FlameButton('Close',window.close, button_color='normal',button_width=100, button_max_width=110)

    # Layout


    grid_layout.setMargin(10)
    grid_layout.setVerticalSpacing(20)
    grid_layout.setHorizontalSpacing(5)

    grid_layout.addWidget(select_reel_group_label, 0, 0)
    grid_layout.addWidget(reel_group_list_push_button, 0, 1)

    grid_layout.addWidget(select_slate_reel_label, 1, 0)
    grid_layout.addWidget(slate_reel_list_push_button, 1, 1)

    grid_layout.addWidget(select_sequence_reel_label, 2, 0)
    grid_layout.addWidget(sequence_reel_list_push_button, 2, 1)

    grid_layout.addWidget(cancel_btn, 3, 0)
    grid_layout.addWidget(ok_btn, 3, 1, QtCore.Qt.AlignRight)

    window.show()


def get_main_menu_custom_ui_actions():



    return [

        {

            'name': folder_name,

            'actions': [

                {

                    'name': action_name,

                    'execute': main_window,

                    'minimumVersion': '2022'

                }

            ]

        }

    ]

