from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from products.models import Product, ProductVariant
from cart.models import Cart, CartItem
import uuid


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]

    # Order Identification
    order_number = models.CharField(
        _('order number'),
        max_length=20,
        unique=True,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    # Order Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )

    # Address Information (snapshot at time of order)
    shipping_address = models.JSONField(_('shipping address'))
    billing_address = models.JSONField(_('billing address'))

    # Pricing
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2
    )
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    grand_total = models.DecimalField(
        _('grand total'),
        max_digits=10,
        decimal_places=2
    )

    # Payment Information
    payment_id = models.CharField(
        _('payment ID'),
        max_length=100,
        blank=True
    )
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)

    # Shipping Information
    tracking_number = models.CharField(
        _('tracking number'),
        max_length=100,
        blank=True
    )
    shipped_at = models.DateTimeField(_('shipped at'), null=True, blank=True)
    delivered_at = models.DateTimeField(
        _('delivered at'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'payment_status']),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate unique order number"""
        timestamp = timezone.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"ORD-{timestamp}-{unique_id}"

    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed']

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    @property
    def is_completed(self):
        return self.status == 'delivered'

    def calculate_totals(self):
        """Calculate order totals from items"""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.grand_total = self.subtotal + self.tax_amount + \
            self.shipping_cost - self.discount_amount
        self.save()

    def create_from_cart(self, cart, shipping_address, billing_address, payment_method):
        """Create order from cart"""
        from products.models import InventoryHistory

        # Create order
        self.user = cart.user
        self.shipping_address = shipping_address
        self.billing_address = billing_address
        self.payment_method = payment_method
        self.subtotal = cart.subtotal
        self.grand_total = cart.subtotal  # Tax and shipping will be added later

        self.save()

        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=self,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=cart_item.price
            )

            # Update inventory
            if cart_item.variant:
                if cart_item.variant.track_quantity:
                    cart_item.variant.quantity -= cart_item.quantity
                    cart_item.variant.save()

                    # Record inventory history
                    InventoryHistory.objects.create(
                        product=cart_item.product,
                        action='sold',
                        quantity_change=-cart_item.quantity,
                        new_quantity=cart_item.variant.quantity,
                        note=f"Order #{self.order_number}"
                    )
            else:
                if cart_item.product.track_quantity:
                    cart_item.product.quantity -= cart_item.quantity
                    cart_item.product.save()

                    # Record inventory history
                    InventoryHistory.objects.create(
                        product=cart_item.product,
                        action='sold',
                        quantity_change=-cart_item.quantity,
                        new_quantity=cart_item.product.quantity,
                        note=f"Order #{self.order_number}"
                    )

        # Clear the cart
        cart.clear()

        return self


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(_('quantity'))
    price = models.DecimalField(
        _('price at purchase'),
        max_digits=10,
        decimal_places=2
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
        ordering = ['created_at']

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{variant_str}"

    @property
    def line_total(self):
        return self.quantity * self.price


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(_('old status'), max_length=20)
    new_status = models.CharField(_('new status'), max_length=20)
    note = models.TextField(_('note'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('order status history')
        verbose_name_plural = _('order status history')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order.order_number} - {self.old_status} → {self.new_status}"


class OrderManager:
    @staticmethod
    def create_order_from_cart(user, cart, address_data, payment_method):
        """Create a new order from user's cart"""
        from users.models import Address

        # Get addresses
        shipping_address = Address.objects.get(
            id=address_data['shipping_address_id'],
            user=user
        )
        billing_address = Address.objects.get(
            id=address_data['billing_address_id'],
            user=user
        )

        # Create address snapshots
        shipping_snapshot = {
            'street': shipping_address.street,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'country': shipping_address.country,
            'zip_code': shipping_address.zip_code
        }

        billing_snapshot = {
            'street': billing_address.street,
            'city': billing_address.city,
            'state': billing_address.state,
            'country': billing_address.country,
            'zip_code': billing_address.zip_code
        }

        # Create order
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_snapshot,
            billing_address=billing_snapshot,
            payment_method=payment_method,
            subtotal=cart.subtotal,
            grand_total=cart.subtotal  # Will be updated with tax/shipping
        )

        # Create order items and update inventory
        order.create_from_cart(cart, shipping_snapshot,
                               billing_snapshot, payment_method)

        return order
