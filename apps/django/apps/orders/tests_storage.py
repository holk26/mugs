import pytest
from django.core.files.base import ContentFile
from apps.orders.models import Order, OrderLine
from apps.products.models import Product, ProductVariant


@pytest.mark.django_db
def test_customer_upload_uses_s3_storage(settings):
    settings.DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    settings.AWS_S3_ENDPOINT_URL = 'http://minio:9000'

    product = Product.objects.create(handle='mug', title='Mug', price='15.00')
    variant = ProductVariant.objects.create(product=product, title='Red', price='15.00')
    order = Order.objects.create(customer_email='test@example.com', total='15.00')
    line = OrderLine.objects.create(order=order, variant=variant, title='Red Mug', quantity=1, price='15.00')

    line.customer_upload.save('test.png', ContentFile(b'fake-image'))
    assert line.customer_upload.name.startswith('drawings/')
