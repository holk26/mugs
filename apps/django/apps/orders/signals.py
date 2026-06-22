from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.email import send_order_confirmation_email, send_order_update_email
from apps.orders.models import Order
from apps.printful.sync import push_order


@receiver(post_save, sender=Order)
def handle_order_paid(sender, instance, created, **kwargs):
    if created:
        return

    if instance.status == 'paid' and not instance.printful_order_id:
        push_order(instance)
        send_order_confirmation_email(instance)
    elif instance.status in ('processing', 'fulfilled', 'shipped', 'cancelled', 'failed'):
        send_order_update_email(instance)
