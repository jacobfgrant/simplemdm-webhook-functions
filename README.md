# SimpleMDM Webhook Functions

AWS Lambda function for responding to SimpleMDM webhook events.

[SimpleMDM](https://simplemdm.com/) allows for simple webhooks (HTTP POST requests) when certain events occur in a SimpleMDM account. These events currently include:

* device.enrolled
* device.unenrolled

By leveraging AWS API Gateway and Lambda and the SimpleMDM API, it is possible to respond to these events in more sophisticated ways. This Lambda function includes several scripts for responding to SimpleMDM events, including creating and deleting munki manifest files in AWS S3, moving devices to different SimpleMDM groups based on user-defined logic and information derived from the SimpleMDM API, and sending notifications to a Slack channel.

This function is designed to be easily modified and extended with additional modules or with changes to the response to specific webhook events. Pull requests are welcome.


## Getting Started

* Set the desired action in response to a specific webhook event by creating the corresponding function in a `webhook_function.py` file, and implement any additional functionality by adding modules and importing them (if you think your module may be useful to others, consider opening a pull request).

	Alternatively, you can use the default behavior provided by the `default_webhook_events.py` file.


* Create the AWS infrastructure. A [Terraform](https://github.com/hashicorp/terraform) file and example variable file can be found in the `terraform/` directory. You can use these to create the necessary AWS infrastructure and set the Lambda environmental variables.

	* Create a zip archive of the files in the `simplemdm_webhook_functions/` directory and upload them as a function in AWS Lambda. Define any environmental variables your functions requires.

	* Create an new API in API Gateway with a POST method using Lambda Proxy integration and the name of your Lambda function.

	* Create the necessary IAM roles and policies and attach them to your function.

* Point SimpleMDM webhooks to your API URL (SimpleMDM > Settings > API).

**Note**: Please be aware that as configured above, there are *no restrictions* on who can access the API. If this is a concern, steps should be taken to address this.


## Further Information

More information on SimpleMDM webhooks can be found [here](https://simplemdm.com/docs/api/#webhooks).

##### Webhook Example

```
{  
    "type":"device.enrolled",
    "at":"2000-01-01T12:00:00.000+00:00",
    "data":{  
      "device":{  
        "id":123456,
        "udid":"99919788-340F-40C3-A3F0-E54421B7A6FD",
        "serial_number":"123ABC456XYZ"
      }
    }
  }
```
