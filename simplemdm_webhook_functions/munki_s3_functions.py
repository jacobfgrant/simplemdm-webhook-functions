"""Munki S3 Functions"""


import os
import plistlib
import boto3
from botocore.exceptions import ClientError

from utils import *


# Classes

class MunkiManifest(object):

    def __init__(self, name):
        self.name = name
        self.catalogs = []
        self.display_name = name
        self.included_manifests = []
        self.user = ""


    def set_display_name(self, display_name):
        self.display_name = str(display_name)


    def add_catalog(self, catalog):
        self.catalogs.append(catalog)


    def add_included_manifest(self, included_manifest):
        self.included_manifest.append(included_manifest)


    def output(self):
        return {
            "catalogs": self.catalogs,
            "display_name": self.display_name,
            "included_manifests": self.included_manifests,
            "managed_installs":[],
            "managed_uninstalls":[],
            "managed_updates":[],
            "optional_installs":[],
            "user": ""
        }


    def write_file(self):
        manifest_file = os.path.join('/tmp/', self.name)
        plistlib.writePlist(self.output(), manifest_file)
        return manifest_file



# Functions


def upload_manifest(manifest, folder, bucket, region, function_log):
    """Upload a munki manifest file to a folder in S3."""
    action_log = ActionLog(
        "upload_manifest",
        {
            "name": os.path.join(folder, manifest.name),
            "bucket": bucket,
            "content": None
        }
    )

    munki_s3 = boto3.client('s3', region_name=region)

    # check if manifest exists
    try:
        munki_s3.head_object(Bucket=bucket, Key=os.path.join(folder, manifest.name))
        action_log.set_status("failure", "AlreadyExists")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            manifest_file = manifest.write_file()

            try:
                munki_s3.upload_file(manifest_file, bucket, os.path.join(folder, manifest.name))
                action_log.set_status("success", {"manifest": manifest.output()})
            except ClientError as e:
                action_log.set_status(
                    "failure",
                    {
                        "error": str(e),
                        "manifest": manifest.output()
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
