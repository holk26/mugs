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

    # Scale the image to fill the target width (cover), then crop vertically
    # centered if it exceeds the target height. This produces a wide print file
    # that uses the full print area instead of leaving large blank margins.
    src_w, src_h = img.size
    if src_w == 0 or src_h == 0:
        raise ImagePostprocessError('Source image has zero width or height')

    scale = target_w / src_w
    scaled_w = target_w
    scaled_h = int(round(src_h * scale))

    img = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    # Build output canvas.
    if background == 'transparent':
        canvas = Image.new('RGBA', (target_w, target_h), (255, 255, 255, 0))
    else:
        canvas = Image.new('RGB', (target_w, target_h), (255, 255, 255))

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

    if scaled_h >= target_h:
        # Crop the vertical overflow, keeping the center of the design.
        crop_top = (scaled_h - target_h) // 2
        img = img.crop((0, crop_top, scaled_w, crop_top + target_h))
        canvas.paste(img, (0, 0))
    else:
        # Center vertically when the design does not fill the full height.
        paste_y = (target_h - scaled_h) // 2
        canvas.paste(img, (0, paste_y))

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
