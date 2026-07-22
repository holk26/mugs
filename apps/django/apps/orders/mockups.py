import io
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFilter

from apps.orders.models import OrderLine


class MockupError(Exception):
    pass


def _create_mug_template(width: int = 800, height: int = 800) -> Image.Image:
    """Create a simple mug-shaped template for product previews."""
    template = Image.new('RGB', (width, height), (250, 250, 248))
    draw = ImageDraw.Draw(template)

    # Mug body: rounded rectangle centered.
    body_margin_x = int(width * 0.18)
    body_top = int(height * 0.22)
    body_bottom = int(height * 0.78)
    body_left = body_margin_x
    body_right = width - body_margin_x
    body_width = body_right - body_left
    body_height = body_bottom - body_top

    # Soft shadow under the mug.
    shadow = Image.new('RGBA', template.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        [body_left - 20, body_bottom - 10, body_right + 20, body_bottom + 30],
        fill=(0, 0, 0, 40),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    template = Image.alpha_composite(template.convert('RGBA'), shadow).convert('RGB')
    draw = ImageDraw.Draw(template)

    # Mug body.
    draw.rounded_rectangle(
        [body_left, body_top, body_right, body_bottom],
        radius=20,
        fill=(255, 255, 255),
        outline=(220, 218, 214),
        width=2,
    )

    # Mug handle: ellipse attached to the right side.
    handle_center_x = body_right
    handle_center_y = body_top + body_height // 2
    handle_width = int(width * 0.12)
    handle_height = int(height * 0.22)
    handle_left = handle_center_x - handle_width // 2
    handle_right = handle_center_x + handle_width // 2
    handle_top = handle_center_y - handle_height // 2
    handle_bottom = handle_center_y + handle_height // 2

    draw.ellipse(
        [handle_left, handle_top, handle_right, handle_bottom],
        fill=(255, 255, 255),
        outline=(220, 218, 214),
        width=2,
    )
    # Inner hole of the handle.
    inner_margin = 8
    draw.ellipse(
        [
            handle_left + inner_margin,
            handle_top + inner_margin,
            handle_right - inner_margin,
            handle_bottom - inner_margin,
        ],
        fill=(250, 250, 248),
        outline=(220, 218, 214),
        width=1,
    )

    # Printable area guide (subtle dashed rectangle inside the body).
    print_margin_x = int(body_width * 0.15)
    print_margin_y = int(body_height * 0.15)
    print_left = body_left + print_margin_x
    print_right = body_right - print_margin_x
    print_top = body_top + print_margin_y
    print_bottom = body_bottom - print_margin_y

    # Dashed outline for the print area.
    dash = 6
    gap = 4
    # Top and bottom dashed lines.
    x = print_left
    while x < print_right:
        draw.line([(x, print_top), (min(x + dash, print_right), print_top)], fill=(200, 198, 194), width=1)
        draw.line([(x, print_bottom), (min(x + dash, print_right), print_bottom)], fill=(200, 198, 194), width=1)
        x += dash + gap
    # Left and right dashed lines.
    y = print_top
    while y < print_bottom:
        draw.line([(print_left, y), (print_left, min(y + dash, print_bottom))], fill=(200, 198, 194), width=1)
        draw.line([(print_right, y), (print_right, min(y + dash, print_bottom))], fill=(200, 198, 194), width=1)
        y += dash + gap

    return template, (print_left, print_top, print_right, print_bottom)


def _open_image(source):
    """Open an image from a FileField or a URL."""
    if hasattr(source, 'file') and source.file:
        return Image.open(source.file)

    url = str(source)
    parsed = urlparse(url)
    if parsed.scheme in ('http', 'https'):
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))

    raise MockupError(f'Unsupported image source: {url}')


def generate_line_mockup(line: OrderLine) -> OrderLine:
    """Generate a product preview by placing the design on a mug template."""
    if not line.variant or not line.variant.product:
        raise MockupError('Line has no product to use as template.')

    design_source = line.processed_upload or line.customer_upload
    if not design_source:
        raise MockupError('Line has no customer upload or processed upload.')

    template, print_area = _create_mug_template()
    print_left, print_top, print_right, print_bottom = print_area
    print_width = print_right - print_left
    print_height = print_bottom - print_top

    design = _open_image(design_source)

    if design.mode in ('RGBA', 'P'):
        design = design.convert('RGBA')
    else:
        design = design.convert('RGB')

    # Fit the design inside the printable area while preserving aspect ratio.
    design.thumbnail((print_width, print_height), Image.Resampling.LANCZOS)
    design_width, design_height = design.size
    x = print_left + (print_width - design_width) // 2
    y = print_top + (print_height - design_height) // 2

    output = template.copy()
    if design.mode == 'RGBA':
        output.paste(design, (x, y), design.split()[3])
    else:
        output.paste(design, (x, y))

    buffer = io.BytesIO()
    output.save(buffer, format='PNG')
    buffer.seek(0)

    line.mockup.save(f'mockup_{line.id}.png', ContentFile(buffer.read()), save=False)
    line.save(update_fields=['mockup'])
    return line
