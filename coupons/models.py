from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from products.models import Product, Category
from orders.models import Order
import uuid
import secrets


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('shipping', 'Free Shipping'),
    ]

    APPLIES_TO_CHOICES = [
        ('all', 'All Products'),
        ('categories', 'Specific Categories'),
        ('products', 'Specific Products'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        _('coupon code'),
        max_length=50,
        unique=True,
        help_text=_('Unique coupon code that customers enter')
    )
    name = models.CharField(_('coupon name'), max_length=100)
    description = models.TextField(_('description'), blank=True)

    # Discount configuration
    discount_type = models.CharField(
        _('discount type'),
        max_length=20,
        choices=DISCOUNT_TYPES,
        default='percentage'
    )
    discount_value = models.DecimalField(
        _('discount value'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Percentage or fixed amount based on discount type')
    )
    applies_to = models.CharField(
        _('applies to'),
        max_length=20,
        choices=APPLIES_TO_CHOICES,
        default='all'
    )

    # Eligibility
    minimum_order_amount = models.DecimalField(
        _('minimum order amount'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    maximum_discount_amount = models.DecimalField(
        _('maximum discount amount'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Maximum discount for percentage coupons')
    )

    # Usage limits
    usage_limit = models.PositiveIntegerField(
        _('usage limit'),
        blank=True,
        null=True,
        help_text=_('Maximum number of times this coupon can be used')
    )
    usage_limit_per_user = models.PositiveIntegerField(
        _('usage limit per user'),
        blank=True,
        null=True,
        help_text=_('Maximum uses per customer')
    )
    used_count = models.PositiveIntegerField(_('used count'), default=0)

    # Date management
    valid_from = models.DateTimeField(_('valid from'), default=timezone.now)
    valid_until = models.DateTimeField(
        _('valid until'),
        blank=True,
        null=True
    )

    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    is_public = models.BooleanField(
        _('is public'),
        default=True,
        help_text=_('Whether this coupon is publicly visible')
    )

    # Related objects
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='coupons'
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='coupons'
    )

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_coupons'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('coupon')
        verbose_name_plural = _('coupons')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
            models.Index(fields=['is_active', 'is_public']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        """Generate a unique coupon code"""
        while True:
            code = secrets.token_urlsafe(8).upper()[:10]
            if not Coupon.objects.filter(code=code).exists():
                return code

    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    @property
    def is_expired(self):
        """Check if coupon has expired"""
        if self.valid_until and timezone.now() > self.valid_until:
            return True
        if self.usage_limit and self.used_count >= self.usage_limit:
            return True
        return False

    def calculate_discount(self, order_amount, cart_items=None):
        """Calculate discount amount for given order amount"""
        if not self.is_valid:
            return 0

        # Check minimum order amount
        if order_amount < self.minimum_order_amount:
            return 0

        discount_amount = 0

        if self.discount_type == 'percentage':
            discount_amount = (order_amount * self.discount_value) / 100
            if self.maximum_discount_amount:
                discount_amount = min(
                    discount_amount, self.maximum_discount_amount)

        elif self.discount_type == 'fixed':
            discount_amount = min(self.discount_value, order_amount)

        elif self.discount_type == 'shipping':
            # Free shipping - this would be handled in shipping calculation
            discount_amount = 0  # Special handling needed

        return discount_amount

    def can_be_used_by_user(self, user):
        """Check if user can use this coupon"""
        if not self.is_valid:
            return False

        if self.usage_limit_per_user:
            user_usage = CouponUsage.objects.filter(
                coupon=self,
                user=user
            ).count()
            if user_usage >= self.usage_limit_per_user:
                return False

        return True

    def mark_used(self, user, order, discount_amount):
        """Mark coupon as used"""
        CouponUsage.objects.create(
            coupon=self,
            user=user,
            order=order,
            discount_amount=discount_amount
        )
        self.used_count += 1
        self.save()


class CouponUsage(models.Model):
    """Track coupon usage by customers"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_usages'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='coupon_usages'
    )
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=10,
        decimal_places=2
    )
    used_at = models.DateTimeField(_('used at'), auto_now_add=True)

    class Meta:
        verbose_name = _('coupon usage')
        verbose_name_plural = _('coupon usages')
        ordering = ['-used_at']
        unique_together = ['coupon', 'order']  # One coupon per order

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"


class CouponRule(models.Model):
    """Advanced rules for coupon application"""
    RULE_TYPES = [
        ('first_order', 'First Order Only'),
        ('specific_customer', 'Specific Customers'),
        ('product_combination', 'Product Combination'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    rule_type = models.CharField(
        _('rule type'),
        max_length=30,
        choices=RULE_TYPES
    )
    configuration = models.JSONField(
        _('configuration'),
        blank=True,
        null=True,
        help_text=_('JSON configuration for the rule')
    )
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('coupon rule')
        verbose_name_plural = _('coupon rules')

    def __str__(self):
        return f"{self.get_rule_type_display()} for {self.coupon.code}"


class CustomerCoupon(models.Model):
    """Coupons assigned to specific customers"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='customer_assignments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_coupons'  # Changed from default
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_coupons_to_users'  # FIX: Different related_name
    )
    assigned_at = models.DateTimeField(_('assigned at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'), blank=True, null=True)
    is_used = models.BooleanField(_('is used'), default=False)
    used_at = models.DateTimeField(_('used at'), blank=True, null=True)

    class Meta:
        verbose_name = _('customer coupon')
        verbose_name_plural = _('customer coupons')
        unique_together = ['coupon', 'user']

    def __str__(self):
        return f"{self.coupon.code} for {self.user.email}"

    @property
    def is_valid(self):
        """Check if customer coupon is valid"""
        if self.is_used:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return self.coupon.is_valid
