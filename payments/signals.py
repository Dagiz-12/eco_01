from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment, Refund


@receiver(post_save, sender=Payment)
def send_payment_notification(sender, instance, created, **kwargs):
    """
    Send email notifications for payment events
    """
    if created:
        # Send payment initiated email
        subject = f"Payment Initiated - Order #{instance.order.order_number}"
        message = f"""
        Dear {instance.user.username},
        
        Your payment for Order #{instance.order.order_number} has been initiated.
        Amount: {instance.amount} {instance.currency}
        Payment Method: {instance.get_payment_method_display()}
        
        Thank you for your purchase!
        
        Best regards,
        Hagerbet E-Commerce Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.user.email],
                fail_silently=True,
            )
            print(f"Payment initiation email sent to {instance.user.email}")
        except Exception as e:
            print(f"Failed to send payment email: {e}")

    # Send payment status update emails
    if not created and instance.status in ['completed', 'failed']:
        if instance.status == 'completed':
            subject = f"Payment Confirmed - Order #{instance.order.order_number}"
            message = f"""
            Dear {instance.user.username},
            
            Your payment for Order #{instance.order.order_number} has been confirmed!
            Amount: {instance.amount} {instance.currency}
            
            Your order is now being processed.
            
            Thank you for your purchase!
            
            Best regards,
            Hagerbet E-Commerce Team
            """
        else:  # failed
            subject = f"Payment Failed - Order #{instance.order.order_number}"
            message = f"""
            Dear {instance.user.username},
            
            Unfortunately, your payment for Order #{instance.order.order_number} has failed.
            Amount: {instance.amount} {instance.currency}
            
            Please try again or contact support if the problem persists.
            
            Best regards,
            Hagerbet E-Commerce Team
            """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.user.email],
                fail_silently=True,
            )
            print(f"Payment status email sent to {instance.user.email}")
        except Exception as e:
            print(f"Failed to send payment status email: {e}")


@receiver(post_save, sender=Refund)
def send_refund_notification(sender, instance, created, **kwargs):
    """
    Send email notifications for refund events
    """
    if created and instance.status == 'processed':
        subject = f"Refund Processed - Order #{instance.payment.order.order_number}"
        message = f"""
        Dear {instance.payment.user.username},
        
        Your refund for Order #{instance.payment.order.order_number} has been processed.
        Refund Amount: {instance.amount} {instance.payment.currency}
        Reason: {instance.reason}
        
        The amount should reflect in your account within 3-5 business days.
        
        Best regards,
        Hagerbet E-Commerce Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.payment.user.email],
                fail_silently=True,
            )
            print(f"Refund email sent to {instance.payment.user.email}")
        except Exception as e:
            print(f"Failed to send refund email: {e}")


@receiver(pre_save, sender=Payment)
def record_payment_status_change(sender, instance, **kwargs):
    """
    Record payment status changes and trigger related actions
    """
    if instance.pk:
        try:
            old_instance = Payment.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                print(
                    f"Payment {instance.payment_id} status changed from {old_instance.status} to {instance.status}")

                # Trigger order status update when payment is completed
                if instance.status == 'completed':
                    instance.order.payment_status = 'paid'
                    instance.order.save()
        except Payment.DoesNotExist:
            pass  # New instance
