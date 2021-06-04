'''
Script Name: Clip path to clipboard
Script Version: 2.0
Flame Version: 2021
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 06.16.19
Update Date: 05.20.21

Custom Action Type: Timeline / Media Panel / Media Hub / Batch

Description:

    Reveal selected clip(s) in system finder window or copy clip path to clipboard

    Right-click on clip in timeline -> Copy... -> Clip Path to Clipboard
    Right-click on clip in media panel -> Copy... -> Clip Path to Clipboard
    Right-click on clip in media hub -> Copy... -> Clip Path to Clipboard
    Right-click on clip in batch -> Copy... -> Clip Path to Clipboard

To install:

    Copy script into /opt/Autodesk/shared/python/clip_path_to_clipboard

Updates:

v2.0 05.20.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.5 05.12.21

    Separated from Reveal in Finder script

    Clips in Timeline can have paths copied to clipboard
'''

from __future__ import print_function

VERSION = 'v2.0'

def media_panel_copy_path(selection):
    from PySide2 import QtWidgets

    print ('\n', '>' * 20, 'reveal in finder %s - copy media panel clip path to clipboard' % VERSION, '<' * 20, '\n')

    clip_paths = ''

    clip_list = [clip.versions[0].tracks[0].segments[0].file_path.rsplit('/', 1)[0] for clip in selection if clip.versions[0].tracks[0].segments[0].file_path]

    # Convert path list to string with new line

    for clip in clip_list:
        clip_paths += clip + '\n'

    # Add clips to clipboard

    qt_app_instance = QtWidgets.QApplication.instance()
    qt_app_instance.clipboard().setText(clip_paths)

    print ('\ndone.\n')

def timeline_copy_path(selection):
    from PySide2 import QtWidgets

    print ('\n', '>' * 20, 'reveal in finder %s - copy timeline clip path to clipboard' % VERSION, '<' * 20, '\n')

    clip_paths = ''

    clip_list = [clip.file_path.rsplit('/', 1)[0] for clip in selection if clip.file_path]

    # Convert path list to string with new line

    for clip in clip_list:
        clip_paths += clip + '\n'

    # Add clips to clipboard

    qt_app_instance = QtWidgets.QApplication.instance()
    qt_app_instance.clipboard().setText(clip_paths)

    print ('\ndone.\n')

def batch_copy_path(selection):
    from PySide2 import QtWidgets

    print ('\n', '>' * 20, 'reveal in finder %s - copy batch clip path to clipboard' % VERSION, '<' * 20, '\n')

    clip_paths = ''

    clip_list = [str(clip.media_path)[1:-1].rsplit('/', 1)[0] for clip in selection if clip.media_path != '']

    # Convert path list to string with new line

    for clip in clip_list:
        clip_paths += clip + '\n'

    # Add clips to clipboard

    qt_app_instance = QtWidgets.QApplication.instance()
    qt_app_instance.clipboard().setText(clip_paths)

    print ('\ndone.\n')

def mediahub_copy_path(selection):
    from PySide2 import QtWidgets

    print ('\n', '>' * 20, 'reveal in finder %s - copy mediahub clip path to clipboard' % VERSION, '<' * 20, '\n')

    clip = selection[0]

    clip_path = clip.path.rsplit('/', 1)[0]

    if clip_path != '':

        # Add clip path  to clipboard

        qt_app_instance = QtWidgets.QApplication.instance()
        qt_app_instance.clipboard().setText(clip_path)

        print ('\ndone.\n')

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

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Copy...',
            'actions': [
                {
                    'name': 'Clip Path to Clipboard',
                    'isVisible': scope_clip,
                    'execute': media_panel_copy_path,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Copy...',
            'actions': [
                {
                    'name': 'Clip Path to Clipboard',
                    'isVisible': scope_batch_clip,
                    'execute': batch_copy_path,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Copy...',
            'actions': [
                {
                    'name': 'Clip Path to Clipboard',
                    'isVisible': scope_file,
                    'execute': mediahub_copy_path,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_timeline_custom_ui_actions():

    return [
        {
            'name': 'Copy...',
            'actions': [
                {
                    'name': 'Clip Path to Clipboard',
                    'isVisible': scope_timeline_clip,
                    'execute': timeline_copy_path,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
