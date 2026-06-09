variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where resources are deployed"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnets for the Application Load Balancer"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnets for the Auto Scaling Group instances"
}

variable "alb_sg_id" {
  type        = string
  description = "Security Group ID for the ALB"
}

variable "launch_template_id" {
  type        = string
  description = "ID of the Launch Template to use for the ASG"
}

variable "launch_template_version" {
  type        = string
  description = "Version of the Launch Template to use for the ASG"
}

variable "certificate_arn" {
  type        = string
  description = "ACM Certificate ARN for the HTTPS listener"
}

variable "asg_min_size" {
  type        = number
  description = "Minimum size of the Auto Scaling Group"
}

variable "asg_max_size" {
  type        = number
  description = "Maximum size of the Auto Scaling Group"
}

variable "asg_desired_capacity" {
  type        = number
  description = "Desired capacity of the Auto Scaling Group"
}

variable "asg_health_check_grace_period" {
  type        = number
  description = "ASG health check grace period in seconds"
}
