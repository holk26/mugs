from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.payments.models import PaymentGateway


@api_view(['GET'])
def payment_gateways(request):
    gateways = PaymentGateway.objects.filter(enabled=True)
    return Response([
        {'code': g.code, 'name': g.name}
        for g in gateways
    ])


@api_view(['POST'])
def checkout_complete(request, order_id):
    gateway_code = request.data.get('gateway')
    # Integration point: validate gateway, capture payment, then mark order paid
    # and trigger Printful order push via apps.orders.signals.payment_captured.
    from apps.orders.models import Order
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return Response({'detail': 'order not found'}, status=404)
    order.status = 'paid'
    order.save()
    return Response({'detail': f'checkout complete for order {order_id} via {gateway_code}'})
