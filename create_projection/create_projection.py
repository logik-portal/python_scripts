'''
Script Name: Create Projection
Script Version: 2.0
Flame Version: 2020.2
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 07.09.19
Update Date: 05.22.21

Custom Action Type: Flame Main Menu

Description:

    Create projector or diffuse projections in Action from selected action layer

    Scene must have another camera added other than just the default camera

    Right-click on Action surface or geo  -> Create Projection... -> Projector Projection
    Right-click on Action surface or geo  -> Create Projection... -> Projector Light-Linked Projection
    Right-click on Action surface or geo  -> Create Projection... -> Diffuse Projection

To install:

    Copy script into /opt/Autodesk/shared/python/create_projection

Updates:

v2.0 05.22.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.6 05.16.21

    Error when creating projection while not having action node selected fixed

v1.5 05.10.20

    Fixed problem with diffuse not switching to new frame camera in Flame 2020.2 and up.

v1.4 10.21.19

    Changed menu to Create Projection...

v1.3 09.15.19

    Code Cleanup
'''

from __future__ import print_function

VERSION = 'v2.0'

def find_line(action_filename, item):

    with open(action_filename, 'r') as action_file:
        for num, line in enumerate(action_file, 1):
            if item in line:
                item_line = num
                return item_line

def find_next_line(action_filename, item, item_line_num):

    with open(action_filename, 'r') as action_file:
        for num, line in enumerate(action_file, 1):
            if num > item_line_num:
                if item in line:
                    item_line = num
                    return item_line

def get_line_value(action_filename, line_number):

    with open(action_filename, 'r') as action_file:
        for num, line in enumerate(action_file, 1):
            if num == line_number:
                item_value = line.rsplit(' ', 1)[1]
                return item_value

#--------------------------------------------#

def get_result_camera():
    import flame

    def find_parent(child_num):

        action_file = open(action_filename)
        lines = action_file.readlines()
        name_line = lines[child_num]
        action_file.close()

        if 'Name' in name_line:
            camera_parent_name = name_line.rsplit(' ', 1)[1][:-1]

            if camera_parent_name == 'scene':
                camera_parent_name = None

            return camera_parent_name

        child_num = child_num - 1
        return find_parent(child_num)

    # Save action to check result camera - result camera should not be default camera

    save_action_path, action_filename, action_node, action_node_name, temp_folder = save_action_node()

    # Find result camera line

    item_line = find_line(action_filename, 'ResultCamChannel')

    result_cam_line = item_line + 3
    # print ('result_cam_line:', result_cam_line)

    # Get result camera value

    item_value = get_line_value(action_filename, result_cam_line)

    result_camera_num = int(item_value) + 1
    # print ('result_camera_num:', result_camera_num)

    # Get list of all camera names in action node

    action_camera_list = ['null camera']
    # print ('action_camera_list:', action_camera_list)

    for item in action_node.nodes:
        if 'Camera' in item.type:
            # print ('Camera Names:', item.name)
            action_camera_list.append(item)
    # print ('action_camera_list:', action_camera_list)

    if len(action_camera_list) == 2:
        result_camera_num = 1

    # Get action result camera

    result_cam = action_camera_list[result_camera_num]
    result_cam_name = str(result_cam.name)[1:-1]
    # print ('result_cam_name:', result_cam_name)

    if result_cam_name != 'DefaultCam':
        result_camera_num = result_camera_num# + 1

        result_cam = action_camera_list[result_camera_num]
        result_cam_name = str(result_cam.name)[1:-1]
        # print ('result_cam_name:', result_cam_name)

    # Get result camera node number for action file to search for node camera is parented to

    item_line = find_line(action_filename, result_cam_name)
    result_cam_number_line = item_line + 1
    # print ('result_cam_number_line:', result_cam_number_line)

    # Get name of node camera is parented to if it has a parent

    item_value = get_line_value(action_filename, result_cam_number_line)
    result_cam_number = item_value
    # print ('result_cam_number:', result_cam_number)

    result_cam_child_num = 'Child ' + result_cam_number
    # print ('result_cam_child_num:', result_cam_child_num)

    item_line = find_line(action_filename, result_cam_child_num)
    child_num = item_line
    # print ('child_num:', child_num)

    # Get name of node parented to camera node

    camera_parent_name = find_parent(child_num)

    # print ('\n >>> done getting result camera <<<\n')

    return camera_parent_name, action_filename, action_node

def create_cur_frame_camera(projection_type):
    import flame

    # Define new camera name

    new_camera_name = name_node('camera_fr')

    # Create list for cameras in Action node

    action_camera_list = ['null camera']

    # Get list of all 3d camera names in action node

    action_node, action_node_name = get_action_node()

    # for item in action_node_values.nodes:

    for item in action_node.nodes:
        if 'Camera' in item.type:
            action_camera_list.append(item.name)

    # print ('action_camera_list:', action_camera_list)

    # Create camera based on projection type
    # Diffuse projection will not create duplicate camera
    # Camera projection will create duplicate camera

    if projection_type == 'diffuse':

        # If 3d camera doesn't exist, create it, name it, get index

        if new_camera_name.endswith('_1'):
            new_camera_name = new_camera_name[:-2]

        if new_camera_name not in action_camera_list:

            camera_exists = False

            new_action_camera_list = ['null camera']

            # Create new camera at current frame

            flame.execute_shortcut('Result View')
            flame.execute_shortcut('Action Create Camera at Camera Position')
            flame.execute_shortcut('Toggle Node Schematic View')

            # Get list of all 3d camera names in action node

            action_node_values = flame.batch.current_node.get_value()

            for item in action_node_values.nodes:
                if 'Camera' in item.type:
                    new_action_camera_list.append(item)
            # print ('new_action_camera_list:', new_action_camera_list, '\n')

            # New camera is last camera in list. Get new camera and new camera index number

            new_camera = new_action_camera_list[-1]
            new_camera.name = new_camera_name
            new_camera_index = len(new_action_camera_list) - 1

            # print ('new_camera_name:', new_camera_name)
            # print ('new_camera:', new_camera)
            # print ('new_camera_index:', new_camera_index)
            # print ('camera_exists:', camera_exists)

        else:
            camera_exists = True

            # If camera already exists at frame get index of existing camera

            new_camera_index = action_camera_list.index(new_camera_name)
            # print ('existing cameraIndex:', new_camera_index)

            new_camera = None

    elif projection_type == 'projector':

        new_action_camera_list = ['null camera']

        # Create new camera at current frame

        flame.execute_shortcut('Result View')
        flame.execute_shortcut('Action Create Camera at Camera Position')
        flame.execute_shortcut('Toggle Node Schematic View')

        # Get list of all 3d camera names in action node

        action_node_values = flame.batch.current_node.get_value()

        for item in action_node_values.nodes:
            if 'Camera' in item.type:
                new_action_camera_list.append(item)
        # print ('new_action_camera_list:', new_action_camera_list)

        # New camera is last camera in list. Get new camera and new camera index number

        new_camera = new_action_camera_list[-1]
        new_camera.name = new_camera_name
        new_camera_index = len(new_action_camera_list) - 1
        # print ('new_camera:', new_camera)
        # print ('new_camera_index:', new_camera_index)

        # camera_exists not needed for projector projections
        # use None value just to send value through return

        camera_exists = None

    print ('\n>>> current frame camera created <<<\n')

    return new_camera, new_camera_name, camera_exists, new_camera_index

def get_action_node():
    import flame

    node_type = str(flame.batch.current_node.get_value().type)[1:-1]
    #print ('node_type:', node_type)

    if node_type == 'Action Media':
        node_value = flame.batch.current_node.get_value()
        node_sockets = node_value.sockets
        output_dict = node_sockets.get('output')
        action_node_name = output_dict.get('Result')[0]
        action_node = flame.batch.get_node(action_node_name)
    else:
        action_node_name = str(flame.batch.current_node.get_value().name)[1:-1]
        action_node = flame.batch.get_node(action_node_name)
    # print ('action_node:', action_node_name)

    return action_node, action_node_name

def save_action_node():
    import flame
    import os

    # Get current action node

    action_node, action_node_name = get_action_node()

    # Save Action node

    temp_folder = '/opt/Autodesk/shared/python/temp_action'
    save_action_path = os.path.join(temp_folder, action_node_name)
    # print ('save_action_path:', save_action_path)

    try:
        os.makedirs(temp_folder)
    except:
        # print ('temp action folder already exists')
        pass

    action_node.save_node_setup(save_action_path)

    # Set Action path and filename variable

    action_filename = save_action_path + '.action'
    # print ('action_filename:', action_filename, '\n')

    # print ('\n>>> action node saved <<<\n')

    return save_action_path, action_filename, action_node, action_node_name, temp_folder

def name_node(node_type, node_num=0):
    import flame

    action_node, action_node_name = get_action_node()

    # Get current frame number

    current_frame = flame.batch.current_frame

    existing_nodes = []

    # for node in flame.batch.current_node.get_value().nodes:

    for node in action_node.nodes:
        node_name = str(node.name)[1:-1]
        existing_nodes.append(node_name)

    node_name = node_type + str(current_frame) + '_' + str(node_num)

    if node_name.endswith('0'):
        node_name = node_name.rsplit('_', 1)[0]

    if node_name not in existing_nodes:
        new_node_name = node_name
        return new_node_name

    node_num = node_num + 1
    return name_node(node_type, node_num)

#--------------------------------------------#

def create_projector_projection(selection):
    import shutil

    print ('\n', '>' * 20, 'create projection %s - projector projection' % VERSION, '<' * 20, '\n')

    # Define projection type for camera creation - diffuse will not duplicate cameras, projection will

    projection_type = 'projector'

    # Get result camera

    camera_parent_name, action_filename, action_node = get_result_camera()

    # Create camera at current frame

    new_camera, new_camera_name, camera_exists, new_camera_index = create_cur_frame_camera(projection_type)

    #    new_camera, new_camera_name = create_cur_frame_camera(projection_type)

    # If result camera has parent, connect new camera to parent

    if camera_parent_name != None:
        parent_node = action_node.get_node(camera_parent_name)
        child_node = action_node.get_node(new_camera_name)
        action_node.connect_nodes(parent_node, child_node, link_type='Default')

    # Get name of surface/geo

    for item in selection:
        geo_name_line = 'Name ' + str(item.name)[1:-1]
        geo_type = item.type
        # print ('geo_name_line:', geo_name_line)

    # Get position of existing projector if one already exists

    node_projector_pos_x_line = 0
    node_projector_pos_y_line = 0

    with open(action_filename, 'r') as action_file:
        for num, line in enumerate(action_file, 1):
            if 'Node Projector' in line:
                node_projector_pos_x_line = num + 7
                node_projector_pos_y_line = num + 8

    if node_projector_pos_x_line != 0:
        # print ('node_projector_pos_x_line:', node_projector_pos_x_line)
        # print ('node_projector_pos_y_line:', node_projector_pos_y_line)

        item_value = get_line_value(action_filename, node_projector_pos_x_line)
        node_projector_pos_x = item_value
        # print ('node_projector_pos_x:', node_projector_pos_x)

        item_value = get_line_value(action_filename, node_projector_pos_y_line)
        node_projector_pos_y = item_value
        # print ('node_projector_pos_y:', node_projector_pos_y)

    # Create projector

    projector = action_node.create_node('Projector')

    # Name projector

    projector_name = name_node('projector_fr')
    projector.name = projector_name

    # Parent camera to projector

    action_node.connect_nodes(new_camera, projector)

    # Assign new_camera field of view to projector

    projector.fov = new_camera.fov
    # print ('projectorFOV:', projector.fov)

    # Zero out projector z position

    projector.position = (0, 0, 0)
    # print ('projectorPosition:', projector.position, '\n')

    # Save action node

    save_action_path, action_filename, action_node, action_node_name, temp_folder = save_action_node()

    # Get line numbers for geo, projector, and camera positions in schematic
    # Get x and y position of surface/geo in schematic

    if geo_type == 'Surface':
        item_line = find_line(action_filename, geo_name_line)

        item_line = find_next_line(action_filename, 'PosX', item_line)

        geo_pos_x_line_num = item_line
        geo_pos_y_line_num = geo_pos_x_line_num + 1

        # print ('geo_pos_x_line_num:', geo_pos_x_line_num)
        # print ('geo_pos_y_line_num:', geo_pos_y_line_num, '\n')

    elif geo_type == 'Geom':
        item_line = find_line(action_filename, geo_name_line)

        item_line = find_next_line(action_filename, 'PosX', item_line)

        geo_pos_x_line_num = item_line
        geo_pos_y_line_num = geo_pos_x_line_num + 1

        # print ('geo_pos_x_line_num:', geo_pos_x_line_num)
        # print ('geo_pos_y_line_num:', geo_pos_y_line_num, '\n')

    # Get x and y position of projector

    item_line = find_line(action_filename, projector_name)
    item_line = find_next_line(action_filename, 'PosX', item_line)

    projector_pos_x_line_num = item_line
    projector_pos_y_line_num = projector_pos_x_line_num + 1

    # print ('projector_pos_x_line_num:', projector_pos_x_line_num)
    # print ('projector_pos_y_line_num:', projector_pos_y_line_num, '\n')

    # Get x and y position of new_camera

    item_line = find_line(action_filename, new_camera_name)

    item_line = find_next_line(action_filename, 'PosX', item_line)

    new_camera_pos_x_line_num = item_line
    new_camera_pos_y_line_num = new_camera_pos_x_line_num + 1

    # print ('new_camera_pos_x_line_num:', new_camera_pos_x_line_num)
    # print ('new_camera_pos_y_line_num:', new_camera_pos_y_line_num, '\n')

    # Get position values for geo in schematic

    item_value = get_line_value(action_filename, geo_pos_x_line_num)
    geo_pos_x = item_value
    # print ('geo_pos_x:', geo_pos_x)

    item_value = get_line_value(action_filename, geo_pos_y_line_num)
    geo_pos_y = item_value
    # print ('geo_pos_y:', geo_pos_y)

    # Set new position values for projector and camera next to geo if no projector existing

    if node_projector_pos_x_line == 0:
        new_projector_pos_x = str(int(geo_pos_x) + 300)
        new_projector_pos_y = geo_pos_y
        # print ('new_projector_pos_x:', new_projector_pos_x)
        # print ('new_projector_pos_y:', new_projector_pos_y)

        new_camera_pos_x = new_projector_pos_x
        new_camera_pos_y = str(int(new_projector_pos_y) + 150)
        # print ('new_camera_pos_x:', new_camera_pos_x)
        # print ('new_camera_pos_y:', new_camera_pos_y, '\n')

    # If projector already exists, place new projector next to that one

    else:
        new_projector_pos_x = str(int(node_projector_pos_x) + 300)
        new_projector_pos_y = node_projector_pos_y
        # print ('new_projector_pos_x:', new_projector_pos_x)
        # print ('new_projector_pos_y:', new_projector_pos_y)

        new_camera_pos_x = new_projector_pos_x
        new_camera_pos_y = str(int(new_projector_pos_y) + 150)
        # print ('new_camera_pos_x:', new_camera_pos_x)
        # print ('new_camera_pos_y:', new_camera_pos_y, '\n')

    # Edit action file to change projector and new camera position

    edit_action = open(action_filename, 'r')
    contents = edit_action.readlines()
    edit_action.close()

    contents[projector_pos_x_line_num] = '        PosX %s\n' % new_projector_pos_x
    contents[projector_pos_y_line_num] = '        PosY %s\n' % new_projector_pos_y

    contents[new_camera_pos_x_line_num] = '        PosX %s\n' % new_camera_pos_x
    contents[new_camera_pos_y_line_num] = '        PosY %s\n' % new_camera_pos_y

    edit_action = open(action_filename, 'w')
    contents = ''.join(contents)
    edit_action.write(contents)
    edit_action.close()

    # Reload Action node

    action_node.load_node_setup(save_action_path)

    # Remove temp action save folder

    shutil.rmtree(temp_folder)

    print ('\n>>> created projector projection <<<\n')

    return action_node, projector_name

def create_light_linked_projector_projection(selection):

    for item in selection:
        select_geo_name = str(item.name)[1:-1]

    # Create projector projection

    action_node, projector_name = create_projector_projection(selection)

    # Light link projector to surface or geo

    parent_node = action_node.get_node(projector_name)
    child_node = action_node.get_node(select_geo_name)
    # print ('parent_node:', parent_node.name)
    # print ('child_node:', child_node.name)

    action_node.connect_nodes(parent_node, child_node, link_type='Light')

def create_diffuse_projection(selection):
    import shutil
    import flame

    print ('\n', '>' * 20, 'create projection %s - diffuse projection' % VERSION, '<' * 20, '\n')

    # Define projection type for camera creation - diffuse will not duplicate cameras, projection will

    projection_type = 'diffuse'

    # Get result camera

    camera_parent_name, action_filename, action_node = get_result_camera()
    # print ('camera parent name:', camera_parent_name)

    # Get position of last camera
    # Find last camera added line
    # Ignore stereo left and right cameras
    #-------------------------------------#

    with open(action_filename, 'r') as action_file:
        for num, line in enumerate(action_file, 1):
            if 'Node Camera' in line:
                next_line = next(action_file)
                if 'right' not in next_line:
                    if 'left' not in next_line:
                        node_camera_name_line = num
                        # print ('node_camera_name_line:', node_camera_name_line)

    # Find X and Y position lines for last camera

    item_line = find_next_line(action_filename, 'PosX', node_camera_name_line)

    node_camera_pos_x_line = item_line
    node_camera_pos_y_line = node_camera_pos_x_line + 1
    # print ('node_camera_pos_x_line:', node_camera_pos_x_line)
    # print ('node_camera_pos_y_line:', node_camera_pos_y_line)

    # Get last camera X value

    item_value = get_line_value(action_filename, node_camera_pos_x_line)
    node_camera_pos_x = str(int(item_value))

    # Get last camera Y value

    item_value = get_line_value(action_filename, node_camera_pos_y_line)
    node_camera_pos_y = item_value

    #-------------------------------------#

    # Create camera at current frame

    new_camera, new_camera_name, camera_exists, new_camera_index = create_cur_frame_camera(projection_type)
    # print ('new_camera_index:', new_camera_index)

    # If new frame camera doesn't already exist add 200 to x possition

    node_camera_pos_x = str(int(node_camera_pos_x) + 200)

    # If result camera has parent, connect new camera to parent

    if camera_parent_name != None:
        parent_node = action_node.get_node(camera_parent_name)
        child_node = action_node.get_node(new_camera_name)
        action_node.connect_nodes(parent_node, child_node, link_type='Default')

    # Create diffuse node

    diffuse_map = action_node.create_node('Diffuse Map')

    # Name diffuse map

    diffuse_map_name = name_node('diffuse_fr')
    diffuse_map.name = diffuse_map_name
    # print ('diffuse_map_name:', diffuse_map_name)

    # Save action node again with new diffuse map added

    save_action_path, action_filename, action_node, action_node_name, temp_folder = save_action_node()

    # Find diffuse map projection map and newly created camera line numbers

    item_line = find_line(action_filename, diffuse_map_name)

    diffuse_projection_camera_line_num = item_line + 21
    diffuse_projection_map_line_num = item_line + 23
    # print ('diffuse_projection_camera_line_num:', diffuse_projection_camera_line_num)
    # print ('diffuse_projection_map_line_num:', diffuse_projection_map_line_num)

    item_line = find_line(action_filename, new_camera_name)

    new_camera_line_num = item_line
    # print ('new_camera_line_num:', new_camera_line_num)

    # Find X and Y position lines for new frame camera

    item_line = find_next_line(action_filename, 'PosX', new_camera_line_num)

    camera_pos_x_line = item_line
    camera_pos_y_line = camera_pos_x_line + 1
    # print ('camera_pos_x_line:', camera_pos_x_line)
    # print ('camera_pos_y_line:', camera_pos_y_line)

    action_file.close()

    camera_index_fix = 2

    # Edit action file to change diffuse map type, projection camera, and position camera next to last exisitng camera

    edit_action = open(action_filename, 'r')
    contents = edit_action.readlines()
    edit_action.close()

    if not camera_exists:
        contents[camera_pos_x_line] = '        PosX %s\n' % node_camera_pos_x
        contents[camera_pos_y_line] = '        PosY %s\n' % node_camera_pos_y

    contents[diffuse_projection_camera_line_num] = '                        MapCamera %s\n' % str(int(new_camera_index) - camera_index_fix)
    contents[diffuse_projection_map_line_num] = '                        MapCoordType PROJECTION\n'

    edit_action = open(action_filename, 'w')
    contents = ''.join(contents)
    edit_action.write(contents)
    edit_action.close()

    # Reload Action node

    action_node.load_node_setup(save_action_path)

    # Remove temp action save folder

    shutil.rmtree(temp_folder)

    print ('\n>>> created diffuse projection <<<\n')

# Scopes
#-------------------------------------#

def scope_geo(selection):

    geo_types = ('Surface', 'Geom')

    for item in selection:
        if item.type in geo_types:
            return True
    return False

# Menus
#-------------------------------------#

def get_action_custom_ui_actions():

    return [
        {
            'name': 'Create Projection...',
            'actions': [
                {
                    'name': 'Projector Projection',
                    'isVisible': scope_geo,
                    'execute': create_projector_projection,
                    'minimumVersion': '2020.2'
                },
                {
                    'name': 'Projector Light-Linked Projection',
                    'isVisible': scope_geo,
                    'execute': create_light_linked_projector_projection,
                    'minimumVersion': '2020.2'
                },
                {
                    'name': 'Diffuse Projection',
                    'isVisible': scope_geo,
                    'execute': create_diffuse_projection,
                    'minimumVersion': '2020.2'
                }
            ]
        }
    ]
