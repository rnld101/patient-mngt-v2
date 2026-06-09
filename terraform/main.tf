# Inbuilt module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = "${var.project_name}-vpc"

  cidr = "10.0.0.0/16"

  azs = [
    "us-east-1a",
    "us-east-1b"
  ]

  public_subnets = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]

  private_subnets = [
    "10.0.11.0/24",
    "10.0.12.0/24"
  ]

  database_subnets = [
    "10.0.21.0/24",
    "10.0.22.0/24"
  ]

  enable_nat_gateway = true

  single_nat_gateway = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  create_database_subnet_group = true

  tags = {
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}

module "kms" {
  source = "./modules/kms"

  project_name = var.project_name
}

module "secrets" {
  source = "./modules/secrets"

  project_name = var.project_name

  # Wired to live RDS outputs — host and db_name are only known after RDS is created
  db_host     = module.rds.endpoint
  db_name     = module.rds.db_name
  db_user     = var.database_username
  db_password = var.database_password

  jwt_secret     = var.jwt_secret
  s3_bucket_name = module.s3.bucket_name
  aws_region     = var.aws_region
}

# KMS dependency
module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  kms_key_arn  = module.kms.kms_key_arn
}

module "security_groups" {
  source = "./modules/security-groups"

  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id
  admin_cidr   = var.admin_cidr
}

module "iam" {
  source = "./modules/iam"

  project_name = var.project_name

  bucket_arn  = module.s3.bucket_arn
  kms_key_arn = module.kms.kms_key_arn
  secret_arn  = module.secrets.secret_arn
}

module "rds" {
  source = "./modules/rds"

  project_name = var.project_name

  database_name     = var.database_name
  database_username = var.database_username
  database_password = var.database_password

  rds_sg_id = module.security_groups.rds_sg_id

  db_subnet_group_name = module.vpc.database_subnet_group_name
}