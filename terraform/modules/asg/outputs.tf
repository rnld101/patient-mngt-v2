output "alb_dns_name" {
  value       = aws_lb.api.dns_name
  description = "DNS name of the Application Load Balancer"
}

output "alb_zone_id" {
  value       = aws_lb.api.zone_id
  description = "Hosted Zone ID of the Application Load Balancer"
}

output "asg_name" {
  value       = aws_autoscaling_group.backend.name
  description = "Name of the Auto Scaling Group"
}
