import os
from decimal import Decimal

from rest_framework import serializers
from apps.products.models import Product, ProductVariant, ProductMedia, Collection
from apps.orders.models import Order, OrderLine
from apps.orders.print_specs import get_print_specs
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
    applied_print_specs = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = [
            'id',
            'product_name',
            'variant_name',
            'quantity',
            'unit_price',
            'total_price',
            'applied_print_specs',
            'processed_upload_prompt',
        ]

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

    def get_applied_print_specs(self, obj):
        return get_print_specs(obj)


class AdminOrderSerializer(serializers.ModelSerializer):
    lines = AdminOrderLineSerializer(many=True, read_only=True)
    raw_upload = serializers.SerializerMethodField()
    processed_upload = serializers.SerializerMethodField()
    processed_upload_error = serializers.SerializerMethodField()
    mockup = serializers.SerializerMethodField()
    discount_code = serializers.SlugRelatedField(read_only=True, slug_field='code')

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'customer_email', 'customer_name',
            'total', 'currency', 'shipping_address', 'raw_upload', 'processed_upload',
            'processed_upload_error', 'mockup', 'discount_code', 'discount_amount',
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

    def get_processed_upload_error(self, order: Order):
        for line in order.lines.all():
            if line.processed_upload_error:
                return line.processed_upload_error
        return None

    def get_mockup(self, order: Order):
        for line in order.lines.all():
            if line.mockup:
                return _upload_representation(line.mockup)
        return None


class AdminProcessImageSerializer(serializers.Serializer):
    provider = serializers.CharField(required=False, allow_blank=True)
    prompt = serializers.CharField(required=False, allow_blank=True)


class AdminOrderLineProcessedUploadSerializer(serializers.ModelSerializer):
    processed_upload = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = [
            'id',
            'processed_upload',
            'processed_upload_prompt',
            'processed_upload_generated_at',
        ]

    def get_processed_upload(self, line: OrderLine):
        return _upload_representation(line.processed_upload)


class AdminOrderLineMockupSerializer(serializers.ModelSerializer):
    customer_upload = serializers.SerializerMethodField()
    processed_upload = serializers.SerializerMethodField()
    mockup = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    variant_name = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = [
            'id', 'product_name', 'variant_name', 'quantity',
            'unit_price', 'total_price',
            'customer_upload', 'processed_upload', 'mockup',
            'processed_upload_error',
        ]

    def get_customer_upload(self, line: OrderLine):
        return _upload_representation(line.customer_upload)

    def get_processed_upload(self, line: OrderLine):
        return _upload_representation(line.processed_upload)

    def get_mockup(self, line: OrderLine):
        return _upload_representation(line.mockup)

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


class AdminPrintfulStoreProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    thumbnail_url = serializers.URLField(required=False, allow_blank=True)
    synced = serializers.IntegerField(required=False)


class AdminPrintfulImportSerializer(serializers.Serializer):
    printful_product_id = serializers.IntegerField(min_value=1)
