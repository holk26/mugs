import stripe
import traceback
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.payments.models import PaymentGateway, WebhookEvent
from apps.orders.models import Order

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

    base_url = settings.SITE_URL.rstrip('/')
    success_url = (
        f'{base_url}/thanks?order={order.id}&session_id={{CHECKOUT_SESSION_ID}}'
    )
    cancel_url = f'{base_url}/checkout?order={order.id}&canceled=1'

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

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'order_id': str(order.id)},
        )
    except stripe.error.StripeError as e:
        return Response({'detail': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    order.payment_intent_id = session.id
    order.save(update_fields=['payment_intent_id'])

    return Response({'url': session.url})


@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    try:
        return _stripe_webhook_inner(request)
    except Exception as exc:
        # Temporary debug response to capture the real failure in production.
        return Response(
            {'detail': str(exc), 'traceback': traceback.format_exc()},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _stripe_webhook_inner(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')

    if not sig_header:
        return Response({'detail': 'Missing signature.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return Response({'detail': 'Invalid payload.'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        return Response({'detail': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

    # Idempotency: each Stripe event has a unique ID. Processing the same event
    # twice must not change the order state or trigger side effects again.
    # `construct_event` returns a StripeObject, which supports attribute access
    # but does not have a `.get()` method like a dict.
    event_id = event.id
    event_type = event.type
    event_obj = event.data.object

    _, created = WebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={
            'event_type': event_type,
            'payload': event_obj.to_dict(),
        },
    )
    if not created:
        return Response({'status': 'already_processed'})

    if event_type == 'checkout.session.completed':
        # StripeObject supports attribute access but not dict methods.
        order_id = getattr(event_obj.metadata, 'order_id', None)
        payment_intent_id = getattr(event_obj, 'payment_intent', None)

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

            if order.status == 'pending':
                order.status = 'paid'
                if payment_intent_id:
                    order.payment_intent_id = payment_intent_id
                order.save(update_fields=['status', 'payment_intent_id'])

    return Response({'status': 'ok'})
