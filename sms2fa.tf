resource "aws_cloudfront_origin_access_identity" "sms2fa" {
  comment = "sms2fa"
}

resource "aws_cloudfront_distribution" "s3_distribution_sms2fa" {
  origin {
    domain_name = aws_s3_bucket.sms2fa.bucket_regional_domain_name
    origin_id   = "origin"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.sms2fa.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "sms2fa"
  default_root_object = "index.html"

  aliases = [var.auth_endpoint]

  default_cache_behavior {
    allowed_methods  = ["HEAD", "GET"]
    cached_methods   = ["HEAD", "GET"]
    target_origin_id = "origin"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn = data.terraform_remote_state.ssl.outputs.cert_arn
    ssl_support_method  = "sni-only"
  }
}

resource "cloudflare_record" "auth" {
  zone_id = lookup(data.cloudflare_zones.zone.zones[0],"id")
  name = var.auth_endpoint
  type = "CNAME"
  value = aws_cloudfront_distribution.s3_distribution_sms2fa.domain_name
  ttl = 120
}
