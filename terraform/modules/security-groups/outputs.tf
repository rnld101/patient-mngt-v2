output "alb_sg_id" {
  value = module.alb_sg.security_group_id
}

output "backend_sg_id" {
  value = module.backend_sg.security_group_id
}

output "rds_sg_id" {
  value = module.rds_sg.security_group_id
}

output "bastion_sg_id" {
  value = module.bastion_sg.security_group_id
}