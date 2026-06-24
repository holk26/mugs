from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from apps.api.permissions import IsAdminUser
from apps.api.pagination import StandardResultsSetPagination
from apps.api.admin_serializers import (
    AdminUserSerializer,
    AdminProductListSerializer,
    AdminProductDetailSerializer,
    AdminProductVariantSerializer,
    AdminProductMediaSerializer,
    AdminOrderSerializer,
    AdminOrderStatusUpdateSerializer,
    AdminPrintfulSyncLogSerializer,
    AdminPrintfulWebhookEventSerializer,
)
from apps.products.models import Product, ProductVariant, ProductMedia
from apps.orders.models import Order
from apps.printful.models import PrintfulSyncLog, PrintfulWebhookEvent
from apps.api.tasks import sync_printful_catalog

User = get_user_model()


class AdminPagination(StandardResultsSetPagination):
    page_size_query_param = 'page_size'


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email']


class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'handle', 'description']
    ordering_fields = ['created_at', 'title', 'price']
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminProductListSerializer
        return AdminProductDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('medias', 'variants', 'collections')
        return queryset


class AdminProductVariantViewSet(viewsets.ModelViewSet):
    serializer_class = AdminProductVariantSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def get_queryset(self):
        return ProductVariant.objects.filter(product_id=self.kwargs['product_id'])

    def perform_create(self, serializer):
        product = Product.objects.get(id=self.kwargs['product_id'])
        serializer.save(product=product)


class AdminProductMediaViewSet(viewsets.ModelViewSet):
    serializer_class = AdminProductMediaSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def get_queryset(self):
        return ProductMedia.objects.filter(product_id=self.kwargs['product_id'])

    def perform_create(self, serializer):
        product = Product.objects.get(id=self.kwargs['product_id'])
        serializer.save(product=product)


class AdminOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['customer_email', 'customer_name', 'id']
    ordering_fields = ['created_at', 'total', 'status']
    lookup_field = 'id'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('lines')

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, id=None):
        order = self.get_object()
        serializer = AdminOrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminOrderSerializer(order).data)


class AdminPrintfulViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request):
        task = sync_printful_catalog.delay()
        return Response({'task_id': task.id, 'status': 'queued'}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], url_path='logs')
    def logs(self, request):
        queryset = PrintfulSyncLog.objects.all().order_by('-started_at')
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminPrintfulSyncLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='webhooks')
    def webhooks(self, request):
        queryset = PrintfulWebhookEvent.objects.all().order_by('-created_at')
        paginator = AdminPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminPrintfulWebhookEventSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
