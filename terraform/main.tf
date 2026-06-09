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

  db_host = var.db_host
  db_name = var.db_name
  db_user = var.db_user
  db_password = var.db_password
  jwt_secret  = var.jwt_secret
  s3_bucket_name = module.s3.bucket_name
  aws_region = var.aws_region
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