#!/bin/bash
api_id=`terraform state show aws_api_gateway_rest_api.sms2fa |grep ' id ' |xargs |cut -d ' ' -f3`
aws apigateway create-deployment --rest-api-id $api_id --stage-name sms2fa
