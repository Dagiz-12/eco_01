# payments/serializers.py
from rest_framework import serializers
from .models import Payment, Refund, PaymentGateway, CBETransaction, TeleBirrTransaction
from orders.serializers import OrderListSerializer


# Add these missing serializers at the top of the file
class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        source='order.order_number', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'payment_id', 'order', 'order_number', 'user', 'user_email',
            'payment_method', 'payment_method_display', 'status', 'status_display',
            'amount', 'currency', 'gateway_payment_id', 'created_at', 'updated_at',
            'completed_at', 'failed_at', 'is_successful', 'can_be_refunded'
        ]
        read_only_fields = [
            'payment_id', 'created_at', 'updated_at', 'completed_at', 'failed_at',
            'is_successful', 'can_be_refunded'
        ]


class RefundSerializer(serializers.ModelSerializer):
    payment_id = serializers.UUIDField(
        source='payment.payment_id', read_only=True)
    order_number = serializers.CharField(
        source='payment.order.order_number', read_only=True)
    currency = serializers.CharField(source='payment.currency', read_only=True)

    class Meta:
        model = Refund
        fields = [
            'refund_id', 'payment', 'payment_id', 'order_number', 'amount', 'currency',
            'reason', 'status', 'gateway_refund_id', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'refund_id', 'created_at', 'processed_at', 'gateway_refund_id'
        ]


class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['payment', 'amount', 'reason']


class StripePaymentIntentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='usd')


class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGateway
        fields = [
            'id', 'name', 'is_active', 'test_mode', 'api_key',
            'api_secret', 'webhook_secret', 'additional_config',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'webhook_secret': {'write_only': True},
        }


# ... the rest of your existing serializers remain the same

class CBEPaymentSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=13,
        required=False,
        help_text="Customer phone number for CBE Birr (optional)"
    )


class TeleBirrPaymentSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=13,
        required=False,
        help_text="Customer phone number for TeleBirr (optional)"
    )


class CBETransactionSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        source='payment.order.order_number', read_only=True)
    payment_status = serializers.CharField(
        source='payment.status', read_only=True)

    class Meta:
        model = CBETransaction
        fields = [
            'id', 'transaction_id', 'order_number', 'payment_status', 'status',
            'ussd_code', 'invoice_number', 'created_at', 'updated_at'
        ]
        read_only_fields = ['transaction_id',
                            'status', 'created_at', 'updated_at']


class TeleBirrTransactionSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        source='payment.order.order_number', read_only=True)
    payment_status = serializers.CharField(
        source='payment.status', read_only=True)

    class Meta:
        model = TeleBirrTransaction
        fields = [
            'id', 'transaction_id', 'order_number', 'payment_status', 'status',
            'ussd_code', 'qr_code_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['transaction_id',
                            'status', 'created_at', 'updated_at']


class PaymentCreateSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES)

    # Stripe specific
    stripe_token = serializers.CharField(required=False, allow_blank=True)

    # PayPal specific
    paypal_order_id = serializers.CharField(required=False, allow_blank=True)

    # CBE specific
    cbe_phone = serializers.CharField(
        required=False, allow_blank=True, max_length=13)

    # TeleBirr specific
    telebirr_phone = serializers.CharField(
        required=False, allow_blank=True, max_length=13)

    def validate(self, attrs):
        payment_method = attrs['payment_method']

        if payment_method == 'stripe' and not attrs.get('stripe_token'):
            raise serializers.ValidationError({
                'stripe_token': 'Stripe token is required for Stripe payments'
            })

        if payment_method == 'paypal' and not attrs.get('paypal_order_id'):
            raise serializers.ValidationError({
                'paypal_order_id': 'PayPal order ID is required for PayPal payments'
            })

        if payment_method == 'cbe':
            # CBE phone validation (optional but recommended)
            phone = attrs.get('cbe_phone', '')
            if phone and not phone.startswith('+251'):
                raise serializers.ValidationError({
                    'cbe_phone': 'Phone number should start with +251'
                })

        if payment_method == 'telebirr':
            # TeleBirr phone validation (optional but recommended)
            phone = attrs.get('telebirr_phone', '')
            if phone and not phone.startswith('+251'):
                raise serializers.ValidationError({
                    'telebirr_phone': 'Phone number should start with +251'
                })

        return attrs
