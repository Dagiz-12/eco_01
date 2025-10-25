from django.contrib import admin
from django.utils.html import format_html
from .models import Wishlist, WishlistItem, WishlistShare


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['added_at', 'updated_at', 'line_total_display']
    fields = ['product', 'notes', 'priority',
              'desired_quantity', 'line_total_display']

    def line_total_display(self, obj):
        return f"${obj.line_total:.2f}" if obj.line_total else "-"
    line_total_display.short_description = 'Total Value'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'name', 'is_public', 'item_count_display',
        'total_value_display', 'created_at'
    ]
    list_filter = ['is_public', 'created_at']
    search_fields = ['user__email', 'user__username', 'name']
    readonly_fields = ['created_at', 'updated_at', 'share_token']
    inlines = [WishlistItemInline]
    actions = ['make_public', 'make_private']

    fieldsets = (
        ('Wishlist Information', {
            'fields': ('user', 'name', 'is_public', 'share_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def item_count_display(self, obj):
        return obj.item_count
    item_count_display.short_description = 'Items'

    def total_value_display(self, obj):
        return f"${obj.total_value:.2f}" if obj.total_value else "-"
    total_value_display.short_description = 'Total Value'

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} wishlists made public.')
    make_public.short_description = "Make selected wishlists public"

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} wishlists made private.')
    make_private.short_description = "Make selected wishlists private"


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = [
        'product_name', 'user_email', 'priority_display',
        'desired_quantity', 'line_total_display', 'added_at'
    ]
    list_filter = ['priority', 'added_at']
    search_fields = [
        'wishlist__user__email', 'product__name', 'notes'
    ]
    readonly_fields = ['added_at', 'updated_at', 'line_total_display']

    fieldsets = (
        ('Item Information', {
            'fields': ('wishlist', 'product', 'notes', 'priority', 'desired_quantity')
        }),
        ('Timestamps', {
            'fields': ('added_at', 'updated_at')
        }),
    )

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

    def user_email(self, obj):
        return obj.wishlist.user.email
    user_email.short_description = 'User'

    def priority_display(self, obj):
        priority_map = {1: '⭐ Low', 2: '⭐⭐ Medium', 3: '⭐⭐⭐ High'}
        return priority_map.get(obj.priority, 'Unknown')
    priority_display.short_description = 'Priority'

    def line_total_display(self, obj):
        return f"${obj.line_total:.2f}" if obj.line_total else "-"
    line_total_display.short_description = 'Line Total'


@admin.register(WishlistShare)
class WishlistShareAdmin(admin.ModelAdmin):
    list_display = [
        'wishlist_user', 'shared_by_email', 'shared_with_email',
        'is_active', 'created_at', 'expires_at_display'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = [
        'wishlist__user__email', 'shared_by__email', 'shared_with_email'
    ]
    readonly_fields = ['created_at']

    fieldsets = (
        ('Sharing Information', {
            'fields': ('wishlist', 'shared_by', 'shared_with_email', 'message')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def wishlist_user(self, obj):
        return obj.wishlist.user.email
    wishlist_user.short_description = 'Wishlist Owner'

    def shared_by_email(self, obj):
        return obj.shared_by.email
    shared_by_email.short_description = 'Shared By'

    def expires_at_display(self, obj):
        return obj.expires_at if obj.expires_at else 'Never'
    expires_at_display.short_description = 'Expires At'

    def has_add_permission(self, request):
        return False  # Shares should be created via API
