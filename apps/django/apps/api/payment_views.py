import stripe
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.payments.models import PaymentGateway
from apps.orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['GET'])
def payment_gateways(request):
    gateways = PaymentGateway.objects.filter(is_enabled=True)
    return Response([
        {'code': g.code, 'name': g.name, 'config': g.config}
        for g in gateways
    ])


@api_view(['POST'])
@permission_classes([AllowAny])
def create_payment_intent(request):
    order_id = request.data.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    if order.status != 'pending':
        return Response({'detail': 'Order is not pending.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),
            currency=order.currency.lower(),
            metadata={'order_id': str(order.id)},
            automatic_payment_methods={'enabled': True},
        )
    except stripe.error.StripeError as e:
        return Response({'detail': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    order.payment_intent_id = intent.id
    order.save(update_fields=['payment_intent_id'])

    return Response({
        'client_secret': intent.client_secret,
        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@api_view(['POST'])
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

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        order_id = intent['metadata'].get('order_id')
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status == 'pending':
            order.status = 'paid'
            order.save(update_fields=['status'])

    return Response({'status': 'ok'})
