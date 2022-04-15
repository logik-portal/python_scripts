'''
Script Name: Multi Batch Render
Script Version: 4.3
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 12.12.18
Update Date: 03.14.22

Custom Action Type: Batch / Media Panel Desktop

Description:

    Batch render multiple batch groups

Menus:

    Right-click in batch -> Render... -> Multi-Batch Render

    Right-click selected batch groups in desktop -> Render... Render Selected Batch Groups

To install:

    Copy script into /opt/Autodesk/shared/python/multi_batch_render

Updates:

    v4.3 03.14.22

        Moved UI widgets to external file - Added new render progress window

    v4.2 02.25.22

        Updated UI for Flame 2023

        Updated config to XML

        Burn button removed - no ability to test

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

import xml.etree.ElementTree as ET
import os, ast
from PySide2 import QtWidgets
from flame_widgets_multi_batch_render import FlameButton, FlameLabel, FlameListWidget, FlamePushButton, FlameMessageWindow, FlameProgressWindow, FlameWindow

VERSION = 'v4.3'

SCRIPT_PATH = '/opt/Autodesk/shared/python/multi_batch_render'

class MultiBatchRender(object):

    def __init__(self, selection):
        import flame

        # Paths

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_xml = os.path.join(self.config_path, 'config.xml')

        # Load config file

        self.config()

        # Init variables

        self.selection = selection
        self.desk = flame.project.current_project.current_workspace.desktop
        self.desktop_batch_group_object_list = self.desk.batch_groups
        self.desktop_batch_group_list = [str(b.name)[1:-1] for b in self.desktop_batch_group_object_list]
        self.batch_to_render = ''
        self.num_batch_groups = ''
        self.batch_groups_rendered = 0
        self.failed_render_list = []

    def config(self):

        def get_config_values():

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            # Get Settings from config XML

            for setting in root.iter('multi_batch_render_settings'):
                self.close_after_render = ast.literal_eval(setting.find('close_after_render').text)

            print ('--> config loaded \n')

        def create_config_file():

            if not os.path.isdir(self.config_path):
                try:
                    os.makedirs(self.config_path)
                except:
                    FlameMessageWindow('Error', 'error', f'Unable to create folder: {self.config_path}<br>Check folder permissions')
            if not os.path.isfile(self.config_xml):
                print ('--> config file does not exist, creating new config file \n')

                config = """
<settings>
    <multi_batch_render_settings>
        <close_after_render>False</close_after_render>
    </multi_batch_render_settings>
</settings>"""

                with open(self.config_xml, 'a') as config_file:
                    config_file.write(config)
                    config_file.close()

        if os.path.isfile(self.config_xml):
            get_config_values()
        else:
            create_config_file()
            if os.path.isfile(self.config_xml):
                get_config_values()

    def main_window(self):

        def list_batch_groups():
            import flame

            current_batch_group = str(flame.batch.name)[1:-1]
            # print ('current_batch_group: ', current_batch_group)

            # Get current batch number

            for i in [i for i, x in enumerate(self.desktop_batch_group_list) if x == current_batch_group]:
                current_batch_num = int(i)
            # print ('current_batch_num: ', current_batch_num)

            # Add names of batch groups to list

            self.batch_group_list.addItems(self.desktop_batch_group_list)
            self.batch_group_list.setCurrentItem(self.batch_group_list.item(current_batch_num))
            self.batch_group_list.setFocus()

        def selected_listbox_batch_groups():

            # List of all items in batchgroup list box

            all_batch_groups_list = [str(self.batch_group_list.item(index)) for index in range(self.batch_group_list.count())]
            # print ('all_batch_groups_list:', all_batch_groups_list)

            # List of selected batchgroups

            self.selected_batch_group_objects = [str(b) for b in self.batch_group_list.selectedItems()]

            # Get index number of selected batch groups

            self.selected_batch_groups = []
            for batch in self.selected_batch_group_objects:
                for i in [i for i, x in enumerate(all_batch_groups_list) if x == batch]:
                    self.selected_batch_groups.append(i)

        def render():

            # Save settings to config file

            xml_tree = ET.parse(self.config_xml)
            root = xml_tree.getroot()

            close_after_render = root.find('.//close_after_render')
            close_after_render.text = str(self.close_batch_pushbutton.isChecked())

            xml_tree.write(self.config_xml)

            print ('--> config saved \n')

            self.window.hide()

            selected_listbox_batch_groups()

            self.render_batch_groups()

        def cancel():

            self.window.close()

            try:
                self.setup_window.close()
            except:
                pass

        gridbox = QtWidgets.QGridLayout()
        self.window = FlameWindow(f'Multi Batch Render <small>{VERSION}', gridbox, 575, 400)

        # Labels

        self.batch_group_label = FlameLabel('Desktop Batch Groups', label_type='underline', label_width=120)

        # Listboxes

        self.batch_group_list = FlameListWidget()

        list_batch_groups()

        # Pushbuttons

        self.close_batch_pushbutton = FlamePushButton('Close Batch', self.close_after_render, button_width=120)
        self.close_batch_pushbutton.setToolTip('Close batch groups after each render is completed.')

        self.exit_flame = FlamePushButton('Exit Flame', False, button_width=120)
        self.exit_flame.setToolTip('Save workspace and exit Flame when render is complete')

        # Buttons

        self.render_btn = FlameButton('Render', render, button_width=120)
        self.cancel_btn = FlameButton('Cancel', cancel, button_width=120)

        # --------------------- #

        # Window Layout

        gridbox.setMargin(20)

        gridbox.addWidget(self.batch_group_label, 0, 0)
        gridbox.addWidget(self.batch_group_list, 1, 0, 7, 1)

        gridbox.addWidget(self.render_btn, 6, 1)
        gridbox.addWidget(self.close_batch_pushbutton, 1, 1)
        gridbox.addWidget(self.exit_flame, 2, 1)
        gridbox.addWidget(self.cancel_btn, 7, 1)

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

        def render_batch_group(batch_to_render):

            # Update progress bar

            self.batch_groups_rendered += 1

            # Check for Render or Write node before rendering
            # If none found, skip and print message

            if [node for node in batch_to_render.nodes if node.type in ('Render', 'Write File')] == []:
                self.failed_render_list.append(batch_to_render.name)
                print (f'--> {batch_to_render.name} has no render or write nodes. Skipping. \n')
                progress_text = f'Rendering Batch: {self.batch_groups_rendered} of {self.num_batch_groups}'

            else:
                progress_text = f'Rendering Batch: {self.batch_groups_rendered} of {self.num_batch_groups}'
                self.progress_window.set_text(progress_text)
                print (progress_text)

                # Replace render/write nodes - fix for flame render node bug

                duplicate_render_nodes()

                # Render in foreground - if render fails add to failed render list

                try:
                    batch_to_render.render()
                except RuntimeError:
                    self.failed_render_list.append(batch_to_render.name)

            # Update progress of renders to progress window

            self.progress_window.set_progress_value(self.batch_groups_rendered)

            if self.batch_groups_rendered == self.num_batch_groups:
                print ('\n--> rendering done ', '\n')

                # If any renders fail, show list when done

                if self.failed_render_list != []:
                    failed_renders = ''
                    for fail in self.failed_render_list:
                        failed_renders += '<dd>' + fail

                    # Send list of failed renders to progress window

                    self.progress_window.set_text(progress_text + f'<br><br>These batch groups failed to render:<br>{failed_renders}')

                self.progress_window.enable_done_button(True)

                # If Exit/Save button is pressed, exit Flame when render is done

                try:
                    if self.exit_flame.isChecked():
                        print ('\n--> Exiting Flame \n')
                        self.render_window.close()
                        flame.exit()
                except:
                    # Render was submitted from right click menu. Do nothing.
                    pass

        self.num_batch_groups = len(self.selected_batch_groups)

        # Open render progress window

        self.progress_window = FlameProgressWindow('Multi-Batch Rendering...', self.num_batch_groups)
        self.progress_window.enable_done_button(False)

        # Render batch groups

        if self.close_after_render:

            # Close batch groups after rendering

            for batch_num in self.selected_batch_groups:
                batch_to_render = self.desk.batch_groups[batch_num]
                batch_to_render.open()

                try:
                    for batch in self.desktop_batch_group_object_list:
                        if batch != batch_to_render:
                            batch.close()
                except:
                    pass

                render_batch_group(batch_to_render)
        else:
            for batch_num in self.selected_batch_groups:
                batch_to_render = self.desk.batch_groups[batch_num]
                render_batch_group(batch_to_render)

#-------------------------------------#

def render_selected(selection):

    print ('\n')
    print ('>' * 20, f'multi batch render {VERSION} - render selected', '<' * 20, '\n')

    script = MultiBatchRender(selection)
    script.render_selected_batch_groups()
    return script

def main_render_window(selection):

    print ('\n')
    print ('>' * 20, f'multi batch render {VERSION}', '<' * 20, '\n')

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
                    'minimumVersion': '2022'
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
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
