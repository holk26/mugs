from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.discounts.models import DiscountCode, DiscountUsage
from apps.orders.models import Order


MAX_COUPON_ATTEMPTS_PER_MINUTE = 30


def _rate_limit_key(identifier: str) -> str:
    return f'discount:rate:{identifier}'


def _check_rate_limit(identifier: str) -> bool:
    key = _rate_limit_key(identifier)
    try:
        attempts = cache.get(key, 0)
        if attempts >= MAX_COUPON_ATTEMPTS_PER_MINUTE:
            return False
        cache.set(key, attempts + 1, timeout=60)
    except Exception:
        pass
    return True


def _get_order(order_id):
    try:
        return Order.objects.get(id=order_id)
    except (Order.DoesNotExist, ValueError):
        return None


def _identifier_from_request(request):
    if request.user.is_authenticated:
        return str(request.user.id)
    return request.data.get('email', '').strip().lower()


def _client_identifier(request) -> str:
    """Return a stable identifier for rate limiting and ownership checks."""
    if request.user.is_authenticated:
        return f'user:{request.user.id}'
    email = request.data.get('email', '').strip().lower()
    if email:
        return f'email:{email}'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return f'ip:{ip}'


def _can_manage_order(order: Order, request) -> bool:
    """Only allow modifying pending orders owned by the same identifier."""
    if order.status != 'pending':
        return False

    if order.user_id and request.user.is_authenticated:
        return order.user_id == request.user.id

    identifier = _identifier_from_request(request)
    if identifier and order.customer_email and identifier == order.customer_email.lower():
        return True

    return False


def _recalculate_order_total(order):
    total = sum(line.price * line.quantity for line in order.lines.all())
    order.total = total - (order.discount_amount or Decimal('0'))
    if order.total < 0:
        order.total = Decimal('0')
    order.save(update_fields=['total', 'discount_amount', 'discount_code'])


def _reserve_discount(order, discount, identifier):
    usage, created = DiscountUsage.objects.get_or_create(
        order=order,
        discount_code=discount,
        defaults={
            'identifier': identifier,
            'status': DiscountUsage.STATUS_RESERVED,
        },
    )
    if not created and usage.status != DiscountUsage.STATUS_RESERVED:
        usage.status = DiscountUsage.STATUS_RESERVED
        usage.identifier = identifier
        usage.save(update_fields=['status', 'identifier'])
    return usage


def _release_discount_reservation(order):
    DiscountUsage.objects.filter(
        order=order,
        status=DiscountUsage.STATUS_RESERVED,
    ).delete()


@api_view(['POST'])
@permission_classes([AllowAny])
def apply_discount(request):
    code = request.data.get('code', '').strip().upper()
    order_id = request.data.get('order_id')

    if not code or not order_id:
        return Response({'detail': 'Code and order_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

    client_id = _client_identifier(request)
    if not _check_rate_limit(client_id):
        return Response({'detail': 'Too many attempts. Please try again later.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    order = _get_order(order_id)
    if not order:
        return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not _can_manage_order(order, request):
        return Response({'detail': 'Order not found or cannot be modified.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        discount = DiscountCode.objects.get(code=code, is_active=True)
    except DiscountCode.DoesNotExist:
        return Response({'detail': 'Invalid discount code.'}, status=status.HTTP_404_NOT_FOUND)

    order_total = sum(line.price * line.quantity for line in order.lines.all())

    if order.discount_code_id == discount.id and order.discount_amount > 0:
        return Response({
            'discount_code': discount.code,
            'discount_type': discount.discount_type,
            'value': str(discount.value),
            'discount_amount': str(order.discount_amount),
            'order_total': str(order.total),
        })

    is_valid, message = discount.is_valid(
        order_total=order_total,
        user=request.user,
        email=_identifier_from_request(request),
    )
    if not is_valid:
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)

    if not discount.applies_to_order(order):
        return Response(
            {'detail': 'This discount code does not apply to the items in your order.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    discount_amount = discount.calculate_discount(order_total)
    identifier = _identifier_from_request(request)

    with transaction.atomic():
        order.discount_code = discount
        order.discount_amount = discount_amount
        _recalculate_order_total(order)
        _reserve_discount(order, discount, identifier)

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

    client_id = _client_identifier(request)
    if not _check_rate_limit(client_id):
        return Response({'detail': 'Too many attempts. Please try again later.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    order = _get_order(order_id)
    if not order:
        return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not _can_manage_order(order, request):
        return Response({'detail': 'Order not found or cannot be modified.'}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        _release_discount_reservation(order)
        order.discount_code = None
        order.discount_amount = Decimal('0')
        _recalculate_order_total(order)

    return Response({
        'discount_code': None,
        'discount_amount': '0.00',
        'order_total': str(order.total),
    })
