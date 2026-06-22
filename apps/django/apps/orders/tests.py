import pytest
from apps.orders.models import Order, OrderLine
from apps.products.models import Product, ProductVariant


@pytest.mark.django_db
def test_create_order():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')
    assert order.lines.count() == 1
    assert float(order.total) == 15.00
