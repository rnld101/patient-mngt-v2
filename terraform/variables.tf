variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type = string
}

# ----- RDS / Database credentials (shared with secrets module) -----

variable "database_name" {
  type        = string
  description = "Name of the MySQL database created inside the RDS instance"
}

variable "database_username" {
  type        = string
  sensitive   = true
  description = "Master username for the RDS instance"
}

variable "database_password" {
  type        = string
  sensitive   = true
  description = "Master password for the RDS instance"
}

# ----- Application secrets -----

variable "jwt_secret" {
  type      = string
  sensitive = true
}

variable "admin_cidr" {
  type        = string
  description = "CIDR block allowed SSH access to the bastion host"
}
