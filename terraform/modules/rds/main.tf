module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-db"

  engine               = "mysql"
  engine_version       = "8.4"
  family               = "mysql8.4"
  major_engine_version = "8.4"

  instance_class = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password

  manage_master_user_password = false

  port = 3306

  multi_az = var.rds_multi_az

  publicly_accessible = false

  vpc_security_group_ids = [
    var.rds_sg_id
  ]

  create_db_subnet_group = false
  db_subnet_group_name   = var.db_subnet_group_name

  backup_retention_period = var.rds_backup_retention_period

  deletion_protection = var.rds_deletion_protection

  skip_final_snapshot = var.rds_skip_final_snapshot

  tags = {
    Name = "${var.project_name}-db"
  }
}