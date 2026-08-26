"""S3 input/output storage for document processing."""
from __future__ import annotations
import os
from typing import Optional

try:
    import boto3
    _S3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        endpoint_url=os.getenv("S3_ENDPOINT_URL"),  # for MinIO
    )
    _BOTO3 = True
except Exception:
    _BOTO3 = False
    _S3 = None

INPUT_BUCKET = os.getenv("S3_INPUT_BUCKET", "doc-processor-input")
OUTPUT_BUCKET = os.getenv("S3_OUTPUT_BUCKET", "doc-processor-output")


def download_document(s3_key: str, local_path: str) -> str:
    """Download a document from S3. Returns local_path."""
    if not _BOTO3:
        raise RuntimeError("boto3 not installed or S3 not configured")
    _S3.download_file(INPUT_BUCKET, s3_key, local_path)
    return local_path


def upload_result(local_path: str, s3_key: str) -> str:
    """Upload an extraction result to S3. Returns the S3 URL."""
    if not _BOTO3:
        raise RuntimeError("boto3 not installed or S3 not configured")
    _S3.upload_file(local_path, OUTPUT_BUCKET, s3_key)
    return f"s3://{OUTPUT_BUCKET}/{s3_key}"


def get_presigned_url(s3_key: str, expires: int = 3600) -> str:
    """Generate a pre-signed URL for downloading a result."""
    if not _BOTO3:
        return f"[mock] s3://{OUTPUT_BUCKET}/{s3_key}"
    return _S3.generate_presigned_url(
        "get_object",
        Params={"Bucket": OUTPUT_BUCKET, "Key": s3_key},
        ExpiresIn=expires,
    )
