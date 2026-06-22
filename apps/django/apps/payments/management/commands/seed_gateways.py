from django.core.management.base import BaseCommand
from apps.payments.models import PaymentGateway


class Command(BaseCommand):
    help = 'Seed default payment gateways'

    def handle(self, *args, **options):
        PaymentGateway.objects.get_or_create(
            code='stripe',
            defaults={'name': 'Stripe', 'enabled': True}
        )
        PaymentGateway.objects.get_or_create(
            code='manual',
            defaults={'name': 'Manual Payment', 'enabled': True}
        )
        self.stdout.write(self.style.SUCCESS('Gateways seeded'))
