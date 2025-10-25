from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import SiteConfiguration


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_site_config(sender, instance, created, **kwargs):
    """Create default site configuration if it doesn't exist"""
    if created and not SiteConfiguration.objects.exists():
        SiteConfiguration.objects.create(
            site_name='HagerBet',
            site_description='Premium E-Commerce Platform',
            contact_email='contact@hagerbet.com'
        )
