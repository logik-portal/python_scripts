'''
Script Name: Set In Point At Two Sec
Script Version: 1.1
Flame Version: 2019
Written by: John Geehreng
Creation Date: 12.08.20
Update Date: 12.08.20

Description: This script sets an In Point at two seconds. It will work for 23.976, 24, 25, 23.97 NDF, and 29.97 DF.
'''

from __future__ import print_function

folder_name = "Set In and Out"
action_name = "Set an In-Point at :02"

def set_in_point(selection):
    import flame

    for sequence in selection:
        print ("*" * 10)
        sequence.out_mark = None
        frameRate = sequence.frame_rate

        if frameRate == '23.976 fps':
            tc_IN = flame.PyTime(49)
            sequence.in_mark = tc_IN

        if frameRate == '24 fps':
            tc_IN = flame.PyTime(49)
            sequence.in_mark = tc_IN

        if frameRate == '25 fps':
            tc_IN = flame.PyTime(51)
            sequence.in_mark = tc_IN

        if frameRate == '29.97 fps NDF':
            tc_IN = flame.PyTime(61)
            sequence.in_mark = tc_IN

        if frameRate == '29.97 fps DF':
            tc_IN = flame.PyTime(61)
            sequence.in_mark = tc_IN

        print ("This is a " + str(frameRate) + " clip.")
        print ("In Point = " + str(tc_IN))

        print ("*" * 10)
        print ("\n")

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
                    'execute': set_in_point,
                    'minimumVersion': '2019'
                }
            ]
        }
    ]
