#!/bin/bash
invoke_url=`terraform state show aws_api_gateway_stage.sms2fa |grep invoke_url |xargs |cut -d ' ' -f3`
cat frontend/index.html |replace 'var api_gateway_root = "https://API_GATEWAY_ENDPOINT/sms2fa";' 'var api_gateway_root = "https://tfqxahiq28.execute-api.eu-west-1.amazonaws.com/sms2fa";' > frontend/index.html.new
mv frontend/index.html.new frontend/index.html
cat frontend/register.html |replace 'var api_gateway_root = "https://API_GATEWAY_ENDPOINT/sms2fa";' 'var api_gateway_root = "https://tfqxahiq28.execute-api.eu-west-1.amazonaws.com/sms2fa";' > frontend/register.html.new
mv frontend/register.html.new frontend/register.html
