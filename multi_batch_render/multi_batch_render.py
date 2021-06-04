'''
Script Name: Multi Batch Render
Script Version: 4.1
Flame Version: 2020
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 12.12.18
Update Date: 05.19.21

Custom Action Type: Batch / Media Panel Desktop

Description:

    Batch render selected batch groups

    To enable burn or close batch groups after render options: Right click in batch -> Render... -> Multi-Batch Render -> Setup

    To render selected batch groups: Right click -> Render... on selected batch groups in desktop

    To select from list of batch groups to render: Right click in batch -> Render... -> Multi-Batch Render

To install:

    Copy script into /opt/Autodesk/shared/python/multi_batch_render

Updates:

v4.1 05.19.21

    Updated to be compatible with Flame 2022/Python 3.7

v3.5 11.29.20

    More UI enhancements / Fixed Font for Linux

    Misc bug fixes

    Batch groups that fail to render won't stop script. Failed batch group renders listed when all renders are complete

v3.2 08.10.20

    Updated UI

v3.1 07.26.20

    Save/Exit button added to main render window. This will save the project and exit Flame when the render is done.

    Fixed errors when attempting to render from desktop with multiple batch groups with same name.

v3.0 07.09.20:

    Fixed errors when attempting to render batch groups with no Render or Write nodes. These batch groups will now be skipped

    Code cleanup

v2.91 05.18.20:

    Render menu no longer incorrectly appears when selecting a batchgroup in a Library or Folder

v2.9 02.23.20:

    Render window now centers in linux

    Script auto replaces all render and write nodes. Works as a fix for when render/write nodes stop working in batch

    Added menu to render current batch to batch menu. Render... -> Render Current - Use when getting errors with existing render and write nodes.

v2.8 02.09.20:

    Window can now be resized

    Fixed bug with Close Batch After Rendering checkbox - showed as checked even after being unchecked.

    Burn button updated when checked or unchecked in setup

v2.7 11.06.19

    Menu now appears as Render... when right-clicking on batch groups and in the batch window

    Removed menu that showed up in media panel when right clicking on items that could not be rendered.

v2.6 10.13.19

    Add option in main setup that will close batch groups when renders are done.

    Removed menu that showed up when clicking on items in media panel that could not be rendered.
'''

from __future__ import print_function
import os
from PySide2 import QtWidgets, QtCore

VERSION = 'v4.1'

SCRIPT_PATH = '/opt/Autodesk/shared/python/multi_batch_render'

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget

    For different label looks use: label_type='normal', label_type='background', or label_type='outline'

    To use:

    label = FlameLabel('Label Name', 'normal', window)
    """

    def __init__(self, label_name, label_type, parent_window, *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent_window)
        self.setMinimumSize(110, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                               'QLabel:disabled {color: #6a6a6a}')
        elif label_type == 'background':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')
        elif label_type == 'outline':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget

    To use:

    button = FlameButton('Button Name', do_this_when_pressed, window)
    """

    def __init__(self, button_name, do_when_pressed, parent_window, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setMinimumSize(QtCore.QSize(120, 28))
        self.setMaximumSize(QtCore.QSize(120, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(do_when_pressed)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlamePushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Widget

    To use:

    pushbutton = FlamePushButton(' Button Name', True_or_False, window)
    """

    def __init__(self, button_name, button_checked, parent_window, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setCheckable(True)
        self.setChecked(button_checked)
        self.setMinimumSize(120, 28)
        self.setMaximumSize(120, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #424142, stop: .91 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #4f4f4f, stop: .91 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .90 #383838, stop: .91 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlameListWidget(QtWidgets.QListWidget):
    """
    Custom Qt Flame List Widget

    To use:

    list_widget = FlameListWidget(window)
    """

    def __init__(self, parent_window, *args, **kwargs):
        super(FlameListWidget, self).__init__(*args, **kwargs)

        self.setMinimumSize(300, 250)
        self.setParent(parent_window)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setStyleSheet('QListWidget {color: #9a9a9a; background-color: #2a2a2a; alternate-background-color: #2d2d2d; outline: none; font: 14px "Discreet"}'
                           'QListWidget::item:selected {color: #d9d9d9; background-color: #474747}')

# ---------------------------------- #

class MultiBatchRender(object):

    def __init__(self, selection):
        import flame

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')

        self.check_config_file()

        # Get config values from config file

        self.load_config_file()

        self.selection = selection

        self.desk = flame.project.current_project.current_workspace.desktop

        self.desktop_batch_group_object_list = self.desk.batch_groups

        self.desktop_batch_group_list = [str(b.name)[1:-1] for b in self.desktop_batch_group_object_list]

        # Init variables

        self.batch_to_render = ''
        self.num_batch_groups = ''
        self.batch_groups_rendered = 0
        self.failed_render_list = []

    def load_config_file(self):
        import ast

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.burn_enabled = ast.literal_eval(values[2])
        self.close_after_render = ast.literal_eval(values[4])

        get_config_values.close()

    def check_config_file(self):
        import ast

        if not os.path.isdir(self.config_path):
            print ('config folder does not exist, creating folder and config file.')
            os.makedirs(self.config_path)

        if not os.path.isfile(self.config_file):
            print ('config file does not exist, creating new config file.')

            config_text = []

            config_text.insert(0, 'Setup values for pyFlame Multi Batch Render script.')
            config_text.insert(1, 'Enable Burn:')
            config_text.insert(2, 'False')
            config_text.insert(3, 'Close Batch After Render:')
            config_text.insert(4, 'False')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

        # Read burn enabled setting

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()
        burn_enabled = ast.literal_eval(values[2])
        get_config_values.close()

        return burn_enabled

    def main_window(self):

        def setup_main_window():

            def setup_save():

                config_text = []

                config_text.insert(0, 'Setup values for pyFlame Multi Batch Render script.')
                config_text.insert(1, 'Enable Burn:')
                config_text.insert(2, enable_burn_pushbutton.isChecked())
                config_text.insert(3, 'Close Batch After Rendering:')
                config_text.insert(4, close_batch_pushbutton.isChecked())

                out_file = open(self.config_file, 'w')
                for line in config_text:
                    print(line, file=out_file)
                out_file.close()

                self.setup_window.close()

                self.window.close()

                self.load_config_file()

                self.main_window()

            def setup_cancel():

                self.setup_window.close()

            self.load_config_file()

            self.setup_window = QtWidgets.QWidget()
            self.setup_window.setMaximumSize(500, 210)
            self.setup_window.setWindowTitle('Multi Batch Render Setup %s' % VERSION)
            self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.setup_window.setStyleSheet('background-color: #313131')

            # Center window in linux

            resolution = QtWidgets.QDesktopWidget().screenGeometry()
            self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                                   (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

            # Pushbuttons

            enable_burn_pushbutton = FlamePushButton(' Enable Burn', self.burn_enabled, self.setup_window)
            enable_burn_pushbutton.setMinimumSize(175, 28)
            enable_burn_pushbutton.setToolTip('Enable to batch submit to burn')

            close_batch_pushbutton = FlamePushButton(' Close Batch Groups', self.close_after_render, self.setup_window)
            close_batch_pushbutton.setMinimumSize(175, 28)
            close_batch_pushbutton.setToolTip('If enabled batch groups will close as renders finish.')

            # Buttons

            save_btn = FlameButton('Save', setup_save, self.setup_window)

            cancel_btn = FlameButton('Cancel', setup_cancel, self.setup_window)

            # --------------------- #

            # Layout

            grid = QtWidgets.QGridLayout()
            grid.setMargin(20)
            grid.addWidget(enable_burn_pushbutton, 0, 0)
            grid.addWidget(close_batch_pushbutton, 1, 0)
            grid.setHorizontalSpacing(80)
            grid.addWidget(save_btn, 0, 2)
            grid.setVerticalSpacing(10)
            grid.addWidget(cancel_btn, 1, 2)

            self.setup_window.setLayout(grid)

            self.setup_window.show()

            return self.setup_window

        def list_batch_groups():
            import flame

            current_batch_group = str(flame.batch.name)[1:-1]
            print ('current_batch_group: ', current_batch_group)

            # Get current batch number

            for i in [i for i, x in enumerate(self.desktop_batch_group_list) if x == current_batch_group]:
                current_batch_num = int(i)
            print ('current_batch_num: ', current_batch_num)

            # Add names of batch groups to list

            print ([b for b in self.desktop_batch_group_list])

            print ([b.name for b in self.desk.batch_groups])

            self.batch_group_list.addItems(self.desktop_batch_group_list)
            self.batch_group_list.setCurrentItem(self.batch_group_list.item(current_batch_num))
            self.batch_group_list.setFocus()

            print ('\n')

        def selected_listbox_batch_groups():
            import flame

            # List of all items in batchgroup list box

            all_batch_groups_list = [str(self.batch_group_list.item(index)) for index in range(self.batch_group_list.count())]
            print ('all_batch_groups_list:', all_batch_groups_list)

            # List of selected batchgroups

            self.selected_batch_group_objects = [str(b) for b in self.batch_group_list.selectedItems()]

            # Get index number of selected batch groups

            self.selected_batch_groups = []
            for batch in self.selected_batch_group_objects:
                for i in [i for i, x in enumerate(all_batch_groups_list) if x == batch]:
                    self.selected_batch_groups.append(i)

        def render():

            self.window.close()

            selected_listbox_batch_groups()

            self.render_batch_groups()

        def burn():

            self.window.close()

            selected_listbox_batch_groups()

            for num in self.selected_batch_groups:
                batch_to_render = self.desktop_batch_group_object_list[num]
                print ('burning:', str(batch_to_render.name)[1:-1], '\n')
                self.submit_burn_render(batch_to_render)

        def cancel():

            self.window.close()

            try:
                self.setup_window.close()
            except:
                pass

        self.window = QtWidgets.QWidget()
        self.window.setMinimumSize(575, 350)
        self.window.setWindowTitle('Multi Batch Render %s' % VERSION)
        self.window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.setStyleSheet('background-color: #313131')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.window.move((resolution.width() / 2) - (self.window.frameSize().width() / 2),
                         (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Labels

        self.batch_group_label = FlameLabel('Desktop Batch Groups', 'normal', self.window)

        # Listboxes

        self.batch_group_list = FlameListWidget(self.window)

        list_batch_groups()

        # Buttons

        self.render_btn = FlameButton('Render', render, self.window)

        self.burn_btn = FlameButton('Burn', burn, self.window)
        if self.burn_enabled:
            self.burn_btn.setEnabled(True)
        else:
            self.burn_btn.setEnabled(False)

        self.exit_btn = FlamePushButton('      Save/Exit', False, self.window)
        self.exit_btn.setToolTip('Enable to save workspace and exit Flame when render is complete')

        self.setup_btn = FlameButton('Setup', setup_main_window, self.window)

        self.cancel_btn = FlameButton('Cancel', cancel, self.window)

        # --------------------- #

        # Window Layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setMargin(20)

        gridbox.addWidget(self.batch_group_label, 0, 0)
        gridbox.addWidget(self.batch_group_list, 1, 0, 7, 1)

        gridbox.addWidget(self.render_btn, 1, 1)
        gridbox.addWidget(self.burn_btn, 2, 1)
        gridbox.addWidget(self.exit_btn, 4, 1)
        gridbox.addWidget(self.setup_btn, 6, 1)
        gridbox.addWidget(self.cancel_btn, 7, 1)

        self.window.setLayout(gridbox)

        self.window.show()

    def get_selected_batch_groups(self):

        self.batchgroup_selection = [batch for batch in self.selection]

        self.selected_batch_groups = []

        for b in self.desktop_batch_group_object_list:
            if b in self.batchgroup_selection:
                batch_num = self.desktop_batch_group_object_list.index(b)
                self.selected_batch_groups.append(batch_num)

        print ('selected batchgroup numbers:', self.selected_batch_groups, '\n')

    def render_selected_batch_groups(self):

        self.get_selected_batch_groups()

        self.render_batch_groups()

    def render_batch_groups(self):
        import flame

        def render_progress_window():

            def render_done_button():

                self.render_window.close()

            # Get number of batchgroups to render

            self.num_batch_groups = len(self.selected_batch_groups)

            # Render progress window
            # ----------------------

            self.render_window = QtWidgets.QWidget()
            self.render_window.setFixedSize(400, 160)
            self.render_window.setWindowTitle('Multi Batch Render %s' % VERSION)
            self.render_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.render_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.render_window.setStyleSheet('background-color: #313131')

            # Center window in linux

            resolution = QtWidgets.QDesktopWidget().screenGeometry()
            self.render_window.move((resolution.width() / 2) - (self.render_window.frameSize().width() / 2),
                                    (resolution.height() / 2) - (self.render_window.frameSize().height() / 2))

            # Label

            self.rendering_label = QtWidgets.QLabel('', self.render_window)
            self.rendering_label.move(30, 20)
            self.rendering_label.resize(300, 22)
            self.rendering_label.setStyleSheet('color: #9a9a9a; font: 14px "Discreet"')

            # Buttons

            self.render_done_btn = QtWidgets.QPushButton('Done', self.render_window)
            self.render_done_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            self.render_done_btn.move(150, 110)
            self.render_done_btn.resize(100, 28)
            self.render_done_btn.setEnabled(False)
            self.render_done_btn.autoDefault()
            self.render_done_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                                               'QPushButton:pressed {font: italic; color: #d9d9d9}')
            self.render_done_btn.clicked.connect(render_done_button)

            # Progress bar

            self.progress_bar = QtWidgets.QProgressBar(self.render_window)
            self.progress_bar.move(30, 60)
            self.progress_bar.resize(340, 28)
            self.progress_bar.setMaximum(self.num_batch_groups)
            self.progress_bar.setStyleSheet('QProgressBar {color: #9a9a9a; font: 14px "Discreet"; text-align: center}'
                                            'QProgressBar:chunk {background-color: #373e47; border-top: 1px solid #242424; border-bottom: 1px solid #474747; border-left: 1px solid #242424; border-right: 1px solid #474747}')

            self.render_window.show()

        def duplicate_render_nodes():
            import flame

            # Duplicate render nodes
            # Fix for flame bug - render nodes stop working

            for n in flame.batch.nodes:
                if n.type in ('Render', 'Write File'):
                    new_node = n.duplicate(keep_node_connections=True)
                    new_node.pos_x = n.pos_x
                    new_node.pos_y = n.pos_y
                    n.delete()

        def render_batch_group():

            # Update progress bar

            self.batch_groups_rendered += 1

            # Check for Render or Write node before rendering
            # If none found, skip and print message

            if [node for node in self.batch_to_render.nodes if node.type in ('Render', 'Write File')] == []:
                self.failed_render_list.append(self.batch_to_render.name)
                print ('\n>>> %s has no render or write nodes. Skipping. <<<\n' % self.batch_to_render.name)
            else:
                self.rendering_label.setText('Rendering Batch %d of %d ...' % (self.batch_groups_rendered, self.num_batch_groups))
                print ('\nRendering Batch %d of %d ...\n' % (self.batch_groups_rendered, self.num_batch_groups))

                # Replace render/write nodes - fix for flame render node bug

                duplicate_render_nodes()

                # Render in foreground
                # If render fails add to failed render list

                try:
                    self.batch_to_render.render()
                except:
                    self.failed_render_list.append(self.batch_to_render.name)

            self.progress_bar.setValue(self.batch_groups_rendered)

            if self.batch_groups_rendered == self.num_batch_groups:
                print ('\n', '>>> rendering done <<<', '\n')

                # If any renders fail, show list when done

                if self.failed_render_list != []:

                    failed_renders = ''

                    for fail in self.failed_render_list:
                        failed_renders += '<dd>' + fail

                    message_box('Failed Renders:<br>%s' % failed_renders)

                self.render_done_btn.setEnabled(True)

                # If Exit/Save button is pressed, exit Flame when render is done

                try:
                    if self.exit_btn.isChecked():
                        print ('\n>>> Exiting Flame <<<\n')
                        self.render_window.close()
                        flame.exit()
                except:
                    # Render was submitted from right click menu. Do nothing.
                    pass

        # Open render progress window

        render_progress_window()

        # Render batch groups

        if self.close_after_render:

            # Close batch groups after rendering

            for batch_num in self.selected_batch_groups:
                self.batch_to_render = self.desk.batch_groups[batch_num]
                self.batch_to_render.open()

                try:
                    for batch in self.desktop_batch_group_object_list:
                        if batch != self.batch_to_render:
                            batch.close()
                except:
                    pass

                render_batch_group()

        else:

            for batch_num in self.selected_batch_groups:
                self.batch_to_render = self.desk.batch_groups[batch_num]
                render_batch_group()

    def burn_selected_batch_groups(self):
        # self.burn_submitted = True

        for batch in self.selection:
            self.submit_burn_render(batch)

    def submit_burn_render(self, batch_to_render):

        # Submit renders to Burn

        print ('submitting to burn...\n')

        try:
            batch_to_render.render(render_option='Burn')
        except:
            print ('\n>>> Burn Submit Failed <<<\n')

#-------------------------------------#

def message_box(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setText(message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131}'
                          'QLabel {color: #9a9a9a; font: 14px "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

def render_selected(selection):

    print ('\n', '>' * 20, 'multi batch render %s - render selected' % VERSION, '<' * 20, '\n')

    script = MultiBatchRender(selection)
    script.render_selected_batch_groups()
    return script

def burn_selected(selection):

    print ('\n', '>' * 20, 'multi batch render %s - burn selected' % VERSION, '<' * 20, '\n')

    script = MultiBatchRender(selection)
    script.burn_selected_batch_groups()

def main_render_window(selection):

    print ('\n', '>' * 20, ' multi batch render %s ' % VERSION, '<' * 20, '\n')

    script = MultiBatchRender(selection)
    script.main_window()

#-------------------------------------#

def scope_batch(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyBatch):
            item_parent = item.parent
            if isinstance(item_parent, flame.PyDesktop):
                return True
    return False

#-------------------------------------#

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Render...',
            'actions': [
                {
                    'name': 'Render Selected Batchgroups',
                    'isVisible': scope_batch,
                    'execute': render_selected,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Render...',
            'actions': [
                {
                    'name': 'Multi-Batch Render',
                    'execute': main_render_window,
                    'minimumVersion': '2020'
                }
            ]
        }
    ]
