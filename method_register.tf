resource "aws_api_gateway_resource" "sms2fa_register" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  parent_id   = aws_api_gateway_rest_api.sms2fa.root_resource_id
  path_part   = "register"
}

resource "aws_api_gateway_method" "sms2fa_register" {
  rest_api_id   = aws_api_gateway_rest_api.sms2fa.id
  resource_id   = aws_api_gateway_resource.sms2fa_register.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "sms2fa_register" {
  rest_api_id             = aws_api_gateway_rest_api.sms2fa.id
  resource_id             = aws_api_gateway_resource.sms2fa_register.id
  http_method             = aws_api_gateway_method.sms2fa_register.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sms2fa_register.invoke_arn
}

resource "aws_api_gateway_integration_response" "sms2fa_register" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_register.id
  http_method = aws_api_gateway_method.sms2fa_register.http_method
  status_code = aws_api_gateway_method_response.response_200_register.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }
}

resource "aws_api_gateway_method_response" "response_200_register" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_register.id
  http_method = aws_api_gateway_method.sms2fa_register.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_model" "model_register" {
  rest_api_id  = aws_api_gateway_rest_api.sms2fa.id
  name         = "register"
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

resource "aws_api_gateway_method" "register_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.sms2fa.id
  resource_id   = aws_api_gateway_resource.sms2fa_register.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "register_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_register.id
  http_method = aws_api_gateway_method.register_options_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}


resource "aws_api_gateway_method_response" "register_options_method_response" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_register.id
  http_method = aws_api_gateway_method.register_options_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "register_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.sms2fa.id
  resource_id = aws_api_gateway_resource.sms2fa_register.id
  http_method = aws_api_gateway_method.register_options_method.http_method
  status_code = aws_api_gateway_method_response.register_options_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }
}
