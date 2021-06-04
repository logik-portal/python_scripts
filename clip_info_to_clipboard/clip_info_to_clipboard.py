'''
Script Name: Clip Info to Clipboard
Script Version: 2.0
Flame Version: 2020.1
Written by: Andy Milkis
Creation Date: 09.08.19
Update Date: 06.04.21

Custom Action Type: Media Panel

Description:

    Copy selected clip info to clipboard

    Right-click on clip in Media Panel -> Clip... -> Copy Clip Info

To install:

    Copy script into /opt/Autodesk/shared/python/clip_info_to_clipboard

Updates:

v2.0 06.04.21

    Updated to be compatible with Flame 2022/Python 3.7
'''

from __future__ import print_function

VERSION = 'v2.0'

def main_window(selection):
    from PySide2 import QtWidgets, QtCore
    from functools import partial

    def get_clip_info(selection, clip_info_listbox):
        import flame

        print ('\n', '>' * 20, 'clip info to clipboard %s' % VERSION, '<' * 20, '\n')

        for seq in selection:
            framerate = seq.frame_rate
            start_time = seq.start_time
            duration = seq.duration.frame
            tc_in = flame.PyTime(str(start_time), framerate)
            end_time = tc_in + (duration -1)
            res = str(end_time)[1:-1]

            clip_name = 'Clip Name: ' + str(seq.name)[1:-1]
            frame_rate = 'Frame Rate: ' + str(framerate)
            clip_dur = 'Clip Duration: ' + str(duration)
            first_frame = 'First Frame TC: ' + str(start_time)
            last_frame = 'Last Frame TC: ' + res

            print ('\n', '\n', '*' * 10)
            print (clip_name, '\n', frame_rate, '\n', clip_dur, '\n', first_frame, '\n', last_frame)
            print ('\n', '*' * 10, '\n')

            clip_info_line = clip_name + ' ' * 5 + frame_rate + ' ' * 5 + clip_dur + ' ' * 5 + first_frame + ' ' * 5 + last_frame

            clip_info_listbox.addItem(clip_info_line)

    def copy_to_clipboard(clip_info_listbox):
        from PySide2 import QtWidgets

        clip_info_list = []

        for item in clip_info_listbox.selectedItems():
            clip_info_list.append(item.text())
            clip_info_list.append('\n')

        all_clip_info = ''.join(clip_info_list)

        qt_app_instance = QtWidgets.QApplication.instance()
        qt_app_instance.clipboard().setText(all_clip_info)

        close_window()

    def close_window():

        window.close()

    window = QtWidgets.QWidget()
    window.setFixedSize(800, 300)
    window.setWindowTitle('Copy Clip Info to Clipboard v1.0')
    window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    window.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    # Labels

    selected_clips_label = QtWidgets.QLabel('Selected Clips:', window)
    selected_clips_label.move(20, 20)

    # Listbox

    clip_info_listbox = QtWidgets.QListWidget(window)
    clip_info_listbox.move(20, 50)
    clip_info_listbox.resize(760, 195)
    clip_info_listbox.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    get_clip_info(selection, clip_info_listbox)
    clip_info_listbox.selectAll()

    # Buttons

    copy_btn = QtWidgets.QPushButton('Copy', window)
    copy_btn.move(450, 260)
    copy_btn.resize(100, 24)
    copy_btn.clicked.connect(partial(copy_to_clipboard, clip_info_listbox))

    cancel_btn = QtWidgets.QPushButton('Cancel', window)
    cancel_btn.move(250, 260)
    cancel_btn.resize(100, 24)
    cancel_btn.clicked.connect(close_window)

    window.show()

    return window

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Clip...',
            'actions': [
                {
                    'name': 'Copy Clip Info',
                    'isVisible': scope_clip,
                    'execute': main_window,
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]
