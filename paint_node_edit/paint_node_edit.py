'''
Script Name: Paint Node Edit
Script Version: 3.2
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 02.01.20
Update Date: 03.16.22

Custom Action Type: Batch Paint Node

Description:

    Delete and edit paint stroke durations in paint node.

Menus:

    Right-click on paint node -> Paint -> Delete Paint Strokes
    Right-click on paint node -> Paint -> Paint Strokes to Sequence: All
    Right-click on paint node -> Paint -> Paint Strokes to Range: All
    Right-click on paint node -> Paint -> Paint Strokes to Current: All
    Right-click on paint node -> Paint -> Paint Strokes to Sequence: Stroke Range
    Right-click on paint node -> Paint -> Paint Strokes to Range: Stroke Range
    Right-click on paint node -> Paint -> Paint Strokes to Current: Stroke Range

To install:

    Copy script into /opt/Autodesk/shared/python/paint_node_edit

Updates:

    v3.2 03.16.22

        UI Widgets moved to separate file

    v3.1 02.25.22

        Updated UI for Flame 2023

    v3.0 05.22.21

        Updated to be compatible with Flame 2022/Python 3.7

    v2.2 01.24.21

        Updated/Improved UI

    v2.1 01.21.21:

        Speed improvements - script no longer needs to save and reload batch setup

        Removed paint stroke tracking - paint stroke limitations made tracking useless

    v1.4 02.07.20:

        Fixed bug that caused Delete Paint Stokes not to work if last stroke in stack was deleted

    v1.3 02.04.20:

        Four new menu options have been added:

            Delete Paint Strokes - Select a range of strokes to delete

            Paint Strokes to Sequence: Range - Select a range of strokes to change to sequence

            Paint Strokes to Range: Range - Select a range of strokes last over a range of frames

            Paint Strokes to Current Frame: Range - Select a range of strokes to be set to current frame

        The old menu options remain but have been named to:

            Paint Strokes to Sequence: All

            Paint Strokes to Range: All

            Paint Strokes to Current Frame: All

    v1.1 02.01.20:

        Three options to choose from:

            Paint Strokes to Sequence

            Paint Strokes to Range

            Paint Strokes to Current Frame

        Changes will be applied to ALL strokes in selected paint node.
'''

from PySide2 import QtWidgets
from functools import partial
import os, re, shutil
from flame_widgets_paint_node_edit import FlameButton, FlameLabel, FlameMessageWindow, FlameSlider, FlameWindow

VERSION = 'v3.2'

# ------------------------------------- #

class EditPaint(object):

    def __init__(self, selection, lifespanstart, lifespanend, range_type, window_height):
        import flame

        print ('\n')
        print ('>' * 20, f'paint node edit {VERSION} - {range_type}', '<' * 20, '\n')

        self.range_type = range_type

        self.window_height = window_height

        self.paint_node = [n for n in selection][0]

        self.paint_node_name = str(self.paint_node.name)[1:-1]
        print ('paint_node:', self.paint_node_name)

        self.lifespanstart = lifespanstart
        self.lifespanend = lifespanend

        # Get batch start frame

        self.batch_start_frame = int(str(flame.batch.start_frame))
        print ('batch_start_frame:', self.batch_start_frame)

        # Get batch duration

        self.batch_duration = int(str(flame.batch.duration))
        print ('batch_duration:', self.batch_duration)

        # Batch end frame

        self.batch_end_frame = (self.batch_start_frame + self.batch_duration) - 1

        # Create temp paint folder

        self.temp_paint_path = '/opt/Autodesk/shared/python/paint_node_edit/temp_paint/'
        if not os.path.isdir(self.temp_paint_path):
            os.makedirs(self.temp_paint_path)

        # Path to save paint node

        self.paint_node_path = os.path.join(self.temp_paint_path, self.paint_node_name + '.paint_node')

        # Save paint node

        self.paint_node.save_node_setup(self.paint_node_path)

        # Load saved paint node

        get_paint_node = open(self.paint_node_path, 'r')
        values = get_paint_node.read().splitlines()

        self.paint_node_code = values[0]

        get_paint_node.close()

        # ------------------------ #

        # Misc Variables

        self.stroke = ''
        self.stroke_x_pos = ''
        self.stroke_y_pos = ''
        self.x_shift = ''
        self.y_shift = ''
        self.rotation = ''
        self.x_scaling = ''
        self.y_scaling = ''
        self.window_title = ''

        # Get last stroke number

        try:
            self.last_stroke = int(re.findall('<stroke(.*?)>', self.paint_node_code)[-1])
            print ('last_stroke:', self.last_stroke, '\n')
        except:
            self.last_stroke = ''

        # If no strokes put up message window

        if self.last_stroke != '':
            if self.range_type == 'sequence all':
                self.editpaint_node_all()
            elif self.range_type == 'current frame all':
                self.editpaint_node_all()
            else:
                self.main_window()
        else:
            FlameMessageWindow('Error', 'error', 'No strokes to edit: Paint something!')

    def main_window(self):
        import flame

        def do_nothing():
            # This does nothing. Just a place holder for the button. Replaced later in script.
            pass

        def start_slider_check(start_slider, end_slider, stroke):

            # Check start slider value against end slider value

            if int(start_slider.text()) > int(end_slider.text()):
                end_slider.setText(start_slider.text())

        def end_slider_check(end_slider, start_slider, stroke):

            # Check end slider value against start slider value

            if int(end_slider.text()) < int(start_slider.text()):
                start_slider.setText(end_slider.text())

        def all_strokes_to_range():

            self.window_title = f'Edit Paint Node <small>{VERSION}</small> - All Paint Strokes to Frame Range'

            # Labels

            self.range1_label = FlameLabel('Frame Range', 'underline')
            self.range2_label = FlameLabel('Start', 'normal')
            self.range3_label = FlameLabel('End', 'normal')

            # Sliders

            self.start_frame_slider = FlameSlider(1, 1, self.batch_duration, False)
            self.end_frame_slider = FlameSlider(self.batch_duration, 1, self.batch_duration, False)

            self.start_frame_slider.textChanged.connect(partial(start_slider_check, self.start_frame_slider, self.end_frame_slider))
            self.end_frame_slider.textChanged.connect(partial(end_slider_check, self.end_frame_slider, self.start_frame_slider))

            # Buttons

            self.apply_btn.clicked.connect(self.editpaint_node_range_all)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_frame_slider, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_frame_slider, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

        def delete_strokes_window():

            self.window_title = f'Edit Paint Node <small>{VERSION}</small> - Delete Paint Strokes'

            # Labels

            self.range1_label = FlameLabel('Stroke Range', 'underline')
            self.range2_label = FlameLabel('Start', 'normal')
            self.range3_label = FlameLabel('End', 'normal')

            # Sliders

            self.start_stroke_slider = FlameSlider(0, 0, self.last_stroke, False)
            self.end_stroke_slider = FlameSlider(self.last_stroke, 0, self.last_stroke, False)

            self.start_stroke_slider.textChanged.connect(partial(start_slider_check, self.start_stroke_slider, self.end_stroke_slider))
            self.end_stroke_slider.textChanged.connect(partial(end_slider_check, self.end_stroke_slider, self.start_stroke_slider))

            # Buttons

            self.apply_btn.clicked.connect(self.delete_paint_strokes)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_stroke_slider, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_stroke_slider, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

        def range_window():

            self.window_title = f'Edit Paint Node <small>{VERSION}</small> - Paint Stroke Range to Frame Range'

            # Labels

            self.range1_label = FlameLabel('Stroke Range', 'underline')
            self.range2_label = FlameLabel('Start', 'normal')
            self.range3_label = FlameLabel('End', 'normal')
            self.range4_label = FlameLabel('Frame Range', 'underline')
            self.range5_label = FlameLabel('Start', 'normal')
            self.range6_label = FlameLabel('End', 'normal')

            # Sliders

            self.start_frame_slider = FlameSlider(1, 1, self.batch_duration, False)
            self.end_frame_slider = FlameSlider(self.batch_duration, 1, self.batch_duration, False)

            self.start_frame_slider.textChanged.connect(partial(start_slider_check, self.start_frame_slider, self.end_frame_slider))
            self.end_frame_slider.textChanged.connect(partial(end_slider_check, self.end_frame_slider, self.start_frame_slider))

            self.start_stroke_slider = FlameSlider(0, 0, self.last_stroke, False)
            self.end_stroke_slider = FlameSlider(self.last_stroke, 0, self.last_stroke, False)

            self.start_stroke_slider.textChanged.connect(partial(start_slider_check, self.start_stroke_slider, self.end_stroke_slider))
            self.end_stroke_slider.textChanged.connect(partial(end_slider_check, self.end_stroke_slider, self.start_stroke_slider))

            # Buttons

            self.apply_btn.clicked.connect(self.editpaint_strokes_range_range)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_stroke_slider, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_stroke_slider, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

            self.gridbox.addWidget(self.range4_label, 4, 0, 1, 5)

            self.gridbox.addWidget(self.range5_label, 6, 0)
            self.gridbox.addWidget(self.start_frame_slider, 6, 1)

            self.gridbox.addWidget(self.range6_label, 6, 3)
            self.gridbox.addWidget(self.end_frame_slider, 6, 4)

            self.gridbox.setRowMinimumHeight(7, 35)

        def stroke_to_current_or_sequence_range_window():

            if self.range_type == 'sequence range':
                title = 'Paint Strokes to Sequence: Stroke Range'
            else:
                title = 'Paint Strokes to Current Frame: Stroke Range'

            self.window_title = f'Edit Paint Node <small>{VERSION}</small> - {title}'

            # Labels

            self.range1_label = FlameLabel('Stroke Range', 'underline')
            self.range2_label = FlameLabel('Start', 'normal')
            self.range3_label = FlameLabel('End', 'normal')

            # Sliders

            self.start_stroke_slider = FlameSlider(0, 0, self.last_stroke, False)
            self.end_stroke_slider = FlameSlider(self.last_stroke, 0, self.last_stroke, False)

            self.start_stroke_slider.textChanged.connect(partial(start_slider_check, self.start_stroke_slider, self.end_stroke_slider))
            self.end_stroke_slider.textChanged.connect(partial(end_slider_check, self.end_stroke_slider, self.start_stroke_slider))

            # Buttons

            self.apply_btn.clicked.connect(self.editpaint_strokes_range)

            # Window Layout

            self.gridbox = QtWidgets.QGridLayout()

            self.gridbox.addWidget(self.range1_label, 1, 0, 1, 5)

            self.gridbox.addWidget(self.range2_label, 2, 0)
            self.gridbox.addWidget(self.start_stroke_slider, 2, 1)

            self.gridbox.setColumnMinimumWidth(2, 100)

            self.gridbox.addWidget(self.range3_label, 2, 3)
            self.gridbox.addWidget(self.end_stroke_slider, 2, 4)

            self.gridbox.setRowMinimumHeight(3, 35)

        def close_window():

            self.window.close()

        # Buttons

        self.apply_btn = FlameButton('Apply', do_nothing)
        self.cancel_btn = FlameButton('Cancel', close_window)

        if self.range_type == 'range all':
            all_strokes_to_range()
        elif self.range_type == 'delete strokes':
            delete_strokes_window()
        elif self.range_type == 'range range':
            range_window()
        elif 'sequence range' or 'current frame range' in self.range_type:
            stroke_to_current_or_sequence_range_window()

        vbox = QtWidgets.QVBoxLayout()
        self.window = FlameWindow(self.window_title, vbox, 600, self.window_height)

        # Window Layout

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(5)
        hbox.addWidget(self.cancel_btn)
        hbox.addStretch(5)
        hbox.addWidget(self.apply_btn)
        hbox.addStretch(5)

        # Main VBox

        vbox.setMargin(20)

        vbox.addLayout(self.gridbox)
        vbox.addStretch(2)
        vbox.addLayout(hbox)

        self.window.show()

    def editpaint_strokes_range_range(self):

        # Variables from window

        start_stroke = int(str(self.start_stroke_slider.text()))
        end_stroke = int(str(self.end_stroke_slider.text()))

        start_frame = int(str(self.start_frame_slider.text()))
        end_frame = int(str(self.end_frame_slider.text()))

        if end_stroke >= start_stroke:
            if end_frame >= start_frame:
                try:
                    self.window.close()
                except:
                    pass

                # Split paint node into strokes

                split_list = self.paint_node_code.split('<PrStroke')

                loop_range = end_stroke - start_stroke + 1

                # Remove selected strokes

                for s in range(loop_range):
                    stroke_start_name = f'<stroke{start_stroke}>'

                    for stroke in split_list:
                        if stroke_start_name in stroke:
                            stroke = '<PrStroke' + stroke

                            # Replace lifespan values

                            new_stroke = re.sub('LifeSpanStart="(.*?)"', f'LifeSpanStart="{start_frame}"', stroke)
                            new_stroke = re.sub('LifeSpanEnd="(.*?)"', f'LifeSpanEnd="{end_frame}"', new_stroke)

                            # Replace stroke code

                            self.paint_node_code = self.paint_node_code.replace(stroke, new_stroke)

                    start_stroke = start_stroke + 1

                self.save_paint_node()
            else:
                FlameMessageWindow('Error', 'error', 'End frame should be equal to or higher than start frame')
        else:
            FlameMessageWindow('Error', 'error', 'End stroke should be equal to or higher than start stroke')

    def editpaint_strokes_range(self):

        start_stroke = int(str(self.start_stroke_slider.text()))
        end_stroke = int(str(self.end_stroke_slider.text()))

        if end_stroke >= start_stroke:
            self.window.close()

            # Split paint node into strokes

            split_list = self.paint_node_code.split('<PrStroke')

            loop_range = end_stroke - start_stroke + 1

            # Edit selected strokes

            for s in range(loop_range):
                stroke_start_name = f'<stroke{start_stroke}>'

                for stroke in split_list:
                    if stroke_start_name in stroke:
                        stroke = '<PrStroke' + stroke

                        # Replace lifespan values

                        new_stroke = re.sub('LifeSpanStart="(.*?)"', f'LifeSpanStart="{self.lifespanstart}"', stroke)
                        new_stroke = re.sub('LifeSpanEnd="(.*?)"', f'LifeSpanEnd="{self.lifespanend}"', new_stroke)

                        # Replace stroke code

                        self.paint_node_code = self.paint_node_code.replace(stroke, new_stroke)

                start_stroke = start_stroke + 1

            self.save_paint_node()

        else:
            FlameMessageWindow('Error', 'error', 'End stroke should be equal to or higher than start stroke')

    def delete_paint_strokes(self):

        delete_start = int(str(self.start_stroke_slider.text()))
        delete_end = int(str(self.end_stroke_slider.text()))

        if delete_end >= delete_start:

            self.window.close()

            delete_start_stroke = delete_start

            # Split paint node into strokes

            split_list = self.paint_node_code.split('<PrStroke')

            split_list_fixed = []

            for line in split_list:
                new_line = line.rsplit('</PrStroke>')[0]
                split_list_fixed.append(new_line)

            loop_range = delete_end - delete_start + 1

            # Remove selected strokes

            for s in range(loop_range):
                stroke_start_name = f'<stroke{delete_start}>'
                stroke_end_name = f'</stroke{delete_start}>'

                for n in split_list_fixed:
                    if stroke_start_name in n:
                        n = '<PrStroke' + n + '</PrStroke>'

                        # Remove selected stroke string

                        self.paint_node_code = self.paint_node_code.replace(n, '')

                delete_start = delete_start + 1

            loop_range = self.last_stroke - delete_end
            stroke_num = delete_end + 1
            new_stroke_num = delete_start_stroke

            for s in range(loop_range):
                stroke_start_name = f'<stroke{stroke_num}>'
                stroke_end_name = f'</stroke{stroke_num}>'

                new_stroke_start_name = f'<stroke{new_stroke_num}>'
                new_stroke_end_name = f'</stroke{new_stroke_num}>'

                self.paint_node_code = self.paint_node_code.replace(stroke_start_name, new_stroke_start_name)
                self.paint_node_code = self.paint_node_code.replace(stroke_end_name, new_stroke_end_name)

                new_stroke_num = new_stroke_num + 1
                stroke_num = stroke_num + 1

            print (f'deleted strokes {delete_start} to {delete_end}\n')

            self.save_paint_node()
        else:
            FlameMessageWindow('Error', 'error', 'End stroke should be equal to or higher than start stroke')

    def editpaint_node_all(self):

        # Replace lifespan values

        self.paint_node_code = re.sub('LifeSpanStart="(.*?)"', f'LifeSpanStart="{self.lifespanstart}"', self.paint_node_code)
        self.paint_node_code = re.sub('LifeSpanEnd="(.*?)"', f'LifeSpanEnd="{self.lifespanend}"', self.paint_node_code)

        self.save_paint_node()

    def editpaint_node_range_all(self):

        start = int(str(self.start_frame_slider.text()))
        end = int(str(self.end_frame_slider.text()))

        if end >= start:
            self.lifespanstart = str(start)
            self.lifespanend = str(end)

            self.window.close()

            self.editpaint_node_all()
        else:
            FlameMessageWindow('Error', 'error', 'End frame should be equal to or higher than start frame')

    #------------------------------------#

    def save_paint_node(self):
        import flame

        # Save paint node setup file

        paint_code = []

        paint_code.insert(0, self.paint_node_code)

        # Overwrite old paint node with new paint node

        out_file = open(self.paint_node_path, 'w')
        for line in paint_code:
            print(line, file=out_file)
        out_file.close()

        self.paint_node.load_node_setup(self.paint_node_path)

        # Delete temp folder

        shutil.rmtree(self.temp_paint_path)

        print ('--> paint node updated\n')

        print ('done.\n')

# ----------- #

def edit_sequence_all(selection):

    window_height = 220

    lifespanstart = '-2147483648'
    lifespanend = '2147483647'

    range_type = 'sequence all'

    EditPaint(selection, lifespanstart, lifespanend, range_type, window_height)

def edit_current_frame_all(selection):
    import flame

    window_height = 220

    current_frame = str(flame.batch.current_frame)
    print ('current_frame:', current_frame, '\n')

    lifespanstart = current_frame
    lifespanend = current_frame

    range_type = 'current frame all'

    EditPaint(selection, lifespanstart, lifespanend, range_type, window_height)

def edit_range_all(selection):

    window_height = 220

    lifespanstart = 1
    lifespanend = 1

    range_type = 'range all'

    return EditPaint(selection, lifespanstart, lifespanend, range_type, window_height)

# ----------- #

def delete_strokes(selection):

    window_height = 220

    lifespanstart = 1
    lifespanend = 1

    range_type = 'delete strokes'

    return EditPaint(selection, lifespanstart, lifespanend, range_type, window_height)

def edit_sequence_range(selection):

    window_height = 220

    lifespanstart = '-2147483648'
    lifespanend = '2147483647'

    range_type = 'sequence range'

    return EditPaint(selection, lifespanstart, lifespanend, range_type, window_height)

def edit_range(selection):

    window_height = 340

    lifespanstart = 1
    lifespanend = 1

    range_type = 'range range'

    return EditPaint(selection, lifespanstart, lifespanend, range_type, window_height)

def edit_current_frame_range(selection):
    import flame

    window_height = 220

    current_frame = str(flame.batch.current_frame)

    lifespanstart = current_frame
    lifespanend = current_frame

    range_type = 'current frame range'

    return EditPaint(selection, lifespanstart, lifespanend, range_type, window_height)

#------------------------------------#

def scope_paint_node(selection):
    import flame

    for item in selection:
        if item.type == 'Paint':
            return True
    return False

#------------------------------------#

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Paint Node...',
            'actions': [
                {
                    'name': 'Delete Paint Strokes',
                    'isVisible': scope_paint_node,
                    'execute': delete_strokes,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Paint Strokes to Sequence: All',
                    'isVisible': scope_paint_node,
                    'execute': edit_sequence_all,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Paint Strokes to Range: All',
                    'isVisible': scope_paint_node,
                    'execute': edit_range_all,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Paint Strokes to Current Frame: All',
                    'isVisible': scope_paint_node,
                    'execute': edit_current_frame_all,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Paint Strokes to Sequence: Stroke Range',
                    'isVisible': scope_paint_node,
                    'execute': edit_sequence_range,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Paint Strokes to Range: Stroke Range',
                    'isVisible': scope_paint_node,
                    'execute': edit_range,
                    'minimumVersion': '2022'
                },
                {
                    'name': 'Paint Strokes to Current Frame: Stroke Range',
                    'isVisible': scope_paint_node,
                    'execute': edit_current_frame_range,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
