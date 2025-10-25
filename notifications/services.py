from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification, EmailLog


class NotificationService:
    """Service class for handling notification delivery"""

    def send_notification(self, notification):
        """Send a notification through appropriate channels"""
        if not notification.should_send():
            return False

        success = False

        # Send email if user has email preference
        if self.should_send_email(notification):
            success = self.send_email_notification(notification)

        # Future: Add push notifications and SMS here

        if success:
            notification.mark_as_sent()

        return success

    def should_send_email(self, notification):
        """Check if email should be sent for this notification"""
        # For now, send email for all notifications
        # In future, check user preferences
        return True

    def send_email_notification(self, notification):
        """Send email notification"""
        try:
            # Send email
            send_mail(
                subject=notification.subject,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=False,
            )

            # Log the email
            EmailLog.objects.create(
                notification=notification,
                recipient=notification.user.email,
                subject=notification.subject,
                body=notification.message,
                status='sent'
            )

            notification.email_sent = True
            notification.save()

            return True

        except Exception as e:
            # Log the failure
            EmailLog.objects.create(
                notification=notification,
                recipient=notification.user.email,
                subject=notification.subject,
                body=notification.message,
                status='failed',
                error_message=str(e)
            )

            notification.status = 'failed'
            notification.save()

            return False

    def send_bulk_notifications(self, notifications):
        """Send multiple notifications efficiently"""
        successful = 0
        failed = 0

        for notification in notifications:
            if self.send_notification(notification):
                successful += 1
            else:
                failed += 1

        return successful, failed
