# SimpleMDM Webhook Functions

AWS Lambda function for responding to SimpleMDM webhook events.

[SimpleMDM](https://simplemdm.com/) allows for simple webhooks (HTTP POST requests) when certain events occur in a SimpleMDM account. These events currently include:

* device.enrolled
* device.unenrolled

By leveraging AWS API Gateway and Lambda and the SimpleMDM API, it is possible to respond to these events in more sophisticated ways. This Lambda function includes several scripts for responding to SimpleMDM events, including creating and deleting munki manifest files in AWS S3 or moving devices to different SimpleMDM groups based on user-defined logic and information derived from the SimpleMDM API. It is designed to be easily extended with additional modules, with only minor changes required to the `lambda_function.py` module necessary.

## Getting Started

* Modify the contents of the webhook event functions in `lambda_function.py` to suit your organization's requirements. Implement any additional functionality by adding modules and importing them into the main file.

* Upload a zip archive of the files in the `simplemdm_webhook_functions/` directory as a function in AWS Lambda. Define any environmental variables your functions requires. (**Note**: In order to create/delete objects in S3, the IAM role you selected for your Lambda function requires S3 privileges for that bucket.)

* Create an new API in API Gateway with a POST method using Lambda Proxy integration and the name of your Lambda function.

* Point SimpleMDM webhooks to your API URL (SimpleMDM > Settings > API).

**Note**: Please be aware that as configured above, there are *no restrictions* on who can access the API. While this allows for easy testing, it also allows third parties with the API URL access as well. Production environments should take steps to address this.


## Further Information

More information on SimpleMDM webhooks can be found here:

https://simplemdm.com/docs/api/#webhooks

##### Webhook Example

```
{  
    "type":"device.enrolled",
    "at":"2018-01-31T11:29:11.190+00:00",
    "data":{  
      "device":{  
        "id":210952,
        "udid":"F49CECA9-2445-40FC-981F-9089D3504EAE",
        "serial_number":"123ABC456XYZ"
      }
    }
  }
```
