def pf_product_handle(product_id):
    return f'pf-{product_id}'


def pf_variant_handle(product_id, variant_id):
    return f'pf-{product_id}-{variant_id}'


def parse_number(value):
    if value is None or value == '':
        return 0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0
