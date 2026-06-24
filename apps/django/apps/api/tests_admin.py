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
