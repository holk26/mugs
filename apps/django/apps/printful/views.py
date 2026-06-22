from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PrintfulWebhookEvent
from .webhooks import verify_printful_signature


@api_view(['POST'])
def printful_webhook(request):
    signature = request.headers.get('X-PF-WEBHOOK-SIGNATURE', '')
    if not verify_printful_signature(request.body, signature):
        return Response({'detail': 'invalid signature'}, status=403)

    event_type = request.data.get('type', 'unknown')
    PrintfulWebhookEvent.objects.create(
        event_type=event_type,
        payload=request.data
    )
    return Response({'status': 'ok'})
