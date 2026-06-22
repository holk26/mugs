import pytest
from apps.printful.models import PrintfulWebhookEvent


@pytest.mark.django_db
def test_webhook_event_str():
    event = PrintfulWebhookEvent.objects.create(event_type='package_shipped', payload={'id': 1})
    assert event.event_type == 'package_shipped'
