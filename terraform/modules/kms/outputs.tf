output "kms_key_arn" {
  value = aws_kms_key.s3_key.arn
}

output "kms_key_id" {
  value = aws_kms_key.s3_key.id
}