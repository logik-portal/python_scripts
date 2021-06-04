'''
Script Name: Color Timewarp Shots
Script Version: 2.0
Flame Version: 2020
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 08.29.19
Update Date: 05.23.21

Custom Action Type: Media Panel Sequence Clips

Description:

    Colors shots in timeline with timewarps red

    Right-click on sequence clip in media panel -> Timeline... -> Color Timewarp Shots

To install:

    Copy script into /opt/Autodesk/shared/python/color_timewarp_shots

Updates:

v2.0 05.23.21

    Updated to be compatible with Flame 2022/Python 3.7
'''

from __future__ import print_function

VERSION = 'v2.0'

def color_timewarp_clip(selection):
    import flame

    print ('\n', '>' * 20, 'color timewarp shots %s' % VERSION, '<' * 20, '\n')

    for shot in selection:
        for version in shot.versions:
            for track in version.tracks:
                for segment in track.segments:
                    for tlfx in segment.effects:
                        if tlfx.type == 'Timewarp':

                            # Set color of clips on timeline

                            segment.colour = (0.5, 0.0, 0.0)

def scope_seq(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PySequence):
            return True
    return False

def get_media_panel_custom_ui_actions():
    return [
        {
            'name': 'Timeline...',
            'actions': [
                {
                    'name': 'Color Timewarped Shots',
                    'isVisible': scope_seq,
                    'execute': color_timewarp_clip,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
