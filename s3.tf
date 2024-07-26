resource "aws_s3_bucket" "sms2fa" {
  bucket = var.s3_bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_policy" "sms2fa" {
  bucket = aws_s3_bucket.sms2fa.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          AWS = "${aws_cloudfront_origin_access_identity.sms2fa.iam_arn}"
        },
        Action = "s3:GetObject",
        Resource = "${aws_s3_bucket.sms2fa.arn}/*"
      }
    ]
  })
}
