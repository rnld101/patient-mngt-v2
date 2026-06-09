output "launch_template_id" {
  value       = aws_launch_template.backend.id
  description = "ID of the created Launch Template"
}

output "launch_template_latest_version" {
  value       = aws_launch_template.backend.latest_version
  description = "Latest version of the created Launch Template"
}
