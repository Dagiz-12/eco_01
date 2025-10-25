from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import user_logged_in
from .models import Cart, CartItem


@receiver(user_logged_in)
def merge_carts_on_login(sender, request, user, **kwargs):
    """
    Merge anonymous cart with user cart when user logs in
    """
    from .models import CartManager

    session_cart_id = request.session.get('cart_id')
    if session_cart_id:
        try:
            user_cart = Cart.objects.get(user=user)
            session_cart = Cart.objects.get(
                id=session_cart_id, user__isnull=True)
            user_cart.merge_with_session_cart(session_cart)
            del request.session['cart_id']
        except Cart.DoesNotExist:
            pass


@receiver(pre_save, sender=CartItem)
def validate_cart_item_stock(sender, instance, **kwargs):
    """
    Validate stock availability before saving cart item
    """
    if instance.pk:  # Only for updates
        original = CartItem.objects.get(pk=instance.pk)
        if original.quantity != instance.quantity:  # Quantity changed
            if instance.variant:
                if instance.variant.track_quantity and instance.variant.quantity < instance.quantity:
                    raise ValueError(
                        f'Only {instance.variant.quantity} items available in stock')
            else:
                if instance.product.track_quantity and instance.product.quantity < instance.quantity:
                    raise ValueError(
                        f'Only {instance.product.quantity} items available in stock')


@receiver(post_save, sender=CartItem)
def update_cart_timestamp(sender, instance, **kwargs):
    """
    Update cart timestamp when items are modified
    """
    instance.cart.save()  # This triggers auto_now on updated_at
