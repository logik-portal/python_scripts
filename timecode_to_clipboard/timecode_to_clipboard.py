'''
Script Name: Timecode to Clipboard
Script Version: 2.0
Flame Version: 2020
Written by: Stefan Gaillot
Creation Date: 09.02.19
Update Date: 11.30.21

Custom Action Type: Timeline / MediaPanel

Description:

    Credits: The clipboard cool QT trick is from Lewis Saunders

    From within the timeline view of a sequence or a clip,
    right-click on a segment and execute the script: Copy TC to Clipboard -> From a Timeline
    This will copy the current timecode (at playhead position) to the os clipboard.
    You can then paste it as text in an email or a text file ...

    From a reel or the media panel,
    right-click on a clip or a sequence and execute the script: Copy TC to Clipboard -> From reel or media panel
    This will copy the current timecode (at playhead position) to the os clipboard.
    You can then paste it as text in an email or a text file ...

To install:

    Copy script into /opt/Autodesk/shared/python
'''

from __future__ import print_function
from PySide2 import QtWidgets

def sequence_current_tc_to_clipboard(selection):
    import flame

    for item in selection:
        if isinstance(item, (flame.PySequence)) or isinstance(item, (flame.PyClip)):
            clip_or_sequence = item
            print ("Current Timecode: ", clip_or_sequence.current_time)

    # This clipboard cool trick from Lewis Saunders.
    qt_app_instance = QtWidgets.QApplication.instance()
    qt_app_instance.clipboard().setText(str(clip_or_sequence.current_time))

def current_tc_to_clipboard(selection):
    import flame

    # count idea and code from Franck Lambertz
    s = selection[0]
    parents_count = 0
    my_clip = s

    # While loop from Franck Lambertz
    while not isinstance(my_clip, flame.PyClip) and not isinstance(my_clip, flame.PySequence):
        parents_count += 1
        if parents_count == 10 or not my_clip.parent:
            print ("Error, can't find the clip info")
            return
        my_clip = my_clip.parent

    clip_or_sequence = my_clip
    sequence_current_tc = clip_or_sequence.current_time.get_value().timecode
    print ("Current Timecode: ", sequence_current_tc)

    # This clipboard trick from Lewis Saunders
    qt_app_instance = QtWidgets.QApplication.instance()
    qt_app_instance.clipboard().setText(sequence_current_tc)

def scope_object(selection):
    import flame
    for item in selection:
        if isinstance(item, (flame.PySequence)) or isinstance(item, (flame.PyClip)):
            return True
    return False

def scope_timeline(selection):
    import flame
    for item in selection:
        if isinstance(item, flame.PySegment):
            return True
    return False

def get_timeline_custom_ui_actions():

    return [
        {
            "name": "Copy...",
            "actions": [
                {
                    "name": "Timecode to Clipboard",
                    "isVisible": scope_timeline,
                    "execute": current_tc_to_clipboard,
                }
            ]
        }
    ]

def get_media_panel_custom_ui_actions():
    return [
        {
            "name": "Copy...",
            "actions": [
                {
                    "name": "Timecode to Clipboard",
                    "isVisible": scope_object,
                    "execute": sequence_current_tc_to_clipboard,
                }
            ]
        }
    ]
