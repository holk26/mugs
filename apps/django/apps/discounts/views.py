from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.discounts.models import DiscountCode, DiscountUsage
from apps.orders.models import Order


def _get_order(order_id):
    try:
        return Order.objects.get(id=order_id)
    except (Order.DoesNotExist, ValueError):
        return None


def _identifier_from_request(request):
    if request.user.is_authenticated:
        return str(request.user.id)
    return request.data.get('email', '').strip().lower()


def _recalculate_order_total(order):
    total = sum(line.price * line.quantity for line in order.lines.all())
    order.total = total - (order.discount_amount or Decimal('0'))
    if order.total < 0:
        order.total = Decimal('0')
    order.save(update_fields=['total', 'discount_amount', 'discount_code'])


@api_view(['POST'])
@permission_classes([AllowAny])
def apply_discount(request):
    code = request.data.get('code', '').strip().upper()
    order_id = request.data.get('order_id')

    if not code or not order_id:
        return Response({'detail': 'Code and order_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

    order = _get_order(order_id)
    if not order:
        return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if order.status != 'pending':
        return Response({'detail': 'Discount can only be applied to pending orders.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        discount = DiscountCode.objects.get(code=code, is_active=True)
    except DiscountCode.DoesNotExist:
        return Response({'detail': 'Invalid discount code.'}, status=status.HTTP_404_NOT_FOUND)

    order_total = sum(line.price * line.quantity for line in order.lines.all())

    is_valid, message = discount.is_valid(
        order_total=order_total,
        user=request.user,
        email=_identifier_from_request(request),
    )
    if not is_valid:
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)

    discount_amount = discount.calculate_discount(order_total)

    with transaction.atomic():
        order.discount_code = discount
        order.discount_amount = discount_amount
        _recalculate_order_total(order)

    return Response({
        'discount_code': discount.code,
        'discount_type': discount.discount_type,
        'value': str(discount.value),
        'discount_amount': str(discount_amount),
        'order_total': str(order.total),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def remove_discount(request):
    order_id = request.data.get('order_id')
    if not order_id:
        return Response({'detail': 'order_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    order = _get_order(order_id)
    if not order:
        return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if order.status != 'pending':
        return Response({'detail': 'Discount can only be removed from pending orders.'}, status=status.HTTP_400_BAD_REQUEST)

    order.discount_code = None
    order.discount_amount = Decimal('0')
    _recalculate_order_total(order)

    return Response({
        'discount_code': None,
        'discount_amount': '0.00',
        'order_total': str(order.total),
    })
