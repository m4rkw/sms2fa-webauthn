resource "aws_iam_role" "sms2fa" {
  name = "sms2fa"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com",
          "edgelambda.amazonaws.com"
        ]
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "sms2fa" {
  name = "sms2fa"

  policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
              "dynamodb:*"
            ],
            "Resource": [
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa",
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_audit"
            ]
        }
    ]
}
POLICY
}

resource "aws_iam_policy_attachment" "sms2fa" {
  name       = "sms2fa"
  roles      = [aws_iam_role.sms2fa.name]
  policy_arn = aws_iam_policy.sms2fa.arn
}

resource "aws_lambda_function" "sms2fa" {
  filename                          = "${path.module}/sms2fa.py.zip"
  function_name                     = "sms2fa"
  role                              = aws_iam_role.sms2fa.arn
  handler                           = "sms2fa.handler"
  source_code_hash                  = filebase64sha256("${path.module}/sms2fa.py.zip")
  runtime                           = "python3.12"
  timeout                           = 30
  layers                            = [data.aws_lambda_layer_version.pushover_layer.arn]
  architectures                     = ["arm64"]

  environment {
    variables = {
      PUSHOVER_USER             = var.pushover_user
      PUSHOVER_APP              = var.pushover_app
      AUTH_ENDPOINT             = var.auth_endpoint
      PROVIDER_REGEX            = "^gwNumber=(.*?)&originator=(.*?)&message=(.*?)&time="
      PROVIDER_FROM_SEGMENT     = "2"
      PROVIDER_MESSAGE_SEGMENT  = "3"
    }
  }
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sms2fa.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:eu-west-1:${local.account_id}:${aws_api_gateway_rest_api.sms2fa.id}/*/${aws_api_gateway_method.sms2fa.http_method}${aws_api_gateway_resource.sms2fa.path}"
}
