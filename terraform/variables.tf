variable "aws_region" {
  type        = string
  description = "AWS region where resources will be deployed"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "A prefix for naming project resources"
}

# ----- VPC / Networking -----

variable "alb_ingress_cidr_blocks" {
  type        = list(string)
  description = "Allowed CIDR blocks for ingress to the Application Load Balancer"
  default     = ["0.0.0.0/0"]
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

# ----- RDS Sizing & Configuration -----

variable "rds_instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  type        = number
  description = "Allocated storage for RDS instance (GB)"
  default     = 20
}

variable "rds_max_allocated_storage" {
  type        = number
  description = "Maximum allocated storage for RDS auto-scaling (GB)"
  default     = 50
}

variable "rds_backup_retention_period" {
  type        = number
  description = "Number of days to retain backups for the RDS instance"
  default     = 7
}

variable "rds_multi_az" {
  type        = bool
  description = "Deploy the RDS instance across multiple availability zones"
  default     = false
}

variable "rds_deletion_protection" {
  type        = bool
  description = "Enable RDS deletion protection"
  default     = false
}

variable "rds_skip_final_snapshot" {
  type        = bool
  description = "Skip final DB snapshot before deletion"
  default     = true
}

# ----- Application secrets -----

variable "jwt_secret" {
  type        = string
  sensitive   = true
  description = "Secret key used for signing JWTs"
}

# ----- Deployment configurations -----

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "Backend EC2 instance type"
}

variable "ebs_volume_size" {
  type        = number
  description = "Size of the root EBS volume in GB"
  default     = 20
}

variable "ebs_volume_type" {
  type        = string
  description = "Type of the root EBS volume"
  default     = "gp3"
}

variable "asg_min_size" {
  type        = number
  description = "Minimum size of the Auto Scaling Group"
  default     = 1
}

variable "asg_max_size" {
  type        = number
  description = "Maximum size of the Auto Scaling Group"
  default     = 2
}

variable "asg_desired_capacity" {
  type        = number
  description = "Desired capacity of the Auto Scaling Group"
  default     = 1
}

variable "asg_health_check_grace_period" {
  type        = number
  description = "ASG health check grace period in seconds"
  default     = 300
}

variable "git_repo_url" {
  type        = string
  default     = "https://github.com/rnld101/patient-mngt-v2.git"
  description = "Git Repository URL to clone application backend"
}

variable "git_tag" {
  type        = string
  default     = "v1.0.0"
  description = "Git Tag/Branch/Commit for deployment"
}

variable "domain_name" {
  type        = string
  description = "Primary custom domain name"
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM Certificate ARN for HTTPS listener and CloudFront"
}
