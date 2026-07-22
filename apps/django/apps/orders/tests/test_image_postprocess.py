import io
import pytest
from PIL import Image
from apps.orders.image_postprocess import postprocess_image, ImagePostprocessError


def _image_bytes(width, height, mode='RGB'):
    img = Image.new(mode, (width, height))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def test_postprocess_png_white_background():
    specs = {
        'width_mm': 240,
        'height_mm': 92,
        'dpi': 300,
        'background': 'white',
        'format': 'png',
    }
    out_bytes, content_type = postprocess_image(_image_bytes(500, 500), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert img.size == (2835, 1087)
    assert img.mode == 'RGB'
    assert content_type == 'image/png'
    assert img.info.get('dpi') == pytest.approx((300.0, 300.0), abs=0.1)


def test_postprocess_transparent_background():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'transparent',
        'format': 'png',
    }
    out_bytes, content_type = postprocess_image(_image_bytes(200, 200, 'RGBA'), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert img.mode == 'RGBA'
    assert content_type == 'image/png'


def test_postprocess_jpeg_forces_white_background():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'transparent',
        'format': 'jpeg',
    }
    out_bytes, content_type = postprocess_image(_image_bytes(200, 200, 'RGBA'), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert img.mode == 'RGB'
    assert content_type == 'image/jpeg'


def test_postprocess_unsupported_format():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
        'format': 'gif',
    }
    with pytest.raises(ImagePostprocessError):
        postprocess_image(_image_bytes(200, 200), specs)


def test_postprocess_grayscale_input():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
        'format': 'png',
    }
    out_bytes, _ = postprocess_image(_image_bytes(200, 200, 'L'), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert img.mode == 'RGB'


def test_postprocess_palette_input():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
        'format': 'png',
    }
    out_bytes, _ = postprocess_image(_image_bytes(200, 200, 'P'), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert img.mode == 'RGB'


def test_postprocess_corrupt_image_bytes():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
        'format': 'png',
    }
    with pytest.raises(ImagePostprocessError):
        postprocess_image(b'not an image', specs)


def test_postprocess_missing_spec_key():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
    }
    with pytest.raises(ImagePostprocessError):
        postprocess_image(_image_bytes(200, 200), specs)


def test_postprocess_invalid_background():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'blue',
        'format': 'png',
    }
    with pytest.raises(ImagePostprocessError):
        postprocess_image(_image_bytes(200, 200), specs)


@pytest.mark.parametrize('field,value', [
    ('width_mm', 0),
    ('width_mm', -10),
    ('height_mm', 0),
    ('height_mm', -10),
    ('dpi', 0),
    ('dpi', -150),
])
def test_postprocess_invalid_dimensions(field, value):
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
        'format': 'png',
    }
    specs[field] = value
    with pytest.raises(ImagePostprocessError):
        postprocess_image(_image_bytes(200, 200), specs)


def test_postprocess_jpeg_dpi_preserved():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
        'format': 'jpeg',
    }
    out_bytes, content_type = postprocess_image(_image_bytes(200, 200), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert content_type == 'image/jpeg'
    assert img.info.get('dpi') == pytest.approx((150.0, 150.0), abs=0.1)


def test_postprocess_image_centered():
    specs = {
        'width_mm': 100,
        'height_mm': 100,
        'dpi': 150,
        'background': 'white',
        'format': 'png',
    }
    # 100mm @ 150 dpi = 591 px target canvas.
    # Create a small non-white image so we can detect its placement.
    source = Image.new('RGB', (100, 100), color=(255, 0, 0))
    buffer = io.BytesIO()
    source.save(buffer, format='PNG')
    out_bytes, _ = postprocess_image(buffer.getvalue(), specs)
    img = Image.open(io.BytesIO(out_bytes))
    # The resized red square should fill the width; verify non-white/red pixels exist.
    assert any(pixel != (255, 255, 255) for pixel in img.get_flattened_data())


def test_postprocess_fills_width_with_vertical_crop():
    """A square image should fill the full width and be cropped vertically."""
    specs = {
        'width_mm': 240,
        'height_mm': 92,
        'dpi': 300,
        'background': 'white',
        'format': 'png',
    }
    # Target: 2835x1087. A 1000x1000 source becomes 2835x2835, cropped to 2835x1087.
    source = Image.new('RGB', (1000, 1000), color=(255, 0, 0))
    buffer = io.BytesIO()
    source.save(buffer, format='PNG')
    out_bytes, _ = postprocess_image(buffer.getvalue(), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert img.size == (2835, 1087)
    # The full canvas should be red (no white margins).
    assert all(pixel == (255, 0, 0) for pixel in img.get_flattened_data())


def test_postprocess_fills_width_and_centers_short_image():
    """A very wide image should fill the width and be centered vertically."""
    specs = {
        'width_mm': 240,
        'height_mm': 92,
        'dpi': 300,
        'background': 'white',
        'format': 'png',
    }
    # Target: 2835x1087. A 2000x500 source becomes 2835x709, centered vertically.
    source = Image.new('RGB', (2000, 500), color=(255, 0, 0))
    buffer = io.BytesIO()
    source.save(buffer, format='PNG')
    out_bytes, _ = postprocess_image(buffer.getvalue(), specs)
    img = Image.open(io.BytesIO(out_bytes))
    assert img.size == (2835, 1087)
    # Top and bottom bands should be white; the center band should be red.
    center_y = img.height // 2
    assert img.getpixel((img.width // 2, center_y)) == (255, 0, 0)
    assert img.getpixel((img.width // 2, 10)) == (255, 255, 255)
    assert img.getpixel((img.width // 2, img.height - 10)) == (255, 255, 255)
