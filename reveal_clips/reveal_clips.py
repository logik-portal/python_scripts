'''
Script Name: Reveal Clips
Script Version: 2.0
Flame Version: 2020.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 06.16.19
Update Date: 05.19.21

Custom Action Type: Timeline / Media Panel / MediaHub / Batch

Description:

    Reveal selected clip(s) in system finder or Flame MediaHub

    Right-click on clip in timeline -> Reveal... -> Reveal Clip in Finder / Reveal Clip in MediaHub

    Right-click on clip in media panel -> Reveal... -> Reveal Clip in Finder / Reveal Clip in MediaHub

    Right-click on clip in batch -> Reveal... -> Reveal Clip in Finder / Reveal Clip in MediaHub

    Right-click on clip in media hub -> Reveal... -> Reveal Clip in Finder

To install:

    Copy script into /opt/Autodesk/shared/python/reveal_clips

Updates:

v2.0 05.19.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.5 05.12.21

    Copy path to clipboard functionality moved to it's own script

    Merged with Reveal in Mediahub script - Reveal in MediaHub options only work in Flame 2021.2

    Clips in Timeline can now be revealed in finder and mediahub

v1.4 05.08.21

    Clips in MediaHub can now be revealed in finder and have paths copied to clipboard

v1.3 04.12.20

    Added ability to copy clip path to clipboard

v1.2 01.25.20

    Menu option will now only show up when right-clicking on clips with file paths

v1.1 08.11.19

    Code cleanup
'''

from __future__ import print_function

VERSION = 'v2.0'

# Reveal in Finder
#-------------------------------------#

def reveal_timeline_finder(selection):

    print ('\n', '>' * 20, 'reveal in finder %s - timeline' % VERSION, '<' * 20, '\n')

    for item in selection:
        clip_path = item.file_path.rsplit('/', 1)[0]
        print ('clip path:', clip_path)
        if clip_path != '':
            open_finder(clip_path)

def reveal_mediapanel_finder(selection):

    print ('\n', '>' * 20, 'reveal in finder %s' % VERSION, '<' * 20, '\n')

    for item in selection:
        clip_path = item.versions[0].tracks[0].segments[0].file_path
        clip_path = clip_path.rsplit('/', 1)[0]
        if clip_path != '':
            print ('clip path:', clip_path)
            open_finder(clip_path)

def reveal_batch_finder(selection):

    print ('\n', '>' * 20, 'reveal in finder %s - batch' % VERSION, '<' * 20, '\n')

    for item in selection:
        if item.media_path is not None:
            clip_path = str(item.media_path)[1:-1]
            clip_path = clip_path.rsplit('/', 1)[0]
            if clip_path != '':
                print ('clip path:', clip_path)
                open_finder(clip_path)

def reveal_mediahub_finder(selection):

    print ('\n', '>' * 20, 'reveal in finder %s - mediahub' % VERSION, '<' * 20, '\n')

    for item in selection:
        clip_path = item.path.rsplit('/', 1)[0]
        print ('clip path:', clip_path)
        if clip_path != '':
            open_finder(clip_path)

def open_finder(clip_path):
    import platform
    import subprocess

    if platform.system() == 'Darwin':
        subprocess.Popen(['open', clip_path])
    else:
        subprocess.Popen(['xdg-open', clip_path])

    print ('\ndone.\n')

# Reveal in MediaHub
#-------------------------------------#

def reveal_timeline_mediahub(selection):

    print ('\n', '>' * 20, 'reveal in media hub %s - timeline clip' % VERSION, '<' * 20, '\n')

    clip_path = str(selection[0].file_path).rsplit('/', 1)[0]

    open_media_hub(clip_path)

def reveal_mediapanel_mediahub(selection):

    print ('\n', '>' * 20, 'reveal in media hub %s - media panel clip' % VERSION, '<' * 20, '\n')

    selected_clip = selection[0]
    clip_path = str(selected_clip.versions[0].tracks[0].segments[0].file_path).rsplit('/', 1)[0]

    open_media_hub(clip_path)

def reveal_batch_mediahub(selection):

    print ('\n', '>' * 20, 'reveal in media hub %s - batch clip' % VERSION, '<' * 20, '\n')

    selected_clip = selection[0]

    clip_path = str(selected_clip.media_path)[1:-1].rsplit('/', 1)[0]

    open_media_hub(clip_path)

def open_media_hub(clip_path):
    import flame

    print ('clip path:', clip_path)
    flame.go_to('MediaHub')

    flame.mediahub.files.set_path(clip_path)


    print ('\n>>> MediaHub opened <<<\n')

# Scopes
#-------------------------------------#

def scope_timeline_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PySegment):
            if item.file_path != '':
                return True
    return False

def scope_batch_clip(selection):
    import flame

    for item in selection:
        if item.type == 'Clip':
            clip_path = str(item.media_path)[1:-1].rsplit('/', 1)[0]
            if clip_path != '':
                return True
    return False

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            if item.versions[0].tracks[0].segments[0].file_path != '':
                return True
    return False

def scope_file(selection):
    import flame
    import re

    for item in selection:
        item_path = str(item.path)
        item_ext = re.search(r'\.\w{3}$', item_path, re.I)
        if item_ext != (None):
            return True
    return False

#-------------------------------------#

def get_timeline_custom_ui_actions():

    return [
        {
            'name': 'Reveal...',
            'actions': [
                {
                    'name': 'Reveal Clip in Finder',
                    'isVisible': scope_timeline_clip,
                    'execute': reveal_timeline_finder,
                    'minimumVersion': '2020.1'
                },
                {
                    'name': 'Reveal Clip in Media Hub',
                    'isVisible': scope_timeline_clip,
                    'execute': reveal_timeline_mediahub,
                    'minimumVersion': '2021.2'
                }
            ]
        }
    ]

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Reveal...',
            'actions': [
                {
                    'name': 'Reveal Clip in Finder',
                    'isVisible': scope_clip,
                    'execute': reveal_mediapanel_finder,
                    'minimumVersion': '2020'
                },
                {
                    'name': 'Reveal Clip in Media Hub',
                    'isVisible': scope_clip,
                    'execute': reveal_mediapanel_mediahub,
                    'minimumVersion': '2021.2'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Reveal...',
            'actions': [
                {
                    'name': 'Reveal Clip in Finder',
                    'isVisible': scope_batch_clip,
                    'execute': reveal_batch_finder,
                    'minimumVersion': '2020'
                },
                {
                    'name': 'Reveal Clip in Media Hub',
                    'isVisible': scope_batch_clip,
                    'execute': reveal_batch_mediahub,
                    'minimumVersion': '2021.2'
                }
            ]
        }
    ]

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Reveal...',
            'actions': [
                {
                    'name': 'Reveal Clip in Finder',
                    'isVisible': scope_file,
                    'execute': reveal_mediahub_finder,
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]
