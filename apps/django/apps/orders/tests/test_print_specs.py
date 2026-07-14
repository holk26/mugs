import pytest
from django.test import override_settings
from apps.orders.models import Order, OrderLine
from apps.orders.print_specs import get_print_specs
from apps.products.models import Product, ProductVariant


@pytest.fixture
def line_with_product():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    line = OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')
    return line


@pytest.mark.django_db
def test_get_print_specs_uses_global_defaults(line_with_product):
    with override_settings(
        PRINTFUL_PRINT_WIDTH_MM=240,
        PRINTFUL_PRINT_HEIGHT_MM=92,
        PRINTFUL_PRINT_DPI=300,
        PRINTFUL_IMAGE_BACKGROUND='white',
        PRINTFUL_IMAGE_FORMAT='png',
    ):
        specs = get_print_specs(line_with_product)
    assert specs == {
        'width_mm': 240,
        'height_mm': 92,
        'dpi': 300,
        'background': 'white',
        'format': 'png',
    }


@pytest.mark.django_db
def test_get_print_specs_uses_product_overrides(line_with_product):
    product = line_with_product.variant.product
    product.print_width_mm = 200
    product.print_height_mm = 80
    product.print_dpi = 150
    product.image_background = 'transparent'
    product.image_format = 'jpeg'
    product.save()

    with override_settings(
        PRINTFUL_PRINT_WIDTH_MM=240,
        PRINTFUL_PRINT_HEIGHT_MM=92,
        PRINTFUL_PRINT_DPI=300,
        PRINTFUL_IMAGE_BACKGROUND='white',
        PRINTFUL_IMAGE_FORMAT='png',
    ):
        specs = get_print_specs(line_with_product)

    assert specs == {
        'width_mm': 200,
        'height_mm': 80,
        'dpi': 150,
        'background': 'transparent',
        'format': 'jpeg',
    }
