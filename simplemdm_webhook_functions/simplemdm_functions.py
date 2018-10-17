"""SimpleMDM Functions"""


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
        ('https://a.simplemdm.com/api/v1/devices/' + device_id),
        auth = (api_key, '')
    )
    
    if api_call.status_code != 200:
        action_log.set_status(
            "failure",
            {
                "action": "api_call",
                "type": "get_devices",
                "code": api_call.status_code
            }
        )
    else:
        action_log.set_result("success")
    
    function_log.log_action(action_log.output())
    return api_call.json()['data']


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
        data = api_call.json()['data']

        for group in data:
            if group['attributes']['name'] == group_name:
                group_id = group['id']
                api_url = ('https://a.simplemdm.com/api/v1/device_groups/' + group_id + '/devices/' + device_id)
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
