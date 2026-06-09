output "api_endpoint" {
  value       = "https://api.${var.domain_name}"
  description = "Domain name endpoint of the API"
}

output "frontend_endpoint" {
  value       = "https://${var.domain_name}"
  description = "Domain name endpoint of the frontend"
}
