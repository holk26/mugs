import pytest
from apps.printful.models import PrintfulWebhookEvent


@pytest.mark.django_db
def test_webhook_event_str():
    event = PrintfulWebhookEvent.objects.create(event_type='package_shipped', payload={'id': 1})
    assert event.event_type == 'package_shipped'


import hashlib
import hmac
import json

from apps.orders.models import Order


def _sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


@pytest.mark.django_db
class TestPrintfulWebhook:
    url = '/api/v1/printful/webhook/'
    secret = 'test-printful-webhook-secret'

    def test_valid_signature_stores_event_type_and_processed(self, client):
        order = Order.objects.create(
            customer_email='a@b.c', total='15.00', status='paid', printful_order_id='777'
        )
        payload = json.dumps({
            'type': 'order_updated',
            'data': {'order': {'id': 777, 'status': 'fulfilled'}},
        }).encode()

        response = client.post(
            self.url,
            payload,
            content_type='application/json',
            HTTP_X_PF_WEBHOOK_SIGNATURE=_sign(payload, self.secret),
        )

        assert response.status_code == 200
        event = PrintfulWebhookEvent.objects.get()
        assert event.event_type == 'order_updated'
        assert event.processed is True
        order.refresh_from_db()
        assert order.status == 'fulfilled'
        assert order.printful_status == 'fulfilled'

    def test_invalid_signature_is_rejected(self, client):
        payload = json.dumps({'type': 'order_updated', 'data': {}}).encode()
        response = client.post(
            self.url,
            payload,
            content_type='application/json',
            HTTP_X_PF_WEBHOOK_SIGNATURE='bad-signature',
        )
        assert response.status_code == 400
        assert PrintfulWebhookEvent.objects.count() == 0
