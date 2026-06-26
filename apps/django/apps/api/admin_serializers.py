import os
from decimal import Decimal

from rest_framework import serializers
from apps.products.models import Product, ProductVariant, ProductMedia, Collection
from apps.orders.models import Order, OrderLine
from apps.printful.models import PrintfulSyncLog, PrintfulWebhookEvent
from django.contrib.auth import get_user_model

User = get_user_model()


def _upload_representation(field):
    if field and field.name:
        return {"file": field.url, "name": os.path.basename(field.name)}
    return None


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']


class AdminProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'type', 'file', 'url', 'alt', 'order']
        extra_kwargs = {
            'url': {'required': False, 'allow_blank': True},
        }


class AdminCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'handle', 'title', 'description', 'created_at', 'updated_at']


class AdminProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'title', 'sku', 'price', 'compare_at_price', 'stock',
            'options', 'active', 'printful_sync_variant_id', 'printful_variant_id',
            'created_at', 'updated_at'
        ]


class AdminProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'handle', 'title', 'price', 'status', 'created_at']


class AdminProductDetailSerializer(serializers.ModelSerializer):
    medias = AdminProductMediaSerializer(many=True, read_only=True)
    variants = AdminProductVariantSerializer(many=True, read_only=True)
    collections = serializers.PrimaryKeyRelatedField(many=True, queryset=Collection.objects.all(), required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'handle', 'title', 'description', 'status',
            'tags', 'price', 'compare_at_price', 'collections',
            'medias', 'variants', 'created_at', 'updated_at'
        ]


class AdminOrderLineSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    variant_name = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = ['product_name', 'variant_name', 'quantity', 'unit_price', 'total_price']

    def get_product_name(self, line: OrderLine) -> str:
        if line.variant and line.variant.product:
            return line.variant.product.title
        return line.title or ''

    def get_variant_name(self, line: OrderLine) -> str:
        if line.variant:
            return line.variant.title or ''
        return ''

    def get_unit_price(self, line: OrderLine) -> str:
        return str(line.price.quantize(Decimal('0.01')))

    def get_total_price(self, line: OrderLine) -> str:
        return str((line.price * line.quantity).quantize(Decimal('0.01')))


class AdminOrderSerializer(serializers.ModelSerializer):
    lines = AdminOrderLineSerializer(many=True, read_only=True)
    raw_upload = serializers.SerializerMethodField()
    processed_upload = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'customer_email', 'customer_name',
            'total', 'currency', 'shipping_address', 'raw_upload', 'processed_upload',
            'lines', 'printful_order_id', 'printful_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total', 'printful_order_id', 'printful_status']

    def get_raw_upload(self, order: Order):
        for line in order.lines.all():
            if line.customer_upload:
                return _upload_representation(line.customer_upload)
        return None

    def get_processed_upload(self, order: Order):
        for line in order.lines.all():
            if line.processed_upload:
                return _upload_representation(line.processed_upload)
        return None


class AdminOrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']


class AdminPrintfulSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintfulSyncLog
        fields = ['id', 'started_at', 'finished_at', 'status', 'products_created', 'products_updated', 'errors']


class AdminPrintfulWebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintfulWebhookEvent
        fields = ['id', 'event_type', 'payload', 'processed', 'created_at']
