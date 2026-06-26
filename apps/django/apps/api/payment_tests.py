import pytest
import stripe
import time
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import User
from apps.products.models import Product, ProductVariant
from apps.orders.models import Order
from apps.payments.models import WebhookEvent


@pytest.mark.django_db
class TestStripeIntent:
    def setup_method(self):
        self.user = User.objects.create_user(
            email='buyer@example.com', username='buyer', password='pass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            user=self.user,
            customer_email='buyer@example.com',
            total='20.00',
            currency='USD',
        )

    @patch('apps.api.payment_views.stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_create):
        mock_create.return_value = MagicMock(id='cs_test', url='https://checkout.stripe.com/test')
        url = reverse('create-checkout-session')
        response = self.client.post(url, {'order_id': str(self.order.id)})
        assert response.status_code == 200
        assert response.data['url'] == 'https://checkout.stripe.com/test'
        self.order.refresh_from_db()
        assert self.order.payment_intent_id == 'cs_test'

        call_kwargs = mock_create.call_args.kwargs
        base = settings.SITE_URL.rstrip('/')
        assert call_kwargs['success_url'].startswith(f'{base}/thanks?order=')
        assert '{CHECKOUT_SESSION_ID}' in call_kwargs['success_url']
        assert call_kwargs['cancel_url'].startswith(f'{base}/checkout?order=')


@pytest.mark.django_db
class TestStripeWebhook:
    def setup_method(self):
        self.user = User.objects.create_user(
            email='buyer@example.com', username='buyer', password='pass'
        )
        self.client = APIClient()
        self.order = Order.objects.create(
            user=self.user,
            customer_email='buyer@example.com',
            total='20.00',
            currency='USD',
        )

    def _event(self, event_id='evt_test_1', payment_intent='pi_test'):
        return {
            'id': event_id,
            'object': 'event',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test',
                    'object': 'checkout.session',
                    'payment_intent': payment_intent,
                    'metadata': {'order_id': str(self.order.id)},
                },
            },
        }

    @patch('apps.api.payment_views.stripe.Webhook.construct_event')
    def test_webhook_marks_order_paid(self, mock_construct):
        mock_construct.return_value = self._event()
        url = reverse('stripe-webhook')
        response = self.client.post(
            url, {}, format='json', HTTP_STRIPE_SIGNATURE='sig_test'
        )
        assert response.status_code == 200
        self.order.refresh_from_db()
        assert self.order.status == 'paid'
        assert self.order.payment_intent_id == 'pi_test'

    @patch('apps.api.payment_views.stripe.Webhook.construct_event')
    def test_webhook_is_idempotent(self, mock_construct):
        event = self._event(event_id='evt_test_2')
        mock_construct.return_value = event
        url = reverse('stripe-webhook')

        response1 = self.client.post(
            url, {}, format='json', HTTP_STRIPE_SIGNATURE='sig_test'
        )
        assert response1.status_code == 200
        assert WebhookEvent.objects.filter(event_id='evt_test_2').count() == 1

        response2 = self.client.post(
            url, {}, format='json', HTTP_STRIPE_SIGNATURE='sig_test'
        )
        assert response2.status_code == 200
        assert WebhookEvent.objects.filter(event_id='evt_test_2').count() == 1
        self.order.refresh_from_db()
        assert self.order.status == 'paid'

    @patch('apps.api.payment_views.stripe.Webhook.construct_event')
    def test_webhook_rejects_invalid_signature(self, mock_construct):
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            'Invalid signature', 'sig'
        )
        url = reverse('stripe-webhook')
        response = self.client.post(url, {}, format='json')
        assert response.status_code == 400
