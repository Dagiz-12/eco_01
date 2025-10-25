from django.contrib import admin
from django.utils.html import format_html
from .models import Coupon, CouponUsage, CouponRule, CustomerCoupon
from django.utils import timezone


class CouponUsageInline(admin.TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ['user', 'order', 'discount_amount', 'used_at']
    fields = ['user', 'order', 'discount_amount', 'used_at']
    can_delete = False


class CouponRuleInline(admin.TabularInline):
    model = CouponRule
    extra = 1
    fields = ['rule_type', 'configuration', 'is_active']


class CustomerCouponInline(admin.TabularInline):
    model = CustomerCoupon
    extra = 0
    readonly_fields = ['assigned_at', 'is_used', 'used_at']
    fields = ['user', 'assigned_by', 'assigned_at',
              'expires_at', 'is_used', 'used_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'discount_display', 'applies_to',
        'is_active', 'is_public', 'used_count_display',
        'validity_status', 'created_at'
    ]
    list_filter = [
        'discount_type', 'applies_to', 'is_active', 'is_public',
        'created_at', 'valid_until'
    ]
    search_fields = ['code', 'name', 'description']
    list_editable = ['is_active', 'is_public']
    readonly_fields = [
        'created_at', 'updated_at', 'used_count', 'validity_status'
    ]
    inlines = [CouponUsageInline, CouponRuleInline, CustomerCouponInline]
    actions = ['activate_coupons', 'deactivate_coupons', 'duplicate_coupons']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Discount Configuration', {
            'fields': (
                'discount_type', 'discount_value', 'applies_to',
                'minimum_order_amount', 'maximum_discount_amount'
            )
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'usage_limit_per_user', 'used_count')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_active', 'is_public')
        }),
        ('Applicability', {
            'fields': ('categories', 'products'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def discount_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        elif obj.discount_type == 'fixed':
            return f"${obj.discount_value}"
        elif obj.discount_type == 'shipping':
            return "Free Shipping"
        return ""
    discount_display.short_description = 'Discount'

    def used_count_display(self, obj):
        if obj.usage_limit:
            return f"{obj.used_count}/{obj.usage_limit}"
        return f"{obj.used_count}"
    used_count_display.short_description = 'Usage'

    def validity_status(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: gray;">Inactive</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif not obj.is_valid:
            return format_html('<span style="color: orange;">Invalid</span>')
        else:
            return format_html('<span style="color: green;">Valid</span>')
    validity_status.short_description = 'Status'

    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} coupons activated.')
    activate_coupons.short_description = "Activate selected coupons"

    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} coupons deactivated.')
    deactivate_coupons.short_description = "Deactivate selected coupons"

    def duplicate_coupons(self, request, queryset):
        duplicated_count = 0
        for coupon in queryset:
            new_coupon = Coupon(
                name=f"{coupon.name} (Copy)",
                description=coupon.description,
                discount_type=coupon.discount_type,
                discount_value=coupon.discount_value,
                applies_to=coupon.applies_to,
                minimum_order_amount=coupon.minimum_order_amount,
                maximum_discount_amount=coupon.maximum_discount_amount,
                usage_limit=coupon.usage_limit,
                usage_limit_per_user=coupon.usage_limit_per_user,
                valid_from=coupon.valid_from,
                valid_until=coupon.valid_until,
                is_active=coupon.is_active,
                is_public=coupon.is_public,
                created_by=request.user
            )
            new_coupon.save()
            new_coupon.categories.set(coupon.categories.all())
            new_coupon.products.set(coupon.products.all())
            duplicated_count += 1

        self.message_user(request, f'{duplicated_count} coupons duplicated.')
    duplicate_coupons.short_description = "Duplicate selected coupons"


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = [
        'coupon_code', 'user_email', 'order_number',
        'discount_amount', 'used_at'
    ]
    list_filter = ['used_at', 'coupon__discount_type']
    search_fields = [
        'coupon__code', 'user__email', 'order__order_number'
    ]
    readonly_fields = ['used_at']

    def coupon_code(self, obj):
        return obj.coupon.code
    coupon_code.short_description = 'Coupon'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order'

    def has_add_permission(self, request):
        return False  # Usages are created automatically


@admin.register(CustomerCoupon)
class CustomerCouponAdmin(admin.ModelAdmin):
    list_display = [
        'coupon_code', 'user_email', 'assigned_by_email',
        'is_used', 'assigned_at', 'expires_at'
    ]
    list_filter = ['is_used', 'assigned_at', 'expires_at']
    search_fields = ['coupon__code', 'user__email', 'assigned_by__email']
    readonly_fields = ['assigned_at', 'used_at']
    actions = ['mark_as_used', 'mark_as_unused']

    def coupon_code(self, obj):
        return obj.coupon.code
    coupon_code.short_description = 'Coupon'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def assigned_by_email(self, obj):
        return obj.assigned_by.email if obj.assigned_by else '-'
    assigned_by_email.short_description = 'Assigned By'

    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True, used_at=timezone.now())
        self.message_user(request, f'{updated} coupons marked as used.')
    mark_as_used.short_description = "Mark selected as used"

    def mark_as_unused(self, request, queryset):
        updated = queryset.update(is_used=False, used_at=None)
        self.message_user(request, f'{updated} coupons marked as unused.')
    mark_as_unused.short_description = "Mark selected as unused"
