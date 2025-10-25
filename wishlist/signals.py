from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Wishlist


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wishlist(sender, instance, created, **kwargs):
    """Automatically create a wishlist when a new user is created"""
    if created:
        Wishlist.objects.get_or_create(user=instance)
