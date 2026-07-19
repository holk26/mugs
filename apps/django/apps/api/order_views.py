from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.orders.models import Order, OrderLine
from .order_serializers import OrderSerializer


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Orders can be created, listed and retrieved, but never updated or
    deleted through the API — a paid order must be immutable for customers."""

    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in ('create', 'upload_drawing', 'order_status'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user).prefetch_related('lines')
        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=['get'], url_path='status')
    def order_status(self, request, pk=None):
        """Lightweight public status check for the post-payment thank-you page.

        Only exposes the order status; the unguessable UUID acts as the
        capability, and no customer data is returned.
        """
        from django.shortcuts import get_object_or_404

        order = get_object_or_404(Order, pk=pk)
        return Response({'id': str(order.id), 'status': order.status})

    @action(detail=True, methods=['post'], url_path='lines/(?P<line_id>[^/.]+)/upload')
    def upload_drawing(self, request, pk=None, line_id=None):
        from django.utils import timezone
        from datetime import timedelta

        # Allow guests to upload by fetching the order directly; the time/status
        # window below prevents abuse of arbitrary order IDs.
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending' or order.created_at < timezone.now() - timedelta(minutes=15):
            return Response({'detail': 'Upload not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            line = order.lines.get(id=line_id)
        except OrderLine.DoesNotExist:
            return Response({'detail': 'Line not found.'}, status=status.HTTP_404_NOT_FOUND)

        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > 10 * 1024 * 1024:
            return Response(
                {'detail': 'File too large. Max 10MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate the actual content, not the declared content_type: the
        # image pipeline (AI cleanup, mockups) only supports real images.
        from PIL import Image

        try:
            image = Image.open(file)
            image.verify()
        except Exception:
            return Response(
                {'detail': 'Invalid image file. Allowed: JPEG, PNG, WEBP.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image.format not in ('JPEG', 'PNG', 'WEBP'):
            return Response(
                {'detail': 'Invalid image file. Allowed: JPEG, PNG, WEBP.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file.seek(0)

        line.customer_upload = file
        line.save()
        return Response({'id': str(line.id), 'customer_upload': line.customer_upload.url})
