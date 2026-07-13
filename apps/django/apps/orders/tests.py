import os
import shutil
import pytest
from io import BytesIO
from unittest.mock import patch
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from apps.orders.models import Order, OrderLine
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

    def teardown_method(self):
        media_root = settings.MEDIA_ROOT
        if os.path.isdir(media_root):
            shutil.rmtree(media_root)

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

    def test_upload_drawing_creates_media_root(self):
        media_root = settings.MEDIA_ROOT
        if os.path.isdir(media_root):
            shutil.rmtree(media_root)
        assert not os.path.exists(media_root)

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

    with patch('apps.orders.signals.process_order_images') as mock_task:
        order.status = 'paid'
        order.save()
        mock_task.delay.assert_called_once_with(order.id)
