'''
Script Name: Add Audio
Script Version: 1.2
Flame Version: 2023
Written by: Michael Vaglienty
Creation Date: 02.04.22
Update Date: 05.31.22

Custom Action Type: Batch

Description:

    Add stereo or 5.1 audio to selected sequences.

    To add stereo audio to a sequence, select the sequence then select the audio clip to be added.
    To add stereo audio to multiple sequences, select in sequence/audio/sequence/audio... order.

    To add 5.1 surround audio to a sequence, select the sequence followed by all the audio channels(LF, RF, C, LFE, LS, RS, Stereo)
    To add 5.1 surround audio to multiple sequences, select in sequence/all audio channels/sequences/all audio channels... order.

    Order of 5.1 surround files does not matter when being selected.
    When added to the sequence they will be put in this order: LF, RF, C, LFE, LS, RS, Stereo

    5.1 surround file names must end with _LF, _RF, _C, _LFE, _LS, _RS, or _Stereo. Case is not important.

Menus:

    Right-click selection of sequences and audio -> Audio -> Insert Stereo Audio - 01:00:00:00
    Right-click selection of sequences and audio -> Audio -> Insert Stereo Audio - 00:59:58:00
    Right-click selection of sequences and audio -> Audio -> Insert 5.1 Audio - 01:00:00:00
    Right-click selection of sequences and audio -> Audio -> Insert 5.1 Audio - 00:59:58:00

To install:

    Copy script into /opt/Autodesk/shared/python/add_audio

Updates:

    v1.2 05.31.22

        Messages print to Flame message window - Flame 2023.1 and later

    v1.1 03.15.22

        Added new message window
'''

from pyflame_lib_add_audio import FlameMessageWindow, pyflame_print
import re

SCRIPT_NAME = 'Add Audio'
SCRIPT_PATH = '/opt/Autodesk/shared/python/add_audio'
VERSION = 'v1.2'

class AddAudio():

    def __init__(self, selection):
        import flame

        print ('\n')
        print ('>' * 10, f'{SCRIPT_NAME} {VERSION}', '<' * 10, '\n')

        self.selection = selection

        self.ws = flame.projects.current_project.current_workspace

        if flame.get_current_tab() == 'MediaHub':
            flame.set_current_tab('Timeline')

    def create_new_library(self, audio_type):
        import flame

        self.audio_library = self.ws.create_library(f'{audio_type}')

        self.audio_library.expanded = True

        pyflame_print(SCRIPT_NAME, 'New audio library created.')

    def add_stereo_audio(self, timecode):
        import flame

        if len(self.selection) < 2:
            return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'At least one clip/sequence and audio clip must be selected.')

        sequence_selection = self.selection[::2]
        audio_selection = self.selection[1::2]

        if len(sequence_selection) != len(audio_selection):
            return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'For every sequence/clip selected an audio clip must be selected.')

        self.create_new_library('Stereo Audio')

        for sequence in sequence_selection:

            duplicate_sequence = flame.media_panel.copy(sequence, self.audio_library)[0]

            # Open sequence

            open_sequence = duplicate_sequence.open_as_sequence()

            # Get sequence frame rate

            open_sequence_frame_rate = open_sequence.frame_rate

            # Set pyTime

            insert_timecode = flame.PyTime(timecode, open_sequence_frame_rate)

            # Add audio track to open sequence

            open_sequence.create_audio()

            # Get corresponding audio clip from audio selection list

            audio_clip = audio_selection[sequence_selection.index(sequence)]

            # Insert audio

            open_sequence.insert(audio_clip, insert_time = insert_timecode)

        FlameMessageWindow('message', f'{SCRIPT_NAME}: Operation Complete', f'Stereo audio added to selected clips at {timecode}.<br><br>New clips can be found here: {str(self.audio_library.name)[1:-1]} Library')

    def add_surround_audio(self, timecode):
        import flame

        def sort_surround_list(audio_selection_list):

            # Sort selected audio files into proper order

            audio_selection_sorted = []

            surround_order = ['LF', 'RF', 'C', 'LFE', 'LS', 'RS', 'Stereo']

            for track in surround_order:
                for audio_clip in audio_selection_list:
                    audio_clip_name = str(audio_clip.name)[1:-1]
                    if re.search(f'{track}$', audio_clip_name, re.I):
                        audio_selection_sorted.append(audio_clip)

            return audio_selection_sorted

        # Check selection

        n = 8
        selected_groups = [self.selection[i * n:(i + 1) * n] for i in range((len(self.selection) + n - 1) // n )]

        for group in selected_groups:
            if len(group) != 8:
                return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Selection should be sequence followed by surround audio tracks:<br><br>LF, RF, C, LFE, LS, RS, Stereo.<br><br>Audio does not need to be in proper order.')

        # Create new library for clips with audio added

        self.create_new_library('5.1 Audio')

        for group in selected_groups:

            duplicate_sequence = flame.media_panel.copy(group[0], self.audio_library)[0]

            audio_selection = group[1:8]

            # Make sure 7 tracks are selected per clip

            if len(audio_selection) != 7:
                return FlameMessageWindow('error', f'{SCRIPT_NAME}: Error', 'Audio selection for 5.1 should contain these tracks:<br><br>LF, RF, C, LFE, LS, RS, Stereo<br><br>Audio does not need to be selected in proper order.')

            # Open sequence

            open_sequence = duplicate_sequence.open_as_sequence()

            # Get sequence frame rate

            open_sequence_frame_rate = open_sequence.frame_rate

            # Set pyTime

            insert_timecode = flame.PyTime(timecode, open_sequence_frame_rate)

            # Sort audio clips to proper order

            audio_selection_sorted = sort_surround_list(audio_selection)

            for audio_clip in audio_selection_sorted:

                # Add audio track to open sequence

                open_sequence.create_audio()

                audio_track = open_sequence.audio_tracks[audio_selection_sorted.index(audio_clip)].channels[0]

                # Insert audio

                open_sequence.overwrite(audio_clip, insert_timecode, audio_track)

        FlameMessageWindow('message', f'{SCRIPT_NAME}: Operation Complete', f'5.1 audio added to selected clips at {timecode}.<br><br>New clips can be found here: {str(self.audio_library.name)[1:-1]} Library')

def add_stereo_audio_one_hour(selection):

    script = AddAudio(selection)
    script.add_stereo_audio('01:00:00:00')

def add_stereo_audio_two_pop(selection):

    script = AddAudio(selection)
    script.add_stereo_audio('00:59:58:00')

def add_surround_audio_one_hour(selection):

    script = AddAudio(selection)
    script.add_surround_audio('01:00:00:00')

def add_surround_audio_two_pop(selection):

    script = AddAudio(selection)
    script.add_surround_audio('00:59:58:00')

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Audio...',
            'actions': [
                {
                    'name': 'Insert Stereo Audio - 01:00:00:00',
                    'execute': add_stereo_audio_one_hour,
                    'minimumVersion': '2023'
                },
                {
                    'name': 'Insert Stereo Audio - 00:59:58:00',
                    'execute': add_stereo_audio_two_pop,
                    'minimumVersion': '2023'
                },
                {
                    'name': 'Insert 5.1 Audio - 01:00:00:00',
                    'execute': add_surround_audio_one_hour,
                    'minimumVersion': '2023'
                },
                {
                    'name': 'Insert 5.1 Audio - 00:59:58:00',
                    'execute': add_surround_audio_two_pop,
                    'minimumVersion': '2023'
                }
            ]
        }
    ]
