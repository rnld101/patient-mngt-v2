variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "domain_name" {
  type        = string
  description = "Primary domain name for the frontend application"
}

variable "certificate_arn" {
  type        = string
  description = "ACM Certificate ARN for HTTPS"
}
