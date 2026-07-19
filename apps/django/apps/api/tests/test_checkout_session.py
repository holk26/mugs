import pytest
from unittest.mock import patch, MagicMock

from apps.orders.models import Order, OrderLine
from apps.products.models import Product, ProductVariant


def _make_order(email='buyer@example.com', quantity=3, price='15.00'):
    product = Product.objects.create(handle='mug', title='Mug', price=price)
    variant = ProductVariant.objects.create(product=product, title='11oz', price=price)
    order = Order.objects.create(customer_email=email, total='0')
    OrderLine.objects.create(
        order=order, variant=variant, title='Mug 11oz', quantity=quantity, price=price
    )
    return order


def _mock_session():
    session = MagicMock()
    session.id = 'cs_test_123'
    session.url = 'https://checkout.stripe.com/pay/cs_test_123'
    return session


@pytest.mark.django_db
class TestCreateCheckoutSession:
    @patch('apps.api.payment_views.stripe.checkout.Session.create')
    def test_unit_amount_is_not_multiplied_by_quantity(self, mock_create, client):
        """Regression test: Stripe must receive the single-unit price; it
        multiplies by quantity itself. 3 x $15 must total $45, not $135."""
        mock_create.return_value = _mock_session()
        order = _make_order(quantity=3, price='15.00')

        response = client.post(
            '/api/v1/payments/stripe/checkout/',
            {'order_id': str(order.id), 'email': 'buyer@example.com'},
            content_type='application/json',
        )

        assert response.status_code == 200
        line_items = mock_create.call_args.kwargs['line_items']
        assert line_items[0]['price_data']['unit_amount'] == 1500
        assert line_items[0]['quantity'] == 3

    @patch('apps.api.payment_views.stripe.checkout.Session.create')
    def test_guest_must_provide_matching_email(self, mock_create, client):
        mock_create.return_value = _mock_session()
        order = _make_order()

        response = client.post(
            '/api/v1/payments/stripe/checkout/',
            {'order_id': str(order.id), 'email': 'someone-else@example.com'},
            content_type='application/json',
        )
        assert response.status_code == 404
        mock_create.assert_not_called()

    @patch('apps.api.payment_views.stripe.checkout.Session.create')
    def test_guest_without_email_cannot_checkout(self, mock_create, client):
        mock_create.return_value = _mock_session()
        order = _make_order()

        response = client.post(
            '/api/v1/payments/stripe/checkout/',
            {'order_id': str(order.id)},
            content_type='application/json',
        )
        assert response.status_code == 404
        mock_create.assert_not_called()


@pytest.mark.django_db
class TestStripeWebhookIdempotency:
    @patch('apps.api.payment_views.stripe.Webhook.construct_event')
    def test_duplicate_event_is_not_reprocessed(self, mock_construct, client, settings):
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        order = _make_order(quantity=1)
        mock_construct.return_value = {
            'id': 'evt_123',
            'type': 'checkout.session.completed',
            'data': {'object': {'metadata': {'order_id': str(order.id)}}},
        }

        first = client.post('/api/v1/payments/stripe/webhook/', '', content_type='application/json', HTTP_STRIPE_SIGNATURE='sig')
        assert first.status_code == 200
        order.refresh_from_db()
        assert order.status == 'paid'

        # Simulate a Stripe retry with the same event id.
        order.status = 'pending'
        order.save(update_fields=['status'])
        second = client.post('/api/v1/payments/stripe/webhook/', '', content_type='application/json', HTTP_STRIPE_SIGNATURE='sig')
        assert second.status_code == 200
        assert second.json() == {'status': 'duplicate'}
        order.refresh_from_db()
        assert order.status == 'pending'
