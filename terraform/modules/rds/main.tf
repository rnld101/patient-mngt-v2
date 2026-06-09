module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-db"

  engine               = "mysql"
  engine_version       = "8.4"
  family               = "mysql8.4"
  major_engine_version = "8.4"

  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 50

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password

  port = 3306

  multi_az = false

  publicly_accessible = false

  vpc_security_group_ids = [
    var.rds_sg_id
  ]

  create_db_subnet_group = false
  db_subnet_group_name   = var.db_subnet_group_name

  backup_retention_period = 7

  deletion_protection = false

  skip_final_snapshot = true

  tags = {
    Name = "${var.project_name}-db"
  }
}