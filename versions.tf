terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }

    cloudflare = {
      source = "cloudflare/cloudflare"
      version = "4.23.0"
    }
  }
  required_version = ">= 0.13"
}
