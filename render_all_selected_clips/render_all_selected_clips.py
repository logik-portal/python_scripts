'''
Script Name: Render All Selected Clips
Script Version: 1.0
Flame Version: 2019.2
Written by: Fred Warren
Creation Date: 07.15.21
Update Date: 07.15.21

Custom Action Type: Media Panel

Description:

    This script adds a custom action that allows all the Timeline FX in
    the currently selected clips to be rendered.
    The minimumVersion is set to 2019.2 because <PyClip>.render() is used.

To install:

    Copy script into /opt/Autodesk/shared/python

'''

def get_media_panel_custom_ui_actions():
    """
    Make the custom actions appear only on a sequence or clip.
    """
    def scope_clip(selection):
        import flame
        for item in selection:
            if isinstance(item, (flame.PySequence, flame.PyClip)):
                return True
        return False

    def render_all_timeline_fx(selection):
        import flame

        for clip in selection:
            clip.render()

    return [
        {
            "name": "CUSTOM: Clips",
            "actions": [
                {
                    "name": "Render TL FX in All Selected Clips",
                    "isVisible": scope_clip,
                    "execute": render_all_timeline_fx,
                    "minimumVersion": "2019.2.0.0"
                }
            ]
        }
    ]
