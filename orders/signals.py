from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order, OrderStatusHistory


@receiver(pre_save, sender=Order)
def record_status_change(sender, instance, **kwargs):
    """
    Record status changes in OrderStatusHistory
    """
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed, record it
                OrderStatusHistory.objects.create(
                    order=instance,
                    old_status=old_instance.status,
                    new_status=instance.status,
                    note='Status updated automatically'
                )
        except Order.DoesNotExist:
            pass  # New instance


@receiver(post_save, sender=Order)
def handle_order_completion(sender, instance, created, **kwargs):
    """
    Handle actions when order is completed
    """
    if instance.status == 'delivered' and not instance.paid_at:
        # Mark as paid when delivered (for COD orders)
        from django.utils import timezone
        instance.paid_at = timezone.now()
        instance.payment_status = 'paid'
        instance.save(update_fields=['paid_at', 'payment_status'])


@receiver(post_save, sender=Order)
def send_order_notifications(sender, instance, created, **kwargs):
    """
    Send notifications for order events
    """
    if created:
        # Send order confirmation email
        print(
            f"Order #{instance.order_number} created - sending confirmation email")

    # Send status update notifications
    if not created and instance.status in ['shipped', 'delivered']:
        print(
            f"Order #{instance.order_number} status updated to {instance.status} - sending notification")
