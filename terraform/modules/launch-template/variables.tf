variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "ami_id" {
  type        = string
  description = "AMI ID for EC2 instances"
}

variable "instance_type" {
  type        = string
  description = "EC2 Instance Type"
}

variable "instance_profile_name" {
  type        = string
  description = "IAM Instance Profile Name for EC2 backend"
}

variable "security_group_id" {
  type        = string
  description = "Backend EC2 Security Group ID"
}

variable "git_repo_url" {
  type        = string
  description = "Git Repository URL to clone application from"
}

variable "git_tag" {
  type        = string
  description = "Git Tag/Branch/Commit to check out"
}

variable "secret_name" {
  type        = string
  description = "AWS Secrets Manager Secret Name"
}

variable "aws_region" {
  type        = string
  description = "AWS Region name"
}

variable "ebs_volume_size" {
  type        = number
  description = "Size of the root EBS volume in GB"
}

variable "ebs_volume_type" {
  type        = string
  description = "Type of the root EBS volume"
}
