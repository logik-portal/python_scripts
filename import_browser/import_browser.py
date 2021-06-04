'''
Script Name: Import Browser
Script Version: 2.0
Flame Version: 2020.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 06.16.19
Update Date: 05.22.21

Custom Action Type: Batch

Description:

    Opens import browser in batch through right click

    Right-click in batch -> Import... -> Import Browser

To install:

    Copy script into /opt/Autodesk/shared/python/import_browser

Updates:

v2.0 05.22.21

    Updated to be compatible with Flame 2022/Python 3.7

v1.1 10.24.19

    Menu renamed to Import...
'''

from __future__ import print_function

VERSION = 'v2.0'

def open_file_browser(selection):
    import flame

    print ('\n', '>' * 20, 'import browser %s' % VERSION, '<' * 20, '\n')

    flame.execute_shortcut('Import...')

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Import...',
            'actions': [
                {
                    'name': 'Import Browser',
                    'execute': open_file_browser,
                    'minimumVersion': '2020.1'
                }
            ]
        }
    ]
