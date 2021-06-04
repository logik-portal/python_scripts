'''
Script Name: Go To Frame 0
Script Version: 1.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 01.01.20
Update Date: 01.01.20

Description:

    Go to frame 0 in timeline
'''

def get_media_panel_custom_ui_actions():

    def scope_clip(selection):
        import flame
        for item in selection:
            if isinstance(item, flame.PyClip):
                return True
        return False

    def go_to(selection):
        import flame
        tc_IN = flame.PyTime(0)
        for sequence in selection:
            sequence.current_time = tc_IN

    return [
        {
            "name": "Timelines",
            "actions": [
                {
                    "name": "Go to Frame 0",
                    "isVisible": scope_clip,
                    "execute": go_to
                }
            ]
        }
    ]
