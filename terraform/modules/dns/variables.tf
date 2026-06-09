variable "domain_name" {
  type        = string
  description = "Base domain name (e.g. lavenbloom.xyz)"
}

variable "alb_dns_name" {
  type        = string
  description = "Application Load Balancer DNS name"
}

variable "alb_zone_id" {
  type        = string
  description = "Application Load Balancer Hosted Zone ID"
}

variable "cloudfront_domain_name" {
  type        = string
  description = "CloudFront Distribution Domain name"
}

variable "cloudfront_hosted_zone_id" {
  type        = string
  description = "CloudFront Distribution Hosted Zone ID"
}
