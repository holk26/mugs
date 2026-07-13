import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from apps.orders.models import Order
from apps.orders.ai_cleanup import generate_cleaned_upload, ImageCleanupError


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_order_images(self, order_id):
    logger.info('Processing images for order %s', order_id)
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.warning('Order %s not found', order_id)
        return {'error': 'Order not found'}

    results = []
    has_errors = False
    for line in order.lines.filter(customer_upload__isnull=False):
        if line.processed_upload:
            results.append({'line_id': str(line.id), 'status': 'skipped'})
            continue
        try:
            provider = getattr(settings, 'AI_IMAGE_PROVIDER', 'gemini')
            generate_cleaned_upload(line, provider=provider)
            results.append({'line_id': str(line.id), 'status': 'processed'})
        except ImageCleanupError as exc:
            has_errors = True
            line.processed_upload_error = str(exc)
            line.save(update_fields=['processed_upload_error'])
            results.append({'line_id': str(line.id), 'status': 'error', 'detail': str(exc)})
            logger.exception('Image cleanup failed for line %s', line.id)

    if has_errors:
        try:
            raise self.retry(exc=ImageCleanupError('Some images failed to process'))
        except MaxRetriesExceededError:
            logger.error('Max retries exceeded for order %s', order_id)
            return {'order_id': str(order_id), 'results': results, 'status': 'max_retries_exceeded'}

    return {'order_id': str(order_id), 'results': results}
