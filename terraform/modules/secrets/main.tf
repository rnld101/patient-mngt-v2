resource "aws_secretsmanager_secret" "app" {
  name = "${var.project_name}-app-secret"

  tags = {
    Name = "${var.project_name}-app-secret"
  }
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id

  secret_string = jsonencode({
    db_host        = var.db_host
    db_name        = var.db_name
    db_user        = var.db_user
    db_password    = var.db_password
    jwt_secret     = var.jwt_secret
    s3_bucket_name = var.s3_bucket_name
    aws_region     = var.aws_region
  })
}