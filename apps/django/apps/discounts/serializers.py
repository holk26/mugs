from rest_framework import serializers

from apps.discounts.models import DiscountCode, DiscountUsage


class AdminDiscountCodeSerializer(serializers.ModelSerializer):
    usage_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DiscountCode
        fields = [
            'id', 'code', 'description', 'discount_type', 'value', 'currency',
            'min_order_amount', 'max_discount_amount',
            'usage_limit_total', 'usage_limit_per_user',
            'starts_at', 'expires_at',
            'applies_to', 'product_ids', 'collection_ids',
            'is_active', 'usage_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['usage_count']


class AdminDiscountUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountUsage
        fields = ['id', 'discount_code', 'order', 'identifier', 'amount_saved', 'created_at']
