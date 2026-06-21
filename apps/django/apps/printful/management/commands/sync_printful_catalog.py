from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.printful.sync import CatalogSync
from apps.printful.models import PrintfulSyncLog


class Command(BaseCommand):
    help = 'Synchronize Printful catalog into Django'

    def handle(self, *args, **options):
        log = PrintfulSyncLog.objects.create(status='running')
        try:
            result = CatalogSync().run()
            log.status = 'completed'
            log.products_created = result['created']
            log.products_updated = result['updated']
            log.errors = result['errors']
        except Exception as e:
            log.status = 'failed'
            log.errors = [{'error': str(e)}]
        finally:
            log.finished_at = timezone.now()
            log.save()

        self.stdout.write(self.style.SUCCESS(
            f"Sync complete: created={log.products_created} updated={log.products_updated} errors={len(log.errors)}"
        ))
