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
