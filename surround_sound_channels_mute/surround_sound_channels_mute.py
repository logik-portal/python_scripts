'''
Script Name: Surround Sound Channels Mute
Script Version: 1.0
Flame Version: 2020
Written by: John Geehreng
Creation Date: 06.06.20
Update Date: 06.06.20

Custom Action Type: MediaPanel

Description:

    Mutes audio tracks 1-5 on all selected clips/sequences.
'''

folder_name = "Audio"
action_name = "Mute Surround Channels"

def mute_channels(selection):
    import flame

    for item in selection:

        atrack = item.audio_tracks[0]
        atrack.mute = True
        atrack = item.audio_tracks[1]
        atrack.mute = True
        atrack = item.audio_tracks[2]
        atrack.mute = True
        atrack = item.audio_tracks[3]
        atrack.mute = True
        atrack = item.audio_tracks[4]
        atrack.mute = True
        atrack = item.audio_tracks[5]
        atrack.mute = True

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
                    'execute': mute_channels,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
