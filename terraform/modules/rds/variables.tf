variable "project_name" {
  type = string
}

variable "database_name" {
  type = string
}

variable "database_username" {
  type = string
}

variable "database_password" {
  type      = string
  sensitive = true
}

variable "rds_sg_id" {
  type = string
}

variable "db_subnet_group_name" {
  type = string
}