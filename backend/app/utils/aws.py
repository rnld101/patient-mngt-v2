import boto3
import json
import mimetypes
from botocore.config import Config
from app.core.config import settings

# Register DICOM MIME type
mimetypes.add_type('application/dicom', '.dcm')

# SigV4 is required for S3 objects encrypted with SSE-KMS.
# All S3 operations use this shared configuration.
_S3_CONFIG = Config(
    signature_version="s3v4",
    s3={"addressing_style": "virtual"}
)


def _s3_client():
    """
    Return a boto3 S3 client configured to use Signature Version 4.

    SigV4 is mandatory when generating pre-signed URLs for objects stored
    in a bucket that uses SSE-KMS encryption.  Without it, AWS rejects the
    request with:
        "Requests specifying Server Side Encryption with AWS KMS managed keys
         require AWS Signature Version 4."

    A new client is created per call so that the correct region is always
    picked up even if settings.aws_region is populated after module import
    (i.e. after Secrets Manager loads it at startup).
    """
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        config=_S3_CONFIG,
    )


def get_secret(secret_name: str) -> dict:
    """
    Retrieve a secret from AWS Secrets Manager.
    Returns the secret as a dictionary.
    """
    client = boto3.client("secretsmanager", region_name=settings.aws_region)

    try:
        response = client.get_secret_value(SecretId=secret_name)

        if "SecretString" in response:
            return json.loads(response["SecretString"])
        else:
            # Handle binary secrets if needed
            return response["SecretBinary"]
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
        settings.jwt_secret_key = secrets.get("jwt_secret")
        settings.s3_bucket_name = secrets.get("s3_bucket_name")
        if not settings.aws_region:
            settings.aws_region = secrets.get("aws_region", "us-east-1")

    except Exception as e:
        raise RuntimeError(f"Failed to load secrets: {str(e)}")


def upload_file_to_s3(file_obj, bucket_name: str, object_key: str, content_type: str = None) -> str:
    """
    Upload a file to S3.
    The bucket must have SSE-KMS encryption enabled as the default.
    S3 applies encryption automatically on every PutObject call.
    Returns the S3 object key (never a public URL — use generate_presigned_url to access).
    """
    try:
        if not content_type:
            content_type, _ = mimetypes.guess_type(object_key)
        
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        _s3_client().upload_fileobj(file_obj, bucket_name, object_key, ExtraArgs=extra_args)
        return object_key
    except Exception as e:
        raise RuntimeError(f"Failed to upload file to S3: {str(e)}")


def generate_presigned_url(bucket_name: str, object_key: str, expiry: int = 3600, mode: str = "view", filename: str = None) -> str:
    """
    Generate a SigV4 pre-signed URL for a private S3 object.

    The URL is valid for `expiry` seconds (default: 1 hour) and can be configured
    as 'inline' (view mode) or 'attachment' (download mode).

    KMS-encrypted objects require SigV4.  The _s3_client() helper ensures
    the correct signature version is used for every call.
    """
    try:
        content_type, _ = mimetypes.guess_type(object_key)
        params = {"Bucket": bucket_name, "Key": object_key}
        
        if mode == "download":
            disposition_filename = filename or object_key.split('/')[-1]
            # Force download/attachment headers
            params["ResponseContentDisposition"] = f'attachment; filename="{disposition_filename}"'
        else:
            # Force inline rendering
            params["ResponseContentDisposition"] = "inline"

        if content_type:
            params["ResponseContentType"] = content_type

        url = _s3_client().generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expiry,
        )
        return url
    except Exception as e:
        raise RuntimeError(f"Failed to generate pre-signed URL: {str(e)}")


def delete_file_from_s3(bucket_name: str, object_key: str) -> None:
    """
    Delete a file from S3.
    Raises RuntimeError if the deletion fails.
    """
    try:
        _s3_client().delete_object(Bucket=bucket_name, Key=object_key)
    except Exception as e:
        raise RuntimeError(f"Failed to delete file from S3: {str(e)}")
