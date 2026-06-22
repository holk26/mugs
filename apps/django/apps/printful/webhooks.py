import hmac
import hashlib
from django.conf import settings


def verify_printful_signature(payload, signature):
    if not settings.PRINTFUL_WEBHOOK_SECRET:
        return False
    expected = hmac.new(
        settings.PRINTFUL_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or '')
