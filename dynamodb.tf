resource "aws_dynamodb_table" "sms2fa" {
  name      = "sms2fa"
  billing_mode = "PAY_PER_REQUEST"
  hash_key  = "token"

  attribute {
    name = "token"
    type = "S"
  }
}

resource "aws_dynamodb_table" "sms2fa_regoptions" {
  name      = "sms2fa_regoptions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key  = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "sms2fa_regtoken" {
  name      = "sms2fa_regtoken"
  billing_mode = "PAY_PER_REQUEST"
  hash_key  = "token"

  attribute {
    name = "token"
    type = "S"
  }
}

resource "aws_dynamodb_table" "sms2fa_user" {
  name      = "sms2fa_user"
  billing_mode = "PAY_PER_REQUEST"
  hash_key  = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "sms2fa_authoptions" {
  name      = "sms2fa_authoptions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key  = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "sms2fa_audit" {
  name      = "sms2fa_audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key  = "id"
  range_key = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }
}
