"""Slack Functions"""


import json
import re
from datetime import datetime
try:
    import requests
except ModuleNotFoundError:
    from botocore.vendored import requests

from utils import *


# Functions

def slack_webhook_message(serial_number, webhook_event, event_time):
    """Create a formatted Slack message."""
    event_time = re.sub(r'([\+|\-]{1}[0-9]{2})\:([0-9]{2})', r'\g<1>\g<2>', event_time)
    event_time = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S.%f%z')
    event_time = event_time.strftime('%A, %B %d, %Y at %H:%M %Z')
    slack_message = {
        'text': (
            "SimpleMDM: Device `" +
            serial_number +
            "` " +
            webhook_event +
            " on " +
            event_time +
            "."
        )
    }
    return slack_message


def send_slack_message(slack_url, slack_message, function_log):
    """Send a message to Slack."""
    action_log = ActionLog(
        "send_slack_message",
        {
            "slack_url": slack_url,
            "slack_message": slack_message
        }
    )

    try:
        response = requests.post(
            slack_url,
            json.dumps(slack_message),
            headers = {'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            action_log.set_status("failure", {"code": response.status_code})
        else:
            action_log.set_status("success")

    except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError) as e:
        action_log.set_status("failure", {"error": str(e)})

    function_log.log_action(action_log.output())



if __name__ == "__main__":
    pass
