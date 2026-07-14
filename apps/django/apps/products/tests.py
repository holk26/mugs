import pytest
from django.core.exceptions import ValidationError

from apps.products.models import Product


@pytest.mark.django_db
def test_create_product():
    product = Product.objects.create(
        handle='test-mug',
        title='Test Mug',
        price='19.99'
    )
    assert product.handle == 'test-mug'
    assert product.title == 'Test Mug'


@pytest.mark.django_db
def test_product_print_spec_defaults():
    product = Product.objects.create(title='Mug', handle='mug')
    assert product.print_width_mm is None
    assert product.print_height_mm is None
    assert product.print_dpi == 0
    assert product.image_background == ''
    assert product.image_format == ''


@pytest.mark.django_db
def test_product_print_spec_save_and_read():
    product = Product.objects.create(
        title='Mug',
        handle='mug',
        print_width_mm=200,
        print_height_mm=300,
        print_dpi=150,
        image_background='transparent',
        image_format='png',
    )
    product.refresh_from_db()
    assert product.print_width_mm == 200
    assert product.print_height_mm == 300
    assert product.print_dpi == 150
    assert product.image_background == 'transparent'
    assert product.image_format == 'png'


@pytest.mark.django_db
def test_product_print_spec_full_clean_defaults():
    product = Product(title='Mug', handle='mug')
    product.full_clean()
    product.save()
    assert product.print_dpi == 0
    assert product.print_width_mm is None
    assert product.print_height_mm is None


@pytest.mark.django_db
def test_product_print_spec_full_clean_valid_values():
    product = Product(
        title='Mug',
        handle='mug',
        print_width_mm=1,
        print_height_mm=1,
        print_dpi=1,
    )
    product.full_clean()
    product.save()


@pytest.mark.django_db
def test_product_print_spec_invalid_dimensions_raise_validation_error():
    product = Product(
        title='Mug',
        handle='mug',
        print_width_mm=0,
        print_height_mm=0,
    )
    with pytest.raises(ValidationError):
        product.full_clean()


@pytest.mark.django_db
def test_product_print_spec_dpi_zero_passes_full_clean():
    product = Product(
        title='Mug',
        handle='mug',
        print_dpi=0,
    )
    product.full_clean()
    product.save()
    assert product.print_dpi == 0


@pytest.mark.django_db
def test_product_invalid_image_background_choice():
    product = Product(
        title='Mug',
        handle='mug',
        image_background='red',
    )
    with pytest.raises(ValidationError):
        product.full_clean()


@pytest.mark.django_db
def test_product_invalid_image_format_choice():
    product = Product(
        title='Mug',
        handle='mug',
        image_format='gif',
    )
    with pytest.raises(ValidationError):
        product.full_clean()
