import io
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from PIL import Image

from apps.orders.models import OrderLine


class MockupError(Exception):
    pass


def _create_blank_template(width: int = 800, height: int = 800) -> Image.Image:
    """Create a generic mug-coloured template when no product image is available."""
    # Warm off-white/cream background that reads as a blank mug surface.
    template = Image.new('RGB', (width, height), (245, 243, 238))

    # Draw a subtle elliptical outline so it doesn't look like a broken image.
    from PIL import ImageDraw
    draw = ImageDraw.Draw(template)
    margin = 60
    draw.ellipse(
        [margin, margin * 2, width - margin, height - margin * 2],
        outline=(210, 205, 195),
        width=4,
    )
    return template


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
    """Generate a simple product preview by overlaying the design on the product image."""
    if not line.variant or not line.variant.product:
        raise MockupError('Line has no product to use as template.')

    design_source = line.processed_upload or line.customer_upload
    if not design_source:
        raise MockupError('Line has no customer upload or processed upload.')

    product_media = line.variant.product.medias.filter(type='image').first()
    if product_media and product_media.file:
        template = _open_image(product_media.file)
    else:
        # Fallback: render the design on a generic mug-coloured canvas.
        template = _create_blank_template()

    design = _open_image(design_source)

    if design.mode in ('RGBA', 'P'):
        design = design.convert('RGBA')
    else:
        design = design.convert('RGB')

    if template.mode in ('RGBA', 'P'):
        template = template.convert('RGBA')
    else:
        template = template.convert('RGB')

    # Use the processed upload as a square-ish design placed in the center of the mug.
    template_width, template_height = template.size
    design_max_width = int(template_width * 0.50)
    design.thumbnail((design_max_width, design_max_width), Image.Resampling.LANCZOS)

    design_width, design_height = design.size
    x = (template_width - design_width) // 2
    y = (template_height - design_height) // 2

    # Create a clean RGB output and paste the design with alpha blending if needed.
    output = Image.new('RGB', template.size, (255, 255, 255))
    output.paste(template, (0, 0))

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
