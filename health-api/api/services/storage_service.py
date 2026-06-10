from __future__ import annotations
import os
import boto3
from botocore.config import Config
from api.core.config import get_settings


def _get_s3_client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.backblaze_endpoint_url,
        aws_access_key_id=s.backblaze_access_key_id,
        aws_secret_access_key=s.backblaze_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def upload_pdf(local_path: str, enrollee_id: str, company_name: str) -> str:
    s3 = _get_s3_client()
    settings = get_settings()
    safe_company = company_name.replace(" ", "_")
    key = f"reports/{safe_company}/{enrollee_id}/{os.path.basename(local_path)}"
    s3.upload_file(local_path, settings.backblaze_bucket_name, key,
                   ExtraArgs={"ContentType": "application/pdf"})
    return key


def get_signed_url(key: str, expiry_seconds: int = 604800) -> str:
    s3 = _get_s3_client()
    settings = get_settings()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.backblaze_bucket_name, "Key": key},
        ExpiresIn=expiry_seconds,
    )
