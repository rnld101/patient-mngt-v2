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


def upload_image_to_s3(file_obj, bucket_name: str, object_key: str) -> str:
    """
    Upload an image to S3.
    The bucket should already have SSE-KMS encryption enabled.
    We do NOT specify encryption parameters here - S3 handles it automatically.
    """
    s3_client = boto3.client('s3', region_name=settings.aws_region)
    
    try:
        # Simple upload without manual encryption specification
        # S3 will automatically apply the bucket's default encryption (SSE-KMS)
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            object_key
        )
        
        # Generate the S3 URL
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        return s3_url
        
    except Exception as e:
        raise RuntimeError(f"Failed to upload image to S3: {str(e)}")
