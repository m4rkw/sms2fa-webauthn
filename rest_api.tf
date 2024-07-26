resource "aws_api_gateway_rest_api" "sms2fa" {
  name = "sms 2fa"
}

resource "aws_api_gateway_deployment" "sms2fa" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.sms2fa.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}
