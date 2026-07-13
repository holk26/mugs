import os
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from celery.exceptions import MaxRetriesExceededError
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APIClient
from apps.orders.models import Order, OrderLine
from apps.orders.tasks import process_order_images
from apps.orders.ai_cleanup import ImageCleanupError
from apps.products.models import Product, ProductVariant
from apps.users.models import User


@pytest.mark.django_db
def test_create_order():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')
    assert order.lines.count() == 1
    assert float(order.total) == 15.00


@pytest.mark.django_db
class TestDrawingUpload:
    def setup_method(self):
        self.user = User.objects.create_user(
            email='buyer@example.com', username='buyer', password='pass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(
            handle='white-mug',
            title='White glossy mug',
            status='active',
            price='15.00',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            title='11oz',
            sku='MUG-11',
            price='15.00',
        )
        self.order = Order.objects.create(
            user=self.user,
            customer_email='buyer@example.com',
            customer_name='Buyer',
            total='15.00',
        )
        self.line = OrderLine.objects.create(
            order=self.order,
            variant=self.variant,
            title=self.product.title,
            quantity=1,
            price='15.00',
        )

    def test_upload_drawing(self):
        url = reverse('order-upload-drawing', kwargs={'pk': self.order.id, 'line_id': self.line.id})
        image = BytesIO(b'fake-image-data')
        image.content_type = 'image/png'
        response = self.client.post(
            url,
            {'file': image},
            format='multipart',
            HTTP_CONTENT_DISPOSITION='attachment; filename="drawing.png"',
        )
        assert response.status_code == 200
        self.line.refresh_from_db()
        assert self.line.customer_upload

    def test_upload_drawing_creates_media_root(self, tmp_path):
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            url = reverse('order-upload-drawing', kwargs={'pk': self.order.id, 'line_id': self.line.id})
            image = BytesIO(b'fake-image-data')
            image.content_type = 'image/png'
            response = self.client.post(
                url,
                {'file': image},
                format='multipart',
                HTTP_CONTENT_DISPOSITION='attachment; filename="drawing.png"',
            )
            assert response.status_code == 200
            self.line.refresh_from_db()
            assert self.line.customer_upload
            assert os.path.exists(self.line.customer_upload.path)


@pytest.mark.django_db
def test_paid_order_triggers_image_processing_task():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')

    with patch('apps.orders.signals.transaction.on_commit') as mock_on_commit:
        mock_on_commit.side_effect = lambda func: func()
        with patch('apps.orders.signals.process_order_images') as mock_task:
            order.status = 'paid'
            order.save()
            mock_task.delay.assert_called_once_with(order.id)


@pytest.mark.django_db
def test_paid_order_does_not_retrigger_task():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00', status='paid')
    OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')

    with patch('apps.orders.signals.process_order_images') as mock_task:
        order.customer_name = 'Updated'
        order.save()
        mock_task.delay.assert_not_called()


@pytest.mark.django_db
def test_process_order_images_success():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    line = OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')
    line.customer_upload = 'drawings/test.png'
    line.save(update_fields=['customer_upload'])

    with patch('apps.orders.tasks.generate_cleaned_upload') as mock_clean:
        result = process_order_images.run(order.id)
        mock_clean.assert_called_once_with(line, provider='gemini')
        assert result['results'][0]['status'] == 'processed'


@pytest.mark.django_db
def test_process_order_images_per_line_error_then_retry():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    line = OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')
    line.customer_upload = 'drawings/test.png'
    line.save(update_fields=['customer_upload'])

    task = process_order_images
    with patch.object(task, 'retry', side_effect=ImageCleanupError('retry')) as mock_retry:
        with patch('apps.orders.tasks.generate_cleaned_upload', side_effect=ImageCleanupError('AI failed')):
            with pytest.raises(ImageCleanupError):
                task.run(order.id)
    line.refresh_from_db()
    assert 'AI failed' in line.processed_upload_error


@pytest.mark.django_db
def test_process_order_images_order_not_found():
    result = process_order_images.run('00000000-0000-0000-0000-000000000000')
    assert result == {'error': 'Order not found'}


@pytest.mark.django_db
def test_paid_order_does_not_auto_push_when_disabled():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(
        product=product, title='Red', price='15.00', printful_variant_id='123'
    )
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')

    with override_settings(PRINTFUL_AUTO_PUSH=False, PRINTFUL_API_TOKEN='token'):
        with patch('apps.orders.signals.transaction.on_commit') as mock_on_commit:
            mock_on_commit.side_effect = lambda func: func()
            with patch('apps.orders.signals.process_order_images'):
                with patch('apps.orders.signals.push_order') as mock_push:
                    order.status = 'paid'
                    order.save()
                    mock_push.assert_not_called()


@pytest.mark.django_db
def test_paid_order_auto_push_when_enabled():
    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(
        product=product, title='Red', price='15.00', printful_variant_id='123'
    )
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')

    with override_settings(PRINTFUL_AUTO_PUSH=True, PRINTFUL_API_TOKEN='token'):
        with patch('apps.orders.signals.transaction.on_commit') as mock_on_commit:
            mock_on_commit.side_effect = lambda func: func()
            with patch('apps.orders.signals.process_order_images'):
                with patch('apps.orders.signals.push_order') as mock_push:
                    order.status = 'paid'
                    order.save()
                    mock_push.assert_called_once_with(order)
