"""
SimpleMDM Functions

Functions for retrieving device data and assigning device groups in
SimpleMDM using the SimpleMDM API.


Author:  Jacob F. Grant
Created: 04/05/18
Updated: 10/19/18
"""


import json
try:
    import requests
except ModuleNotFoundError:
    from botocore.vendored import requests

from utils import *


# Functions

def get_device_info(device_id, api_key, function_log):
    """Get device info from SimpleMDM API."""
    action_log = ActionLog(
        "get_device_info",
        {"device_id": device_id}
    )

    api_call = requests.get(
        ('https://a.simplemdm.com/api/v1/devices/' + str(device_id)),
        auth = (api_key, '')
    )
    
    if api_call.status_code != 200:
        device_info = None
        action_log.set_status(
            "failure",
            {
                "action": "api_call",
                "type": "get_devices",
                "code": api_call.status_code
            }
        )
    else:
        device_info = json.loads(api_call.text)['data']
        action_log.set_status("success", {"device_info": device_info})
    
    function_log.log_action(action_log.output())
    return device_info


def assign_device_group(device_id, group_name, api_key, function_log):
    """Assign a device to a SimpleMDM device group."""
    action_log = ActionLog(
        "assign_device_group",
        {
            "device_id": device_id,
            "assign_group": group_name
        }
    )

    api_call = requests.get(
        'https://a.simplemdm.com/api/v1/device_groups',
        auth = (api_key, '')
    )

    if api_call.status_code == 200:
        data = json.loads(api_call.text)['data']

        for group in data:
            if group['attributes']['name'] == group_name:
                group_id = group['id']
                api_url = ('https://a.simplemdm.com/api/v1/device_groups/' + str(group_id) + '/devices/' + str(device_id))
                assign_device_call = requests.post(api_url, auth = (api_key, ''))
                
                if assign_device_call.status_code == 204:
                    action_log.set_status("success")
                else:
                    action_log.set_status(
                        "failure",
                        {
                            "action": "api_call_set_group",
                            "code": api_call.status_code
                        }
                    )
                function_log.log_action(action_log.output())
                return

        action_log.set_status(
            "failure",
            "GroupNotFound"
        )
    else:
        action_log.set_status(
            "failure",
            {
                "action": "get_device_groups_api_call",
                "code": api_call.status_code
            }
        )

    function_log.log_action(act_log.output())
    return



if __name__ == "__main__":
    pass
