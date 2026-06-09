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
