##### SimpleMDM Webhook Functions ######

### Configure variables
variable "aws_access_key" {
  type        = "string"
  description = "AWS Access Key"
}

variable "aws_secret_key" {
  type        = "string"
  description = "AWS Secret Key"
}

variable "aws_region" {
  type        = "string"
  description = "AWS Region"
  default     = "us-west-1"
}

variable "zip_file_path" {
  type        = "string"
  description = "Path to .zip file containing the Lambda function"
}

variable "log_bucket_name" {
  type        = "string"
  description = "S3 bucket for Lambda function logs"
}

variable "munki_repo_manifests_folder" {
  type        = "string"
  description = "Munki repo manifests folder"
  default     = "manifests"
}

variable "munki_repo_bucket_name" {
  type        = "string"
  description = "Munki repo S3 bucket name"
  default     = ""
}

variable "munki_repo_bucket_region" {
  type        = "string"
  description = "Munki repo S3 bucket region"
  default     = ""
}

variable "simplemdm_api_key" {
  type        = "string"
  description = "API key for SimpleMDM"
  default     = ""
}

variable "slack_url" {
  type        = "string"
  description = "Slack message URL"
  default     = ""
}


### Configure the AWS Provider

provider "aws" {
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
  region     = "${var.aws_region}"
}


### Configure infrastructure


# Log S3 Bucket
resource "aws_s3_bucket" "log_s3_bucket" {
  bucket        = "${var.log_bucket_name}"
  acl           = "private"
  force_destroy = false
}


# Lambda Function
resource "aws_lambda_function" "simplemdm_webhooks_lambda_function" {
  function_name = "SimpleMDM-Webhooks"
  description   = "Function for responding to SimpleMDM webhooks."
  filename      = "${var.zip_file_path}"
  role          = "${aws_iam_role.simplemdm_webhooks_iam_role.arn}"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.6"
  timeout       = 10

  environment {
    variables = {
      LOG_BUCKET               = "${var.log_bucket_name}",
      MUNKI_MANIFEST_FOLDER    = "${var.munki_repo_manifests_folder}",
      MUNKI_REPO_BUCKET        = "${var.munki_repo_bucket_name}",
      MUNKI_REPO_BUCKET_REGION = "${var.munki_repo_bucket_region}"
      SIMPLEMDM_API_KEY        = "${var.simplemdm_api_key}"
      SLACK_URL                = "${var.slack_url}"
    }
  }
}


# IAM Role
resource "aws_iam_role" "simplemdm_webhooks_iam_role" {
  name               = "simplemdm-webhooks-lambda-role"
  description        = "SimpleMDM Webhooks Lambda role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}


# S3 Write IAM Policy
resource "aws_iam_role_policy" "s3_write_role_policy" {
  name   = "S3WritePolicy"
  role   = "${aws_iam_role.simplemdm_webhooks_iam_role.id}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::${var.log_bucket_name}",
                "arn:aws:s3:::${var.munki_repo_bucket_name}",
                "arn:aws:s3:::*/*"
            ]
        }
    ]
}
EOF
}


# API Gateway
resource "aws_api_gateway_rest_api" "simplemdm_webhook_api_gateway" {
  name        = "SimpleMDMWebhooks"
  description = "API Gateway for SimpleMDM Webhooks"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}


# API Gateway Deployment
resource "aws_api_gateway_deployment" "prod_deployment" {
  rest_api_id = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.id}"
  stage_name  = "v1"
  depends_on  = [
    "aws_api_gateway_integration.api_simplemdm_resource_lambda_integration"
  ]
}


# API Gateway Resource
resource "aws_api_gateway_resource" "api_simplemdm_resource" {
  rest_api_id = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.id}"
  parent_id   = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.root_resource_id}"
  path_part   = "simplemdm"
}


# API Gateway Method
resource "aws_api_gateway_method" "api_simplemdm_post_method" {
  rest_api_id   = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.id}"
  resource_id   = "${aws_api_gateway_resource.api_simplemdm_resource.id}"
  http_method   = "POST"
  authorization = "NONE"
}


# API Gateway Lambda Integration
resource "aws_api_gateway_integration" "api_simplemdm_resource_lambda_integration" {
  rest_api_id             = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.id}"
  resource_id             = "${aws_api_gateway_resource.api_simplemdm_resource.id}"
  http_method             = "${aws_api_gateway_method.api_simplemdm_post_method.http_method}"
  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.simplemdm_webhooks_lambda_function.arn}/invocations"
}


# API Gateway Method Response (200)
resource "aws_api_gateway_method_response" "http_200_response" {
  rest_api_id = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.id}"
  resource_id = "${aws_api_gateway_resource.api_simplemdm_resource.id}"
  http_method = "${aws_api_gateway_method.api_simplemdm_post_method.http_method}"
  status_code = "200"
}


# API Gateway Lambda Integration Response (200)
resource "aws_api_gateway_integration_response" "http_200_lambda_response" {
  rest_api_id = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.id}"
  resource_id = "${aws_api_gateway_resource.api_simplemdm_resource.id}"
  http_method = "${aws_api_gateway_method.api_simplemdm_post_method.http_method}"
  status_code = "${aws_api_gateway_method_response.http_200_response.status_code}"

  depends_on  = ["aws_api_gateway_integration.api_simplemdm_resource_lambda_integration"]
}


# API Gateway Lambda Permission
resource "aws_lambda_permission" "add_api_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.simplemdm_webhooks_lambda_function.arn}"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.simplemdm_webhook_api_gateway.execution_arn}/*/POST/simplemdm"
}
