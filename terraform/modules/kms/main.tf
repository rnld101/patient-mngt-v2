resource "aws_kms_key" "s3_key" {
  description             = "KMS key for patient documents bucket"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-s3-kms"
  }
}

resource "aws_kms_alias" "s3_alias" {
  name          = "alias/${var.project_name}-s3"
  target_key_id = aws_kms_key.s3_key.key_id
}