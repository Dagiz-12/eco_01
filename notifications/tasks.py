from celery import shared_task
from django.utils import timezone
from django.core.mail import mail_admins
from .models import Notification, InventoryAlert
from .services import NotificationService
from products.models import Product

from django.contrib.auth.models import User


@shared_task
def send_pending_notifications():
    """Send all pending notifications"""
    pending_notifications = Notification.objects.filter(
        status='pending',
        scheduled_for__lte=timezone.now()
    ).select_related('user')

    notification_service = NotificationService()
    successful, failed = notification_service.send_bulk_notifications(
        pending_notifications)

    # Log results
    if failed > 0:
        mail_admins(
            subject='Notification Delivery Report',
            message=f'Successfully sent {successful} notifications. Failed: {failed}'
        )

    return {'successful': successful, 'failed': failed}


@shared_task
def check_inventory_alerts():
    """Check and trigger inventory alerts"""
    alerts_triggered = 0
    inventory_alerts = InventoryAlert.objects.filter(
        is_active=True
    ).select_related('product')

    notification_service = NotificationService()

    for alert in inventory_alerts:
        if alert.should_alert():
            # Create notification for admins
            admins = User.objects.filter(is_staff=True)

            for admin in admins:
                notification = Notification.objects.create(
                    user=admin,
                    subject=f'Low Stock Alert: {alert.product.name}',
                    message=(
                        f"Product '{alert.product.name}' is running low on stock.\n"
                        f"Current quantity: {alert.product.quantity}\n"
                        f"Alert threshold: {alert.threshold}\n"
                        f"Please restock soon."
                    ),
                    notification_type='inventory',
                    priority='high',
                    related_product=alert.product
                )

                notification_service.send_notification(notification)

            alert.notified_at = timezone.now()
            alert.save()
            alerts_triggered += 1

    return alerts_triggered


@shared_task
def cleanup_old_notifications():
    """Clean up old notifications to prevent database bloat"""
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=90)  # Keep 90 days

    deleted_count, _ = Notification.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['read', 'failed']
    ).delete()

    return {'deleted_count': deleted_count}
