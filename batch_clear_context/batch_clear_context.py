'''
Script Name: Batch Clear Context
Script Version: 1.0
Flame Version: 2020
Written by: John Fegan
Creation Date: 09.29.19
Update Date: 09.29.19

Custom Action Type: Batch

Description:

    Clears All Context Views

To install:

    Copy script into /opt/Autodesk/shared/python/batch_clear_context
'''

def clear_context_views(selection):
    import flame

    flame.batch.clear_context(1)
    flame.batch.clear_context(2)
    flame.batch.clear_context(3)
    flame.batch.clear_context(4)
    flame.batch.clear_context(5)
    flame.batch.clear_context(6)
    flame.batch.clear_context(7)
    flame.batch.clear_context(8)
    flame.batch.clear_context(9)
    flame.batch.clear_context(10)

def get_batch_custom_ui_actions():

    return [
        {
            "name": "Batch",
            "actions": [
                {
                    "name": "Clear All Context Views",
                    "execute": clear_context_views,
                    "minimumVersion": "2020"
                }
            ]
        }
    ]
