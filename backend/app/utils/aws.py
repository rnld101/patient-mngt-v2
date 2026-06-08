import boto3
import json
from app.core.config import settings


def get_secret(secret_name: str) -> dict:
    """
    Retrieve a secret from AWS Secrets Manager.
    Returns the secret as a dictionary.
    """
    client = boto3.client('secretsmanager', region_name=settings.aws_region)

    try:
        response = client.get_secret_value(SecretId=secret_name)

        if 'SecretString' in response:
            secret = response['SecretString']
            return json.loads(secret)
        else:
            # Handle binary secrets if needed
            return response['SecretBinary']
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve secret {secret_name}: {str(e)}")


def load_secrets_from_manager(secret_name: str):
    """
    Load secrets from AWS Secrets Manager and update settings.
    This should be called during application startup.
    """
    try:
        secrets = get_secret(secret_name)

        # Update settings with secrets
        settings.database_url = (
            f"mysql+pymysql://{secrets.get('db_user')}:{secrets.get('db_password')}"
            f"@{secrets.get('db_host')}/{secrets.get('db_name')}"
        )
        settings.jwt_secret_key = secrets.get('jwt_secret')
        settings.s3_bucket_name = secrets.get('s3_bucket_name')
        if not settings.aws_region:
            settings.aws_region = secrets.get('aws_region', 'us-east-1')

    except Exception as e:
        raise RuntimeError(f"Failed to load secrets: {str(e)}")


def upload_file_to_s3(file_obj, bucket_name: str, object_key: str) -> str:
    """
    Upload a file to S3.
    The bucket should already have SSE-KMS encryption enabled.
    S3 applies the bucket's default encryption (SSE-KMS) automatically.
    Returns the S3 object key (not a public URL — use generate_presigned_url to access).
    """
    s3_client = boto3.client('s3', region_name=settings.aws_region)

    try:
        s3_client.upload_fileobj(file_obj, bucket_name, object_key)
        return object_key
    except Exception as e:
        raise RuntimeError(f"Failed to upload file to S3: {str(e)}")


def generate_presigned_url(bucket_name: str, object_key: str, expiry: int = 3600) -> str:
    """
    Generate a pre-signed URL for a private S3 object.
    The URL is valid for `expiry` seconds (default: 1 hour).
    """
    s3_client = boto3.client('s3', region_name=settings.aws_region)

    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiry
        )
        return url
    except Exception as e:
        raise RuntimeError(f"Failed to generate pre-signed URL: {str(e)}")


def delete_file_from_s3(bucket_name: str, object_key: str) -> None:
    """
    Delete a file from S3.
    Raises RuntimeError if deletion fails.
    """
    s3_client = boto3.client('s3', region_name=settings.aws_region)

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
    except Exception as e:
        raise RuntimeError(f"Failed to delete file from S3: {str(e)}")
