import pytest
from apps.discounts.models import DiscountCode
from apps.orders.models import Order, OrderLine
from apps.products.models import Collection, Product, ProductVariant


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
