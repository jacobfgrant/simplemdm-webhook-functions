"""SimpleMDM Functions"""


import json
try:
    import requests
except ModuleNotFoundError:
    from botocore.vendored import requests

from utils import log_action


# Functions

def get_device_info(device_id, api_key, function_log):
    """Get device info from SimpleMDM API"""
    action_log = {
                  "action": "get_device_info",
                  "info": {
                           "device_id": device_id
                           },
                  "result": None
                  }

    device_info = requests.get(('https://a.simplemdm.com/api/v1/devices/' + device_id), auth = (api_key, ''))
    if device_info.status_code != 200:
        action_log['result'] = {
                                "result": "failed_api_call",
                                "action": "get_device_info",
                                'code': device_info.status_code
                                }
    else:
        action_log['result'] = "Success"
    
    log_action(function_log, action_log)
    return device_info.json()['data']


def assign_device_group(device_id, group_name, api_key, function_log):
    """Assigns a device to a SimpleMDM device group"""
    action_log = {
                  "action": "assign_device_group",
                  "info": {
                           "device_id": device_id,
                           "assign_group": group_name
                           },
                  "result": None
                  }

    api_call = requests.get('https://a.simplemdm.com/api/v1/device_groups', auth = (api_key, ''))
    if api_call.status_code == 200:
        data = api_call.json()['data']

        for group in data:
            if group['attributes']['name'] == group_name:
                group_id = group['id']
                api_url = ('https://a.simplemdm.com/api/v1/device_groups/' + group_id + '/devices/' + device_id)
                assign_device_call = requests.post(api_url, auth = (api_key, ''))
                
                if assign_device_call.status_code == 204:
                    action_log['result'] = "Success"
                    log_action(function_log, action_log)
                else:
                    action_log['result'] = {
                                            "result": "failed_api_call",
                                            "action": "assign_device",
                                            'code': api_call.status_code
                                            }
        action_log['result'] = "GroupNotFound"
    else:
        action_log['result'] = {
                                "result": "failed_api_call",
                                "action": "get_device_groups",
                                'code': api_call.status_code
                                }

    log_action(function_log, action_log)
