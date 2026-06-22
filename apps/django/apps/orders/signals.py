from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def push_order_to_printful(sender, instance, **kwargs):
    if instance.status != 'paid' or instance.printful_order_id:
        return
    from apps.printful.sync import push_order
    push_order(instance)
