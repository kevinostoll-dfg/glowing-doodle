"""S3-compatible storage client for DigitalOcean Spaces."""

import boto3
from botocore.config import Config

from shared.config import get_settings


def _get_s3_client():
    """Create an S3 client configured for DigitalOcean Spaces."""
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4"),
    )


def upload_recording(file_data: bytes, key: str, content_type: str = "audio/wav") -> str:
    """Upload a recording to S3-compatible storage.

    Returns the object key.
    """
    settings = get_settings()
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=file_data,
        ContentType=content_type,
    )
    return key


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for a recording."""
    settings = get_settings()
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def delete_recording(key: str) -> None:
    """Delete a recording from storage."""
    settings = get_settings()
    client = _get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket, Key=key)
