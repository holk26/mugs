from django.db import transaction
from apps.products.models import Product, ProductVariant, ProductMedia
from .client import PrintfulClient
from .transformers import (
    printful_store_product_to_product,
    printful_sync_variant_to_variant,
)
from .utils import pf_product_handle


class CatalogSync:
    def __init__(self, client=None):
        self.client = client or PrintfulClient()
        self.created = 0
        self.updated = 0
        self.errors = []

    def run(self):
        offset = 0
        limit = 100
        total = float('inf')

        while offset < total:
            response = self.client.get_store_products(limit=limit, offset=offset)
            products = response.get('result', [])
            paging = response.get('paging', {})
            total = paging.get('total', len(products))

            for summary in products:
                try:
                    self._sync_product(summary['id'])
                except Exception as e:
                    self.errors.append({'product_id': summary['id'], 'error': str(e)})

            offset += limit

        return {
            'created': self.created,
            'updated': self.updated,
            'errors': self.errors,
        }

    def _sync_product(self, printful_product_id):
        response = self.client.get_store_product(printful_product_id)
        sync_product = response['result']['sync_product']
        sync_variants = response['result']['sync_variants']

        product_data = printful_store_product_to_product(sync_product, sync_variants)
        handle = product_data['handle']

        product, created = Product.objects.update_or_create(
            handle=handle,
            defaults={
                'title': product_data['title'],
                'description': product_data['description'],
                'status': product_data['status'],
                'tags': product_data['tags'],
                'price': product_data['price'],
            }
        )

        if created:
            self.created += 1
        else:
            self.updated += 1

        # Sync variants
        incoming_sync_ids = set()

        for sync_variant in sync_variants:
            variant_data = printful_sync_variant_to_variant(sync_variant, sync_product)
            incoming_sync_ids.add(variant_data['printful_sync_variant_id'])

            variant, _ = ProductVariant.objects.update_or_create(
                product=product,
                printful_sync_variant_id=variant_data['printful_sync_variant_id'],
                defaults={
                    'title': variant_data['title'],
                    'price': variant_data['price'],
                    'stock': variant_data['stock'],
                    'active': variant_data['active'],
                    'options': variant_data['options'],
                    'printful_variant_id': variant_data['printful_variant_id'],
                }
            )

            # Use first variant price as product price if main price is 0
            if product.price == 0 and variant_data['price']:
                product.price = variant_data['price']
                product.save(update_fields=['price'])

        # Remove variants no longer in Printful
        product.variants.exclude(printful_sync_variant_id__in=incoming_sync_ids).delete()

        # Sync media from first active variant
        for sync_variant in sync_variants:
            variant_data = printful_sync_variant_to_variant(sync_variant, sync_product)
            if variant_data['media']:
                for index, url in enumerate(variant_data['media']):
                    ProductMedia.objects.get_or_create(
                        product=product,
                        url=url,
                        defaults={'type': 'image', 'order': index}
                    )
                break


def push_order(order, confirm=False):
    """Push a paid order to Printful as a draft by default.

    Draft orders must be explicitly confirmed before Printful fulfills them.
    Pass ``confirm=True`` only when a human has reviewed and approved the order.
    """
    from django.db import transaction
    from django.conf import settings
    from apps.products.models import ProductVariant
    from .transformers import storecraft_address_to_printful_recipient

    def _do_push():
        client = PrintfulClient()
        items = []
        for line in order.lines.select_related('variant'):
            if not line.variant or not line.variant.printful_variant_id:
                continue
            item = {
                'variant_id': int(line.variant.printful_variant_id),
                'quantity': line.quantity,
                'retail_price': str(line.price),
                'files': [],
            }
            upload_file = line.processed_upload or line.customer_upload
            if upload_file:
                absolute_url = upload_file.url
                if absolute_url.startswith('/'):
                    absolute_url = f"{settings.SITE_URL.rstrip('/')}{absolute_url}"
                item['files'].append({
                    'url': absolute_url,
                    'type': 'default',
                })
            items.append(item)

        if not items:
            return None

        recipient = storecraft_address_to_printful_recipient(order.shipping_address)
        result = client.create_order({
            'external_id': str(order.id),
            'recipient': recipient,
            'items': items,
            'shipping': 'STANDARD',
        }, confirm=confirm)

        pf_order = result.get('result', {})
        order.printful_order_id = str(pf_order.get('id', ''))
        order.printful_status = pf_order.get('status', '')
        order.save(update_fields=['printful_order_id', 'printful_status'])
        return order.printful_order_id

    transaction.on_commit(_do_push)


def confirm_printful_order(order):
    """Confirm an existing Printful draft order so it enters fulfillment."""
    from django.db import transaction

    if not order.printful_order_id:
        raise ValueError('Order has not been pushed to Printful yet')

    def _do_confirm():
        client = PrintfulClient()
        result = client.confirm_order(order.printful_order_id)
        pf_order = result.get('result', {})
        order.printful_status = pf_order.get('status', order.printful_status)
        order.save(update_fields=['printful_status'])
        return order.printful_status

    transaction.on_commit(_do_confirm)
