import uuid
from django.db import models


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    handle = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('active', 'Active'), ('archived', 'Archived')],
        default='draft'
    )
    tags = models.JSONField(default=list, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    options = models.JSONField(default=dict, blank=True)
    printful_sync_variant_id = models.CharField(max_length=50, blank=True)
    printful_variant_id = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.product.title} - {self.title}"


def product_media_upload_path(instance, filename):
    return f'products/{instance.product.id}/media/{filename}'


class ProductMedia(models.Model):
    MEDIA_TYPES = [('image', 'Image'), ('video', 'Video')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='medias', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=MEDIA_TYPES, default='image')
    file = models.ImageField(upload_to=product_media_upload_path, blank=True, null=True)
    url = models.URLField()
    alt = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'product media'

    def save(self, *args, **kwargs):
        if self.file and not self.url:
            self.url = self.file.url
        super().save(*args, **kwargs)

    def __str__(self):
        return self.alt or self.url


class Collection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    handle = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    products = models.ManyToManyField(Product, related_name='collections', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
