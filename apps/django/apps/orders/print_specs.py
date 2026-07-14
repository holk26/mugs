from django.conf import settings


def get_print_specs(line):
    """Resolve effective print specs for an OrderLine.

    Product overrides take precedence over global settings.
    """
    product = line.variant.product if line.variant else None

    def _coalesce(product_value, global_value):
        if product and product_value not in (None, '', 0):
            return product_value
        return global_value

    return {
        'width_mm': _coalesce(
            product.print_width_mm if product else None,
            settings.PRINTFUL_PRINT_WIDTH_MM,
        ),
        'height_mm': _coalesce(
            product.print_height_mm if product else None,
            settings.PRINTFUL_PRINT_HEIGHT_MM,
        ),
        'dpi': _coalesce(
            product.print_dpi if product else None,
            settings.PRINTFUL_PRINT_DPI,
        ),
        'background': _coalesce(
            product.image_background if product else None,
            settings.PRINTFUL_IMAGE_BACKGROUND,
        ),
        'format': _coalesce(
            product.image_format if product else None,
            settings.PRINTFUL_IMAGE_FORMAT,
        ),
    }
