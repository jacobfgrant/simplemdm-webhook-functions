"""
Default Webhook Functions

The (default) functions for responding to specific SimpleMDM webhook
events.

To override any of these functions, add your version to a
'webhook_functions.py' file in the same directory. Be sure to import the
necessary modules and environmental files.


Author:  Jacob F. Grant
Created: 10/19/18
Updated: 10/16/18
"""


from utils import *

from munki_s3_functions import *
from simplemdm_functions import *
from slack_functions import *

from env_vars import *


# Webhook Event Functions

def device_enrolled(data, function_log):
    """Device enrolled in SimpleMDM."""
    manifest = MunkiManifest(data['device']['serial_number'])
    manifest.add_catalog(MUNKI_CATALOG)

    if SIMPLEMDM_API_KEY:
        device_info = get_device_info(
            data['device']['id'],
            SIMPLEMDM_API_KEY,
            function_log
        )
        if device_info:
            manifest.set_display_name(device_info['attributes']['name'])
            device_type = device_info['attributes']['model_name']
            assign_group = None
            if 'MacBook' in device_type:
                assign_group = 'Laptops'
                included_manifest = 'Laptops'
            elif 'Mac' in device_type:
                assign_group = 'Desktops'
                included_manifest = 'Desktops'
            elif 'iPhone' in device_type:
                assign_group = 'iPhones'

            if assign_group:
                assign_device_group(
                    data['device']['id'],
                    assign_group,
                    SIMPLEMDM_API_KEY,
                    function_log
                )

    if MUNKI_REPO_BUCKET and MUNKI_REPO_BUCKET_REGION:
        try:
            manifest.add_included_manifest(included_manifest)
        except NameError:
            manifest.add_included_manifest('site_default')
            
            upload_manifest(
                manifest,
                MUNKI_MANIFEST_FOLDER,
                MUNKI_REPO_BUCKET,
                MUNKI_REPO_BUCKET_REGION,
                function_log
            )

    if SLACK_URL:
        send_slack_message(
            SLACK_URL,
            slack_webhook_message(
                data['device']['serial_number'],
                'enrolled',
                function_log.at
            ),
            function_log
        )


def device_unenrolled(data, function_log):
    """Device unenrolled from SimpleMDM."""
    if SLACK_URL:
        send_slack_message(
            SLACK_URL,
            slack_webhook_message(
                data['device']['serial_number'],
                'unenrolled',
                function_log.at
            ),
            function_log
        )



if __name__ == "__main__":
    pass
