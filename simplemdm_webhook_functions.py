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


def create_manifest(name, folder, bucket):
    """Create a munki manifest file and upload it to folder in S3"""
    # check if manifest exists
    try:
        s3.head_object(Bucket=bucket, Key=os.path.join(folder, name))
        return True
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            return None
    s3.upload_file(generate_manifest_file(name), bucket, os.path.join(folder, name))


def delete_manifest(name, folder, bucket):
    """Delete a munki manifest file from S3"""
    s3.delete_object(Bucket=bucket, Key=os.path.join(folder, name))


def assign_device_group(device_id, group_name, API_KEY):
    """Assigns a device to a SimpleMDM device group"""
    # assign device to group using logic below
    api_call = requests.get('https://a.simplemdm.com/api/v1/device_groups', auth = (API_KEY, ''))
    if api_call.statuscode == 200:
        data = api_call.json()['data']
        for group in data:
            if group['attributes']['name'] == group_name:
                group_id = group['id']
                api_url = ('https://a.simplemdm.com/api/v1/device_groups/' + group_id + '/devices/' + device_id)
                assign_device_call = requests.post(api_url, auth = (API_KEY, ''))
                if assign_device_call.status_code == 204:
                    print("Success")



# Webhook Event Functions

def device_enrolled(data):
    """Device enrolled from SimpleMDM"""
    create_manifest(data['device']['serial_number'],
                    MANIFEST_FOLDER,
                    MUNKI_REPO_BUCKET_NAME
                    )


def device_unenrolled(data):
    """Device unenrolled from SimpleMDM"""
    return



## HANDLER FUNCTION ##

def lambda_handler(event, context):
    """Handler function for AWS Lambda"""
    event_body = json.loads(event['body'])

    # "device.enrolled" webhook
    if event_body['type'] == 'device.enrolled':
        device_enrolled(event_body['data'])

    # "device.unenrolled" webhook
    if event_body['type'] == 'device.unenrolled':
        device_unenrolled(event_body['data'])

    return True




## MAIN FUNCTION ##

def main():
    pass
    



if __name__ == "__main__":
    main()
