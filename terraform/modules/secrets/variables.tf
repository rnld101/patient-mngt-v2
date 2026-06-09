variable "project_name" {
  type = string
}

variable "db_host" {
  type      = string
  sensitive = true
}

variable "db_name" {
  type      = string
  sensitive = true
}

variable "db_user" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "jwt_secret" {
  type      = string
  sensitive = true
}

variable "s3_bucket_name" {
    type = string  
}

variable "aws_region" {
    type = string
}