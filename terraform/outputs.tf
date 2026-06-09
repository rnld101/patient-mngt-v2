output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnets" {
  value = module.vpc.public_subnets
}

output "private_subnets" {
  value = module.vpc.private_subnets
}

output "database_subnets" {
  value = module.vpc.database_subnets
}

output "kms_key_arn" {
  value = module.kms.kms_key_arn
}

output "secret_arn" {
  value = module.secrets.secret_arn
}

output "bucket_name" {
  value = module.s3.bucket_name
}

output "bucket_arn" {
  value = module.s3.bucket_arn
}

output "rds_endpoint" {
  description = "RDS instance endpoint - also stored in Secrets Manager under db_host"
  value       = module.rds.endpoint
}

output "rds_db_name" {
  description = "MySQL database name inside the RDS instance"
  value       = module.rds.db_name
}

# ----- Deployment outputs -----

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.asg.alb_dns_name
}

output "api_endpoint" {
  description = "Backend API URL endpoint"
  value       = module.dns.api_endpoint
}

output "frontend_endpoint" {
  description = "Frontend website domain endpoint"
  value       = module.dns.frontend_endpoint
}

output "cloudfront_domain_name" {
  description = "Default domain name of the CloudFront distribution"
  value       = module.frontend.cloudfront_domain_name
}

output "frontend_bucket_name" {
  description = "Name of the frontend static assets S3 bucket"
  value       = module.frontend.frontend_bucket_name
}

output "asg_name" {
  description = "Name of the Auto Scaling Group"
  value       = module.asg.asg_name
}
