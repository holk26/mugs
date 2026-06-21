from django.contrib import admin
from .models import Product, ProductVariant, ProductMedia, Collection

admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductMedia)
admin.site.register(Collection)
