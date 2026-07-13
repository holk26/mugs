import json
from decimal import Decimal
from unittest.mock import patch

import pytest
import stripe

from apps.discounts.models import DiscountCode, DiscountUsage
from apps.orders.models import Order, OrderLine
from apps.products.models import Product, ProductVariant


@pytest.mark.django_db
@patch('apps.api.payment_views.stripe.Webhook.construct_event')
def test_webhook_handles_stripe_object_payload(mock_construct, client, settings):
    """Stripe's SDK returns StripeObject instances, not plain dicts."""
    settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'

    product = Product.objects.create(handle='mug-test', title='Mug Test', price='8.00')
    variant = ProductVariant.objects.create(product=product, title='11 oz', price='8.00')
    order = Order.objects.create(
        customer_email='test-smoke@example.com',
        customer_name='Test User',
        total='8.00',
        status='pending',
    )
    OrderLine.objects.create(order=order, variant=variant, title='Mug Test', quantity=1, price='8.00')
    discount = DiscountCode.objects.create(
        code='BIENVENIDO', discount_type='percentage', value='10', applies_to='all', is_active=True
    )
    order.discount_code = discount
    order.discount_amount = Decimal('0.80')
    order.save()

    payload = {
        'id': 'evt_test_123',
        'object': 'event',
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': 'cs_test_123',
                'metadata': {'order_id': str(order.id)},
                'shipping_details': {
                    'name': 'Test User',
                    'address': {
                        'line1': '123 Main St',
                        'line2': '',
                        'city': 'Toronto',
                        'state': 'ON',
                        'postal_code': 'M5H 2N2',
                        'country': 'CA',
                    },
                },
            }
        },
    }
    mock_construct.return_value = stripe._util.convert_to_stripe_object(payload)

    response = client.post(
        '/api/v1/payments/stripe/webhook/',
        json.dumps(payload),
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE='sig',
    )

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == 'paid'
    assert order.shipping_address == {
        'name': 'Test User',
        'line1': '123 Main St',
        'line2': '',
        'city': 'Toronto',
        'state': 'ON',
        'postal_code': 'M5H 2N2',
        'country': 'CA',
    }
    usage = DiscountUsage.objects.get(order=order, discount_code=discount)
    assert usage.status == DiscountUsage.STATUS_CONFIRMED
    assert usage.amount_saved == Decimal('0.80')
