import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.api.permissions import IsAdminUser

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
