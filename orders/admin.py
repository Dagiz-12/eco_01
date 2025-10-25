from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price', 'line_total', 'created_at']
    fields = ['product', 'variant', 'quantity', 'price', 'line_total']

    def line_total(self, obj):
        return f"${obj.line_total:.2f}"
    line_total.short_description = 'Line Total'


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_at', 'created_by']
    fields = ['old_status', 'new_status', 'note', 'created_by', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user_email', 'status', 'payment_status',
        # CHANGED: actions -> order_actions
        'payment_method', 'grand_total_display', 'created_at', 'order_actions'
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__username']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 'paid_at',
        'shipped_at', 'delivered_at', 'subtotal', 'grand_total'
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method')
        }),
        ('Address Information', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'grand_total')
        }),
        ('Payment & Shipping', {
            'fields': ('payment_id', 'paid_at', 'tracking_number', 'shipped_at', 'delivered_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def grand_total_display(self, obj):
        return f"${obj.grand_total:.2f}"
    grand_total_display.short_description = 'Total'

    def order_actions(self, obj):  # CHANGED: actions -> order_actions
        return format_html(
            '<a href="/admin/orders/order/{}/change/">Edit</a>',
            obj.id
        )
    order_actions.short_description = 'Actions'  # CHANGED: actions -> order_actions


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_number', 'product',
                    'variant', 'quantity', 'price', 'line_total_display']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['created_at', 'line_total']

    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order Number'

    def line_total_display(self, obj):
        return f"${obj.line_total:.2f}"
    line_total_display.short_description = 'Line Total'


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'old_status',
                    'new_status', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__order_number']
    readonly_fields = ['created_at']

    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order Number'

    def has_add_permission(self, request):
        return False  # Status history should only be created automatically
