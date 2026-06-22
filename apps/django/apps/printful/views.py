import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from apps.printful.models import PrintfulWebhookEvent
from apps.printful.webhooks import verify_printful_signature
from apps.printful.transformers import printful_order_status_to_order_status
from apps.orders.models import Order


@csrf_exempt
@require_http_methods(['POST'])
def printful_webhook(request):
    payload = request.body
    signature = request.headers.get('X-PF-WEBHOOK-SIGNATURE', '')

    if not verify_printful_signature(payload, signature):
        return JsonResponse({'detail': 'Invalid signature.'}, status=400)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

    PrintfulWebhookEvent.objects.create(payload=data)

    event_type = data.get('type', '')
    printful_data = data.get('data', {})
    printful_order_id = str(printful_data.get('order', {}).get('id', ''))

    if printful_order_id and event_type.startswith('order_'):
        try:
            order = Order.objects.get(printful_order_id=printful_order_id)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'ignored'})

        pf_status = printful_data.get('order', {}).get('status', '')
        new_status = printful_order_status_to_order_status(pf_status)
        if new_status and order.status != new_status:
            order.status = new_status
            order.printful_status = pf_status
            order.save(update_fields=['status', 'printful_status'])

    return JsonResponse({'status': 'ok'})
