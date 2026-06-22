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
