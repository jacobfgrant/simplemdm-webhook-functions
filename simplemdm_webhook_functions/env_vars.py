"""
Environmental Variables

The environmental variables for the SimpleMDM webhook Lambda function.

To include additonal environmental variables, set them here using the
set_env_var() function or in an 'additional_env_vars.py' file.


Author:  Jacob F. Grant
Created: 10/19/18
Updated: 10/19/18
"""


from utils import set_env_var


# Import additional environmental variables
try:
    from additional_env_vars import *
except (ModuleNotFoundError, ImportError):
    pass


# Environmental Variables

LOG_BUCKET = set_env_var('LOG_BUCKET')
MUNKI_CATALOG = set_env_var('MUNKI_CATALOG', 'production')
MUNKI_MANIFEST_FOLDER = set_env_var('MUNKI_MANIFEST_FOLDER', 'manifests').strip('')
MUNKI_REPO_BUCKET = set_env_var('MUNKI_REPO_BUCKET')
MUNKI_REPO_BUCKET_REGION = set_env_var('MUNKI_REPO_BUCKET_REGION')
SIMPLEMDM_API_KEY = set_env_var('SIMPLEMDM_API_KEY')
SLACK_URL = set_env_var('SLACK_URL')



if __name__ == "__main__":
    pass
