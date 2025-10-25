from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from products.models import Product, ProductVariant


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(
        _('session key'),
        max_length=40,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        indexes = [
            models.Index(fields=['user', 'session_key']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Anonymous Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def total(self):
        # For now, total is same as subtotal. Tax and shipping will be added later.
        return self.subtotal

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()

    def merge_with_session_cart(self, session_cart):
        """Merge session cart with user cart after login"""
        if session_cart and session_cart != self:
            for session_item in session_cart.items.all():
                # Try to find existing item with same product and variant
                existing_item = self.items.filter(
                    product=session_item.product,
                    variant=session_item.variant
                ).first()

                if existing_item:
                    existing_item.quantity += session_item.quantity
                    existing_item.save()
                else:
                    # Create new item in user's cart
                    CartItem.objects.create(
                        cart=self,
                        product=session_item.product,
                        variant=session_item.variant,
                        quantity=session_item.quantity,
                        price=session_item.price
                    )

            # Delete the session cart
            session_cart.delete()


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    price = models.DecimalField(
        _('price at time of adding'),
        max_digits=10,
        decimal_places=2
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ['cart', 'product', 'variant']
        ordering = ['created_at']

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{variant_str}"

    @property
    def line_total(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        # Set price from product or variant if not provided
        if not self.price:
            if self.variant and self.variant.price:
                self.price = self.variant.price
            else:
                self.price = self.product.price
        super().save(*args, **kwargs)

    def is_available(self):
        """Check if the item is still available in inventory"""
        if self.variant:
            return self.variant.track_quantity and self.variant.quantity >= self.quantity
        else:
            return self.product.track_quantity and self.product.quantity >= self.quantity


class CartManager:
    @staticmethod
    def get_or_create_cart(request):
        """
        Get or create cart for authenticated user or anonymous user
        """
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            # Merge session cart if exists
            session_cart_id = request.session.get('cart_id')
            if session_cart_id:
                try:
                    session_cart = Cart.objects.get(
                        id=session_cart_id, user__isnull=True)
                    cart.merge_with_session_cart(session_cart)
                    del request.session['cart_id']
                except Cart.DoesNotExist:
                    pass
            return cart
        else:
            cart_id = request.session.get('cart_id')
            if cart_id:
                try:
                    return Cart.objects.get(id=cart_id, user__isnull=True)
                except Cart.DoesNotExist:
                    pass

            # Create new anonymous cart
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
            return cart
