import pytest
from io import BytesIO
from django.urls import reverse
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
class DrawingUploadTests:
    def setup_method(self):
        self.user = User.objects.create_user(email='buyer@example.com', password='pass')
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
        response = self.client.post(url, {'file': image}, format='multipart')
        assert response.status_code == 200
        self.line.refresh_from_db()
        assert self.line.customer_upload
