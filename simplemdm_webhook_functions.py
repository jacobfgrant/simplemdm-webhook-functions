"""SimpleMDM Webhook Functions"""


import os
import json
import plistlib
try:
    import requests
except ModuleNotFoundError:
    from botocore.vendored import requests
import boto3
from botocore.exceptions import ClientError



# Set environmental variables

def set_env_var(name, default):
    """Set an environmental variable or use given default value"""
    try:
        var = os.environ[name]
    except KeyError as e:
        print("Warning: Environmental variable " + str(e) + " not defined.")
        print("\t Using default value: " + str(default))
        var = default
    return var


API_KEY = set_env_var('API_KEY', None)
MANIFEST_FOLDER = set_env_var('MANIFEST_FOLDER', 'manifests').strip('/')
MUNKI_REPO_BUCKET = set_env_var('MUNKI_REPO_BUCKET', None)



# Create client objects

s3 = boto3.client('s3', region_name='us-east-1')



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


def generate_manifest_file(name, catalogs=['production'], included_manifests=['site_default']):
    """Generate a manifest file"""
    manifest_info = {
                     "catalogs": catalogs,
                     "display_name":"",
                     "included_manifests": included_manifests,
                     "managed_installs":[],
                     "managed_uninstalls":[],
                     "managed_updates":[],
                     "optional_installs":[],
                     "user":""
                     }
    manifest_file = os.path.join('/tmp/', name)
    plistlib.writePlist(manifest_info, manifest_file)
    return manifest_file, manifest_info


def create_manifest(name, folder, bucket, function_log):
    """Create a munki manifest file and upload it to folder in S3"""
    action_log = {
                  "action": "create_manifest",
                  "info": {
                           "name": os.path.join(folder, name),
                           "bucket": bucket,
                           "content": None
                           },
                  "result": None
                  }

    # check if manifest exists
    try:
        s3.head_object(Bucket=bucket, Key=os.path.join(folder, name))
        action_log['result'] = 'AlreadyExists'
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            manifest_file, action_log['info']['content'] = generate_manifest_file(name)
            try:
                s3.upload_file(manifest_file, bucket, os.path.join(folder, name))
                action_log['result'] = 'Success'
            except ClientError as e:
                action_log['result'] = e
        else:
            action_log['result'] = e

    log_action(function_log, action_log)


def delete_manifest(name, folder, bucket, function_log):
    """Delete a munki manifest file from S3"""
    action_log = {
                  "action": "delete_manifest",
                  "info": {
                           "name": os.path.join(folder, name),
                           "bucket": bucket
                           },
                  "result": None
                  }

    try:
        s3.delete_object(Bucket=bucket, Key=os.path.join(folder, name))
        action_log['result'] = "Success"
    except ClientError as e:
        action_log['result'] = e.response['Error']['Code']
    
    log_action(function_log, action_log)


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


def log_action(function_log, action_log):
    """Updates a function log with an action's item log"""
    function_log["eventLog"].append(action_log)


def generate_api_response(response_code, function_log):
    """Return formatted API response"""
    response = {
                "isBase64Encoded": False,
                "statusCode": response_code,
                "headers": { "Content-Type": "application/json"},
                "body": json.dumps(function_log)
                }
    return response



# Webhook Event Functions

def device_enrolled(data, function_log):
    """Device enrolled in SimpleMDM"""
    if MUNKI_REPO_BUCKET:
        create_manifest(data['device']['serial_number'],
                        MANIFEST_FOLDER,
                        MUNKI_REPO_BUCKET,
                        function_log
                        )

    if API_KEY:
        device_info = get_device_info(data['device']['id'],
                                      API_KEY,
                                      function_log
                                      )
        device_type = device_info['attributes']['model']
        assign_group = None
        if 'MacBook' in device_type:
            assign_group = 'Laptops'
        elif 'iMac' in device_type:
            assign_group = 'Desktops'
        elif 'iPhone' in device_type:
            assign_group = 'iPhones'
        if assign_group:
            assign_device_group(data['device']['id'],
                                assign_group,
                                API_KEY,
                                function_log
                                )


def device_unenrolled(data, function_log):
    """Device unenrolled from SimpleMDM"""



## HANDLER FUNCTION ##

def lambda_handler(event, context):
    """Handler function for AWS Lambda"""
    # create log
    function_log = {
                    "requestInfo": {
                                    "type": None,
                                    "at": None,
                                    "data": None
                                    },
                    "eventLog": []
                    }
    
    # check if body included in request
    try:
        event_body = json.loads(event['body'])
    except KeyError as e:
        log_action(function_log, ('ERROR: ' + str(e) + ' not included in request'))
        return generate_api_response(400, function_log)
    
    # check if request body is incomplete
    incomplete_request = False
    for key in ['type', 'at', 'data']:
        try:
            function_log['requestInfo'][key] = event_body[key]
        except KeyError as e:
            log_action(function_log, ('ERROR: ' + str(e) + ' not included in request'))
            incomplete_request = True
    if incomplete_request:
        return generate_api_response(400, function_log)
    
    # "device.enrolled" webhook
    if function_log['requestInfo']['type'] == 'device.enrolled':
        device_enrolled(event_body['data'], function_log)

    # "device.unenrolled" webhook
    if function_log['requestInfo']['type'] == 'device.unenrolled':
        device_unenrolled(event_body['data'], function_log)

    return generate_api_response(200, function_log)



## MAIN FUNCTION ##

def main():
    pass


if __name__ == "__main__":
    main()
