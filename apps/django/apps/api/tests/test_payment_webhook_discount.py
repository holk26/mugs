import pytest
from decimal import Decimal
from unittest.mock import patch

from apps.discounts.models import DiscountCode, DiscountUsage
from apps.orders.models import Order, OrderLine
from apps.products.models import Product, ProductVariant


@pytest.mark.django_db
class TestStripeWebhookDiscountConfirmation:
    def setup_method(self):
        self.product = Product.objects.create(handle='mug', title='Mug', price='15.00')
        self.variant = ProductVariant.objects.create(product=self.product, title='Red', price='15.00')
        self.order = Order.objects.create(customer_email='test@example.com', total='15.00')
        OrderLine.objects.create(order=self.order, variant=self.variant, title='Red Mug', quantity=1, price='15.00')
        self.discount = DiscountCode.objects.create(code='SAVE10', discount_type='percentage', value='10', applies_to='all', is_active=True)
        self.order.discount_code = self.discount
        self.order.discount_amount = Decimal('1.50')
        self.order.save()

    @patch('apps.api.payment_views.stripe.Webhook.construct_event')
    def test_webhook_confirms_reserved_usage(self, mock_construct, client, settings):
        mock_construct.return_value = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'metadata': {'order_id': str(self.order.id)},
                    'shipping_details': {
                        'name': 'Test User',
                        'address': {
                            'line1': '123 Main',
                            'city': 'City',
                            'state': 'ST',
                            'postal_code': '12345',
                            'country': 'US',
                        },
                    },
                },
            },
        }
        DiscountUsage.objects.create(
            order=self.order,
            discount_code=self.discount,
            identifier='email:test@example.com',
            status=DiscountUsage.STATUS_RESERVED,
        )
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        response = client.post(
            '/api/v1/payments/stripe/webhook/',
            '',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig',
        )
        assert response.status_code == 200
        usage = DiscountUsage.objects.get(order=self.order, discount_code=self.discount)
        assert usage.status == DiscountUsage.STATUS_CONFIRMED
        assert usage.amount_saved == Decimal('1.50')

    @patch('apps.api.payment_views.stripe.Webhook.construct_event')
    def test_webhook_creates_confirmed_usage_without_reservation(self, mock_construct, client, settings):
        mock_construct.return_value = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'metadata': {'order_id': str(self.order.id)},
                    'shipping_details': {
                        'name': 'Test User',
                        'address': {
                            'line1': '123 Main',
                            'city': 'City',
                            'state': 'ST',
                            'postal_code': '12345',
                            'country': 'US',
                        },
                    },
                },
            },
        }
        assert DiscountUsage.objects.filter(order=self.order, discount_code=self.discount).count() == 0
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        response = client.post(
            '/api/v1/payments/stripe/webhook/',
            '',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig',
        )
        assert response.status_code == 200
        usage = DiscountUsage.objects.get(order=self.order, discount_code=self.discount)
        assert usage.status == DiscountUsage.STATUS_CONFIRMED
        assert usage.amount_saved == Decimal('1.50')

    @patch('apps.api.payment_views.stripe.Webhook.construct_event')
    def test_webhook_idempotent(self, mock_construct, client, settings):
        mock_construct.return_value = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'metadata': {'order_id': str(self.order.id)},
                    'shipping_details': {
                        'name': 'Test User',
                        'address': {
                            'line1': '123 Main',
                            'city': 'City',
                            'state': 'ST',
                            'postal_code': '12345',
                            'country': 'US',
                        },
                    },
                },
            },
        }
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        response = client.post(
            '/api/v1/payments/stripe/webhook/',
            '',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig',
        )
        assert response.status_code == 200

        response = client.post(
            '/api/v1/payments/stripe/webhook/',
            '',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig',
        )
        assert response.status_code == 200
        assert DiscountUsage.objects.filter(order=self.order, discount_code=self.discount).count() == 1
