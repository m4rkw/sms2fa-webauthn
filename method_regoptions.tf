resource "aws_api_gateway_resource" "sms2fa_regoptions" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  parent_id   = aws_api_gateway_rest_api.sms2fa.root_resource_id
  path_part   = "regoptions"
}

resource "aws_api_gateway_method" "sms2fa_regoptions" {
  rest_api_id   = aws_api_gateway_rest_api.sms2fa.id
  resource_id   = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "sms2fa_regoptions" {
  rest_api_id             = aws_api_gateway_rest_api.sms2fa.id
  resource_id             = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method             = aws_api_gateway_method.sms2fa_regoptions.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sms2fa_regoptions.invoke_arn
}

resource "aws_api_gateway_integration_response" "sms2fa_regoptions" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method = aws_api_gateway_method.sms2fa_regoptions.http_method
  status_code = aws_api_gateway_method_response.response_200_regoptions.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}

resource "aws_api_gateway_method_response" "response_200_regoptions" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method = aws_api_gateway_method.sms2fa_regoptions.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_model" "model_regoptions" {
  rest_api_id  = aws_api_gateway_rest_api.sms2fa.id
  name         = "regoptions"
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

resource "aws_api_gateway_method" "regoptions_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.sms2fa.id
  resource_id   = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "regoptions_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method = aws_api_gateway_method.regoptions_options_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}


resource "aws_api_gateway_method_response" "regoptions_options_method_response" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method = aws_api_gateway_method.regoptions_options_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "regoptions_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_regoptions.id
  http_method = aws_api_gateway_method.regoptions_options_method.http_method
  status_code = aws_api_gateway_method_response.regoptions_options_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}
