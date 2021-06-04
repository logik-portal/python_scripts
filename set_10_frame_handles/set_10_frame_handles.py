'''
Script Name: Set 10 Frame Handles
Script Version: 1.1
Flame Version: 2019
Written by: John Geehreng
Creation Date: 01.22.21
Update Date:

Description: Set 10 frame handles
'''

from __future__ import print_function

folder_name = "Set In and Out"
action_name = "Set 10 Frame Handles - In and Outs"

def set_handles(selection):
    import flame
    for sequence in selection:
        print ("\n" *2)
        print ("*" * 10)

        sequence.in_mark = None
        sequence.out_mark = None
        print (sequence.name)
        print (sequence.duration.frame)
        i = sequence.duration.frame
        out = int(i) - 9
        print ("clip length is " + str(i) + " frames")
        tc_IN = flame.PyTime(11)
        tc_OUT= flame.PyTime(out)
        sequence.in_mark = tc_IN
        sequence.out_mark = tc_OUT
        print ("In Point = " + str(tc_IN))
        print ("Out Point = " + str(tc_OUT))

        print ("*" * 10)
        print ("\n" *2)

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
                    'execute': set_handles,
                    'minimumVersion': '2019'
                }
            ]
        }
    ]
