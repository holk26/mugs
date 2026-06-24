from celery import shared_task
from apps.printful.sync import CatalogSync
from apps.printful.models import PrintfulSyncLog


@shared_task(bind=True)
def sync_printful_catalog(self):
    log = PrintfulSyncLog.objects.create(status='running')
    try:
        result = CatalogSync().run()
        log.products_created = result['created']
        log.products_updated = result['updated']
        log.errors = result['errors']
        log.status = 'completed' if not result['errors'] else 'completed_with_errors'
    except Exception as exc:
        log.status = 'failed'
        log.errors = [{'error': str(exc)}]
        raise self.retry(exc=exc, countdown=60, max_retries=1)
    finally:
        from django.utils import timezone
        log.finished_at = timezone.now()
        log.save()
    return {
        'log_id': str(log.id),
        'status': log.status,
        'created': log.products_created,
        'updated': log.products_updated,
    }
