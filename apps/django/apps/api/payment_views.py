import stripe
from decimal import Decimal
from django.conf import settings
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.payments.models import PaymentGateway
from apps.orders.models import Order
from apps.discounts.models import DiscountCode, DiscountUsage

stripe.api_key = settings.STRIPE_SECRET_KEY


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

    if order.status != 'pending':
        return Response({'detail': 'Order is not pending.'}, status=status.HTTP_400_BAD_REQUEST)

    site_url = settings.SITE_URL.rstrip('/')
    success_url = f'{site_url}/thanks/?order={order.id}&session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{site_url}/checkout/?order={order.id}&canceled=1'

    line_items = [
        {
            'price_data': {
                'currency': order.currency.lower(),
                'unit_amount': int(line.price * line.quantity * 100),
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
                    'currency': order.currency.lower(),
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
            'allowed_countries': ['US', 'CA', 'MX', 'ES', 'AR', 'CL', 'CO', 'PE', 'UY', 'EC', 'BO', 'VE', 'PA', 'CR', 'GT', 'SV', 'HN', 'NI', 'DO', 'PR'],
        },
    }

    subtotal = sum(line.price * line.quantity for line in order.lines.all())
    if order.discount_code and order.discount_amount and order.discount_amount > 0 and order.discount_amount <= subtotal:
        try:
            coupon = stripe.Coupon.create(
                amount_off=int(order.discount_amount * 100),
                currency=order.currency.lower(),
                duration='once',
                name=order.discount_code.code,
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

    order_id = None
    if event['type'] == 'checkout.session.completed':
        order_id = event['data']['object'].get('metadata', {}).get('order_id')
    elif event['type'] == 'payment_intent.succeeded':
        order_id = event['data']['object'].get('metadata', {}).get('order_id')

    if order_id:
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(id=order_id)
            except Order.DoesNotExist:
                return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

            if order.status == 'pending':
                order.status = 'paid'
                order.save(update_fields=['status'])

            if event['type'] == 'checkout.session.completed':
                session_obj = event['data']['object']
                shipping = session_obj.get('shipping_details') or session_obj.get('customer_details', {}).get('shipping', {})
                address = shipping.get('address', {})
                if address:
                    order.shipping_address = {
                        'name': shipping.get('name', order.customer_name),
                        'line1': address.get('line1', ''),
                        'line2': address.get('line2', ''),
                        'city': address.get('city', ''),
                        'state': address.get('state', ''),
                        'postal_code': address.get('postal_code', ''),
                        'country': address.get('country', ''),
                    }
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
