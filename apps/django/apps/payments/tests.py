import pytest
from apps.payments.models import PaymentGateway


@pytest.mark.django_db
def test_gateway_str():
    gateway = PaymentGateway.objects.create(code='stripe', name='Stripe')
    assert str(gateway) == 'Stripe'
