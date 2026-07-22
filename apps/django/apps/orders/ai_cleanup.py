import base64
import io
import mimetypes
import os

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.orders.image_postprocess import postprocess_image
from apps.orders.print_specs import get_print_specs


class ImageCleanupError(Exception):
    pass


def _media_base_url():
    return os.environ.get('PUBLIC_DJANGO_API_URL', 'https://backshop.app.moonsbow.com')


def _resolve_image_url(file_field):
    """Return an absolute HTTPS URL for the uploaded file."""
    if not file_field or not file_field.name:
        raise ImageCleanupError('No customer upload found for this line')
    url = file_field.url
    if url.startswith('/'):
        base = _media_base_url()
        url = f"{base.rstrip('/')}{url}"
    return url


def _download_image(url):
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ImageCleanupError(f'Failed to download image: {exc}') from exc
    return response.content, response.headers.get('content-type', '')


def _extension_from_content_type(content_type):
    ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.png'
    return ext


def _prompt():
    return getattr(settings, 'AI_IMAGE_PROMPT', (
        "Clean up this image for printing on a white ceramic mug. Remove the background, "
        "keep only the main subject, and rearrange it into a horizontal panoramic composition "
        "that fills a wide print area. The design should stretch across the width of the mug, "
        "with the main elements distributed horizontally rather than stacked vertically. "
        "Make colors vibrant and ensure a clean transparent or white background suitable for "
        "sublimation printing. Preserve the original subject faithfully."
    ))


def _build_prompt(operator_prompt=None, specs=None):
    base = _prompt()
    parts = [base]
    if operator_prompt:
        parts.append(f"Additional operator instructions: {operator_prompt}")
    if specs:
        parts.append(
            f"Technical requirements: final output must be a {specs['format']} image "
            f"with {specs['background']} background, {specs['dpi']} DPI, "
            f"suitable for a {specs['width_mm']}x{specs['height_mm']} mm print area. "
            "Preserve the original subject faithfully."
        )
    return "\n".join(parts)


def cleanup_image_with_openai(file_field, operator_prompt=None, specs=None):
    from openai import OpenAI

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ImageCleanupError('OpenAI API key is not configured')

    url = _resolve_image_url(file_field)
    image_bytes, content_type = _download_image(url)

    client = OpenAI(api_key=api_key)
    model = getattr(settings, 'OPENAI_IMAGE_MODEL', 'gpt-image-2')

    try:
        response = client.images.edit(
            image=image_bytes,
            prompt=_build_prompt(operator_prompt, specs),
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


def cleanup_image_with_gemini(file_field, operator_prompt=None, specs=None):
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ImageCleanupError('Google Gen AI SDK is not installed') from exc

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ImageCleanupError('Gemini API key is not configured')

    url = _resolve_image_url(file_field)
    image_bytes, content_type = _download_image(url)
    mime_type = (content_type.split(';')[0] or 'image/png')

    client = genai.Client(api_key=api_key)
    model = getattr(settings, 'GEMINI_IMAGE_MODEL', 'gemini-2.5-flash-image')

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                _build_prompt(operator_prompt, specs),
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
            ),
        )
    except Exception as exc:
        raise ImageCleanupError(f'Gemini image edit failed: {exc}') from exc

    if not response.candidates:
        raise ImageCleanupError('Gemini returned no candidates')

    parts = response.candidates[0].content.parts
    for part in parts:
        inline_data = getattr(part, 'inline_data', None)
        if inline_data and inline_data.data:
            return inline_data.data, inline_data.mime_type or 'image/png'

    raise ImageCleanupError('Gemini returned no image data')


def cleanup_image_with_ai(file_field, provider=None, operator_prompt=None, specs=None):
    """Clean up an image using the configured or requested AI provider."""
    provider = provider or getattr(settings, 'AI_IMAGE_PROVIDER', 'openai').lower()

    if provider == 'gemini':
        return cleanup_image_with_gemini(file_field, operator_prompt=operator_prompt, specs=specs)
    if provider == 'openai':
        return cleanup_image_with_openai(file_field, operator_prompt=operator_prompt, specs=specs)

    if settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY:
        return cleanup_image_with_gemini(file_field, operator_prompt=operator_prompt, specs=specs)
    if settings.OPENAI_API_KEY:
        return cleanup_image_with_openai(file_field, operator_prompt=operator_prompt, specs=specs)

    raise ImageCleanupError('No AI image provider is configured')


def generate_cleaned_upload(order_line, provider=None, operator_prompt=None):
    """Generate an AI-cleaned upload for an OrderLine and save it.

    Returns True on success, raises ImageCleanupError on failure.
    """
    if not order_line.customer_upload:
        raise ImageCleanupError('Order line has no customer upload')

    specs = get_print_specs(order_line)
    image_bytes, _content_type = cleanup_image_with_ai(
        order_line.customer_upload,
        provider=provider,
        operator_prompt=operator_prompt,
        specs=specs,
    )
    image_bytes, content_type = postprocess_image(image_bytes, specs)
    original_name = os.path.basename(order_line.customer_upload.name)
    root, _ = os.path.splitext(original_name)
    ext = specs['format'].lower()
    filename = f"{root}_cleaned.{ext}"

    order_line.processed_upload.save(filename, ContentFile(image_bytes), save=False)
    order_line.processed_upload_prompt = operator_prompt or ''
    order_line.processed_upload_generated_at = timezone.now()
    order_line.processed_upload_error = ''
    order_line.save(update_fields=[
        'processed_upload',
        'processed_upload_prompt',
        'processed_upload_generated_at',
        'processed_upload_error',
    ])
    return True
