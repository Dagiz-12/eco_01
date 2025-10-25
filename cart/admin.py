from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['price', 'created_at', 'updated_at']
    fields = ['product', 'variant', 'quantity',
              'price', 'line_total', 'created_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key',
                    'total_items', 'subtotal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'session_key']
    readonly_fields = ['created_at', 'updated_at', 'subtotal', 'total_items']
    inlines = [CartItemInline]

    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'

    def subtotal(self, obj):
        return f"${obj.subtotal:.2f}"
    subtotal.short_description = 'Subtotal'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'variant',
                    'quantity', 'price', 'line_total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['cart__user__email', 'product__name', 'variant__name']
    readonly_fields = ['created_at', 'updated_at', 'line_total']

    def line_total(self, obj):
        return f"${obj.line_total:.2f}"
    line_total.short_description = 'Line Total'
