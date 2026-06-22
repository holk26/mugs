from django.conf import settings
from django.core.mail import send_mail


ORDER_CONFIRMED_SUBJECT = "We received your Recuerdo Momentos order!"
ORDER_UPDATE_SUBJECT = "Your Recuerdo Momentos order has been updated"


def _format_lines(order):
    lines = []
    for line in order.lines.select_related('variant').all():
        upload = "uploaded" if line.customer_upload else "not uploaded"
        lines.append(f"- {line.quantity}x {line.title} (${line.price} each, drawing {upload})")
    return "\n".join(lines)


def send_order_confirmation_email(order):
    if not order.customer_email:
        return

    body = f"""Hi {order.customer_name or 'there'},

Thank you for your order at Recuerdo Momentos.

Order: {order.id}
Status: {order.status}
Total: ${order.total} {order.currency}

Items:
{_format_lines(order)}

We will carefully digitize the drawing and keep you updated.

— Recuerdo Momentos
"""
    send_mail(
        subject=ORDER_CONFIRMED_SUBJECT,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        fail_silently=True,
    )


def send_order_update_email(order):
    if not order.customer_email:
        return

    body = f"""Hi {order.customer_name or 'there'},

Your order {order.id} has been updated.

New status: {order.status}
Printful status: {order.printful_status or 'pending'}

You can reply to this email if you have questions.

— Recuerdo Momentos
"""
    send_mail(
        subject=ORDER_UPDATE_SUBJECT,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        fail_silently=True,
    )
