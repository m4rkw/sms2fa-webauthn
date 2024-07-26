resource "aws_iam_role" "sms2fa_register" {
  name = "sms2fa_register"

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

resource "aws_iam_policy" "sms2fa_register" {
  name = "sms2fa_register"

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
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_regoptions",
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_regtoken",
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_user",
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_audit"
            ]
        }
    ]
}
POLICY
}

resource "aws_iam_policy_attachment" "sms2fa_register" {
  name       = "sms2fa_register"
  roles      = [aws_iam_role.sms2fa_register.name]
  policy_arn = aws_iam_policy.sms2fa_register.arn
}

resource "aws_lambda_function" "sms2fa_register" {
  filename                          = "${path.module}/sms2fa_register.py.zip"
  function_name                     = "sms2fa_register"
  role                              = aws_iam_role.sms2fa_register.arn
  handler                           = "sms2fa_register.handler"
  source_code_hash                  = filebase64sha256("${path.module}/sms2fa_register.py.zip")
  runtime                           = "python3.12"
  timeout                           = 30
  architectures                     = ["arm64"]
  layers                            = [
    data.aws_lambda_layer_version.webauthn_layer.arn,
    data.aws_lambda_layer_version.pushover_layer.arn
  ]

  environment {
    variables = {
      AUTH_ENDPOINT = var.auth_endpoint
      PUSHOVER_USER             = var.pushover_user
      PUSHOVER_APP              = var.pushover_app
    }
  }
}

resource "aws_lambda_permission" "api_gateway_invoke_register" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sms2fa_register.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:eu-west-1:${local.account_id}:${aws_api_gateway_rest_api.sms2fa.id}/*/${aws_api_gateway_method.sms2fa_register.http_method}${aws_api_gateway_resource.sms2fa_register.path}"
}
