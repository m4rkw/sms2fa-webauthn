# SMS 2FA

## Overview

This is an example AWS implementation of secure 2FA SMS based on my post here:
https://github.com/m4rkw/sim-swap-defence

The basic idea is that you rent a virtual mobile number from a telephony
provider such as AQL, and use that number for all services that require
SMS-based 2FA. The text messages are sent to the virtual number and then
forwarded to a url endpoint.

This endpoint is serviced by a lambda function which extracts the OTP code from
the message and stores it, and then sends a push notification to the device to
indicate there's an OTP code available. This push notification contains an
embedded url which then directs the user to an authentication page which
authenticates the device using a webauthn passkey flow.

On success, the OTP token is then shown.

## Implementation details

- sms2fa lambda function - this receives the calls from the telephony provider
  and is called from API Gateway

This example code is designed to work with AQL but should be easy to adapt for
different providers.

- s3-backed frontend - using cloudfront the front-end html/javascript enable the
  webauthn authentication flows in the browser

- other lambda functions - the other four lambda functions are all called from
  API Gateway by the frontend code and facilitate the webauthn.

- Currently it only supports a single user for simplicity. Generating a new
  registration URL and re-registering will remove the previously stored passkey.

## Requirements

- Terraform
- An AWS account with billing configured. Since this system is entirely
  serverless and very infrequently called, you can expect it to cost almost
  nothing to operate.
- An AQL virtual mobile number or similar service from another provider
- An ssl certificate configured in AWS for the domain you intend to use
- Docker to create the Lambda layer artefacts
- A domain to use for the frontend
- The DNS zone for the domain hosted on CloudFlare - not stricly necessary but
  that's what I'm using for this example because they have a Terraform provider
  and unlike AWS domain hosting is free there. It should be pretty easy to
  adapt this to Route53 or another provider if you prefer.
- A Pushover.net account for the push notifications

## Setup process

1. Create the Lambda layers

note: requires docker

````
$ cd layers
$ ./build_layers.sh
$ aws lambda publish-layer-version --layer-name webauthn-layer-python312 \
    --zip-file fileb://webauthn_layer.zip --compatible-runtimes python3.12
$ aws lambda publish-layer-version --layer-name pushover-layer-python312 \
    --zip-file fileb://pushover_layer.zip --compatible-runtimes python3.12
````

2. Create input.tf and specify the terraform workspace that has your ssl
certificate. The other workspace should output a key called "cert\_arn" with
the ARN of the certificate.

````
data "terraform_remote_state" "ssl" {
  backend = "s3"
  config = {
    bucket = "<YOUR BUCKET>"
    key = "/path/to/terraform.tfstate"
    region = "eu-west-1"
    profile = "default"
  }
}
````

3. Configure a state backend for the SMS2FA workspace:

````
$ cat state.tf
terraform {
  backend "s3" {
    bucket = "<YOUR BUCKET>"
    key = "/path/to/terraform.tfstate"
    region = "eu-west-1"
    encrypt = true
  }
}
````

4. Configure terraform.tfvars with these input variables:

````
aws_region              = "eu-west-1"
domain                  = "mydomain.com"
auth_endpoint           = "auth.mydomain.com"
cloudflare_api_token    = "MY_CLOUDFLARE_TOKEN"
s3_bucket_name          = "my_sms2fa_bucket"
pushover_user           = "YOUR_PUSHOVER_USER_KEY"
pushover_app            = "YOUR_PUSHOVER_APP_KEY"
````

5. Build the artefacts:

````
$ ./build_artefacts.sh
````

6. Execute the terraform to build all the resources:

````
$ terraform init
$ terraform apply
````

7. Deploy the API to activate it:

````
$ ./deploy_api.sh
````

8. Update the auth endpoint URLs in the frontend HTML:

````
$ ./update_frontend.sh
````

9. Sync the frontend code to the S3 bucket:

````
$ aws s3 sync frontend/ s3://my_sms2fa_bucket/
````

10. Point your virtual mobile number at the sms2fa endpoint, you can get the
base URL with:

````
$ terraform state show aws_api_gateway_stage.sms2fa |grep invoke_url |xargs |cut -d ' ' -f3
https://<SOMETHING>.execute-api.eu-west-1.amazonaws.com/sms2fa
````

The URL to assign the virtual mobile number to would then be:

````
https://<SOMETHING>.execute-api.eu-west-1.amazonaws.com/sms2fa/sms
````

11. Generate a registration URL:

````
$ ./bin/generate_registration_url.py
````

12. Visit the link in order to create your passkey and register it with the
service.

Now when OTP codes are sent to the virtual number you should receive a
notification that will then authenticate via webauthn and then reveal the OTP
code.
