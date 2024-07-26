resource "aws_api_gateway_stage" "sms2fa" {
  deployment_id = aws_api_gateway_deployment.sms2fa.id
  rest_api_id   = aws_api_gateway_rest_api.sms2fa.id
  stage_name    = "sms2fa"
}

resource "aws_api_gateway_method_settings" "sms2fa" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  stage_name  = aws_api_gateway_stage.sms2fa.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
  }
}
