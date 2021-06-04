'''
Script Name: Clip to Batch Group
Script Version: 2.1
Flame Version: 2020.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 06.16.19
Update Date: 05.19.21

Custom Action Type: Media Hub

Description:

    Import selected clips from the mediahub into newly created batch groups set to clip length with a render node

    -------------------------------------

    Option to switch to batch tab when batch groups are done being created can be
    turned off and on. Edit the following line in the __init__ section to either be True or False:

    self.go_to_batch = False

    Additional naming can be added to the end of batch group names. Edit the following line
    in the __init__ section. Naming must be in quotes.

    self.additional_naming = '_comp'

    Names of the batch group reels that are created by default can be
    changed by editing these two lines in the __init__ section:

    schematic_reel_list = ['Elements', 'Plates', 'PreRenders', 'Ref']
    shelf_reel_list = ['Renders']

    -------------------------------------

    To import clips into batch group with shot name extracted from clip name:

    Right-click on clip in MediaHub -> Import... -> Create New Batch Group - Shot Name
    Right-click on clip in MediaHub -> Import... -> Create New Batch Group - Shot Name - All Clips One Batch

    To import clips into batch group with clip name:

    Right-click on clip in MediaHub -> Import... -> Create New Batch Group - Clip Name
    Right-click on clip in MediaHub -> Import... -> Create New Batch Group - Clip Name - All Clips One Batch

    To create batch group from clips in media panel with shot name extracted from clip name:

    Right-click on clip in Media Panel -> Create New Batch Group... -> Shot Name

    To create batch group from clips in media panel with clip name:

    Right-click on clip in Media Panel -> Create New Batch Group... -> Clip Name

To install:

    Copy script into /opt/Autodesk/shared/python/clip_to_batch_group

Updates:

v2.1 05.19.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.8 05.15.21

    Properly names batch group with shot name when clip name starts with number - 123_030_bty_plate -> 123_030_comp

v1.7 02.19.21

    Option added to switch to batch tab or not when batch groups are create can be toggled
    by editing self.go_to_batch value in __init__. Must be True or False.

    Mediahub menu options added to import all selected clips into one batch group. Clip selected first is
    plate used for shot length and timecode.

v1.6 11.18.20

    Added Mux nodes with context 1 and 2 preset

v1.5 09.10.20

    Batch groups can now be imported and named after either the clip name or shot name

    Script will now switch to the Batch tab when creating a batch group from the media panel - caused an error before

v1.4 04.20.20

    Added ability to create batchgroup from clip in Media Panel

    Right-click on clip in Media Panel -> Clips... -> Create New Batchgroup

v1.3 11.01.19

    Changed menu name to Import...

    Render node takes frame rate from imported clip

v1.1 08.13.19

    Code cleanup
'''

from __future__ import print_function

VERSION = 'v2.1'

class CreateBatchGroup(object):

    def __init__(self, clip):
        import flame

        self.clip = clip
        self.clips_list = clip

        # Init variables

        self.clip_path = ''
        self.clip_name = ''

        # Additional naming to add to end of batch group name

        self.additional_naming = '_comp'

        # Go to batch tab when done creating batch groups

        self.go_to_batch = True

        # Names for shelf and schematic reels can be added or deleted here
        # Each reel name must be in quotes and seperated by commas
        # self.clip_reel points to the reel where clips will be imported to
        # The order of self.clip_reel in the list can changed but do not
        # remove it from the schematic reel list.

        self.clip_reel = 'Plates'

        self.schematic_reel_list = [self.clip_reel, 'Elements', 'PreRenders', 'Ref', 'Roto']
        self.shelf_reel_list = ['Renders']

        self.clip_reel_index = self.schematic_reel_list.index(self.clip_reel)

        # Create batch group

        self.batch_group = flame.batch.create_batch_group(
            'New Batch',
            duration=100,
            reels=self.schematic_reel_list,
            shelf_reels=self.shelf_reel_list)

    def import_batch_group(self):
        import flame

        # Get clip path

        self.clip_path = str(self.clip.path)
        print ('clip_path:', self.clip_path)

        # Import clip to batchgroup

        flame.batch.import_clip(self.clip_path, self.clip_reel)

        # Get batch group name

        self.name_batch_group_clip_name()

        # Create render node and set render node properties

        self.create_nodes()

    def import_all_batch_group(self):
        import flame

        # Import clip to batch group

        for clip in self.clips_list:
            self.clip_path = str(clip.path)
            print ('clip_path:', self.clip_path)
            flame.batch.import_clip(self.clip_path, self.clip_reel)

        # Get batch group name

        self.name_batch_group_clip_name()

        # Create render node and set render node properties

        self.create_nodes()

    def import_batch_group_shot_name(self):
        import flame

        # Get clip path

        self.clip_path = str(self.clip.path)
        print ('clip_path:', self.clip_path)

        # Import clip to batchgroup

        flame.batch.import_clip(self.clip_path, self.clip_reel)

        # Get batch group name

        self.name_batch_group_shot_name()

        # Create render node and set render node properties

        self.create_nodes()

    def import_all_batchgroup_shot_name(self):
        import flame

        # Import clip to batch group

        for clip in self.clips_list:
            self.clip_path = str(clip.path)
            print ('clip_path:', self.clip_path)

            flame.batch.import_clip(self.clip_path, self.clip_reel)

        # Get batch group name

        self.name_batch_group_shot_name()

        # Create render node and set render node properties

        self.create_nodes()

    def clip_batch_group(self):
        import flame

        flame.go_to('Batch')

        # Copy clip to batchgroup

        flame.media_panel.copy(self.clip, self.batch_group.reels[self.clip_reel_index])

        # Get batch group name

        self.name_batch_group_clip_name()

        # Create render node and set render node properties

        self.create_nodes()

    def all_clips_batch_group(self):
        import flame

        # Switch to batch tab

        flame.go_to('Batch')

        # Copy clip to batch group

        for clip in self.clips_list:
            flame.media_panel.copy(clip, self.batch_group.reels[self.clip_reel_index])

        # Get batch group name

        self.name_batch_group_clip_name()

        # Create render node and set render node properties

        self.create_nodes()

    def clip_batch_group_shot_name(self):
        import flame

        # Switch to batch tab

        flame.go_to('Batch')

        # Copy clip to batch group

        flame.media_panel.copy(self.clip, self.batch_group.reels[self.clip_reel_index])

        # Get batch group name

        self.name_batch_group_shot_name()

        # Create render node and setup render node properties

        self.create_nodes()

    def all_clips_batch_group_shot_name(self):
        import flame

        # Switch to batch tab

        flame.go_to('Batch')

        # Copy clip to batch group

        for clip in self.clips_list:
            flame.media_panel.copy(clip, self.batch_group.reels[self.clip_reel_index])

        # Get batch group name

        self.name_batch_group_shot_name()

        # Create render node and setup render node properties

        self.create_nodes()

    def name_batch_group_shot_name(self):
        import flame
        import re

        # Name batch group using shot name

        self.clip = flame.batch.nodes[0]
        self.clip_name = str(self.clip.name)[1:-1]
        print ('clip_name:', self.clip_name)

        # Split clip name into list by numbers in clip name

        shot_name_split = re.split(r'(\d+)', self.clip_name)
        shot_name_split = [s for s in shot_name_split if s != '']
        print ('shot_name_split:', shot_name_split)

        # Recombine shot name split list into new batch group name
        # Else statement is used if clip name starts with number

        if shot_name_split[1].isalnum():
            shot_name = shot_name_split[0] + shot_name_split[1] + self.additional_naming
        else:
            shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2] + self.additional_naming

        print ('shot_name:', shot_name)

        self.batch_group.name = shot_name

    def name_batch_group_clip_name(self):
        import flame

        # Name batch group with clip name

        self.clip = flame.batch.nodes[0]
        self.clip_name = str(self.clip.name)[1:-1]
        self.batch_group.name = self.clip_name + self.additional_naming

    def create_nodes(self):
        import flame

        # Set batch group duration

        self.batch_group.duration = self.clip.duration

        # Get clip timecode

        imported_clip = self.batch_group.reels[self.clip_reel_index].clips[0]
        clip_timecode = imported_clip.start_time
        clip_frame_rate = imported_clip.frame_rate
        print ('clip_timecode:', clip_timecode)
        print ('clip_frame_rate:', clip_frame_rate)

        # Create mux nodes

        plate_in_mux = self.batch_group.create_node('Mux')
        plate_in_mux.name = 'plate_in'
        plate_in_mux.set_context(1, 'Default')
        plate_in_mux.pos_x = 400
        plate_in_mux.pos_y = -30

        render_out_mux = self.batch_group.create_node('Mux')
        render_out_mux.name = 'render_out'
        render_out_mux.set_context(2, 'Default')
        render_out_mux.pos_x = plate_in_mux.pos_x + 1600
        render_out_mux.pos_y = plate_in_mux.pos_y - 30

        # Create render node

        render_node = self.batch_group.create_node('Render')
        render_node.frame_rate = clip_frame_rate
        render_node.range_end = self.clip.duration
        render_node.source_timecode = clip_timecode
        render_node.record_timecode = clip_timecode
        render_node.name = '<batch iteration>'
        render_node.pos_x = render_out_mux.pos_x + 400
        render_node.pos_y = render_out_mux.pos_y -30

        # Connect nodes

        flame.batch.connect_nodes(self.clip, 'Default', plate_in_mux, 'Default')
        flame.batch.connect_nodes(plate_in_mux, 'Result', render_out_mux, 'Default')
        flame.batch.connect_nodes(render_out_mux, 'Result', render_node, 'Default')

        try:
            flame.go_to('Batch')
            flame.batch.frame_all()

            if not self.go_to_batch:
                flame.go_to('Mediahub')
        except:
            pass

        print ('\n', '>>> %s batchgroup created <<<' % self.clip_name, '\n')

# ------------------------------------------------- #

def clip_to_batch_group(selection):

    print ('\n', '>' * 20, 'clip to batchgroup %s' % VERSION, '<' * 20, '\n')

    for clip in selection:
        create = CreateBatchGroup(clip)
        create.clip_batch_group()

def clip_to_batch_group_shot_name(selection):

    print ('\n', '>' * 20, 'clip to batchgroup %s' % VERSION, '<' * 20, '\n')

    for clip in selection:
        create = CreateBatchGroup(clip)
        create.clip_batch_group_shot_name()

def import_to_batch_group(selection):

    print ('\n', '>' * 20, 'clip to batchgroup %s - import clips' % VERSION, '<' * 20, '\n')

    for clip in selection:
        create = CreateBatchGroup(clip)
        create.import_batch_group()

def import_all_to_batch_group(selection):

    print ('\n', '>' * 20, 'clip to batchgroup %s - import all clips to single batch group' % VERSION, '<' * 20, '\n')

    create = CreateBatchGroup(selection)
    create.import_all_batch_group()

def import_to_batch_group_shot_name(selection):

    print ('\n', '>' * 20, 'clip to batchgroup %s - import clips' % VERSION, '<' * 20, '\n')

    for clip in selection:
        create = CreateBatchGroup(clip)
        create.import_batch_group_shot_name()

def import_all_to_batch_group_shot_name(selection):

    print ('\n', '>' * 20, 'clip to batchgroup %s - import all clips to single batch group' % VERSION, '<' * 20, '\n')

    create = CreateBatchGroup(selection)
    create.import_all_batchgroup_shot_name()

# ------------------------------------------------- #

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def scope_file(selection):
    import re

    for item in selection:
        item_path = str(item.path)
        item_ext = re.search(r'\.\w{3}$', item_path, re.I)
        if item_ext != (None):
            return True
    return False

# ------------------------------------------------- #

def get_mediahub_files_custom_ui_actions():

    return [
        {
            'name': 'Import...',
            'actions': [
                {
                    'name': 'Create New Batch Group - Shot Name',
                    'isVisible': scope_file,
                    'execute': import_to_batch_group_shot_name,
                    'minimumVersion': '2020.1'
                },
                {
                    'name': 'Create New Batch Group - Shot Name - All Clips One Batch',
                    'isVisible': scope_file,
                    'execute': import_all_to_batch_group_shot_name,
                    'minimumVersion': '2020.1'
                },
                {
                    'name': 'Create New Batch Group - Clip Name',
                    'isVisible': scope_file,
                    'execute': import_to_batch_group,
                    'minimumVersion': '2020.1'
                },
                {
                    'name': 'Create New Batch Group - Clip Name - All Clips One Batch',
                    'isVisible': scope_file,
                    'execute': import_all_to_batch_group,
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Create New Batch Group...',
            'actions': [
                {
                    'name': 'Shot Name',
                    'isVisible': scope_clip,
                    'execute': clip_to_batch_group_shot_name,
                    'minimumVersion': '2020.1',
                },
                {
                    'name': 'Clip Name',
                    'isVisible': scope_clip,
                    'execute': clip_to_batch_group,
                    'minimumVersion': '2020.1',
                }
            ]
        }
    ]
