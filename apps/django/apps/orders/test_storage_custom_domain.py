import pytest
from django.conf import settings
from apps.orders.storage import customer_upload_storage


@pytest.mark.django_db
def test_customer_upload_storage_ignores_media_custom_domain():
    """Reproduce bug: drawings bucket inherits AWS_S3_CUSTOM_DOMAIN from media bucket.

    In production AWS_S3_CUSTOM_DOMAIN points to the public media bucket
    (e.g. minio.app.moonsbow.com/mugs-media). The private drawings storage must
    not reuse that domain, otherwise presigned URLs for customer uploads point
    to the wrong bucket and the dashboard cannot display the image.
    """
    settings.AWS_S3_ENDPOINT_URL = 'http://minio:9000'
    settings.AWS_STORAGE_BUCKET_NAME = 'mugs-media'
    settings.DRAWINGS_BUCKET_NAME = 'mugs-drawings'
    settings.AWS_S3_CUSTOM_DOMAIN = 'minio.app.moonsbow.com/mugs-media'
    settings.AWS_DEFAULT_ACL = 'public-read'
    settings.AWS_QUERYSTRING_AUTH = False

    storage = customer_upload_storage()

    assert storage.bucket_name == 'mugs-drawings', (
        f"Expected drawings bucket 'mugs-drawings', got '{storage.bucket_name}'"
    )
    assert storage.custom_domain != settings.AWS_S3_CUSTOM_DOMAIN, (
        f"Drawings storage must not reuse media custom_domain "
        f"'{settings.AWS_S3_CUSTOM_DOMAIN}'"
    )


@pytest.mark.django_db
def test_customer_upload_url_points_to_drawings_bucket():
    """Without a custom domain the URL must include the drawings bucket."""
    settings.AWS_S3_ENDPOINT_URL = 'http://minio:9000'
    settings.AWS_STORAGE_BUCKET_NAME = 'mugs-media'
    settings.DRAWINGS_BUCKET_NAME = 'mugs-drawings'
    settings.AWS_S3_CUSTOM_DOMAIN = 'minio.app.moonsbow.com/mugs-media'
    settings.AWS_DEFAULT_ACL = 'public-read'
    settings.AWS_QUERYSTRING_AUTH = False

    storage = customer_upload_storage()
    url = storage.url('drawings/2026/07/20/test.png')

    assert 'mugs-drawings' in url, (
        f"URL should reference the drawings bucket, got: {url}"
    )
    assert 'mugs-media' not in url, (
        f"URL should not reference the media bucket, got: {url}"
    )
