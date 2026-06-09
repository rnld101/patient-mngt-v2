variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "database_name" {
  type        = string
  description = "Name of the MySQL database inside the RDS instance"
}

variable "database_username" {
  type        = string
  description = "Master username for the RDS instance"
}

variable "database_password" {
  type        = string
  sensitive   = true
  description = "Master password for the RDS instance"
}

variable "rds_sg_id" {
  type        = string
  description = "Security group ID for RDS"
}

variable "db_subnet_group_name" {
  type        = string
  description = "Database subnet group name"
}

variable "rds_instance_class" {
  type        = string
  description = "RDS instance class"
}

variable "rds_allocated_storage" {
  type        = number
  description = "Allocated storage (GB)"
}

variable "rds_max_allocated_storage" {
  type        = number
  description = "Maximum allocated storage for autoscaling (GB)"
}

variable "rds_backup_retention_period" {
  type        = number
  description = "Backup retention period in days"
}

variable "rds_multi_az" {
  type        = bool
  description = "Enable Multi-AZ deployment"
}

variable "rds_deletion_protection" {
  type        = bool
  description = "Enable deletion protection"
}

variable "rds_skip_final_snapshot" {
  type        = bool
  description = "Skip final snapshot before deletion"
}