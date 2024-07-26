resource "aws_iam_role" "sms2fa_regoptions" {
  name = "sms2fa_regoptions"

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

resource "aws_iam_policy" "sms2fa_regoptions" {
  name = "sms2fa_regoptions"

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
              "arn:aws:dynamodb:eu-west-1:${local.account_id}:table/sms2fa_audit"
            ]
        }
    ]
}
POLICY
}

resource "aws_iam_policy_attachment" "sms2fa_regoptions" {
  name       = "sms2fa_regoptions"
  roles      = [aws_iam_role.sms2fa_regoptions.name]
  policy_arn = aws_iam_policy.sms2fa_regoptions.arn
}

resource "aws_lambda_function" "sms2fa_regoptions" {
  filename                          = "${path.module}/sms2fa_regoptions.py.zip"
  function_name                     = "sms2fa_regoptions"
  role                              = aws_iam_role.sms2fa_regoptions.arn
  handler                           = "sms2fa_regoptions.handler"
  source_code_hash                  = filebase64sha256("${path.module}/sms2fa_regoptions.py.zip")
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

resource "aws_lambda_permission" "api_gateway_invoke_regoptions" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sms2fa_regoptions.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:eu-west-1:${local.account_id}:${aws_api_gateway_rest_api.sms2fa.id}/*/${aws_api_gateway_method.sms2fa_regoptions.http_method}${aws_api_gateway_resource.sms2fa_regoptions.path}"
}
