from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserNotificationPreference
from orders.models import Order
from payments.models import Payment
from .services import NotificationService


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    """Automatically create notification preferences for new users"""
    if created:
        UserNotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=Order)
def send_order_status_notification(sender, instance, created, **kwargs):
    """Send notifications for order status changes"""
    if not created:  # Only for updates
        notification_service = NotificationService()

        # Determine notification type based on status change
        if instance.status == 'confirmed':
            subject = f'Order Confirmed: {instance.order_number}'
            message = f'Your order {instance.order_number} has been confirmed and is being processed.'
            notification_type = 'order'

        elif instance.status == 'shipped':
            subject = f'Order Shipped: {instance.order_number}'
            message = f'Your order {instance.order_number} has been shipped. Tracking: {instance.tracking_number or "N/A"}'
            notification_type = 'shipping'

        elif instance.status == 'delivered':
            subject = f'Order Delivered: {instance.order_number}'
            message = f'Your order {instance.order_number} has been delivered. Thank you for shopping with us!'
            notification_type = 'shipping'

        else:
            return

        # Create and send notification
        notification = instance.notifications.create(
            user=instance.user,
            subject=subject,
            message=message,
            notification_type=notification_type,
            related_order=instance
        )

        notification_service.send_notification(notification)


@receiver(post_save, sender=Payment)
def send_payment_notification(sender, instance, created, **kwargs):
    """Send notifications for payment updates"""
    notification_service = NotificationService()

    if instance.status == 'completed':
        subject = f'Payment Confirmed: Order {instance.order.order_number}'
        message = f'Your payment for order {instance.order.order_number} has been confirmed. Thank you!'
        notification_type = 'payment'

    elif instance.status == 'failed':
        subject = f'Payment Failed: Order {instance.order.order_number}'
        message = f'Your payment for order {instance.order.order_number} has failed. Please try again or contact support.'
        notification_type = 'payment'

    else:
        return

    # Create and send notification
    notification = instance.order.notifications.create(
        user=instance.order.user,
        subject=subject,
        message=message,
        notification_type=notification_type,
        related_order=instance.order
    )

    notification_service.send_notification(notification)
