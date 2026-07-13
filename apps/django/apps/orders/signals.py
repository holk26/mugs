from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.core.email import send_order_confirmation_email, send_order_update_email
from apps.orders.models import Order
from apps.printful.sync import push_order
from apps.orders.tasks import process_order_images


@receiver(pre_save, sender=Order)
def capture_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = Order.objects.values_list('status', flat=True).get(pk=instance.pk)
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def handle_order_paid(sender, instance, created, **kwargs):
    if created:
        return

    previous_status = getattr(instance, '_previous_status', None)

    if instance.status == 'paid' and previous_status != 'paid':
        def _on_commit():
            process_order_images.delay(instance.id)
            if settings.PRINTFUL_API_TOKEN and not instance.printful_order_id:
                push_order(instance)
            send_order_confirmation_email(instance)

        transaction.on_commit(_on_commit)
    elif instance.status in ('processing', 'fulfilled', 'cancelled', 'failed') and instance.printful_order_id:
        transaction.on_commit(lambda: send_order_update_email(instance))
