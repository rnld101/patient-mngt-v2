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

# ----- Deployment configurations -----

variable "ami_id" {
  type        = string
  default     = "ami-091138d0f0d41ff90"
  description = "Ubuntu 22.04 LTS AMI ID"
}

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "Backend EC2 instance type"
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
  default     = "lavenbloom.xyz"
  description = "Primary custom domain name"
}

variable "acm_certificate_arn" {
  type        = string
  default     = "arn:aws:acm:us-east-1:130290476321:certificate/704cd3dd-6fe1-4b83-a780-ae8bcfc31f2f"
  description = "Discovered ACM Certificate ARN"
}
