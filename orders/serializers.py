from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from products.serializers import ProductListSerializer, ProductVariantSerializer
from users.serializers import AddressSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'quantity', 'price',
            'line_total', 'created_at'
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(
        source='created_by.email', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'old_status', 'new_status', 'note',
            'created_by_email', 'created_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    can_be_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status', 'payment_method',
            'grand_total', 'items_count', 'can_be_cancelled', 'created_at'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    shipping_address = serializers.JSONField()
    billing_address = serializers.JSONField()
    can_be_cancelled = serializers.ReadOnlyField()
    is_paid = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status', 'payment_method',
            'shipping_address', 'billing_address', 'subtotal', 'tax_amount',
            'shipping_cost', 'discount_amount', 'grand_total', 'items',
            'payment_id', 'paid_at', 'tracking_number', 'shipped_at',
            'delivered_at', 'can_be_cancelled', 'is_paid', 'is_completed',
            'status_history', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.Serializer):
    shipping_address_id = serializers.IntegerField()
    billing_address_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES)

    def validate(self, attrs):
        user = self.context['request'].user

        # Validate shipping address
        from users.models import Address
        try:
            shipping_address = Address.objects.get(
                id=attrs['shipping_address_id'],
                user=user
            )
        except Address.DoesNotExist:
            raise serializers.ValidationError({
                'shipping_address_id': 'Shipping address not found'
            })

        # Validate billing address
        try:
            billing_address = Address.objects.get(
                id=attrs['billing_address_id'],
                user=user
            )
        except Address.DoesNotExist:
            raise serializers.ValidationError({
                'billing_address_id': 'Billing address not found'
            })

        # Validate cart
        cart = self.context['cart']
        if cart.items.count() == 0:
            raise serializers.ValidationError({
                'cart': 'Cart is empty'
            })

        # Validate stock for all items
        for item in cart.items.all():
            if not item.is_available():
                raise serializers.ValidationError({
                    'cart': f'Product {item.product.name} is out of stock'
                })

        attrs['shipping_address'] = shipping_address
        attrs['billing_address'] = billing_address
        return attrs


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status', 'tracking_number']

    def validate_status(self, value):
        instance = self.instance
        if value == 'cancelled' and not instance.can_be_cancelled:
            raise serializers.ValidationError(
                'This order cannot be cancelled'
            )
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        instance = self.context['order']
        if value == 'cancelled' and not instance.can_be_cancelled:
            raise serializers.ValidationError(
                'This order cannot be cancelled'
            )
        return value
