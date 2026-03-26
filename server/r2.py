"""
Cloudflare R2 Storage Client
S3-compatible API for uploading and managing media assets
"""

import os
import boto3
from botocore.config import Config
from typing import Optional, Dict
import hashlib

# R2 Configuration
R2_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
R2_ACCESS_KEY = os.environ.get("CF_R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.environ.get("CF_R2_SECRET_KEY", "")
R2_BUCKET = "mood42-assets"
R2_PUBLIC_URL = "https://pub-c60e3a4de388402ba5e40acbc497a6d6.r2.dev"

# S3-compatible endpoint for R2
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Local cache of uploaded files: hash -> r2_url
_upload_cache: Dict[str, str] = {}


def get_r2_client():
    """Get boto3 S3 client configured for Cloudflare R2."""
    if not R2_ACCOUNT_ID or not R2_ACCESS_KEY or not R2_SECRET_KEY:
        print("[R2] Missing credentials - set CF_ACCOUNT_ID, CF_R2_ACCESS_KEY, CF_R2_SECRET_KEY")
        return None

    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "adaptive"}
        ),
    )


def upload_to_r2(
    data: bytes,
    key: str,
    content_type: str = "video/mp4",
    metadata: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Upload data to R2 bucket.

    Args:
        data: File content as bytes
        key: Object key (path in bucket, e.g., "video/my_video.mp4")
        content_type: MIME type
        metadata: Optional metadata dict (attribution, source, etc.)

    Returns:
        Public URL if successful, None otherwise
    """
    # Check cache by content hash
    content_hash = hashlib.md5(data).hexdigest()
    if content_hash in _upload_cache:
        print(f"[R2] Already uploaded (cached): {key}")
        return _upload_cache[content_hash]

    client = get_r2_client()
    if not client:
        return None

    try:
        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        client.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=data,
            **extra_args
        )

        public_url = f"{R2_PUBLIC_URL}/{key}"
        _upload_cache[content_hash] = public_url
        print(f"[R2] Uploaded: {key} ({len(data) // 1024} KB)")
        return public_url

    except Exception as e:
        print(f"[R2] Upload failed: {e}")
        return None


def check_exists(key: str) -> bool:
    """Check if an object exists in R2."""
    client = get_r2_client()
    if not client:
        return False

    try:
        client.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False


def get_public_url(key: str) -> str:
    """Get public URL for an R2 object."""
    return f"{R2_PUBLIC_URL}/{key}"


def is_configured() -> bool:
    """Check if R2 credentials are configured."""
    return bool(R2_ACCOUNT_ID and R2_ACCESS_KEY and R2_SECRET_KEY)


def list_objects(prefix: str = "") -> list:
    """
    List all objects in R2 bucket with given prefix.
    Returns list of dicts with key, size, last_modified.
    """
    client = get_r2_client()
    if not client:
        return []

    objects = []
    try:
        paginator = client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': f"{R2_PUBLIC_URL}/{obj['Key']}"
                })
        print(f"[R2] Listed {len(objects)} objects with prefix '{prefix}'")
    except Exception as e:
        print(f"[R2] List failed: {e}")

    return objects


def get_object_metadata(key: str) -> Optional[Dict]:
    """Get metadata for an R2 object."""
    client = get_r2_client()
    if not client:
        return None

    try:
        response = client.head_object(Bucket=R2_BUCKET, Key=key)
        return {
            'content_type': response.get('ContentType'),
            'size': response.get('ContentLength'),
            'metadata': response.get('Metadata', {}),
            'last_modified': response.get('LastModified'),
        }
    except Exception as e:
        print(f"[R2] Get metadata failed for {key}: {e}")
        return None
