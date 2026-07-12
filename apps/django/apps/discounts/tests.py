import pytest
from pytest_django.asserts import assertNumQueries

from apps.discounts.models import DiscountCode, DiscountUsage
from apps.orders.models import Order, OrderLine
from apps.products.models import Collection, Product, ProductVariant


@pytest.mark.django_db
class TestApplyDiscountView:
    def setup_method(self):
        self.product = Product.objects.create(
            handle='mug',
            title='Mug',
            price='15.00',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            title='Red',
            price='15.00',
        )
        self.order = Order.objects.create(
            customer_email='test@example.com',
            total='15.00',
        )
        OrderLine.objects.create(
            order=self.order,
            variant=self.variant,
            title='Red Mug',
            quantity=1,
            price='15.00',
        )
        self.discount = DiscountCode.objects.create(
            code='SAVE10',
            discount_type='percentage',
            value='10',
            applies_to='all',
            is_active=True,
        )

    def test_apply_discount_without_email_returns_404(self, client):
        response = client.post(
            '/api/v1/discounts/apply',
            {'order_id': str(self.order.id), 'code': 'SAVE10'},
            content_type='application/json',
        )
        assert response.status_code == 404
        assert 'cannot be modified' in response.json()['detail']

    def test_apply_discount_with_matching_email_succeeds(self, client):
        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'SAVE10',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert response.json()['discount_code'] == 'SAVE10'
        assert response.json()['discount_amount'] == '1.5000'

    def test_apply_discount_with_wrong_email_returns_404(self, client):
        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'SAVE10',
                'email': 'other@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 404

    def test_remove_discount_with_matching_email_succeeds(self, client):
        self.order.discount_code = self.discount
        self.order.discount_amount = 1.50
        self.order.save()

        response = client.post(
            '/api/v1/discounts/remove',
            {'order_id': str(self.order.id), 'email': 'test@example.com'},
            content_type='application/json',
        )
        assert response.status_code == 200
        assert response.json()['discount_amount'] == '0.00'

    def test_apply_discount_creates_reserved_usage(self, client):
        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'SAVE10',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        usage = self.order.discount_usages.get()
        assert usage.status == 'reserved'
        assert usage.identifier == 'email:test@example.com'

    def test_apply_discount_idempotent(self, client):
        payload = {
            'order_id': str(self.order.id),
            'code': 'SAVE10',
            'email': 'test@example.com',
        }
        response = client.post('/api/v1/discounts/apply', payload, content_type='application/json')
        assert response.status_code == 200

        response = client.post('/api/v1/discounts/apply', payload, content_type='application/json')
        assert response.status_code == 200
        assert self.order.discount_usages.count() == 1

    def test_per_user_usage_limit_by_email(self, client):
        self.discount.usage_limit_per_user = 1
        self.discount.save()

        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'SAVE10',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 200

        second_order = Order.objects.create(
            customer_email='test@example.com',
            total='15.00',
        )
        OrderLine.objects.create(
            order=second_order,
            variant=self.variant,
            title='Red Mug',
            quantity=1,
            price='15.00',
        )
        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(second_order.id),
                'code': 'SAVE10',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'maximum number of times' in response.json()['detail'].lower()

    def test_apply_discount_respects_total_usage_limit(self, client):
        self.discount.usage_limit_total = 1
        self.discount.save()

        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'SAVE10',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 200

        second_order = Order.objects.create(
            customer_email='other@example.com',
            total='15.00',
        )
        OrderLine.objects.create(
            order=second_order,
            variant=self.variant,
            title='Red Mug',
            quantity=1,
            price='15.00',
        )
        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(second_order.id),
                'code': 'SAVE10',
                'email': 'other@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'usage limit' in response.json()['detail'].lower()

    def test_remove_discount_deletes_reserved_usage(self, client):
        client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'SAVE10',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert self.order.discount_usages.count() == 1

        response = client.post(
            '/api/v1/discounts/remove',
            {'order_id': str(self.order.id), 'email': 'test@example.com'},
            content_type='application/json',
        )
        assert response.status_code == 200
        assert self.order.discount_usages.count() == 0

    def test_apply_discount_releases_previous_reservation(self, client):
        discount_a = DiscountCode.objects.create(
            code='CODEA',
            discount_type='percentage',
            value='10',
            applies_to='all',
            is_active=True,
        )
        discount_b = DiscountCode.objects.create(
            code='CODEB',
            discount_type='percentage',
            value='20',
            applies_to='all',
            is_active=True,
        )

        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'CODEA',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert DiscountUsage.objects.filter(discount_code=discount_a).count() == 1

        response = client.post(
            '/api/v1/discounts/apply',
            {
                'order_id': str(self.order.id),
                'code': 'CODEB',
                'email': 'test@example.com',
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert DiscountUsage.objects.filter(discount_code=discount_a).count() == 0
        assert DiscountUsage.objects.filter(discount_code=discount_b).count() == 1


@pytest.mark.django_db
class TestDiscountCodeAppliesToOrder:
    def setup_method(self):
        self.product = Product.objects.create(
            handle='mug',
            title='Mug',
            price='15.00',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            title='Red',
            price='15.00',
        )
        self.order = Order.objects.create(
            customer_email='test@example.com',
            total='15.00',
        )
        OrderLine.objects.create(
            order=self.order,
            variant=self.variant,
            title='Red Mug',
            quantity=1,
            price='15.00',
        )

    def test_applies_to_all_returns_true(self):
        discount = DiscountCode.objects.create(
            code='ALL',
            discount_type='percentage',
            value='10',
            applies_to='all',
        )
        assert discount.applies_to_order(self.order) is True

    def test_applies_to_products_with_matching_product(self):
        discount = DiscountCode.objects.create(
            code='PRODUCT',
            discount_type='percentage',
            value='10',
            applies_to='products',
            product_ids=[str(self.product.id)],
        )
        assert discount.applies_to_order(self.order) is True

    def test_applies_to_products_without_matching_product(self):
        other_product = Product.objects.create(
            handle='other-mug',
            title='Other Mug',
            price='20.00',
        )
        discount = DiscountCode.objects.create(
            code='PRODUCT',
            discount_type='percentage',
            value='10',
            applies_to='products',
            product_ids=[str(other_product.id)],
        )
        assert discount.applies_to_order(self.order) is False

    def test_applies_to_collections_with_matching_collection(self):
        collection = Collection.objects.create(
            handle='featured',
            title='Featured',
        )
        collection.products.add(self.product)
        discount = DiscountCode.objects.create(
            code='COLLECTION',
            discount_type='percentage',
            value='10',
            applies_to='collections',
            collection_ids=[str(collection.id)],
        )
        assert discount.applies_to_order(self.order) is True

    def test_applies_to_collections_without_matching_collection(self):
        other_collection = Collection.objects.create(
            handle='other',
            title='Other',
        )
        discount = DiscountCode.objects.create(
            code='COLLECTION',
            discount_type='percentage',
            value='10',
            applies_to='collections',
            collection_ids=[str(other_collection.id)],
        )
        assert discount.applies_to_order(self.order) is False

    def test_applies_to_products_query_count(self):
        discount = DiscountCode.objects.create(
            code='PRODUCT',
            discount_type='percentage',
            value='10',
            applies_to='products',
            product_ids=[str(self.product.id)],
        )
        with assertNumQueries(1):
            discount.applies_to_order(self.order)

    def test_applies_to_collections_query_count(self):
        collection = Collection.objects.create(
            handle='featured',
            title='Featured',
        )
        collection.products.add(self.product)
        discount = DiscountCode.objects.create(
            code='COLLECTION',
            discount_type='percentage',
            value='10',
            applies_to='collections',
            collection_ids=[str(collection.id)],
        )
        with assertNumQueries(2):
            discount.applies_to_order(self.order)
