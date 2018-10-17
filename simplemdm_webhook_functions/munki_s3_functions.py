"""Munki S3 Functions"""


import os
import plistlib
import boto3
from botocore.exceptions import ClientError

from utils import *


# Environmental Variables

MANIFEST_FOLDER = set_env_var('MANIFEST_FOLDER', 'manifests').strip('/')
MUNKI_REPO_BUCKET = set_env_var('MUNKI_REPO_BUCKET', None)
MUNKI_REPO_BUCKET_REGION = set_env_var('MUNKI_REPO_BUCKET_REGION', None)


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


def create_manifest(name, folder, bucket, region, function_log):
    """Create a munki manifest file and upload it to a folder in S3."""
    action_log = ActionLog(
        "create_manifest",
        {
            "name": os.path.join(folder, name),
            "bucket": bucket,
            "content": None
        }
    )

    munki_s3 = boto3.client('s3', region_name=region)

    # check if manifest exists
    try:
        munki_s3.head_object(Bucket=bucket, Key=os.path.join(folder, name))
        action_log.set_status("failure", "AlreadyExists")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            manifest_file, manfiest_info = generate_manifest_file(name)

            try:
                munki_s3.upload_file(manifest_file, bucket, os.path.join(folder, name))
                action_log.set_status("success", {"manifest": manfiest_info})
            except ClientError as e:
                action_log.set_status(
                    "failure",
                    {
                        "error": str(e),
                        "manifest": manfiest_info
                    }
                )

        else:
            action_log.set_status("failure", {"error": str(e)})

    function_log.log_action(action_log.output())


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
    action_log = ActionLog(
        "delete_manifest",
        {
            "name": os.path.join(folder, name),
            "bucket": bucket
        }
    )

    munki_s3 = boto3.client('s3', region_name=region)

    try:
        munki_s3.delete_object(Bucket=bucket, Key=os.path.join(folder, name))
        action_log.set_status("success")
    except ClientError as e:
        action_log.set_status("failure", {"error": str(e)})
    
    function_log.log_action(action_log.output())



if __name__ == "__main__":
    pass
