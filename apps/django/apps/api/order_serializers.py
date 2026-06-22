from rest_framework import serializers
from apps.orders.models import Order, OrderLine
from apps.products.models import ProductVariant


class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ['id', 'variant', 'title', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'customer_email', 'customer_name',
            'total', 'currency', 'shipping_address', 'lines',
            'printful_order_id', 'printful_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'total', 'printful_order_id', 'printful_status']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        order = Order.objects.create(**validated_data)
        total = 0
        for line_data in lines_data:
            variant = line_data.get('variant')
            line = OrderLine.objects.create(
                order=order,
                variant=variant,
                title=variant.title if variant else line_data.get('title', ''),
                quantity=line_data.get('quantity', 1),
                price=variant.price if variant else line_data.get('price', 0),
            )
            total += line.price * line.quantity
        order.total = total
        order.save()
        return order
