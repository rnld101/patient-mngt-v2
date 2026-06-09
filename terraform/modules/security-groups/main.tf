module "alb_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.3"

  name        = "${var.project_name}-alb-sg"
  description = "ALB Security Group"

  vpc_id = var.vpc_id

  ingress_rules = [
    "http-80-tcp",
    "https-443-tcp"
  ]

  ingress_cidr_blocks = var.alb_ingress_cidr_blocks

  egress_rules = [
    "all-all"
  ]
}

module "backend_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.3"

  name        = "${var.project_name}-backend-sg"
  description = "Backend Security Group"

  vpc_id = var.vpc_id

  ingress_with_source_security_group_id = [
    {
      description              = "FastAPI from ALB"
      from_port                = 8000
      to_port                  = 8000
      protocol                 = "tcp"
      source_security_group_id = module.alb_sg.security_group_id
    }
  ]

  egress_rules = [
    "all-all"
  ]
}

module "rds_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.3"

  name        = "${var.project_name}-rds-sg"
  description = "RDS Security Group"

  vpc_id = var.vpc_id

  ingress_with_source_security_group_id = [
    {
      rule                     = "mysql-tcp"
      source_security_group_id = module.backend_sg.security_group_id
    }
  ]

  egress_rules = [
    "all-all"
  ]
}