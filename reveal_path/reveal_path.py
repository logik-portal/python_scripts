'''
Script Name: Reveal Path
Script Version: 2.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 06.16.19
Update Date: 05.26.22

Custom Action Type: Timeline / Media Panel / MediaHub / Batch

Description:

    Reveal the path of a clip, open clip, or write node in the finder or Media Hub.

    Script was formerly called Reveal Clips.

Menus:

    Right-click on clip in timeline -> Reveal... -> Reveal Clip in Finder / Reveal Clip in MediaHub

    Right-click on clip in media panel -> Reveal... -> Reveal Clip in Finder / Reveal Clip in MediaHub

    Right-click on clip in batch -> Reveal... -> Reveal Clip in Finder / Reveal Clip in MediaHub

    Right-click on clip in media hub -> Reveal... -> Reveal Clip in Finder

    Right-click in MediaHub tab -> Reveal... -> Reveal MediaHub Path in Finder

    Right-click on Write File node in batch -> Reveal... -> Reveal in Finder

    Right-click on Write File node in batch -> Reveal... -> Reveal in MediaHub

To install:

    Copy script into /opt/Autodesk/shared/python/reveal_path

Updates:

    v2.2 05.26.22

        Messages print to Flame message window - Flame 2023.1 and later

        Path is copied to clipboard

    v2.1 10.21.21

        Path that the MediaHub is currently open to can be revealed in Finder

        Write File node render path can be revealed in the MediaHub or in Finder

        Only the following tokens are currently supported with the write file node:

            project
            project nickname
            batch iteration
            batch name
            ext
            name
            shot name
            version padding
            version
            user
            user nickname

    v2.0 05.19.21

        Updated to be compatible with Flame 2022/Python 3.7

    v1.5 05.12.21

        Copy path to clipboard functionality moved to it's own script

        Merged with Reveal in Mediahub script - Reveal in MediaHub options only work in Flame 2021.2

        Clips in Timeline can now be revealed in Finder and Mediahub

    v1.4 05.08.21

        Clips in MediaHub can now be revealed in Finder and have paths copied to clipboard

    v1.2 01.25.20

        Menu option will now only show up when right-clicking on clips with file paths

    v1.1 08.11.19

        Code cleanup
'''

import os, re, platform, subprocess
from pyflame_lib_reveal_path import pyflame_print
from PySide2 import QtWidgets

SCRIPT_NAME = 'Reveal Path'
VERSION = 'v2.2'

print('\n')

# Reveal in Finder
#-------------------------------------#

def reveal_timeline_finder(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - timeline', '<' * 10, '\n')

    for item in selection:
        clip_path = item.file_path.rsplit('/', 1)[0]
        if clip_path:
            open_finder(clip_path)

def reveal_mediapanel_finder(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

    for item in selection:
        clip_path = item.versions[0].tracks[0].segments[0].file_path
        clip_path = clip_path.rsplit('/', 1)[0]
        if clip_path:
            open_finder(clip_path)

def reveal_batch_finder(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - batch', '<' * 10, '\n')

    for item in selection:
        if item.media_path is not None:
            clip_path = str(item.media_path)[1:-1]
            clip_path = clip_path.rsplit('/', 1)[0]
            if clip_path:
                open_finder(clip_path)

def reveal_mediahub_clip_finder(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - mediahub', '<' * 10, '\n')

    for item in selection:
        clip_path = item.path.rsplit('/', 1)[0]
        if clip_path:
            open_finder(clip_path)

def reveal_mediahub_path_finder(selection):
    import flame

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - mediahub', '<' * 10, '\n')

    open_finder(flame.mediahub.files.get_path())

def reveal_write_file_node_path_finder(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - write file node', '<' * 10, '\n')

    resolved_path = resolve_write_file_node_path(selection[0])

    if os.path.isdir(resolved_path):
        open_finder(resolved_path)
    else:
        pyflame_print(SCRIPT_NAME, 'Write File node path not found', message_type='error')

def open_finder(path: str):

    # Open finder window to path

    if platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])

    # Copy path to clipboard

    qt_app_instance = QtWidgets.QApplication.instance()
    qt_app_instance.clipboard().setText(path)

    pyflame_print(SCRIPT_NAME, f'Path opened in Finder: {path}')

# Reveal in MediaHub
#-------------------------------------#

def reveal_timeline_mediahub(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - timeline clip', '<' * 10, '\n')

    path = str(selection[0].file_path).rsplit('/', 1)[0]

    open_media_hub(path)

def reveal_mediapanel_mediahub(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - media panel clip', '<' * 10, '\n')

    selected_clip = selection[0]
    path = str(selected_clip.versions[0].tracks[0].segments[0].file_path).rsplit('/', 1)[0]

    open_media_hub(path)

def reveal_batch_mediahub(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - batch clip', '<' * 10, '\n')

    selected_clip = selection[0]

    path = str(selected_clip.media_path)[1:-1].rsplit('/', 1)[0]

    open_media_hub(path)

def reveal_write_file_node_path_mediahub(selection):

    print('>' * 10, f'{SCRIPT_NAME} {VERSION} - write file node', '<' * 10, '\n')

    resolved_path = resolve_write_file_node_path(selection[0])

    if os.path.isdir(resolved_path):
        open_media_hub(resolved_path)
    else:
        pyflame_print(SCRIPT_NAME, 'Write File node path not found', message_type='error')

def open_media_hub(path):
    import flame

    # Open path in MediaHub

    flame.go_to('MediaHub')
    flame.mediahub.files.set_path(path)

    # Copy path to clipboard

    qt_app_instance = QtWidgets.QApplication.instance()
    qt_app_instance.clipboard().setText(path)

    pyflame_print(SCRIPT_NAME, f'Path opened in MediaHub: {path}')

#-------------------------------------#

def resolve_write_file_node_path(write_node) -> str:
    import flame

    # Get paths from write file node

    media_path = str(write_node.media_path)[1:-1]
    print('media path:', media_path)

    media_path_pattern = str(write_node.media_path_pattern)[1:-1]
    print('media_path_pattern:', media_path_pattern)

    # Get token values

    project = str(flame.project.current_project.name)
    project_nickname = str(flame.project.current_project.nickname)
    batch_iteration = str(flame.batch.current_iteration.name)
    batch_name = str(flame.batch.name)[1:-1]
    ext = str(write_node.format_extension)[1:-1]
    name = str(write_node.name)[1:-1]
    shot_name = str(write_node.shot_name)[1:-1]
    version_padding = write_node.version_padding
    version = write_node.version_number
    version = ('0' * (version_padding - len(str(version))) + str(version))
    user = str(flame.users.current_user.name)
    user_nickname = str(flame.users.current_user.nickname)


    token_dict = {
        '<project>': project,
        '<project nickname>': project_nickname,
        '<batch iteration>': batch_iteration,
        '<batch name>': batch_name,
        '<ext>': ext,
        '<name>': name,
        '<shot name>':shot_name,
        '<version padding>': str(version_padding),
        '<version>': version,
        '<user>': user,
        '<user nickname>': user_nickname
        }

    # Replace tokens in pattern path with values

    for token, value in token_dict.items():
        media_path_pattern = media_path_pattern.replace(token, value)

    # Combine media path and resolved pattern path
    # Remove last two items in path assuming last two items
    # are versioned render folder and file name

    resolved_path = os.path.join(media_path, media_path_pattern)
    resolved_path = resolved_path.rsplit('/', 2)[0]

    print('resolved_path:', resolved_path, '\n')

    return resolved_path

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

    for item in selection:
        item_path = str(item.path)
        item_ext = re.search(r'\.\w{3}$', item_path, re.I)
        if item_ext != (None):
            return True
    return False

def scope_mediahub_tab(selection):
    import flame

    if flame.get_current_tab() == 'MediaHub' and flame.mediahub.files.get_path():
        return True
    return False

def scope_write_file_node(selection):
    import flame

    for item in selection:
        if item.type == 'Write File':
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
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Reveal Clip in Media Hub',
                    'isVisible': scope_timeline_clip,
                    'execute': reveal_timeline_mediahub,
                    'minimumVersion': '2022'
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
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Reveal Clip in Media Hub',
                    'isVisible': scope_batch_clip,
                    'execute': reveal_batch_mediahub,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Reveal Write File Path in Finder',
                    'isVisible': scope_write_file_node,
                    'execute': reveal_write_file_node_path_finder,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Reveal Write File Path in Media Hub',
                    'isVisible': scope_write_file_node,
                    'execute': reveal_write_file_node_path_mediahub,
                    'minimumVersion': '2022'
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
                    'execute': reveal_mediahub_clip_finder,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Reveal MediaHub Path in Finder',
                    'isVisible': scope_mediahub_tab,
                    'execute': reveal_mediahub_path_finder,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
