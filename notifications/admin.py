from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Notification, NotificationTemplate, UserNotificationPreference,
    InventoryAlert, EmailLog
)


class EmailLogInline(admin.TabularInline):
    model = EmailLog
    extra = 0
    readonly_fields = ['sent_at', 'status', 'message_id']
    fields = ['recipient', 'subject', 'status', 'sent_at', 'message_id']
    can_delete = False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'subject_preview', 'notification_type',
        # CHANGED: actions -> notification_actions
        'status_badge', 'priority', 'created_at', 'notification_actions'
    ]
    list_filter = ['notification_type', 'status', 'priority', 'created_at']
    search_fields = [
        'user__email', 'subject', 'message',
        'related_order__order_number', 'related_product__name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'sent_at', 'read_at',
        'email_sent', 'push_sent', 'sms_sent'
    ]
    inlines = [EmailLogInline]
    # This should be a list, not a method
    actions = ['mark_as_sent', 'mark_as_read', 'resend_failed']

    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'template', 'subject', 'message', 'notification_type', 'priority')
        }),
        ('Related Objects', {
            'fields': ('related_order', 'related_product', 'context_data'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'scheduled_for')
        }),
        ('Delivery Status', {
            'fields': ('email_sent', 'push_sent', 'sms_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'read_at')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def subject_preview(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Subject'

    def status_badge(self, obj):
        status_colors = {
            'pending': 'orange',
            'sent': 'blue',
            'delivered': 'green',
            'read': 'green',
            'failed': 'red'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    # CHANGED: actions -> notification_actions
    def notification_actions(self, obj):
        links = []
        if obj.status in ['pending', 'failed']:
            links.append(
                f'<a href="/admin/notifications/notification/{obj.id}/resend/">Resend</a>')
        return format_html(' | '.join(links))
    # CHANGED: actions -> notification_actions
    notification_actions.short_description = 'Actions'

    def mark_as_sent(self, request, queryset):
        updated = queryset.update(status='sent')
        self.message_user(request, f'{updated} notifications marked as sent.')
    mark_as_sent.short_description = "Mark selected as sent"

    def mark_as_read(self, request, queryset):
        updated = queryset.update(status='read')
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected as read"

    def resend_failed(self, request, queryset):
        from .services import NotificationService
        service = NotificationService()
        resent_count = 0

        for notification in queryset.filter(status='failed'):
            if service.send_notification(notification):
                resent_count += 1

        self.message_user(
            request, f'Resent {resent_count} failed notifications.')
    resend_failed.short_description = "Resend failed notifications"


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'category', 'is_active',
        'created_at', 'updated_at'
    ]
    list_filter = ['template_type', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'body_template']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    actions = []  # Explicitly define actions as empty list

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'category', 'is_active')
        }),
        ('Content', {
            'fields': ('subject', 'subject_template', 'body_template')
        }),
        ('Help', {
            'fields': ('variables_help',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'email_order_updates', 'email_shipping_updates',
        'email_marketing', 'updated_at'
    ]
    list_filter = [
        'email_order_updates', 'email_shipping_updates',
        'email_marketing', 'updated_at'
    ]
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    actions = []  # Explicitly define actions as empty list

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Email Preferences', {
            'fields': (
                'email_order_updates', 'email_shipping_updates',
                'email_payment_updates', 'email_inventory_alerts',
                'email_marketing'
            )
        }),
        ('Push Preferences', {
            'fields': ('push_order_updates', 'push_promotions'),
            'classes': ('collapse',)
        }),
        ('SMS Preferences', {
            'fields': ('sms_order_updates', 'sms_shipping_updates'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'


@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = [
        'product_name', 'threshold', 'current_quantity',
        'is_active', 'notified_at', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__name']
    list_editable = ['threshold', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'notified_at']
    actions = ['check_alerts']  # This is correct - a list of method names

    fieldsets = (
        ('Alert Configuration', {
            'fields': ('product', 'threshold', 'is_active')
        }),
        ('Status', {
            'fields': ('notified_at',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

    def current_quantity(self, obj):
        return obj.product.quantity
    current_quantity.short_description = 'Current Quantity'

    def check_alerts(self, request, queryset):
        from .tasks import check_inventory_alerts
        alerts_triggered = check_inventory_alerts()
        self.message_user(
            request, f'Triggered {alerts_triggered} inventory alerts.')
    check_alerts.short_description = "Check selected alerts"


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = [
        'recipient', 'subject_preview', 'status_badge',
        'sent_at', 'message_id_preview'
    ]
    list_filter = ['status', 'sent_at']
    search_fields = ['recipient', 'subject', 'message_id']
    readonly_fields = ['sent_at']
    actions = []  # Explicitly define actions as empty list

    def subject_preview(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Subject'

    def status_badge(self, obj):
        color = 'green' if obj.status == 'sent' else 'red'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def message_id_preview(self, obj):
        return obj.message_id[:20] + '...' if obj.message_id and len(obj.message_id) > 20 else obj.message_id or '-'
    message_id_preview.short_description = 'Message ID'

    def has_add_permission(self, request):
        return False  # Email logs are created automatically
