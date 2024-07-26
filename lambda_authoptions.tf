resource "aws_iam_role" "sms2fa_authoptions" {
  name = "sms2fa_authoptions"

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

resource "aws_iam_policy" "sms2fa_authoptions" {
  name = "sms2fa_authoptions"

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
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_authoptions",
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_user",
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_audit"
            ]
        }
    ]
}
POLICY
}

resource "aws_iam_policy_attachment" "sms2fa_authoptions" {
  name       = "sms2fa_authoptions"
  roles      = [aws_iam_role.sms2fa_authoptions.name]
  policy_arn = aws_iam_policy.sms2fa_authoptions.arn
}

resource "aws_lambda_function" "sms2fa_authoptions" {
  filename                          = "${path.module}/sms2fa_authoptions.py.zip"
  function_name                     = "sms2fa_authoptions"
  role                              = aws_iam_role.sms2fa_authoptions.arn
  handler                           = "sms2fa_authoptions.handler"
  source_code_hash                  = filebase64sha256("${path.module}/sms2fa_authoptions.py.zip")
  runtime                           = "python3.12"
  timeout                           = 30
  architectures                     = ["arm64"]
  layers                            = [data.aws_lambda_layer_version.webauthn_layer.arn]

  environment {
    variables = {
      AUTH_ENDPOINT = var.auth_endpoint
    }
  }
}

resource "aws_lambda_permission" "api_gateway_invoke_authoptions" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sms2fa_authoptions.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:eu-west-1:${local.account_id}:${aws_api_gateway_rest_api.sms2fa.id}/*/${aws_api_gateway_method.sms2fa_authoptions.http_method}${aws_api_gateway_resource.sms2fa_authoptions.path}"
}
