from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Product, ProductImage, ProductVariant, ProductAttribute, InventoryHistory


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['name', 'sku', 'price',
              'compare_price', 'quantity', 'track_quantity']


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    fields = ['name', 'value']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent',
                    'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'brand', 'price', 'quantity',
        'status', 'is_featured', 'is_in_stock', 'created_at'
    ]
    list_filter = ['status', 'category', 'brand', 'is_featured', 'created_at']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'quantity', 'status', 'is_featured']
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    inlines = [ProductImageInline,
               ProductVariantInline, ProductAttributeInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description')
        }),
        ('Categorization', {
            'fields': ('category', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'cost_per_item')
        }),
        ('Inventory', {
            'fields': ('sku', 'barcode', 'track_quantity', 'quantity', 'low_stock_threshold')
        }),
        ('Status & SEO', {
            'fields': ('status', 'is_featured', 'is_digital', 'meta_title', 'meta_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
    )

    def is_in_stock(self, obj):
        return obj.is_in_stock
    is_in_stock.boolean = True
    is_in_stock.short_description = 'In Stock'


@admin.register(InventoryHistory)
class InventoryHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'action', 'quantity_change',
                    'new_quantity', 'created_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['product__name', 'note']
    readonly_fields = ['created_at']

    def has_add_permission(self, request):
        return False  # Inventory history should only be created automatically
