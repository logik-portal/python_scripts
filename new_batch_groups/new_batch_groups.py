'''
Script Name: Create New Batch Group
Script Version: 1.5
Flame Version: 2020.1
Written by: Andy Milkis
Creation Date: 01.17.20
Update Date: 01.17.20

Custom Action Type: Batch

Description:

    Creates a new Batch Group with four Schematic Reels: Src, Ref, Notes & Precomps
    To change the names and number of Schematic reels, just edit what is in line 39 "schem_reels"
    To change the name of the batch group that is created change the name in quotes in line 44

To install:

    Copy script into /opt/Autodesk/shared/python/new_batch_groups
'''

def get_media_panel_custom_ui_actions():

    def scope_desktop(selection):
        import flame
        for item in selection:
            if isinstance(item, (flame.PyDesktop)):
                return True
        return False

    def create_new_batch_group(selection):
        import flame

        # Define the Project, Workspace and Desktop objects to simplify the script later on.
        desk = flame.project.current_project.current_workspace.desktop

        # Define arrays of reels to be used in the creation of a Batch Group by default.
        schem_reels = ["Src", "Ref", "Notes", "Precomps"]
        shelf_reels = ["Renders"]

        # Create a Batch Group and we use the arrays above to create the desired reels.
        desk.create_batch_group("New_Batch", reels = schem_reels, shelf_reels = shelf_reels)

    return [
        {
            "name": "CUSTOM: Desktop",
            "actions": [
                {
                    "name": "Create New Batch Group",
                    "isVisible": scope_desktop,
                    "execute": create_new_batch_group
                }
            ]
        }
    ]
