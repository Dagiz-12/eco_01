from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from orders.models import Order, OrderItem
from products.models import Product
from users.models import User
from .models import AdminNotification, DashboardStats


@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    if created:
        AdminNotification.objects.create(
            title='New Order Received',
            message=f'New order #{instance.order_number} has been placed',
            notification_type='order',
            related_object_id=instance.id
        )


@receiver(post_save, sender=User)
def create_user_verification_notification(sender, instance, created, **kwargs):
    if created and not instance.email_verified:
        AdminNotification.objects.create(
            title='New User Registration',
            message=f'New user {instance.email} registered and needs verification',
            notification_type='user',
            related_object_id=instance.id
        )


@receiver(post_save, sender=Product)
def check_low_stock(sender, instance, **kwargs):
    if hasattr(instance, 'inventory') and instance.inventory.quantity <= 10:
        AdminNotification.objects.create(
            title='Low Stock Alert',
            message=f'Product {instance.name} is running low on stock ({instance.inventory.quantity} remaining)',
            notification_type='inventory',
            related_object_id=instance.id
        )


@receiver(post_save, sender=Order)
@receiver(post_delete, sender=Order)
@receiver(post_save, sender=User)
@receiver(post_delete, sender=User)
def update_dashboard_stats(sender, **kwargs):
    """Update dashboard statistics when relevant models change"""
    from django.utils import timezone
    from datetime import date

    today = date.today()

    # Get or create today's stats
    stats, created = DashboardStats.objects.get_or_create(date=today)

    # Update stats
    stats.total_orders = Order.objects.count()
    stats.total_revenue = Order.objects.filter(payment_status='paid').aggregate(
        total=Sum('grand_total')
    )['total'] or 0
    stats.total_customers = User.objects.filter(role='customer').count()
    stats.total_products = Product.objects.count()
    stats.pending_orders = Order.objects.filter(status='pending').count()

    stats.save()
