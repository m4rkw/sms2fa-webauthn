resource "aws_api_gateway_resource" "sms2fa" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  parent_id   = aws_api_gateway_rest_api.sms2fa.root_resource_id
  path_part   = "sms"
}

resource "aws_api_gateway_method" "sms2fa" {
  rest_api_id   = aws_api_gateway_rest_api.sms2fa.id
  resource_id   = aws_api_gateway_resource.sms2fa.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "sms2fa" {
  rest_api_id             = aws_api_gateway_rest_api.sms2fa.id
  resource_id             = aws_api_gateway_resource.sms2fa.id
  http_method             = aws_api_gateway_method.sms2fa.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sms2fa.invoke_arn
}

resource "aws_api_gateway_integration_response" "sms2fa" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa.id
  http_method = aws_api_gateway_method.sms2fa.http_method
  status_code = aws_api_gateway_method_response.response_200.status_code
}

resource "aws_api_gateway_method_response" "response_200" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa.id
  http_method = aws_api_gateway_method.sms2fa.http_method
  status_code = "200"
}

resource "aws_api_gateway_model" "model" {
  rest_api_id  = aws_api_gateway_rest_api.sms2fa.id
  name         = "response"
  description  = "API response for sms2fa"
  content_type = "application/json"
  schema = jsonencode({
    "$schema" = "http://json-schema.org/draft-04/schema#"
    title     = "response"
    type      = "object"
    properties = {
      status = {
        type = "string"
      }
    }
  })
}
