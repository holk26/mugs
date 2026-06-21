from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.products.models import Product, Collection
from .serializers import ProductListSerializer, ProductDetailSerializer, CollectionSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(status='active')
    lookup_field = 'handle'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        expand = self.request.query_params.get('expand', '')
        if 'medias' in expand:
            queryset = queryset.prefetch_related('medias')
        if self.action == 'retrieve' or 'variants' in expand:
            queryset = queryset.prefetch_related('variants')
        return queryset


class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    lookup_field = 'handle'

    @action(detail=True, methods=['get'])
    def products(self, request, handle=None):
        collection = self.get_object()
        products = collection.products.filter(status='active')
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
