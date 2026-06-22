import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import User
from apps.products.models import Product, ProductVariant
from apps.orders.models import Order


@pytest.mark.django_db
class StripeIntentTests:
    def setup_method(self):
        self.user = User.objects.create_user(email='buyer@example.com', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            user=self.user,
            customer_email='buyer@example.com',
            total='20.00',
            currency='USD',
        )

    @patch('apps.api.payment_views.stripe.PaymentIntent.create')
    def test_create_intent(self, mock_create):
        mock_create.return_value = MagicMock(id='pi_test', client_secret='pi_test_secret')
        url = reverse('create-payment-intent')
        response = self.client.post(url, {'order_id': str(self.order.id)})
        assert response.status_code == 200
        assert response.data['client_secret'] == 'pi_test_secret'
        self.order.refresh_from_db()
        assert self.order.payment_intent_id == 'pi_test'
