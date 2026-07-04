import base64

from unittest.mock import patch, MagicMock

import pytest
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, APIClient
from apps.api.permissions import IsAdminUser
from apps.api.admin_serializers import AdminProductListSerializer
from apps.api.tasks import sync_printful_catalog
from apps.products.models import Product, ProductVariant
from apps.orders.models import Order, OrderLine
from apps.printful.models import PrintfulSyncLog

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
def test_admin_order_push_printful(admin_client):
    order = Order.objects.create(
        customer_email='a@b.com',
        total=10,
        shipping_address={
            'name': 'Homero',
            'line1': '123 Main St',
            'city': 'Springfield',
            'state': 'IL',
            'postal_code': '62701',
            'country': 'US',
        },
    )
    product = Product.objects.create(handle='mug', title='Mug', price=10)
    variant = ProductVariant.objects.create(
        product=product,
        title='11oz',
        price=10,
        printful_variant_id='12345',
    )
    OrderLine.objects.create(order=order, variant=variant, title='Mug', quantity=1, price=10)

    mock_result = {'result': {'id': 98765, 'status': 'draft'}}
    with patch('apps.printful.sync.PrintfulClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client.create_order.return_value = mock_result
        mock_client_class.return_value = mock_client

        response = admin_client.post(f'/api/v1/admin/orders/{order.id}/printful/push/')

    assert response.status_code == 200
    assert response.json()['printful_order_id'] == '98765'
    order.refresh_from_db()
    assert order.printful_order_id == '98765'
    assert order.printful_status == 'draft'


@pytest.mark.django_db
def test_admin_order_confirm_printful(admin_client):
    order = Order.objects.create(
        customer_email='a@b.com',
        total=10,
        printful_order_id='98765',
        printful_status='draft',
    )

    mock_result = {'result': {'id': 98765, 'status': 'pending'}}
    with patch('apps.printful.sync.PrintfulClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client.confirm_order.return_value = mock_result
        mock_client_class.return_value = mock_client

        response = admin_client.post(f'/api/v1/admin/orders/{order.id}/printful/confirm/')

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.printful_status == 'pending'


@pytest.mark.django_db
def test_admin_order_push_printful_uses_processed_upload(admin_client):
    order = Order.objects.create(
        customer_email='a@b.com',
        total=10,
        shipping_address={
            'name': 'Homero',
            'line1': '123 Main St',
            'city': 'Springfield',
            'state': 'IL',
            'postal_code': '62701',
            'country': 'US',
        },
    )
    product = Product.objects.create(handle='mug', title='Mug', price=10)
    variant = ProductVariant.objects.create(
        product=product,
        title='11oz',
        price=10,
        printful_variant_id='12345',
    )
    line = OrderLine.objects.create(order=order, variant=variant, title='Mug', quantity=1, price=10)
    line.customer_upload = 'drawings/2026/07/03/test.png'
    line.processed_upload = 'processed/2026/07/03/test_cleaned.png'
    line.save()

    mock_result = {'result': {'id': 98765, 'status': 'draft'}}
    with patch('apps.printful.sync.PrintfulClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client.create_order.return_value = mock_result
        mock_client_class.return_value = mock_client

        response = admin_client.post(f'/api/v1/admin/orders/{order.id}/printful/push/')

    assert response.status_code == 200
    call_args = mock_client.create_order.call_args
    call_kwargs = call_args.kwargs
    body = call_kwargs.get('body') or call_args[0][0]
    files = body['items'][0]['files']
    assert any('processed' in f['url'] for f in files)


@pytest.mark.django_db
def test_admin_order_process_image(admin_client):
    order = Order.objects.create(
        customer_email='a@b.com',
        total=10,
    )
    product = Product.objects.create(handle='mug', title='Mug', price=10)
    variant = ProductVariant.objects.create(
        product=product,
        title='11oz',
        price=10,
        printful_variant_id='12345',
    )
    line = OrderLine.objects.create(order=order, variant=variant, title='Mug', quantity=1, price=10)
    line.customer_upload = 'drawings/2026/07/03/test.png'
    line.save()

    with patch('apps.orders.ai_cleanup.generate_cleaned_upload') as mock_cleanup:
        mock_cleanup.return_value = True
        response = admin_client.post(f'/api/v1/admin/orders/{order.id}/lines/{line.id}/process-image/')

    assert response.status_code == 200
    mock_cleanup.assert_called_once_with(line)
