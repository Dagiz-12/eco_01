from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from orders.models import Order
import uuid
import hashlib
import hmac
import time
from django.utils import timezone


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('cbe', 'CBE Birr'),
        ('telebirr', 'TeleBirr'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]

    # Core payment fields
    payment_id = models.UUIDField(
        _('payment ID'), default=uuid.uuid4, unique=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='ETB')

    # Gateway information
    gateway_payment_id = models.CharField(
        _('gateway payment ID'),
        max_length=100,
        blank=True
    )
    gateway_response = models.JSONField(
        _('gateway response'),
        blank=True,
        null=True
    )

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    completed_at = models.DateTimeField(
        _('completed at'), blank=True, null=True)
    failed_at = models.DateTimeField(_('failed at'), blank=True, null=True)

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.payment_id}"

    @property
    def is_successful(self):
        return self.status in ['completed', 'refunded', 'partially_refunded']

    @property
    def can_be_refunded(self):
        return self.status in ['completed', 'partially_refunded']

    def mark_as_completed(self, gateway_payment_id=None, response_data=None):
        self.status = 'completed'
        self.completed_at = timezone.now()
        if gateway_payment_id:
            self.gateway_payment_id = gateway_payment_id
        if response_data:
            self.gateway_response = response_data
        self.save()

    def mark_as_failed(self, response_data=None):
        self.status = 'failed'
        self.failed_at = timezone.now()
        if response_data:
            self.gateway_response = response_data
        self.save()


class Refund(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]

    refund_id = models.UUIDField(
        _('refund ID'), default=uuid.uuid4, unique=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=10,
        decimal_places=2
    )
    reason = models.TextField(_('reason'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    gateway_refund_id = models.CharField(
        _('gateway refund ID'),
        max_length=100,
        blank=True
    )
    gateway_response = models.JSONField(
        _('gateway response'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    processed_at = models.DateTimeField(
        _('processed at'), blank=True, null=True)

    class Meta:
        verbose_name = _('refund')
        verbose_name_plural = _('refunds')

    def __str__(self):
        return f"Refund {self.refund_id} for Payment {self.payment.payment_id}"


class PaymentGateway(models.Model):
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('cbe', 'CBE Birr'),
        ('telebirr', 'TeleBirr'),
    ]

    name = models.CharField(
        _('gateway name'),
        max_length=20,
        choices=GATEWAY_CHOICES,
        unique=True
    )
    is_active = models.BooleanField(_('is active'), default=True)
    test_mode = models.BooleanField(_('test mode'), default=True)
    api_key = models.CharField(
        _('API key'),
        max_length=255,
        blank=True
    )
    api_secret = models.CharField(
        _('API secret'),
        max_length=255,
        blank=True
    )
    webhook_secret = models.CharField(
        _('webhook secret'),
        max_length=255,
        blank=True
    )
    additional_config = models.JSONField(
        _('additional configuration'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('payment gateway')
        verbose_name_plural = _('payment gateways')

    def __str__(self):
        return self.get_name_display()


class CBETransaction(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='cbe_transaction'
    )
    transaction_id = models.CharField(
        _('CBE transaction ID'),
        max_length=100,
        unique=True
    )
    merchant_id = models.CharField(_('merchant ID'), max_length=50)
    terminal_id = models.CharField(_('terminal ID'), max_length=50)
    invoice_number = models.CharField(_('invoice number'), max_length=50)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )
    cbe_response = models.JSONField(_('CBE response'), blank=True, null=True)
    callback_received = models.BooleanField(
        _('callback received'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('CBE transaction')
        verbose_name_plural = _('CBE transactions')

    def __str__(self):
        return f"CBE Transaction {self.transaction_id}"


class TeleBirrTransaction(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='telebirr_transaction'
    )
    transaction_id = models.CharField(
        _('TeleBirr transaction ID'),
        max_length=100,
        unique=True
    )
    short_code = models.CharField(_('short code'), max_length=20)
    app_key = models.CharField(_('app key'), max_length=100, blank=True)
    app_secret = models.CharField(_('app secret'), max_length=100, blank=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )
    telebirr_response = models.JSONField(
        _('TeleBirr response'), blank=True, null=True)
    ussd_code = models.CharField(_('USSD code'), max_length=50, blank=True)
    qr_code_url = models.URLField(_('QR code URL'), blank=True)
    callback_received = models.BooleanField(
        _('callback received'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('TeleBirr transaction')
        verbose_name_plural = _('TeleBirr transactions')

    def __str__(self):
        return f"TeleBirr Transaction {self.transaction_id}"


class PaymentManager:
    GATEWAY_MAP = {
        'stripe': 'StripeGateway',
        'paypal': 'PayPalGateway',
        'cbe': 'CBEGateway',
        'telebirr': 'TeleBirrGateway'
    }

    @staticmethod
    def get_gateway(payment_method):
        """Get gateway instance for payment method"""
        from .gateways import (
            StripeGateway, PayPalGateway, CBEGateway, TeleBirrGateway
        )

        gateway_class = {
            'stripe': StripeGateway,
            'paypal': PayPalGateway,
            'cbe': CBEGateway,
            'telebirr': TeleBirrGateway
        }.get(payment_method)

        if not gateway_class:
            raise ValueError(f"Unsupported payment method: {payment_method}")

        return gateway_class()

    @staticmethod
    def process_payment(payment, **kwargs):
        """Process payment using appropriate gateway"""
        gateway = PaymentManager.get_gateway(payment.payment_method)
        result = gateway.initiate_payment(payment, **kwargs)

        if result['success']:
            payment.mark_as_completed(
                gateway_payment_id=result.get('gateway_payment_id'),
                response_data=result.get('response_data')
            )
        else:
            payment.mark_as_failed(response_data=result.get('response_data'))

        return result['success'], result['message']

    @staticmethod
    def verify_payment(payment_method, transaction_id):
        """Verify payment using gateway"""
        gateway = PaymentManager.get_gateway(payment_method)
        return gateway.verify_payment(transaction_id)

    @staticmethod
    def process_refund(payment, amount, reason):
        """Process refund using gateway"""
        if not payment.can_be_refunded:
            return False, 'Payment cannot be refunded'

        gateway = PaymentManager.get_gateway(payment.payment_method)
        result = gateway.process_refund(payment, amount, reason)

        return result['success'], result['message']

    @staticmethod
    def handle_webhook(payment_method, payload, signature=None):
        """Handle webhook using gateway"""
        gateway = PaymentManager.get_gateway(payment_method)
        return gateway.handle_webhook(payload, signature)

    @staticmethod
    def create_payment(order, payment_method):
        """Create a new payment for an order"""
        payment = Payment.objects.create(
            order=order,
            user=order.user,
            payment_method=payment_method,
            amount=order.grand_total,
            currency='ETB'  # or get from order
        )
        return payment

    @staticmethod
    def process_stripe_payment(payment, stripe_token):
        """Process Stripe payment"""
        # This would integrate with Stripe API
        # For now, return success for testing
        return True, "Stripe payment processed successfully"

    @staticmethod
    def process_paypal_payment(payment, paypal_order_id):
        """Process PayPal payment"""
        # This would integrate with PayPal API
        return True, "PayPal payment processed successfully"

    @staticmethod
    def initiate_cbe_payment(payment, phone_number):
        """Initiate CBE payment"""
        # Create CBE transaction
        cbe_transaction = CBETransaction.objects.create(
            payment=payment,
            transaction_id=f"CBE_{payment.payment_id}",
            merchant_id="TEST_MERCHANT",
            terminal_id="TEST_TERMINAL",
            invoice_number=f"INV_{payment.order.order_number}"
        )
        return True, "CBE payment initiated", {"ussd_code": "*127*..."}

    @staticmethod
    def initiate_telebirr_payment(payment, phone_number):
        """Initiate TeleBirr payment"""
        # Create TeleBirr transaction
        telebirr_transaction = TeleBirrTransaction.objects.create(
            payment=payment,
            transaction_id=f"TELEBIRR_{payment.payment_id}",
            short_code="TEST_SHORT_CODE"
        )
        return True, "TeleBirr payment initiated", {"ussd_code": "*127*..."}

    @staticmethod
    def verify_cbe_payment(transaction_id):
        """Verify CBE payment"""
        try:
            transaction = CBETransaction.objects.get(
                transaction_id=transaction_id)
            transaction.status = 'completed'
            transaction.save()
            transaction.payment.mark_as_completed()
            return True, "CBE payment verified successfully"
        except CBETransaction.DoesNotExist:
            return False, "CBE transaction not found"

    @staticmethod
    def verify_telebirr_payment(transaction_id):
        """Verify TeleBirr payment"""
        try:
            transaction = TeleBirrTransaction.objects.get(
                transaction_id=transaction_id)
            transaction.status = 'completed'
            transaction.save()
            transaction.payment.mark_as_completed()
            return True, "TeleBirr payment verified successfully"
        except TeleBirrTransaction.DoesNotExist:
            return False, "TeleBirr transaction not found"

    @staticmethod
    def handle_cbe_callback(callback_data):
        """Handle CBE webhook callback"""
        # Implement CBE callback handling
        return True, "Callback processed successfully"

    @staticmethod
    def handle_telebirr_callback(callback_data):
        """Handle TeleBirr webhook callback"""
        # Implement TeleBirr callback handling
        return True, "Callback processed successfully"
