import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, APIClient
from apps.api.permissions import IsAdminUser
from apps.api.admin_serializers import AdminProductListSerializer
from apps.api.tasks import sync_printful_catalog
from apps.products.models import Product
from apps.orders.models import Order
from apps.printful.models import PrintfulSyncLog
from apps.printful.sync import push_order, confirm_printful_order

User = get_user_model()


@pytest.mark.django_db
def test_is_admin_user_permission():
    factory = APIRequestFactory()
    admin = User.objects.create_user(email='admin@test.com', username='admin@test.com', password='pass', is_staff=True)
    regular = User.objects.create_user(email='user@test.com', username='user@test.com', password='pass', is_staff=False)

    permission = IsAdminUser()

    admin_request = factory.get('/')
    admin_request.user = admin
    assert permission.has_permission(admin_request, None) is True

    regular_request = factory.get('/')
    regular_request.user = regular
    assert permission.has_permission(regular_request, None) is False


@pytest.mark.django_db
def test_signin_returns_user_and_is_staff(client):
    User.objects.create_user(email='admin@test.com', username='admin@test.com', password='pass', is_staff=True)
    response = client.post('/api/v1/auth/signin/', {'email': 'admin@test.com', 'password': 'pass'}, content_type='application/json')
    assert response.status_code == 200
    assert response.json()['user']['email'] == 'admin@test.com'
    assert response.json()['user']['is_staff'] is True


@pytest.mark.django_db
def test_admin_product_list_serializer():
    product = Product.objects.create(handle='test-mug', title='Test Mug', price=15.00, status='active')
    serializer = AdminProductListSerializer(product)
    assert serializer.data['title'] == 'Test Mug'


@pytest.mark.django_db
def test_sync_printful_catalog_task_creates_log():
    mock_sync = MagicMock()
    mock_sync.run.return_value = {'created': 1, 'updated': 2, 'errors': []}
    with patch('apps.api.tasks.CatalogSync', return_value=mock_sync):
        result = sync_printful_catalog()
    assert PrintfulSyncLog.objects.count() == 1
    assert result['created'] == 1
    assert result['updated'] == 2

import uuid
from rest_framework.test import APIClient
from apps.products.models import Product
from apps.orders.models import Order

@pytest.fixture
def admin_client():
    user = User.objects.create_user(email='admin@test.com', username='admin@test.com', password='pass', is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def regular_client():
    user = User.objects.create_user(email='user@test.com', username='user@test.com', password='pass', is_staff=False)
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_admin_products_list_requires_admin(admin_client, regular_client):
    Product.objects.create(handle='mug-1', title='Mug 1', price=10, status='active')
    assert admin_client.get('/api/v1/admin/products/').status_code == 200
    assert regular_client.get('/api/v1/admin/products/').status_code == 403

@pytest.mark.django_db
def test_admin_orders_update_status(admin_client):
    order = Order.objects.create(customer_email='a@b.com', total=10)
    response = admin_client.patch(f'/api/v1/admin/orders/{order.id}/status/', {'status': 'paid'}, content_type='application/json')
    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == 'paid'


@pytest.mark.django_db
@patch('apps.api.admin_views.push_order')
def test_admin_push_order_to_printful(mock_push, admin_client):
    mock_push.return_value = 'pf_12345'
    order = Order.objects.create(customer_email='a@b.com', total=10, status='paid')
    response = admin_client.post(f'/api/v1/admin/orders/{order.id}/printful/push/')
    assert response.status_code == 200
    assert response.json()['printful_order_id'] == 'pf_12345'
    mock_push.assert_called_once_with(order, confirm=False)


@pytest.mark.django_db
def test_admin_push_order_to_printful_already_pushed(admin_client):
    order = Order.objects.create(
        customer_email='a@b.com', total=10, status='paid',
        printful_order_id='pf_existing', printful_status='draft'
    )
    response = admin_client.post(f'/api/v1/admin/orders/{order.id}/printful/push/')
    assert response.status_code == 400
    assert 'already pushed' in response.json()['detail'].lower()


@pytest.mark.django_db
@patch('apps.api.admin_views.confirm_printful_order')
def test_admin_confirm_printful_order(mock_confirm, admin_client):
    mock_confirm.return_value = 'pending'
    order = Order.objects.create(
        customer_email='a@b.com', total=10, status='paid',
        printful_order_id='pf_12345', printful_status='draft'
    )
    response = admin_client.post(f'/api/v1/admin/orders/{order.id}/printful/confirm/')
    assert response.status_code == 200
    mock_confirm.assert_called_once_with(order)
