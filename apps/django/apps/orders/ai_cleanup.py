import base64
import io
import mimetypes
import os
import re
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from openai import OpenAI


class ImageCleanupError(Exception):
    pass


def _resolve_image_url(file_field):
    """Return an absolute HTTPS URL for the uploaded file."""
    if not file_field or not file_field.name:
        raise ImageCleanupError('No customer upload found for this line')
    url = file_field.url
    if url.startswith('/'):
        base = os.environ.get('PUBLIC_DJANGO_API_URL', 'https://mugs.app.moonsbow.com')
        url = f"{base.rstrip('/')}{url}"
    return url


def _download_image(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content, response.headers.get('content-type', '')


def _extension_from_content_type(content_type):
    ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.png'
    return ext


def cleanup_image_with_ai(file_field):
    """Download the customer's upload, ask OpenAI to clean it up, and return bytes.

    Uses OpenAI's image editing API (gpt-image-2 by default) so the original
    subject is preserved while the background is removed / centered for mug
    printing.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ImageCleanupError('OpenAI API key is not configured')

    url = _resolve_image_url(file_field)
    image_bytes, content_type = _download_image(url)
    ext = _extension_from_content_type(content_type)

    client = OpenAI(api_key=api_key)
    prompt = settings.OPENAI_IMAGE_PROMPT
    model = settings.OPENAI_IMAGE_MODEL

    try:
        response = client.images.edit(
            image=image_bytes,
            prompt=prompt,
            model=model,
            n=1,
            size='1024x1024',
            response_format='b64_json',
            output_format='png',
            background='transparent',
        )
    except Exception as exc:
        raise ImageCleanupError(f'OpenAI image edit failed: {exc}') from exc

    if not response.data:
        raise ImageCleanupError('OpenAI returned no image data')

    b64 = response.data[0].b64_json
    if not b64:
        raise ImageCleanupError('OpenAI returned empty image data')

    return base64.b64decode(b64), 'image/png'


def generate_cleaned_upload(order_line):
    """Generate an AI-cleaned upload for an OrderLine and save it.

    Returns True on success, raises ImageCleanupError on failure.
    """
    from apps.orders.models import OrderLine

    if not order_line.customer_upload:
        raise ImageCleanupError('Order line has no customer upload')

    image_bytes, content_type = cleanup_image_with_ai(order_line.customer_upload)
    original_name = os.path.basename(order_line.customer_upload.name)
    root, _ = os.path.splitext(original_name)
    filename = f"{root}_cleaned.png"

    order_line.processed_upload.save(filename, ContentFile(image_bytes), save=False)
    order_line.processed_upload_generated_at = timezone.now()
    order_line.processed_upload_error = ''
    order_line.save(update_fields=['processed_upload', 'processed_upload_generated_at', 'processed_upload_error'])
    return True
