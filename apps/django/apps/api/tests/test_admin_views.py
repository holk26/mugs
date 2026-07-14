import pytest
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.orders.models import Order, OrderLine
from apps.orders.ai_cleanup import ImageCleanupError
from apps.orders.image_postprocess import ImagePostprocessError
from apps.products.models import Product, ProductVariant


User = get_user_model()


@pytest.fixture
def admin_client():
    user = User.objects.create_superuser(
        email='admin@example.com',
        username='admin',
        password='password',
    )
    token = RefreshToken.for_user(user).access_token
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.fixture
def paid_order_with_upload():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(
        customer_email='test@example.com',
        status='paid',
        total='15.00',
    )
    line = OrderLine.objects.create(
        order=order,
        variant=variant,
        title='Red Mug',
        quantity=1,
        price='15.00',
    )
    line.customer_upload.save('drawing.png', ContentFile(b'fake image data'), save=True)
    return order


def _mock_generate_cleaned_upload(line, provider=None, operator_prompt=None):
    line.processed_upload_prompt = operator_prompt or ''
    line.save(update_fields=['processed_upload_prompt'])


@pytest.mark.django_db
def test_process_line_image_accepts_prompt(admin_client, paid_order_with_upload, settings):
    settings.AI_IMAGE_PROVIDER = 'openai'
    order = paid_order_with_upload
    line = order.lines.first()
    url = f'/api/v1/admin/orders/{order.id}/lines/{line.id}/process-image/'

    with patch(
        'apps.orders.ai_cleanup.generate_cleaned_upload',
        side_effect=_mock_generate_cleaned_upload,
    ) as mock_generate:
        response = admin_client.post(url, {'prompt': 'Make it blue'}, format='json')

    assert response.status_code == 200
    assert response.data['processed_upload_prompt'] == 'Make it blue'
    mock_generate.assert_called_once_with(line, provider='openai', operator_prompt='Make it blue')


@pytest.mark.django_db
def test_process_line_image_omits_prompt(admin_client, paid_order_with_upload, settings):
    settings.AI_IMAGE_PROVIDER = 'openai'
    order = paid_order_with_upload
    line = order.lines.first()
    url = f'/api/v1/admin/orders/{order.id}/lines/{line.id}/process-image/'

    with patch(
        'apps.orders.ai_cleanup.generate_cleaned_upload',
        side_effect=_mock_generate_cleaned_upload,
    ) as mock_generate:
        response = admin_client.post(url, {}, format='json')

    assert response.status_code == 200
    mock_generate.assert_called_once_with(line, provider='openai', operator_prompt='')


@pytest.mark.django_db
def test_process_line_image_empty_prompt(admin_client, paid_order_with_upload, settings):
    settings.AI_IMAGE_PROVIDER = 'openai'
    order = paid_order_with_upload
    line = order.lines.first()
    url = f'/api/v1/admin/orders/{order.id}/lines/{line.id}/process-image/'

    with patch(
        'apps.orders.ai_cleanup.generate_cleaned_upload',
        side_effect=_mock_generate_cleaned_upload,
    ) as mock_generate:
        response = admin_client.post(url, {'prompt': ''}, format='json')

    assert response.status_code == 200
    mock_generate.assert_called_once_with(line, provider='openai', operator_prompt='')


@pytest.mark.django_db
def test_process_line_image_cleanup_error_returns_502(admin_client, paid_order_with_upload, settings):
    settings.AI_IMAGE_PROVIDER = 'openai'
    order = paid_order_with_upload
    line = order.lines.first()
    url = f'/api/v1/admin/orders/{order.id}/lines/{line.id}/process-image/'

    with patch(
        'apps.orders.ai_cleanup.generate_cleaned_upload',
        side_effect=ImageCleanupError('AI provider failed'),
    ) as mock_generate:
        response = admin_client.post(url, {'prompt': 'Make it blue'}, format='json')

    assert response.status_code == 502
    assert response.data['detail'] == 'AI provider failed'
    mock_generate.assert_called_once_with(line, provider='openai', operator_prompt='Make it blue')


@pytest.mark.django_db
def test_process_line_image_returns_502_on_postprocess_error(admin_client, paid_order_with_upload, settings):
    settings.AI_IMAGE_PROVIDER = 'openai'
    order = paid_order_with_upload
    line = order.lines.first()
    url = f'/api/v1/admin/orders/{order.id}/lines/{line.id}/process-image/'

    with patch(
        'apps.orders.ai_cleanup.generate_cleaned_upload',
        side_effect=ImagePostprocessError('Invalid specs'),
    ) as mock_generate:
        response = admin_client.post(url, {'prompt': 'Make it blue'}, format='json')

    assert response.status_code == 502
    assert response.data['detail'] == 'Invalid specs'
    mock_generate.assert_called_once_with(line, provider='openai', operator_prompt='Make it blue')
