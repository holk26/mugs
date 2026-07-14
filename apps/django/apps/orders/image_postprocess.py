import io
from PIL import Image


class ImagePostprocessError(Exception):
    pass


def _mm_to_px(mm, dpi):
    """Convert millimetres to pixels at the given DPI, rounding to nearest pixel."""
    return int(round(mm * dpi / 25.4))


def postprocess_image(image_bytes: bytes, specs: dict) -> tuple[bytes, str]:
    """Adjust an image to exact Printful specs.

    Returns (image_bytes, content_type).
    """
    required_keys = ('width_mm', 'height_mm', 'dpi', 'background', 'format')
    for key in required_keys:
        if key not in specs:
            raise ImagePostprocessError(f'Missing required spec: {key}')

    width_mm = specs['width_mm']
    height_mm = specs['height_mm']
    dpi = specs['dpi']
    background = specs['background']
    fmt = specs['format'].lower()

    for name, value in (('width_mm', width_mm), ('height_mm', height_mm), ('dpi', dpi)):
        if not isinstance(value, int) or value <= 0:
            raise ImagePostprocessError(f'{name} must be a positive integer')

    if background not in ('white', 'transparent'):
        raise ImagePostprocessError(f"background must be 'white' or 'transparent', got {background!r}")

    if fmt not in ('png', 'jpeg'):
        raise ImagePostprocessError(f'Unsupported output format: {fmt}')

    if background == 'transparent' and fmt == 'jpeg':
        # JPEG cannot be transparent; force white background.
        background = 'white'

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        raise ImagePostprocessError(f'Cannot open image: {exc}') from exc

    target_w = _mm_to_px(width_mm, dpi)
    target_h = _mm_to_px(height_mm, dpi)

    # Preserve aspect ratio, fit inside target box.
    img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

    # Build output canvas.
    if background == 'transparent':
        canvas = Image.new('RGBA', (target_w, target_h), (255, 255, 255, 0))
    else:
        canvas = Image.new('RGB', (target_w, target_h), (255, 255, 255))

    # Center the resized image.
    paste_x = (target_w - img.width) // 2
    paste_y = (target_h - img.height) // 2

    if canvas.mode == 'RGBA':
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
    elif canvas.mode == 'RGB':
        if img.mode in ('RGBA', 'P'):
            # Flatten transparency onto white.
            img = img.convert('RGBA')
            white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
            img = Image.alpha_composite(white_bg, img).convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

    canvas.paste(img, (paste_x, paste_y))

    buffer = io.BytesIO()
    if fmt == 'png':
        canvas.save(
            buffer,
            format='PNG',
            dpi=(dpi, dpi),
            optimize=True,
        )
        content_type = 'image/png'
    else:
        if canvas.mode == 'RGBA':
            canvas = canvas.convert('RGB')
        canvas.save(
            buffer,
            format='JPEG',
            dpi=(dpi, dpi),
            quality=95,
            optimize=True,
        )
        content_type = 'image/jpeg'

    buffer.seek(0)
    return buffer.read(), content_type
