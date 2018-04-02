"""SimpleMDM Webhook Functions"""


import os
import json
import plistlib
import requests
import boto3
from botocore.exceptions import ClientError



# Set environmental variables

API_KEY = None
MUNKI_REPO_BUCKET_NAME = None
MUNKI_REPO_BUCKET_NAME = None
MUNKI_REPO_BUCKET_REGION = None
MANIFEST_FOLDER = 'manifests'

try:
    MUNKI_REPO_BUCKET = os.environ['MUNKI_REPO_BUCKET']
    MUNKI_REPO_BUCKET_NAME = os.environ['MUNKI_REPO_BUCKET_NAME']
    MUNKI_REPO_BUCKET_REGION = os.environ['MUNKI_REPO_BUCKET_REGION']
    MANIFEST_FOLDER = os.environ['MANIFEST_FOLDER']
except KeyError as e:
    print("Warning: Environmental variable(s) not defined")

MANIFEST_FOLDER = MANIFEST_FOLDER.strip('/')



# Create client objects

s3 = boto3.client('s3', region_name='us-east-1')



# Functions

def get_device_info(device_id, api_key):
    """Get device info from SimpleMDM API"""
    device_info = requests.get(('https://a.simplemdm.com/api/v1/devices/' + device_id), auth = (api_key, ''))
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
    return manifest_file


def create_manifest(name, folder, bucket, function_log):
    """Create a munki manifest file and upload it to folder in S3"""
    action_log = {
                "action": "create_manifest",
                "info": {
                         "name": os.path.join(folder, name),
                         "bucket": bucket
                         },
                "result": None
                }

    # check if manifest exists
    try:
        s3.head_object(Bucket=bucket, Key=os.path.join(folder, name))
        action_log['result'] = 'AlreadyExists'
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            s3.upload_file(generate_manifest_file(name), bucket, os.path.join(folder, name))
            action_log['result'] = 'Success'
        else:
            action_log['result'] = e

    return log_action(function_log, action_log)


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
    
    return log_action(function_log, action_log)


def assign_device_group(device_id, group_name, api_key, function_log):
    """Assigns a device to a SimpleMDM device group"""
    action_log = {
                "action": "assign_device_group",
                "info": {
                         "device_id": device_id,
                         "new_group_name": group_name
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
                    return log_action(function_log, action_log)
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

    return log_action(function_log, action_log)


def log_action(function_log, action_log):
    """Updates a function log with an action's item log"""
    return function_log["eventLog"].append(action_log)


def generate_api_response(response_code, function_log):
    """Return formatted API response"""
    response = {
                "isBase64Encoded": False,
                "statusCode": response_code,
                "headers": { "Content-Type": "application/json"},
                "body": function_log
                }
    return response



# Webhook Event Functions

def device_enrolled(data, function_log):
    """Device enrolled from SimpleMDM"""
    create_manifest(data['device']['serial_number'],
                    MANIFEST_FOLDER,
                    MUNKI_REPO_BUCKET_NAME,
                    function_log
                    )
    return function_log


def device_unenrolled(data, function_log):
    """Device unenrolled from SimpleMDM"""
    return function_log



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
        function_log = log_action(function_log, ('ERROR: ' + str(e) + ' not included in request'))
        return generate_api_response(400, function_log)
    
    # check if request body is incomplete
    incomplete_request = False
    for key in ['type', 'at', 'data']:
        try:
            function_log = {key: event_body[key]}
        except KeyError as e:
            function_log = log_action(function_log, ('ERROR: ' + str(e) + ' not included in request'))
            incomplete_request = True
    if incomplete_request:
        return generate_api_response(400, function_log)
    
    # "device.enrolled" webhook
    if event_body['type'] == 'device.enrolled':
        function_log = device_enrolled(event_body['data'], function_log)

    # "device.unenrolled" webhook
    if event_body['type'] == 'device.unenrolled':
        function_log = device_unenrolled(event_body['data'], function_log)

    return generate_api_response(200, function_log)



## MAIN FUNCTION ##

def main():
    pass


if __name__ == "__main__":
    main()
