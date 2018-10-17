"""SimpleMDM Webhook Lambda Function

AWS Lambda function for responding to SimpleMDM webhook events.
The following events are currently available:

- device.enrolled
- device.unenrolled

Addition information can be found at:
https://simplemdm.com/docs/api/#webhooks


The actions to be performed in response to the above events are included
in the corresponding event function below.

To further extend the response to a webhook event, import the desired
functions include them in the event. Ideally, any new functions should
use the FunctionLog and ActionLog objects from utils.py to log their
actions and new environmental variables should be set with the set_env_var()
function.

Author:  Jacob F. Grant
Created: 03/30/18
Updated: 10/16/18
"""


import os
import json

from utils import *
from munki_s3_functions import *
from simplemdm_functions import *
from slack_functions import *


# Environmental Variables

LOG_BUCKET = set_env_var('LOG_BUCKET')
MUNKI_REPO_BUCKET = set_env_var('MUNKI_REPO_BUCKET')
MUNKI_REPO_BUCKET_REGION = set_env_var('MUNKI_REPO_BUCKET_REGION')
SIMPLEMDM_API_KEY = set_env_var('SIMPLEMDM_API_KEY')
SLACK_URL = set_env_var('SLACK_URL')


# Webhook Event Functions

def device_enrolled(data, function_log):
    """Device enrolled in SimpleMDM."""
    if MUNKI_REPO_BUCKET and MUNKI_REPO_BUCKET_REGION:
        create_manifest(
            data['device']['serial_number'],
            MANIFEST_FOLDER,
            MUNKI_REPO_BUCKET,
            MUNKI_REPO_BUCKET_REGION,
            function_log
        )

    if SIMPLEMDM_API_KEY:
        device_info = get_device_info(
            data['device']['id'],
            SIMPLEMDM_API_KEY,
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
            assign_device_group(
                data['device']['id'],
                assign_group,
                SIMPLEMDM_API_KEY,
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


## HANDLER FUNCTION ##

def lambda_handler(event, context):
    """Handler function for AWS Lambda."""
    # create log
    function_log = FunctionLog()
    
    # check if body included in request
    try:
        action_log = ActionLog("check_event_data")
        function_log.type = event['type']
        function_log.at = event['at']
        function_log.data = event['data']
    except KeyError as e:
        action_log.set_status("failure", str(e) + " not included in request")
        function_log.log_action(action_log.output())
        function_log.log_to_s3(LOG_BUCKET)
        return function_log.generate_api_response(400)

    action_log.set_status("success")
    function_log.log_action(action_log.output())
    
    # "device.enrolled" webhook
    if event['type'] == 'device.enrolled':
        device_enrolled(event['data'], function_log)

    # "device.unenrolled" webhook
    if event['type'] == 'device.unenrolled':
        device_unenrolled(event['data'], function_log)

    function_log.log_to_s3(LOG_BUCKET)
    return function_log.generate_api_response(200)



## MAIN FUNCTION ##

def main():
    pass


if __name__ == "__main__":
    main()
