from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from products.models import Product
import uuid


class Wishlist(models.Model):
    """User's wishlist containing multiple products"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    name = models.CharField(
        _('wishlist name'),
        max_length=100,
        default='My Wishlist'
    )
    is_public = models.BooleanField(
        _('is public'),
        default=False,
        help_text=_('Whether this wishlist is visible to others')
    )
    share_token = models.UUIDField(
        _('share token'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('wishlist')
        verbose_name_plural = _('wishlists')
        ordering = ['-created_at']

    def __str__(self):
        return f"Wishlist for {self.user.email}"

    @property
    def item_count(self):
        return self.items.count()

    @property
    def total_value(self):
        """Calculate total value of all items in wishlist"""
        return sum(item.product.price for item in self.items.all() if item.product.price)

    def add_product(self, product, notes=''):
        """Add a product to wishlist"""
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=self,
            product=product,
            defaults={'notes': notes}
        )
        if not created and notes:
            wishlist_item.notes = notes
            wishlist_item.save()
        return wishlist_item, created

    def remove_product(self, product):
        """Remove a product from wishlist"""
        deleted_count, _ = WishlistItem.objects.filter(
            wishlist=self,
            product=product
        ).delete()
        return deleted_count > 0

    def contains_product(self, product):
        """Check if product is in wishlist"""
        return self.items.filter(product=product).exists()

    def get_share_url(self, request):
        """Generate shareable URL for public wishlists"""
        if self.is_public:
            return request.build_absolute_uri(
                f'/api/wishlist/shared/{self.share_token}/'
            )
        return None


class WishlistItem(models.Model):
    """Individual item in a wishlist"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Personal notes about this product')
    )
    priority = models.PositiveSmallIntegerField(
        _('priority'),
        default=1,
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')],
        help_text=_('How much you want this item')
    )
    desired_quantity = models.PositiveIntegerField(
        _('desired quantity'),
        default=1
    )
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('wishlist item')
        verbose_name_plural = _('wishlist items')
        ordering = ['-priority', '-added_at']
        unique_together = ['wishlist', 'product']

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.email}'s wishlist"

    @property
    def line_total(self):
        """Calculate line total based on product price and desired quantity"""
        if self.product.price:
            return self.product.price * self.desired_quantity
        return 0

    def move_to_cart(self, cart):
        """Move this item to the user's cart"""
        from cart.models import CartItem

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=self.product,
            defaults={
                'quantity': self.desired_quantity
            }
        )

        if not created:
            cart_item.quantity += self.desired_quantity
            cart_item.save()

        # Remove from wishlist after moving to cart
        self.delete()

        return cart_item, created


class WishlistShare(models.Model):
    """Track wishlist sharing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_wishlists'
    )
    shared_with_email = models.EmailField(
        _('shared with email'),
        blank=True
    )
    message = models.TextField(
        _('sharing message'),
        blank=True
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(
        _('expires at'),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('wishlist share')
        verbose_name_plural = _('wishlist shares')
        ordering = ['-created_at']

    def __str__(self):
        return f"Wishlist shared by {self.shared_by.email}"
