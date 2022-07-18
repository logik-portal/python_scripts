'''
Script Name: Refresh Python Hooks
Script Version: 1.0
Flame Version: 2022
Written by: Michael Vaglienty
Creation Date: 05.12.22
Update Date: 05.24.22

Custom Action Type: Batch / Flame Main Menu

Description:

    Refresh python hooks and print message to Flame message window(2023.1 and later) and terminal.

    Message to Flame message window only shows up in Flame 2023.1 and later.

Menus:

    Flame Main Menu -> Refresh Python Hooks -> Refresh Python Hooks

    Right-click in batch -> Refresh Python Hooks -> Refresh Python Hooks

To install:

    Copy script into /opt/Autodesk/shared/python/refresh_python_hooks
'''

from pyflame_lib_refresh_python_hooks import pyflame_refresh_hooks

SCRIPT_NAME = 'Refresh Python Hooks'

def refresh_hooks(selection):

    pyflame_refresh_hooks(SCRIPT_NAME)

def get_main_menu_custom_ui_actions():
    return [
        {
            'name': 'Refresh Python Hooks',
            'actions': [
                {
                    'name': 'Refresh Python Hooks',
                    'execute': refresh_hooks,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():
    return [
        {
            'name': 'Refresh Python Hooks',
            'actions': [
                {
                    'name': 'Refresh Python Hooks',
                    'execute': refresh_hooks,
                    'minimumVersion': '2022'
                }
            ]
        }
    ]
