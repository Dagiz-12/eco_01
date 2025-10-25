from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import HomePageContent, NewsletterSubscriber, SiteConfiguration, ContactMessage, FAQ
from django.utils import timezone


@admin.register(HomePageContent)
class HomePageContentAdmin(admin.ModelAdmin):
    list_display = ['section', 'title', 'is_active', 'order', 'updated_at']
    list_filter = ['section', 'is_active', 'created_at']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_sections', 'deactivate_sections']

    fieldsets = (
        ('Section Information', {
            'fields': ('section', 'title', 'subtitle', 'content', 'is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def activate_sections(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} sections activated.')
    activate_sections.short_description = "Activate selected sections"

    def deactivate_sections(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} sections deactivated.')
    deactivate_sections.short_description = "Deactivate selected sections"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'is_active',
                    'subscribed_at', 'unsubscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email', 'user__email']
    readonly_fields = ['subscribed_at', 'unsubscribed_at']
    actions = ['activate_subscribers', 'deactivate_subscribers']

    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(request, f'{updated} subscribers activated.')
    activate_subscribers.short_description = "Activate selected subscribers"

    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(
            is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{updated} subscribers deactivated.')
    deactivate_subscribers.short_description = "Deactivate selected subscribers"


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'contact_email', 'updated_at']
    readonly_fields = ['updated_at']

    def has_add_permission(self, request):
        # Allow only one instance
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_closed']

    fieldsets = (
        ('Message Information', {
            'fields': ('name', 'email', 'subject', 'message', 'status')
        }),
        ('Technical Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        status_colors = {
            'new': 'red',
            'read': 'orange',
            'replied': 'blue',
            'closed': 'green'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def mark_as_read(self, request, queryset):
        updated = queryset.update(status='read')
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = "Mark selected as read"

    def mark_as_replied(self, request, queryset):
        updated = queryset.update(status='replied')
        self.message_user(request, f'{updated} messages marked as replied.')
    mark_as_replied.short_description = "Mark selected as replied"

    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} messages marked as closed.')
    mark_as_closed.short_description = "Mark selected as closed"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_faqs', 'deactivate_faqs']

    fieldsets = (
        ('FAQ Information', {
            'fields': ('question', 'answer', 'category', 'order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def activate_faqs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} FAQs activated.')
    activate_faqs.short_description = "Activate selected FAQs"

    def deactivate_faqs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} FAQs deactivated.')
    deactivate_faqs.short_description = "Deactivate selected FAQs"
