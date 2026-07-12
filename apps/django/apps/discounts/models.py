import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.orders.models import Order
from apps.products.models import Collection, Product


class DiscountCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed amount'),
    ]

    APPLIES_TO_CHOICES = [
        ('all', 'All products'),
        ('products', 'Specific products'),
        ('collections', 'Specific collections'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    usage_limit_total = models.PositiveIntegerField(null=True, blank=True)
    usage_limit_per_user = models.PositiveIntegerField(null=True, blank=True)

    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    applies_to = models.CharField(max_length=20, choices=APPLIES_TO_CHOICES, default='all')
    product_ids = models.JSONField(default=list, blank=True)
    collection_ids = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def clean(self):
        self.code = self.code.strip().upper()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def usage_count(self):
        return self.usages.count()

    def is_valid(self, order_total: Decimal, user=None, email: str = '') -> tuple[bool, str]:
        if not self.is_active:
            return False, 'Discount code is inactive'

        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False, 'Discount code is not active yet'
        if self.expires_at and now > self.expires_at:
            return False, 'Discount code has expired'

        counted_usages = self.usages.filter(
            status__in=(DiscountUsage.STATUS_RESERVED, DiscountUsage.STATUS_CONFIRMED)
        )
        usage_count = counted_usages.count()

        if self.usage_limit_total is not None and usage_count >= self.usage_limit_total:
            return False, 'Discount code usage limit reached'

        if self.min_order_amount is not None and order_total < self.min_order_amount:
            return False, f'Minimum order amount is {self.min_order_amount}'

        if self.usage_limit_per_user is not None and self.usage_limit_per_user > 0:
            identifier = str(user.id) if user and user.is_authenticated else email
            if identifier:
                user_usage = counted_usages.filter(identifier=identifier).count()
                if user_usage >= self.usage_limit_per_user:
                    return False, 'You have already used this discount code the maximum number of times'

        return True, ''

    def calculate_discount(self, order_total: Decimal) -> Decimal:
        if self.discount_type == 'percentage':
            discount = (order_total * self.value) / Decimal('100')
            if self.max_discount_amount is not None:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = self.value

        return min(discount, order_total)

    def applies_to_order(self, order: Order) -> bool:
        if self.applies_to == 'all':
            return True

        lines = order.lines.select_related('variant__product').all()

        if self.applies_to == 'products':
            product_ids = {str(pid) for pid in self.product_ids}
            return any(
                line.variant and str(line.variant.product_id) in product_ids
                for line in lines
            )

        if self.applies_to == 'collections':
            collection_ids = {str(cid) for cid in self.collection_ids}
            product_ids = {
                str(line.variant.product_id)
                for line in lines
                if line.variant
            }
            if not product_ids:
                return False
            return Collection.objects.filter(
                id__in=collection_ids,
                products__id__in=product_ids,
            ).exists()

        return False


class DiscountUsage(models.Model):
    STATUS_RESERVED = 'reserved'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CHOICES = [
        (STATUS_RESERVED, 'Reserved'),
        (STATUS_CONFIRMED, 'Confirmed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discount_code = models.ForeignKey(DiscountCode, related_name='usages', on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='discount_usages', on_delete=models.CASCADE, null=True, blank=True)
    identifier = models.CharField(max_length=255, blank=True, db_index=True)
    amount_saved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RESERVED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'discount_code'],
                name='unique_order_discount_code',
            ),
        ]
