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
use the log_action() function from utils.py to update the function log
and new environmental variables should be set with the set_env_var()
function.

Author:  Jacob F. Grant
Created: 03/30/18
Updated: 04/05/18
"""


import os
import json

from utils import *
from munki_s3_functions import *
from simplemdm_functions import *
from slack_functions import *


# Set environmental variables

# Munki S3 functions env vars
MANIFEST_FOLDER = set_env_var('MANIFEST_FOLDER', 'manifests').strip('/')
MUNKI_REPO_BUCKET = set_env_var('MUNKI_REPO_BUCKET', None)

# SimpleMDM functions env vars
API_KEY = set_env_var('API_KEY', None)

# Slack functions env vars
SLACK_URL = set_env_var('SLACK_URL', None)


# Webhook Event Functions

def device_enrolled(data, function_log):
    """Device enrolled in SimpleMDM."""
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

    if SLACK_URL:
        send_slack_message(SLACK_URL,
                           slack_webhook_message(data['device']['serial_number'],
                                                 'enrolled', 
                                                 function_log['requestInfo']['at']
                                                 )
                           )


def device_unenrolled(data, function_log):
    """Device unenrolled from SimpleMDM."""
    if SLACK_URL:
        send_slack_message(SLACK_URL,
                           slack_webhook_message(data['device']['serial_number'],
                                                 'unenrolled', 
                                                 function_log['requestInfo']['at']
                                                 )
                           )


## HANDLER FUNCTION ##

def lambda_handler(event, context):
    """Handler function for AWS Lambda."""
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
