from rest_framework import serializers
from apps.products.models import Product, ProductVariant, ProductMedia, Collection


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'type', 'url', 'alt', 'order']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'title', 'sku', 'price', 'compare_at_price', 'stock', 'options', 'active']


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'handle', 'title', 'price', 'compare_at_price', 'status', 'medias']

    medias = ProductMediaSerializer(many=True, read_only=True)


class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'handle', 'title', 'description', 'status',
            'tags', 'price', 'compare_at_price', 'medias', 'variants', 'created_at', 'updated_at'
        ]

    medias = ProductMediaSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'handle', 'title', 'description']
