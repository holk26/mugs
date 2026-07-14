import pytest
from apps.products.models import Product


@pytest.mark.django_db
def test_create_product():
    product = Product.objects.create(
        handle='test-mug',
        title='Test Mug',
        price='19.99'
    )
    assert product.handle == 'test-mug'
    assert str(product.title) == 'Test Mug'


@pytest.mark.django_db
def test_product_print_spec_defaults():
    product = Product.objects.create(title='Mug', handle='mug')
    assert product.print_width_mm is None
    assert product.print_height_mm is None
    assert product.print_dpi == 0
    assert product.image_background == ''
    assert product.image_format == ''
