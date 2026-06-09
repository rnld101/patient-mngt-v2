output "instance_profile_name" {
  value = aws_iam_instance_profile.backend.name
}

output "role_arn" {
  value = aws_iam_role.backend.arn
}

output "role_name" {
  value = aws_iam_role.backend.name
}