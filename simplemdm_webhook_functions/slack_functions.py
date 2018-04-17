"""Slack Functions"""


import json
try:
    import requests
except ModuleNotFoundError:
    from botocore.vendored import requests

from utils import log_action


# Functions

def slack_webhook_message(serial_number, webhook_event, event_time):
    """Create a formatted Slack message."""
    slack_message = {
                     'text': 'SimpleMDM: '
                             'Device ' +
                             serial_number +
                             ' has ' +
                             webhook_event +
                             ' at ' +
                             event_time +
                             '.'
                     }
    return slack_message




def send_slack_message(slack_url, slack_message):
    """Send a message to Slack."""
    action_log = {
                  "action": "send_slack_message",
                  "info": {
                           "slack_url": slack_url,
                           "slack_message": slack_message
                           },
                  "result": None
                  }

    response = requests.post(
                             slack_url,
                             json.dumps(slack_message),
                             headers = {'Content-Type': 'application/json'}
                             )
    if response.status_code != 200:
        action_log['result'] = "Failed"
    else:
        action_log['result'] = "Success"
    
    log_action(function_log, action_log)
