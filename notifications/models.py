from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from orders.models import Order
from products.models import Product
import uuid
import json


class NotificationTemplate(models.Model):
    """Reusable templates for different types of notifications"""
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]

    CATEGORY_CHOICES = [
        ('order', 'Order Updates'),
        ('shipping', 'Shipping Updates'),
        ('payment', 'Payment Updates'),
        ('inventory', 'Inventory Alerts'),
        ('marketing', 'Marketing'),
        ('system', 'System Notifications'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('template name'), max_length=100)
    template_type = models.CharField(
        _('template type'),
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='email'
    )
    category = models.CharField(
        _('category'),
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    subject = models.CharField(
        _('email subject'),
        max_length=200,
        blank=True
    )
    subject_template = models.TextField(
        _('subject template'),
        blank=True,
        help_text=_('Jinja2 template for dynamic subjects')
    )
    body_template = models.TextField(
        _('body template'),
        help_text=_('Jinja2 template for notification body')
    )
    is_active = models.BooleanField(_('is active'), default=True)
    variables_help = models.TextField(
        _('variables help'),
        blank=True,
        help_text=_('Documentation for available template variables')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('notification template')
        verbose_name_plural = _('notification templates')
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def render_subject(self, context):
        """Render subject using template"""
        if self.subject_template:
            return render_to_string(
                f"notifications/{self.name}_subject.txt",
                context
            ).strip()
        return self.subject

    def render_body(self, context):
        """Render body using template"""
        return render_to_string(
            f"notifications/{self.name}_body.txt",
            context
        )


class Notification(models.Model):
    """Individual notifications sent to users"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Notification content
    subject = models.CharField(_('subject'), max_length=200)
    message = models.TextField(_('message'))
    notification_type = models.CharField(
        _('notification type'),
        max_length=20,
        choices=NotificationTemplate.CATEGORY_CHOICES
    )

    # Status and tracking
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.CharField(
        _('priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal'
    )

    # Related objects (for context)
    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Delivery information
    email_sent = models.BooleanField(_('email sent'), default=False)
    push_sent = models.BooleanField(_('push sent'), default=False)
    sms_sent = models.BooleanField(_('sms sent'), default=False)

    # Metadata
    context_data = models.JSONField(
        _('context data'),
        blank=True,
        null=True,
        help_text=_('Additional context data for the notification')
    )
    scheduled_for = models.DateTimeField(
        _('scheduled for'),
        blank=True,
        null=True
    )
    sent_at = models.DateTimeField(_('sent at'), blank=True, null=True)
    read_at = models.DateTimeField(_('read at'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.email}: {self.subject}"

    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()

    def mark_as_read(self):
        """Mark notification as read"""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save()

    def send_email(self):
        """Send email notification"""
        try:
            send_mail(
                subject=self.subject,
                message=self.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=False,
            )
            self.email_sent = True
            self.mark_as_sent()
            return True
        except Exception as e:
            self.status = 'failed'
            self.save()
            # Log the error
            print(f"Failed to send email notification: {e}")
            return False

    def should_send(self):
        """Check if notification should be sent now"""
        if self.scheduled_for:
            return timezone.now() >= self.scheduled_for
        return True


class EmailLog(models.Model):
    """Log of all emails sent for auditing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='email_logs'
    )
    recipient = models.EmailField(_('recipient'))
    subject = models.CharField(_('subject'), max_length=200)
    body = models.TextField(_('body'))
    sent_at = models.DateTimeField(_('sent at'), auto_now_add=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[('sent', 'Sent'), ('failed', 'Failed')]
    )
    error_message = models.TextField(_('error message'), blank=True)
    message_id = models.CharField(
        _('message ID'),
        max_length=200,
        blank=True,
        help_text=_('Email service message ID')
    )

    class Meta:
        verbose_name = _('email log')
        verbose_name_plural = _('email logs')
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email to {self.recipient} at {self.sent_at}"


class UserNotificationPreference(models.Model):
    """User preferences for notification types"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Email preferences
    email_order_updates = models.BooleanField(
        _('order updates email'),
        default=True
    )
    email_shipping_updates = models.BooleanField(
        _('shipping updates email'),
        default=True
    )
    email_payment_updates = models.BooleanField(
        _('payment updates email'),
        default=True
    )
    email_inventory_alerts = models.BooleanField(
        _('inventory alerts email'),
        default=False
    )
    email_marketing = models.BooleanField(
        _('marketing emails'),
        default=False
    )

    # Push preferences (for future mobile app)
    push_order_updates = models.BooleanField(
        _('order updates push'),
        default=True
    )
    push_promotions = models.BooleanField(
        _('promotions push'),
        default=False
    )

    # SMS preferences
    sms_order_updates = models.BooleanField(
        _('order updates sms'),
        default=False
    )
    sms_shipping_updates = models.BooleanField(
        _('shipping updates sms'),
        default=False
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user notification preference')
        verbose_name_plural = _('user notification preferences')

    def __str__(self):
        return f"Notification preferences for {self.user.email}"

    def can_send_email(self, notification_type):
        """Check if user allows email for this notification type"""
        preference_map = {
            'order': 'email_order_updates',
            'shipping': 'email_shipping_updates',
            'payment': 'email_payment_updates',
            'inventory': 'email_inventory_alerts',
            'marketing': 'email_marketing',
        }
        preference_field = preference_map.get(notification_type)
        return getattr(self, preference_field, False) if preference_field else True


class InventoryAlert(models.Model):
    """Track inventory alerts for products"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_alerts'
    )
    threshold = models.PositiveIntegerField(
        _('threshold'),
        help_text=_('Alert when stock falls below this number')
    )
    is_active = models.BooleanField(_('is active'), default=True)
    notified_at = models.DateTimeField(_('notified at'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('inventory alert')
        verbose_name_plural = _('inventory alerts')
        unique_together = ['product', 'threshold']

    def __str__(self):
        return f"Inventory alert for {self.product.name} (threshold: {self.threshold})"

    def should_alert(self):
        """Check if alert should be triggered"""
        return (self.is_active and
                self.product.quantity <= self.threshold and
                (not self.notified_at or
                 self.product.updated_at > self.notified_at))
