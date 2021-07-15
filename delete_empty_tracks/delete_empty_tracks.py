'''
Script Name: Delete Empty Tracks
Script Version: 1.0
Flame Version: 2021.1
Written by: Fred Warren
Creation Date: 07.15.21
Update Date: 07.15.21

Custom Action Type: Media Panel

Description:

   This script adds three custom actions to delete empty video and/or audio
   tracks of a <PySequence>. The minimumVersion is set to 2021.1 because
   <PySegment>.type is used.

To install:

    Copy script into /opt/Autodesk/shared/python

'''


def get_media_panel_custom_ui_actions():
    """
    Make the custom actions appear only on a sequence.
    """
    def scope_clip(selection):
        import flame
        for item in selection:
            if isinstance(item, flame.PySequence):
                return True
        return False

    def delete_empty_video_tracks(selection):
        import flame

        for clip in selection:
            for version in clip.versions:
                skip_next_chn = False
                for track in version.tracks:
                    if skip_next_chn:
                        skip_next_chn = False
                        continue
                    if len(track.segments) == 1 and track.segments[0].type == "Gap":
                       skip_next_chn = version.stereo
                       flame.delete(track)

    def delete_empty_audio_tracks(selection):
        import flame

        for clip in selection:
            for audio_track in clip.audio_tracks:
                skip_next_chn = False
                for channel in audio_track.channels:
                    if skip_next_chn:
                        skip_next_chn = False
                        continue
                    if len(channel.segments) == 1 and channel.segments[0].type == "Gap":
                        skip_next_chn = audio_track.stereo
                        flame.delete(channel)

    def delete_all_empty_tracks(selection):
        """
        Execute both actions at once.
        """
        delete_empty_video_tracks(selection)
        delete_empty_audio_tracks(selection)

    return [
        {
            "name": "CUSTOM: Sequence",
            "actions": [
                {
                    "name": "Delete Empty Video Tracks",
                    "isVisible": scope_clip,
                    "execute": delete_empty_video_tracks,
                    "minimumVersion": "2021.1.0.0"
                },
                {
                    "name": "Delete Empty Audio Tracks",
                    "isVisible": scope_clip,
                    "execute": delete_empty_audio_tracks,
                    "minimumVersion": "2021.1.0.0"
                },
                {
                    "name": "Delete All Empty Tracks",
                    "isVisible": scope_clip,
                    "execute": delete_all_empty_tracks,
                    "minimumVersion": "2021.1.0.0"
                }
            ]
        }
    ]
