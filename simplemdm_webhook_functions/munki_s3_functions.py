"""Munki S3 Functions"""


import os
import plistlib
import boto3
from botocore.exceptions import ClientError

from utils import *


# Environmental Variables

MANIFEST_FOLDER = set_env_var('MANIFEST_FOLDER', 'manifests').strip('/')
MUNKI_REPO_BUCKET = set_env_var('MUNKI_REPO_BUCKET', None)


# Create client objects

s3 = boto3.client('s3', region_name='us-east-1')


# Functions

def generate_manifest_file(name, catalogs=['production'], included_manifests=['site_default']):
    """Generate a munki manifest file."""
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
    """Create a munki manifest file and upload it to a folder in S3."""
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
    """Delete a munki manifest file from S3."""
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
