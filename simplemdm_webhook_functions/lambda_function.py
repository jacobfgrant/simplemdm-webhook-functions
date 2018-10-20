"""
SimpleMDM Webhook Lambda Function

AWS Lambda function for responding to SimpleMDM webhook events.
The following events are currently available:

- device.enrolled
- device.unenrolled

Addition information can be found at:
https://simplemdm.com/docs/api/#webhooks


The actions to be performed in response to the above events are included
in the corresponding event functions 'default_webhook_functions.py' module.

To modify or extend the response to a webhook event, add a modified
version of the webhook event function to a 'webhook_functions.py' file
and import any necessary modules--including customized ones--and
environmental variables.

Ideally, any new functions should use the FunctionLog and ActionLog
objects from utils.py to log their actions and new environmental
variables should be set in 'additional_env_vars.py' using the
set_env_var() function.


Author:  Jacob F. Grant
Created: 03/30/18
Updated: 10/19/18
"""


from utils import *

from env_vars import LOG_BUCKET


# Webhook Event Functions

# device_enrolled
try:
    from webhook_functions import device_enrolled
except (ModuleNotFoundError, ImportError):
    from default_webhook_functions import device_enrolled

# device_unenrolled
try:
    from webhook_functions import device_unenrolled
except (ModuleNotFoundError, ImportError):
    from default_webhook_functions import device_unenrolled


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
