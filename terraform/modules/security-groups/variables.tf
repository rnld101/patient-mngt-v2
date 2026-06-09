variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where security groups will be created"
}

variable "alb_ingress_cidr_blocks" {
  type        = list(string)
  description = "Allowed CIDR blocks for ingress to the Application Load Balancer"
}