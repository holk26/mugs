import stripe
from decimal import Decimal
from django.conf import settings
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.payments.models import PaymentGateway, WebhookEvent
from apps.orders.models import Order
from apps.discounts.models import DiscountCode, DiscountUsage

stripe.api_key = settings.STRIPE_SECRET_KEY


def _order_belongs_to_request(order, request):
    """Verify the requester owns the order.

    Authenticated users must match the order's user (or its customer email for
    guest orders they claim). Guests must provide the order's customer email.
    """
    if request.user.is_authenticated:
        if order.user_id:
            return order.user_id == request.user.id
        return bool(request.user.email) and request.user.email.lower() == (order.customer_email or '').lower()
    email = (request.data.get('email') or '').strip().lower()
    return bool(email) and email == (order.customer_email or '').lower()


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_gateways(request):
    gateways = PaymentGateway.objects.filter(enabled=True)
    return Response([
        {'code': g.code, 'name': g.name}
        for g in gateways
    ])


@api_view(['POST'])
@permission_classes([AllowAny])
def create_checkout_session(request):
    order_id = request.data.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    if not _order_belongs_to_request(order, request):
        # 404 instead of 403 to avoid leaking the existence of the order.
        return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if order.status != 'pending':
        return Response({'detail': 'Order is not pending.'}, status=status.HTTP_400_BAD_REQUEST)

    site_url = settings.SITE_URL.rstrip('/')
    success_url = f'{site_url}/thanks/?order={order.id}&session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{site_url}/checkout/?order={order.id}&canceled=1'

    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order.id)
        if order.status != 'pending':
            return Response({'detail': 'Order is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        subtotal = sum(line.price * line.quantity for line in order.lines.all())
        discount_code = order.discount_code
        discount_amount = order.discount_amount
        currency = order.currency

    line_items = [
        {
            'price_data': {
                'currency': currency.lower(),
                # unit_amount is the price of ONE unit; Stripe multiplies it by
                # quantity below. Do not multiply by line.quantity here.
                'unit_amount': int(line.price * 100),
                'product_data': {
                    'name': line.title,
                },
            },
            'quantity': line.quantity,
        }
        for line in order.lines.all()
    ]

    if not line_items:
        line_items = [
            {
                'price_data': {
                    'currency': currency.lower(),
                    'unit_amount': int(order.total * 100),
                    'product_data': {
                        'name': 'Order total',
                    },
                },
                'quantity': 1,
            }
        ]

    session_kwargs = {
        'payment_method_types': ['card'],
        'line_items': line_items,
        'mode': 'payment',
        'success_url': success_url,
        'cancel_url': cancel_url,
        'metadata': {'order_id': str(order.id)},
        'shipping_address_collection': {
            'allowed_countries': settings.STRIPE_CHECKOUT_SHIPPING_COUNTRIES,
        },
    }

    if discount_code and discount_amount and discount_amount > 0 and discount_amount <= subtotal:
        try:
            coupon = stripe.Coupon.create(
                amount_off=int(discount_amount * 100),
                currency=currency.lower(),
                duration='once',
                name=discount_code.code,
            )
            session_kwargs['discounts'] = [{'coupon': coupon.id}]
        except stripe.error.StripeError as e:
            return Response({'detail': f'Failed to create discount: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    try:
        session = stripe.checkout.Session.create(**session_kwargs)
    except stripe.error.StripeError as e:
        return Response({'detail': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    order.payment_intent_id = session.id
    order.save(update_fields=['payment_intent_id'])

    return Response({'url': session.url})



@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return Response({'detail': 'Invalid payload.'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        return Response({'detail': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

    # Stripe's newer SDK returns StripeObject instances from construct_event.
    # Normalize the whole payload to plain dicts so the rest of the view can
    # use `.get()` safely, both in production and in unit tests.
    event = stripe._util.convert_to_dict(event)

    # Idempotency: Stripe retries webhooks, so record processed event ids and
    # acknowledge duplicates without reprocessing them.
    event_id = event.get('id')
    if event_id:
        with transaction.atomic():
            _, created = WebhookEvent.objects.get_or_create(
                event_id=event_id,
                defaults={'event_type': event.get('type', ''), 'payload': event},
            )
        if not created:
            return Response({'status': 'duplicate'})

    order_id = None
    if event['type'] == 'checkout.session.completed':
        order_id = event.get('data', {}).get('object', {}).get('metadata', {}).get('order_id')
    elif event['type'] == 'payment_intent.succeeded':
        order_id = event.get('data', {}).get('object', {}).get('metadata', {}).get('order_id')

    def _extract_shipping_address(session_obj, fallback_name):
        shipping = (
            session_obj.get('shipping_details')
            or session_obj.get('customer_details', {}).get('shipping', {})
            or {}
        )
        address = shipping.get('address') or session_obj.get('customer_details', {}).get('address', {})
        if not address:
            return None
        return {
            'name': shipping.get('name')
                or session_obj.get('customer_details', {}).get('name', fallback_name),
            'line1': address.get('line1', ''),
            'line2': address.get('line2', ''),
            'city': address.get('city', ''),
            'state': address.get('state', ''),
            'postal_code': address.get('postal_code', ''),
            'country': address.get('country', ''),
        }

    if order_id:
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(id=order_id)
            except Order.DoesNotExist:
                return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

            if order.status == 'pending':
                order.status = 'paid'
                order.save(update_fields=['status'])

            session_obj = event.get('data', {}).get('object', {})
            if event['type'] == 'checkout.session.completed':
                address = _extract_shipping_address(session_obj, order.customer_name)
                if address:
                    order.shipping_address = address
                    order.save(update_fields=['shipping_address'])
            elif event['type'] == 'payment_intent.succeeded':
                # Payment intents from Stripe Checkout embed the completed session
                # in charges.data[].billing_details or the expanded payment_intent.
                # We only update the address if we don't already have a line1.
                current = order.shipping_address or {}
                if not current.get('line1'):
                    address = _extract_shipping_address(session_obj, order.customer_name)
                    if address:
                        order.shipping_address = address
                        order.save(update_fields=['shipping_address'])

            if order.discount_code:
                discount_code = DiscountCode.objects.select_for_update().get(pk=order.discount_code.pk)
                identifier = DiscountUsage.normalize_identifier(
                    user=order.user,
                    email=order.customer_email,
                )
                try:
                    usage, created = DiscountUsage.objects.get_or_create(
                        order=order,
                        discount_code=discount_code,
                        defaults={
                            'identifier': identifier,
                            'status': DiscountUsage.STATUS_CONFIRMED,
                            'amount_saved': order.discount_amount or Decimal('0'),
                        },
                    )
                    if not created:
                        usage.status = DiscountUsage.STATUS_CONFIRMED
                        usage.amount_saved = order.discount_amount or Decimal('0')
                        usage.save(update_fields=['status', 'amount_saved'])
                except IntegrityError:
                    usage = DiscountUsage.objects.get(order=order, discount_code=discount_code)
                    usage.status = DiscountUsage.STATUS_CONFIRMED
                    usage.amount_saved = order.discount_amount or Decimal('0')
                    usage.save(update_fields=['status', 'amount_saved'])

    return Response({'status': 'ok'})
