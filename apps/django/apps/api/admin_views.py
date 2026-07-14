from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.conf import settings
from datetime import timedelta
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
    AdminCollectionSerializer,
    AdminOrderSerializer,
    AdminOrderStatusUpdateSerializer,
    AdminProcessImageSerializer,
    AdminOrderLineProcessedUploadSerializer,
    AdminOrderLineMockupSerializer,
    AdminPrintfulSyncLogSerializer,
    AdminPrintfulWebhookEventSerializer,
    AdminPrintfulStoreProductSerializer,
    AdminPrintfulImportSerializer,
)
from apps.discounts.models import DiscountCode, DiscountUsage
from apps.discounts.serializers import AdminDiscountCodeSerializer, AdminDiscountUsageSerializer
from apps.products.models import Product, ProductVariant, ProductMedia, Collection
from apps.orders.models import Order, OrderLine
from apps.printful.models import PrintfulSyncLog, PrintfulWebhookEvent
from apps.printful.sync import push_order, confirm_printful_order
from apps.api.tasks import sync_printful_catalog
from apps.orders.ai_cleanup import ImageCleanupError
from apps.orders.image_postprocess import ImagePostprocessError
from apps.orders.mockups import generate_line_mockup, MockupError

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


class AdminCollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all().order_by('-created_at')
    serializer_class = AdminCollectionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'handle']
    ordering_fields = ['created_at', 'title']
    lookup_field = 'id'


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

    @action(detail=True, methods=['post'], url_path='printful/push')
    def push_printful(self, request, id=None):
        """Push the order to Printful as a draft for human review."""
        order = self.get_object()
        if order.printful_order_id:
            return Response(
                {'detail': 'Order already pushed to Printful.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            printful_id = push_order(order, confirm=False)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({
            'detail': 'Order pushed to Printful as draft.',
            'printful_order_id': printful_id,
        })

    @action(detail=True, methods=['post'], url_path='printful/confirm')
    def confirm_printful(self, request, id=None):
        """Confirm a Printful draft order so it enters fulfillment."""
        order = self.get_object()
        if not order.printful_order_id:
            return Response(
                {'detail': 'Order has not been pushed to Printful yet.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            confirm_printful_order(order)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        order.refresh_from_db()
        return Response(AdminOrderSerializer(order).data)

    @action(detail=True, methods=['post'], url_path='lines/(?P<line_id>[^/.]+)/process-image')
    def process_line_image(self, request, id=None, line_id=None):
        """Generate an AI-cleaned image for a specific order line.

        Accepts an optional JSON body with:
        - provider: AI provider to use (e.g. 'openai' or 'gemini').
        - prompt: Additional operator instructions for the image cleanup.
        """
        order = self.get_object()
        try:
            line = order.lines.get(id=line_id)
        except OrderLine.DoesNotExist:
            return Response({'detail': 'Line not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not line.customer_upload:
            return Response(
                {'detail': 'This line has no customer upload.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminProcessImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data.get('provider') or getattr(settings, 'AI_IMAGE_PROVIDER', 'openai')
        operator_prompt = serializer.validated_data.get('prompt', '')

        try:
            from apps.orders.ai_cleanup import generate_cleaned_upload
            generate_cleaned_upload(line, provider=provider, operator_prompt=operator_prompt)
        except (ImageCleanupError, ImagePostprocessError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(AdminOrderLineProcessedUploadSerializer(line).data)

    @action(detail=True, methods=['post'], url_path='lines/(?P<line_id>[^/.]+)/mockup')
    def generate_mockup(self, request, id=None, line_id=None):
        """Generate a product preview mockup for a specific order line."""
        order = self.get_object()
        try:
            line = order.lines.get(id=line_id)
        except OrderLine.DoesNotExist:
            return Response({'detail': 'Line not found.'}, status=status.HTTP_404_NOT_FOUND)

        design_source = line.processed_upload or line.customer_upload
        if not design_source:
            return Response(
                {'detail': 'This line has no customer upload or processed upload.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            generate_line_mockup(line)
        except MockupError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(AdminOrderLineMockupSerializer(line).data)


class AdminStatsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        today = timezone.now().date()
        orders_today = Order.objects.filter(created_at__date=today).count()
        active_products = Product.objects.filter(status='active').count()
        last_sync = PrintfulSyncLog.objects.filter(
            status__in=['completed', 'completed_with_errors']
        ).order_by('-finished_at').first()
        return Response({
            'orders_today': orders_today,
            'active_products': active_products,
            'last_sync_at': last_sync.finished_at.isoformat() if last_sync and last_sync.finished_at else None,
        })


class AdminPrintfulViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request):
        from apps.printful.sync import CatalogSync

        log = PrintfulSyncLog.objects.create(status='running')
        try:
            result = CatalogSync().run()
            log.status = 'completed' if not result['errors'] else 'completed_with_errors'
            log.products_created = result['created']
            log.products_updated = result['updated']
            log.errors = result['errors']
        except Exception as exc:
            log.status = 'failed'
            log.errors = [{'error': str(exc)}]
        finally:
            log.finished_at = timezone.now()
            log.save()

        return Response({
            'log_id': str(log.id),
            'status': log.status,
            'created': log.products_created,
            'updated': log.products_updated,
            'errors': log.errors,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='store-products')
    def store_products(self, request):
        from apps.printful.sync import CatalogSync

        search = request.query_params.get('search', '').strip()
        try:
            limit = min(int(request.query_params.get('limit', 100)), 100)
            offset = max(int(request.query_params.get('offset', 0)), 0)
        except ValueError:
            return Response(
                {'detail': 'Invalid pagination parameters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = CatalogSync().client
        response = client.get_store_products(limit=limit, offset=offset)
        products = response.get('result', [])
        paging = response.get('paging', {})

        if search:
            products = [
                p for p in products
                if search.lower() in (p.get('name') or '').lower()
            ]

        serializer = AdminPrintfulStoreProductSerializer(products, many=True)
        return Response({
            'items': serializer.data,
            'total': paging.get('total', len(products)),
            'limit': limit,
            'offset': offset,
        })

    @action(detail=False, methods=['post'], url_path='store-products/import')
    def import_store_product(self, request):
        from apps.printful.sync import CatalogSync

        serializer = AdminPrintfulImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        printful_product_id = serializer.validated_data['printful_product_id']

        try:
            product, created = CatalogSync().sync_product(printful_product_id)
        except Exception as exc:
            return Response(
                {'detail': f'Failed to import Printful product: {exc}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'id': str(product.id),
            'handle': product.handle,
            'title': product.title,
            'created': created,
        }, status=status.HTTP_200_OK)

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
