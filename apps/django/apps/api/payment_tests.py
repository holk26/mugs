import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import User
from apps.products.models import Product, ProductVariant
from apps.orders.models import Order


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

    @override_settings(SITE_URL='https://example.com')
    @patch('apps.api.payment_views.stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_create):
        mock_create.return_value = MagicMock(id='cs_test', url='https://checkout.stripe.com/test')
        url = reverse('create-checkout-session')
        response = self.client.post(url, {'order_id': str(self.order.id)})
        assert response.status_code == 200
        assert response.data['url'] == 'https://checkout.stripe.com/test'
        self.order.refresh_from_db()
        assert self.order.payment_intent_id == 'cs_test'

        expected_success = f'https://example.com/thanks/?order={self.order.id}&session_id={{CHECKOUT_SESSION_ID}}'
        expected_cancel = f'https://example.com/checkout/?order={self.order.id}&canceled=1'
        assert mock_create.call_args.kwargs['success_url'] == expected_success
        assert mock_create.call_args.kwargs['cancel_url'] == expected_cancel
