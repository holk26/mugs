from celery import shared_task
from apps.orders.models import Order
from apps.orders.ai_cleanup import generate_cleaned_upload, ImageCleanupError


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_order_images(self, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return {'error': 'Order not found'}

    results = []
    for line in order.lines.filter(customer_upload__isnull=False):
        if line.processed_upload:
            results.append({'line_id': str(line.id), 'status': 'skipped'})
            continue
        try:
            generate_cleaned_upload(line, provider='gemini')
            results.append({'line_id': str(line.id), 'status': 'processed'})
        except ImageCleanupError as exc:
            line.processed_upload_error = str(exc)
            line.save(update_fields=['processed_upload_error'])
            results.append({'line_id': str(line.id), 'status': 'error', 'detail': str(exc)})
            raise self.retry(exc=exc)

    return {'order_id': str(order_id), 'results': results}
