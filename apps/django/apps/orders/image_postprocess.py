import io
from PIL import Image


class ImagePostprocessError(Exception):
    pass


def _mm_to_px(mm, dpi):
    return int(round(mm * dpi / 25.4))


def postprocess_image(image_bytes: bytes, specs: dict) -> tuple[bytes, str]:
    """Adjust an image to exact Printful specs.

    Returns (image_bytes, content_type).
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        raise ImagePostprocessError(f'Cannot open image: {exc}') from exc

    width_mm = specs['width_mm']
    height_mm = specs['height_mm']
    dpi = specs['dpi']
    background = specs['background']
    fmt = specs['format'].lower()

    if fmt not in ('png', 'jpeg'):
        raise ImagePostprocessError(f'Unsupported output format: {fmt}')

    if background == 'transparent' and fmt == 'jpeg':
        # JPEG cannot be transparent; force white background.
        background = 'white'

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

    if canvas.mode == 'RGBA' and img.mode != 'RGBA':
        img = img.convert('RGBA')
    elif canvas.mode == 'RGB' and img.mode in ('RGBA', 'P'):
        # Flatten onto white background.
        alpha = img.convert('RGBA').split()[-1]
        white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(white_bg, img.convert('RGBA')).convert('RGB')
    elif img.mode == 'P':
        img = img.convert('RGB')

    if img.mode == 'RGBA' and canvas.mode == 'RGB':
        canvas.paste(img, (paste_x, paste_y), img.split()[-1])
    else:
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
