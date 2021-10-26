'''
Script Name: Neat Freak
Script Version: 1.1
Flame Version: 2021.2
Written by: Michael Vaglienty
Creation Date: 10.22.21
Update Date: 10.26.21

Custom Action Type: Batch

Description:

    Builds batch setup to process multiple clips through Neat.

    Only works with Neat v5

    Render node outputs are set to match each clip(name, duration, timecode, fps, bit-depth).

    Menu:

        Right-click on any clip in media panel -> Neat... -> Degrain Clips

To install:

    Copy script into /opt/Autodesk/shared/python/pyFlame/neat_freak

Updates:

    v1.1 10.26.21

        Script now attempts to add shot name to render node
'''

from __future__ import print_function
import re

VERSION = 'v1.1'

class NeatFreak(object):

    def __init__(self, selection):

        print ('\n', '>' * 20, 'neat freak %s - denoise clip' % VERSION, '<' * 20, '\n')

        self.selection = selection

        # Init Variables

        self.batchgroup = ''
        self.clip = ''
        self.plates_reel = ''
        self.y_position = 0
        self.neat_node = ''
        self.batch_clip = ''
        self.clip_node = ''
        self.clip_name = ''
        self.clip_duration = ''
        self.clip_frame_rate = ''
        self.clip_timecode = ''
        self.clip_bit_depth = ''
        self.batch_duration = 1

        self.neat_clips()

    def neat_clips(self):
        import flame

        flame.go_to('Batch')

        self.create_batch_group()

        for clip in self.selection:
            self.clip = clip

            self.copy_clip_to_batch()

            # Get clip variables for batch and render node settings

            self.get_clip_info()

            # Create neat and render nodes

            self.create_batch_nodes()

        self.batchgroup.frame_all()

    def create_batch_group(self):
        import flame

        self.batchgroup = flame.batch.create_batch_group('Neat', reels=['plates'])

        self.plates_reel = self.batchgroup.reels[0]

        self.batchgroup.expanded = False

    def copy_clip_to_batch(self):
        import flame

        flame.media_panel.copy(self.clip, self.plates_reel)

    def get_clip_info(self):
        import flame

        self.clip_name = str(self.clip.name)[1:-1]

        # Get clip node from batch for clip duration

        self.clip_node = [n for n in flame.batch.nodes if n.name == self.clip_name][0]

        # Get clip values

        self.clip_duration = self.clip_node.duration
        self.clip_frame_rate = self.clip.frame_rate
        self.clip_timecode = self.clip.start_time
        self.clip_bit_depth = self.clip.bit_depth
        # self.clip_shot_name = self.clip.shot_name

        self.get_shot_name()

        if self.clip_bit_depth < 16:
            self.clip_bit_depth = str(self.clip_bit_depth) + '-bit'
        else:
            self.clip_bit_depth = str(self.clip_bit_depth) + '-bit fp'

        # Set batch duration if duration of current clip is longer than last or Default

        if int(str(self.clip_duration)) > int(str(self.batch_duration)):
            self.batchgroup.duration = int(str(self.clip_duration))

    def create_batch_nodes(self):
        import flame

        # Add neat node

        self.neat_node = self.batchgroup.create_node('OpenFX')
        self.neat_node.change_plugin('Reduce Noise v5')
        self.neat_node.pos_x = 0
        self.neat_node.pos_y = self.y_position

        # Add render node

        self.render_node = self.batchgroup.create_node('Render')
        self.render_node.range_end = self.clip_duration
        self.render_node.frame_rate = self.clip_frame_rate
        self.render_node.source_timecode = self.clip_timecode
        self.render_node.record_timecode = self.clip_timecode
        self.render_node.bit_depth = self.clip_bit_depth
        self.render_node.name = self.clip_name + '_neat'
        self.render_node.pos_x = self.neat_node.pos_x + 300
        self.render_node.pos_y = self.y_position - 25

        if self.clip_shot_name:
            self.render_node.shot_name = self.clip_shot_name

        # Move clip

        self.clip_node.pos_x = self.neat_node.pos_x - 300
        self.clip_node.pos_y = self.y_position + 25

        # Connect nodes

        flame.batch.connect_nodes(self.clip_node, 'Default', self.neat_node, 'Default')
        flame.batch.connect_nodes(self.neat_node, 'Default', self.render_node, 'Default')

        self.y_position = self.y_position - 200

    def get_shot_name(self):

            # Get shot name from assigned clip shot name

            if self.clip.versions[0].tracks[0].segments[0].shot_name != '':
                self.clip_shot_name = str(self.clip.versions[0].tracks[0].segments[0].shot_name)[1:-1]
            else:
                # If shot name not assigned to clip, guess at shot name from clip name

                clip_name = str(self.clip.name)[1:-1]
                # print ('clip_name:', clip_name)

                # Split clip name into list by numbers in clip name

                shot_name_split = re.split(r'(\d+)', clip_name)
                shot_name_split = [s for s in shot_name_split if s != '']
                # print ('shot_name_split:', shot_name_split)

                # Recombine shot name split list into new batch group name
                # Else statement is used if clip name starts with number

                if shot_name_split[1].isalnum():
                    self.clip_shot_name = shot_name_split[0] + shot_name_split[1]
                else:
                    self.clip_shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]

# ---------------------------------------- #

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

# ---------------------------------------- #

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Neat...',
            'actions': [
                {
                    'name': 'Denoise Clips',
                    'isVisible': scope_clip,
                    'execute': NeatFreak,
                    'minimumVersion': '2021.2'
                }
            ]
        }
    ]
