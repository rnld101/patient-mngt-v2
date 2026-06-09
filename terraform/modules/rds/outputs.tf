output "endpoint" {
  value = module.rds.db_instance_address
}

output "db_name" {
  value = module.rds.db_instance_name
}