from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Product, Category, Brand, InventoryHistory


@receiver(pre_save, sender=Product)
def generate_product_slug(sender, instance, **kwargs):
    """
    Automatically generate slug for products if not provided
    """
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug


@receiver(pre_save, sender=Category)
def generate_category_slug(sender, instance, **kwargs):
    """
    Automatically generate slug for categories if not provided
    """
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug


@receiver(pre_save, sender=Brand)
def generate_brand_slug(sender, instance, **kwargs):
    """
    Automatically generate slug for brands if not provided
    """
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        while Brand.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug


@receiver(post_save, sender=Product)
def create_initial_inventory_record(sender, instance, created, **kwargs):
    """
    Create initial inventory history record when product is created
    """
    if created and instance.track_quantity:
        InventoryHistory.objects.create(
            product=instance,
            action='stock_in',
            quantity_change=instance.quantity,
            new_quantity=instance.quantity,
            note='Initial stock'
        )


@receiver(post_save, sender=Product)
def update_published_date(sender, instance, **kwargs):
    """
    Update published_at when product status changes to published
    """
    if instance.status == 'published' and not instance.published_at:
        from django.utils import timezone
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])
