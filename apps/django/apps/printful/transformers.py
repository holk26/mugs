from decimal import Decimal
from .utils import pf_product_handle, pf_variant_handle, parse_number


def printful_store_product_to_product(sync_product, sync_variants=None):
    sync_variants = sync_variants or []
    active = sync_product.get('is_ignored') is not True and any(
        v.get('availability_status') == 'active' for v in sync_variants
    )

    return {
        'handle': pf_product_handle(sync_product['id']),
        'title': sync_product.get('name') or f'Printful Product {sync_product["id"]}',
        'description': sync_product.get('description') or '',
        'status': 'active' if active else 'draft',
        'tags': ['printful'],
        'price': Decimal('0'),
        'printful_sync_product_id': str(sync_product['id']),
    }


def printful_sync_variant_to_variant(sync_variant, parent_product):
    media = []
    if sync_variant.get('product', {}).get('image'):
        media.append(sync_variant['product']['image'])

    for file in sync_variant.get('files', []):
        url = file.get('preview_url') or file.get('url')
        if url and url not in media:
            media.append(url)

    options = {}
    if sync_variant.get('size'):
        options['size'] = sync_variant['size']
    if sync_variant.get('color'):
        options['color'] = sync_variant['color']

    return {
        'handle': pf_variant_handle(parent_product['id'], sync_variant['id']),
        'title': sync_variant.get('name') or f"{parent_product.get('name')} variant",
        'price': Decimal(str(parse_number(sync_variant.get('retail_price')))),
        'stock': 100 if sync_variant.get('availability_status') == 'active' else 0,
        'active': sync_variant.get('is_ignored') is not True and sync_variant.get('availability_status') == 'active',
        'options': options,
        'printful_sync_variant_id': str(sync_variant['id']),
        'printful_variant_id': str(sync_variant.get('variant_id')),
        'media': media,
    }


def storecraft_address_to_printful_recipient(address, contact=None):
    contact = contact or {}
    from_contact = ' '.join(filter(None, [contact.get('firstname'), contact.get('lastname')]))
    from_address = ' '.join(filter(None, [address.get('firstname'), address.get('lastname')]))
    name = from_contact or from_address or 'Customer'

    return {
        'name': name,
        'company': address.get('company', ''),
        'address1': address.get('street1', ''),
        'address2': address.get('street2', ''),
        'city': address.get('city', ''),
        'state_code': address.get('state', ''),
        'country_code': address.get('country', ''),
        'zip': address.get('zip_code') or address.get('postal_code', ''),
        'phone': contact.get('phone_number') or address.get('phone_number', ''),
        'email': contact.get('email', ''),
    }


def storecraft_line_items_to_printful_items(line_items, variants_map):
    items = []
    for item in line_items:
        pf_variant_id = variants_map.get(item.get('id'))
        if not pf_variant_id:
            continue
        items.append({
            'variant_id': int(pf_variant_id),
            'quantity': item.get('qty', 1),
            'retail_price': str(item.get('price') or 0),
        })
    return items


def printful_shipping_rate_to_shipping_method(rate):
    return {
        'code': f'pf-ship-{rate.get("id")}',
        'name': rate.get('name') or f"Printful {rate.get('id')}",
        'price': Decimal(str(parse_number(rate.get('rate')))),
    }


def printful_order_status_to_order_status(pf_status):
    mapping = {
        'draft': 'pending',
        'pending': 'pending',
        'inreview': 'pending',
        'inprocess': 'processing',
        'partial': 'processing',
        'fulfilled': 'fulfilled',
        'canceled': 'cancelled',
        'failed': 'failed',
        'onhold': 'failed',
    }
    return mapping.get(pf_status, 'pending')
