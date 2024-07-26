data "aws_caller_identity" "current" {}

data "cloudflare_zones" "zone" {
  filter {
    name = var.domain
  }
}

data "aws_lambda_layer_version" "webauthn_layer" {
  layer_name = "webauthn-layer-python312"
}

data "aws_lambda_layer_version" "pushover_layer" {
  layer_name = "pushover-layer-python312"
}
