"""General utilities and functions"""


import os
import json
import time
from datetime import datetime
import boto3
from botocore.exceptions import ClientError


# Functions

def set_env_var(name, default):
    """Set an environmental variable or use given default value."""
    try:
        var = os.environ[name]
    except KeyError as e:
        print("Warning: Environmental variable " + str(e) + " not defined.")
        print("\t Using default value: " + str(default))
        var = default
    return var



# Classes

class FunctionLog(object):

    def __init__(self):
        self.type = None
        self.at = None
        self.data = None
        self.event_log = []
        self.time = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            datetime.utcnow().utctimetuple()
        )


    def log_action(self, action):
        try:
            self.event_log.append(action.output())
        except AttributeError:
            self.event_log.append(action)


    def output(self):
        return {
            "run_time": self.time,
            "request_info": {
                "type": self.type,
                "at": self.at,
                "data": self.data  
            },
            "event_log": self.event_log
        }

    
    def generate_api_response(self, response_code):
        return {
            "isBase64Encoded": False,
            "statusCode": response_code,
            "headers": { "Content-Type": "application/json"},
            "body": json.dumps(self.output())   
        }

    
    def log_to_s3(self, bucket, bucket_region=None):
        #log_s3 = boto3.client('s3', region_name=bucket_region)
        log_s3 = boto3.client('s3')
        log_name = 'simplemdm-webhook-log-' + str(int(time.time())) + '.json'
        log_file = os.path.join(
            '/tmp/',
            log_name
        )
        with open(log_file, 'w') as file:
            json.dump(self.output(), file)
        try:
            log_s3.upload_file(log_file, bucket, log_name)
        except ClientError:
            pass


class ActionLog(object):

    def __init__(self, action, info={}):
        self.action = action
        self.info = info
        self.status = {
            "result": None,
            "info": {}
        }


    def set_status(self, result, info={}):
        self.status = {
            "result": result,
            "info": info
        }


    def output(self):
        return {
            "action": self.action,
            "info": self.info,
            "status": self.status
        }



if __name__ == "__main__":
    pass
