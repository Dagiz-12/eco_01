from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from users.models import User


class Category(models.Model):
    name = models.CharField(_('category name'), max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})


class Brand(models.Model):
    name = models.CharField(_('brand name'), max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('brand')
        verbose_name_plural = _('brands')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Basic Information
    name = models.CharField(_('product name'), max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(_('description'))
    short_description = models.TextField(
        _('short description'), max_length=500, blank=True)

    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='products'
    )

    # Pricing
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2
    )
    compare_price = models.DecimalField(
        _('compare at price'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Original price for showing discounts')
    )
    cost_per_item = models.DecimalField(
        _('cost per item'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Cost price for profit calculation')
    )

    # Inventory
    sku = models.CharField(_('SKU'), max_length=100, unique=True)
    barcode = models.CharField(_('barcode'), max_length=100, blank=True)
    track_quantity = models.BooleanField(_('track quantity'), default=True)
    quantity = models.IntegerField(_('quantity'), default=0)
    low_stock_threshold = models.IntegerField(
        _('low stock threshold'), default=5)

    # Status & Metadata
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_featured = models.BooleanField(_('is featured'), default=False)
    is_digital = models.BooleanField(_('is digital product'), default=False)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['status']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self):
        return self.quantity > 0 if self.track_quantity else True

    @property
    def is_low_stock(self):
        return self.track_quantity and self.quantity <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    @property
    def wishlist_count(self):
        """Number of times this product has been added to wishlists"""
        return self.wishlist_items.count()

    # Add this method to products/models.py in Product class

    @property
    def primary_image(self):
        """Get the primary product image or first available image"""
        primary = self.images.filter(is_primary=True).first()
        if primary and primary.image:
            return primary.image.url  # FIX: Add .url to get the actual URL
        first_image = self.images.first()
        return first_image.image.url if first_image and first_image.image else None


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        _('image'),
        upload_to='products/'
    )
    alt_text = models.CharField(
        _('alt text'),
        max_length=200,
        blank=True
    )
    is_primary = models.BooleanField(_('is primary image'), default=False)
    order = models.PositiveIntegerField(_('display order'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(_('variant name'), max_length=100)
    sku = models.CharField(_('SKU'), max_length=100, unique=True)
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    compare_price = models.DecimalField(
        _('compare at price'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    quantity = models.IntegerField(_('quantity'), default=0)
    track_quantity = models.BooleanField(_('track quantity'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('product variant')
        verbose_name_plural = _('product variants')
        unique_together = ['product', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductAttribute(models.Model):
    name = models.CharField(_('attribute name'), max_length=100)
    value = models.CharField(_('attribute value'), max_length=100)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attributes'
    )

    class Meta:
        verbose_name = _('product attribute')
        verbose_name_plural = _('product attributes')
        unique_together = ['product', 'name']

    def __str__(self):
        return f"{self.name}: {self.value}"


class InventoryHistory(models.Model):
    ACTION_CHOICES = [
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('sold', 'Sold'),
        ('returned', 'Returned'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity_change = models.IntegerField()
    new_quantity = models.IntegerField()
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('inventory history')
        verbose_name_plural = _('inventory history')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.action} - {self.quantity_change}"
