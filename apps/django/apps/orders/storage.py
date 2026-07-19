from django.conf import settings


def customer_upload_storage():
    """Storage backend for original customer drawings (PII).

    In production (S3/MinIO configured via AWS_S3_ENDPOINT_URL) drawings go to
    a dedicated private bucket served through presigned URLs, unlike product
    media which lives in the public bucket. In development they fall back to
    the default local filesystem storage.
    """
    if settings.AWS_S3_ENDPOINT_URL:
        from storages.backends.s3boto3 import S3Boto3Storage

        return S3Boto3Storage(
            bucket_name=settings.DRAWINGS_BUCKET_NAME,
            default_acl='private',
            querystring_auth=True,
            file_overwrite=False,
        )

    from django.core.files.storage import default_storage

    return default_storage
