output "frontend_bucket_name" {
  value       = aws_s3_bucket.frontend.id
  description = "Name of the frontend S3 bucket"
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "Domain name of the CloudFront distribution"
}

output "cloudfront_hosted_zone_id" {
  value       = aws_cloudfront_distribution.frontend.hosted_zone_id
  description = "Hosted Zone ID of the CloudFront distribution"
}
