from decimal import Decimal

import pytest

from apps.api.admin_serializers import AdminOrderLineSerializer
from apps.orders.models import Order, OrderLine
from apps.products.models import Product, ProductVariant


@pytest.fixture
def order_line():
    product = Product.objects.create(handle='mug', title='Mug', price=Decimal('15.00'))
    variant = ProductVariant.objects.create(product=product, title='Red', price=Decimal('15.00'))
    order = Order.objects.create(
        customer_email='test@example.com',
        status='pending',
        total=Decimal('15.00'),
    )
    line = OrderLine.objects.create(
        order=order,
        variant=variant,
        title='Red Mug',
        quantity=1,
        price=Decimal('15.00'),
    )
    return line


@pytest.mark.django_db
def test_admin_order_line_serializer_includes_specs(order_line, settings):
    settings.PRINTFUL_PRINT_WIDTH_MM = 240
    serializer = AdminOrderLineSerializer(order_line)
    assert serializer.data['applied_print_specs']['width_mm'] == 240
