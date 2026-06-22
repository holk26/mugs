from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.orders.models import Order, OrderLine
from .order_serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in ('create', 'upload_drawing'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user).prefetch_related('lines')
        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=['post'], url_path='lines/(?P<line_id>[^/.]+)/upload')
    def upload_drawing(self, request, pk=None, line_id=None):
        from django.utils import timezone
        from datetime import timedelta

        order = self.get_object()
        if order.status != 'pending' or order.created_at < timezone.now() - timedelta(minutes=15):
            return Response({'detail': 'Upload not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            line = order.lines.get(id=line_id)
        except OrderLine.DoesNotExist:
            return Response({'detail': 'Line not found.'}, status=status.HTTP_404_NOT_FOUND)

        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        valid_types = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
        if file.content_type not in valid_types:
            return Response(
                {'detail': f'Invalid file type. Allowed: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file.size > 10 * 1024 * 1024:
            return Response(
                {'detail': 'File too large. Max 10MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        line.customer_upload = file
        line.save()
        return Response({'id': str(line.id), 'customer_upload': line.customer_upload.url})
