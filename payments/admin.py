# payments/admin.py - Use this version
from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, Refund, CBETransaction, TeleBirrTransaction, PaymentGateway


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ['refund_id', 'created_at', 'processed_at']
    fields = ['refund_id', 'amount', 'reason',
              'status', 'gateway_refund_id', 'created_at']


class CBETransactionInline(admin.StackedInline):
    model = CBETransaction
    extra = 0
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    fields = ['transaction_id', 'merchant_id', 'terminal_id',
              'invoice_number', 'status', 'callback_received']


class TeleBirrTransactionInline(admin.StackedInline):
    model = TeleBirrTransaction
    extra = 0
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    fields = ['transaction_id', 'short_code', 'status',
              'ussd_code', 'qr_code_url', 'callback_received']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'order_number', 'user_email',
                    'payment_method', 'status', 'amount_display', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['payment_id', 'order__order_number',
                     'user__email', 'gateway_payment_id']
    readonly_fields = ['payment_id', 'created_at', 'updated_at',
                       'completed_at', 'failed_at', 'order_number', 'user_email']
    inlines = [RefundInline, CBETransactionInline, TeleBirrTransactionInline]
    actions = []

    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'order', 'user', 'payment_method', 'status')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'gateway_payment_id', 'gateway_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'failed_at')
        }),
    )

    def order_number(self, obj):
        return obj.order.order_number if obj.order else 'N/A'
    order_number.short_description = 'Order Number'

    def user_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    user_email.short_description = 'User Email'

    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id', 'payment_id', 'order_number',
                    'amount_display', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['refund_id', 'payment__payment_id',
                     'payment__order__order_number']
    readonly_fields = ['refund_id', 'created_at', 'processed_at']
    actions = []

    def payment_id(self, obj):
        return obj.payment.payment_id if obj.payment else 'N/A'
    payment_id.short_description = 'Payment ID'

    def order_number(self, obj):
        if obj.payment and obj.payment.order:
            return obj.payment.order.order_number
        return 'N/A'
    order_number.short_description = 'Order Number'

    def amount_display(self, obj):
        if obj.payment:
            return f"{obj.amount} {obj.payment.currency}"
        return f"{obj.amount}"
    amount_display.short_description = 'Amount'


@admin.register(CBETransaction)
class CBETransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order_number', 'status',
                    'amount_display', 'callback_received', 'created_at']
    list_filter = ['status', 'callback_received', 'created_at']
    search_fields = ['transaction_id', 'payment__order__order_number']
    readonly_fields = ['transaction_id',
                       'created_at', 'updated_at', 'cbe_response']
    actions = []

    def order_number(self, obj):
        if obj.payment and obj.payment.order:
            return obj.payment.order.order_number
        return 'N/A'
    order_number.short_description = 'Order Number'

    def amount_display(self, obj):
        if obj.payment:
            return f"{obj.payment.amount} {obj.payment.currency}"
        return 'N/A'
    amount_display.short_description = 'Amount'


@admin.register(TeleBirrTransaction)
class TeleBirrTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order_number', 'status',
                    'amount_display', 'ussd_code_display', 'callback_received', 'created_at']
    list_filter = ['status', 'callback_received', 'created_at']
    search_fields = ['transaction_id', 'payment__order__order_number']
    readonly_fields = ['transaction_id', 'created_at',
                       'updated_at', 'telebirr_response']
    actions = []

    def order_number(self, obj):
        if obj.payment and obj.payment.order:
            return obj.payment.order.order_number
        return 'N/A'
    order_number.short_description = 'Order Number'

    def amount_display(self, obj):
        if obj.payment:
            return f"{obj.payment.amount} {obj.payment.currency}"
        return 'N/A'
    amount_display.short_description = 'Amount'

    def ussd_code_display(self, obj):
        return obj.ussd_code or '-'
    ussd_code_display.short_description = 'USSD Code'


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active',
                    'test_mode', 'created_at', 'updated_at']
    list_filter = ['is_active', 'test_mode', 'name']
    list_editable = ['is_active', 'test_mode']
    readonly_fields = ['created_at', 'updated_at']
    actions = []

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active', 'test_mode')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret', 'webhook_secret'),
            'classes': ('collapse',)
        }),
        ('Additional Configuration', {
            'fields': ('additional_config',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['name']
        return self.readonly_fields
