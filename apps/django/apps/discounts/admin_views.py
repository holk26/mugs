from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from apps.api.permissions import IsAdminUser
from apps.api.pagination import StandardResultsSetPagination
from apps.discounts.models import DiscountCode, DiscountUsage
from apps.discounts.serializers import AdminDiscountCodeSerializer, AdminDiscountUsageSerializer


class AdminDiscountCodeViewSet(viewsets.ModelViewSet):
    queryset = DiscountCode.objects.annotate(
        _usage_count=Count('usages')
    ).order_by('-created_at')
    serializer_class = AdminDiscountCodeSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'description']
    ordering_fields = ['created_at', 'code', 'starts_at', 'expires_at']
    lookup_field = 'id'

    @action(detail=True, methods=['get'], url_path='usages')
    def usages(self, request, id=None):
        discount = self.get_object()
        queryset = discount.usages.all().order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminDiscountUsageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
