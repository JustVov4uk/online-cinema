from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

from src.core.config import get_settings

AVATAR_CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def get_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


def ensure_bucket_exists(bucket_name: str) -> None:
    s3_client = get_s3_client()

    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        s3_client.create_bucket(Bucket=bucket_name)


def build_avatar_object_key(user_id: int, content_type: str) -> str:
    file_extension = AVATAR_CONTENT_TYPE_EXTENSIONS[content_type]
    return f"avatars/users/{user_id}/{uuid4().hex}.{file_extension}"


def upload_avatar_to_storage(
    *,
    user_id: int,
    content: bytes,
    content_type: str,
) -> str:
    settings = get_settings()
    bucket_name = settings.S3_BUCKET_NAME
    object_key = build_avatar_object_key(user_id=user_id, content_type=content_type)
    s3_client = get_s3_client()

    ensure_bucket_exists(bucket_name=bucket_name)
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=content,
        ContentType=content_type,
    )

    return f"{settings.S3_PUBLIC_BASE_URL}/{object_key}"
