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

# ----- Dynamic Data Lookups -----

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
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

  project_name            = var.project_name
  vpc_id                  = module.vpc.vpc_id
  alb_ingress_cidr_blocks = var.alb_ingress_cidr_blocks
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

  rds_instance_class          = var.rds_instance_class
  rds_allocated_storage       = var.rds_allocated_storage
  rds_max_allocated_storage   = var.rds_max_allocated_storage
  rds_backup_retention_period = var.rds_backup_retention_period
  rds_multi_az                = var.rds_multi_az
  rds_deletion_protection     = var.rds_deletion_protection
  rds_skip_final_snapshot     = var.rds_skip_final_snapshot
}

module "launch_template" {
  source = "./modules/launch-template"

  project_name          = var.project_name
  ami_id                = data.aws_ami.ubuntu.id
  instance_type         = var.instance_type
  instance_profile_name = module.iam.instance_profile_name
  security_group_id     = module.security_groups.backend_sg_id
  git_repo_url          = var.git_repo_url
  git_tag               = var.git_tag
  secret_name           = module.secrets.secret_arn
  aws_region            = var.aws_region
  ebs_volume_size       = var.ebs_volume_size
  ebs_volume_type       = var.ebs_volume_type
}

module "asg" {
  source = "./modules/asg"

  project_name                  = var.project_name
  vpc_id                        = module.vpc.vpc_id
  public_subnet_ids             = module.vpc.public_subnets
  private_subnet_ids            = module.vpc.private_subnets
  alb_sg_id                     = module.security_groups.alb_sg_id
  launch_template_id            = module.launch_template.launch_template_id
  launch_template_version       = module.launch_template.launch_template_latest_version
  certificate_arn               = var.acm_certificate_arn
  asg_min_size                  = var.asg_min_size
  asg_max_size                  = var.asg_max_size
  asg_desired_capacity          = var.asg_desired_capacity
  asg_health_check_grace_period = var.asg_health_check_grace_period
}


module "frontend" {
  source = "./modules/frontend"

  project_name    = var.project_name
  domain_name     = var.domain_name
  certificate_arn = var.acm_certificate_arn
}

module "dns" {
  source = "./modules/dns"

  domain_name               = var.domain_name
  alb_dns_name              = module.asg.alb_dns_name
  alb_zone_id               = module.asg.alb_zone_id
  cloudfront_domain_name    = module.frontend.cloudfront_domain_name
  cloudfront_hosted_zone_id = module.frontend.cloudfront_hosted_zone_id
}

# ----- Private VPC Interface Endpoints -----

resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.project_name}-vpce-sg"
  description = "Security Group for VPC Interface Endpoints"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "${var.project_name}-vpce-sg"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}

resource "aws_vpc_endpoint" "ssm" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ssm"
  vpc_endpoint_type = "Interface"

  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  subnet_ids          = module.vpc.private_subnets
  private_dns_enabled = true

  tags = {
    Name      = "${var.project_name}-ssm-vpce"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}

resource "aws_vpc_endpoint" "ssmmessages" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ssmmessages"
  vpc_endpoint_type = "Interface"

  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  subnet_ids          = module.vpc.private_subnets
  private_dns_enabled = true

  tags = {
    Name      = "${var.project_name}-ssmmessages-vpce"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}

resource "aws_vpc_endpoint" "ec2messages" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ec2messages"
  vpc_endpoint_type = "Interface"

  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  subnet_ids          = module.vpc.private_subnets
  private_dns_enabled = true

  tags = {
    Name      = "${var.project_name}-ec2messages-vpce"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type = "Interface"

  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  subnet_ids          = module.vpc.private_subnets
  private_dns_enabled = true

  tags = {
    Name      = "${var.project_name}-secretsmanager-vpce"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}

# ----- Private S3 Gateway Endpoint -----

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat(module.vpc.private_route_table_ids, module.vpc.public_route_table_ids)

  tags = {
    Name      = "${var.project_name}-s3-vpce"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}