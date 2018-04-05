"""General utilities and functions"""


import os
import json


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


def log_action(function_log, action_log):
    """Update a function log with an action's item log."""
    function_log["eventLog"].append(action_log)


def generate_api_response(response_code, function_log):
    """Return a properly formatted API response."""
    response = {
                "isBase64Encoded": False,
                "statusCode": response_code,
                "headers": { "Content-Type": "application/json"},
                "body": json.dumps(function_log)
                }
    return response
