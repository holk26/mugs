import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderLine
from apps.products.models import Product, ProductVariant

User = get_user_model()


@pytest.mark.django_db
class TestOrderViewSetPermissions:
    def setup_method(self):
        self.user = User.objects.create_user(email='buyer@example.com', username='buyer', password='pass')
        self.other = User.objects.create_user(email='other@example.com', username='other', password='pass')
        product = Product.objects.create(handle='mug', title='Mug', price='15.00')
        variant = ProductVariant.objects.create(product=product, title='11oz', price='15.00')
        self.order = Order.objects.create(
            user=self.user, customer_email='buyer@example.com', total='15.00', status='paid'
        )
        OrderLine.objects.create(order=self.order, variant=variant, title='Mug', quantity=1, price='15.00')
        self.client = APIClient()

    def test_owner_cannot_delete_order(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/v1/orders/{self.order.id}/')
        assert response.status_code == 405
        assert Order.objects.filter(id=self.order.id).exists()

    def test_owner_cannot_update_order(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/v1/orders/{self.order.id}/',
            {'customer_name': 'Changed'},
            content_type='application/json',
        )
        assert response.status_code == 405

    def test_user_cannot_retrieve_others_order(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(f'/api/v1/orders/{self.order.id}/')
        assert response.status_code == 404

    def test_owner_can_retrieve_own_order(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/orders/{self.order.id}/')
        assert response.status_code == 200

    def test_list_only_shows_own_orders(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get('/api/v1/orders/')
        assert response.status_code == 200
        assert response.json()['results'] == []
