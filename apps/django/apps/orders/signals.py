import logging
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.email import send_order_confirmation_email, send_order_update_email
from apps.orders.models import Order
from apps.printful.sync import push_order

logger = logging.getLogger("mugs.orders")


@receiver(post_save, sender=Order)
def handle_order_paid(sender, instance, created, **kwargs):
    if created:
        return

    if instance.status == 'paid' and not instance.printful_order_id:
        # In development or until manual approval is implemented, do not push
        # automatically to Printful. This prevents test orders from being sent
        # to production fulfillment.
        if getattr(settings, 'PRINTFUL_AUTO_PUSH', False):
            try:
                push_order(instance)
            except Exception as exc:
                logger.exception("Failed to push order %s to Printful: %s", instance.id, exc)

        try:
            send_order_confirmation_email(instance)
        except Exception as exc:
            logger.exception("Failed to send confirmation email for order %s: %s", instance.id, exc)

    elif instance.status in ('processing', 'fulfilled', 'cancelled', 'failed') and instance.printful_order_id:
        try:
            send_order_update_email(instance)
        except Exception as exc:
            logger.exception("Failed to send update email for order %s: %s", instance.id, exc)
