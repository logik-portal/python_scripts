'''
Script Name: Render All Layers
Script Version: 1.0
Flame Version: 2021
Written by: John Geehreng
Creation Date: 01.23.21
Update Date: 01.23.21

Description: Use this if you want to render every layer in multiple sequences.
'''

folder_name = "Timelines"
action_name = "Render All Layers"


def render_layers(selection):
    import flame

    #set variables
    wks = flame.project.current_project.current_workspace
    dsk = flame.project.current_project.current_workspace.desktop

    for item in selection:
        item.render('All')

def scope_clip(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': folder_name,
            'actions': [
                {
                    'name': action_name,
                    'isVisible': scope_clip,
                    'execute': render_layers,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
