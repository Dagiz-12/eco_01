from rest_framework import serializers
from .models import Coupon, CouponUsage, CouponRule, CustomerCoupon
from products.serializers import CategorySerializer, ProductListSerializer
from users.serializers import UserProfileSerializer


class CouponRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponRule
        fields = [
            'id', 'rule_type', 'configuration', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CouponSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    products = ProductListSerializer(many=True, read_only=True)
    created_by = UserProfileSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    usage_percentage = serializers.SerializerMethodField()
    discount_display = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'description', 'discount_type', 'discount_value',
            'applies_to', 'minimum_order_amount', 'maximum_discount_amount',
            'usage_limit', 'usage_limit_per_user', 'used_count', 'valid_from',
            'valid_until', 'is_active', 'is_public', 'categories', 'products',
            'created_by', 'is_valid', 'is_expired', 'usage_percentage',
            'discount_display', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'used_count', 'created_by', 'is_valid', 'is_expired',
            'usage_percentage', 'created_at', 'updated_at'
        ]

    def get_usage_percentage(self, obj):
        if obj.usage_limit:
            return (obj.used_count / obj.usage_limit) * 100
        return 0

    def get_discount_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}% OFF"
        elif obj.discount_type == 'fixed':
            return f"${obj.discount_value} OFF"
        elif obj.discount_type == 'shipping':
            return "FREE SHIPPING"
        return ""


class CouponCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'name', 'description', 'discount_type', 'discount_value',
            'applies_to', 'minimum_order_amount', 'maximum_discount_amount',
            'usage_limit', 'usage_limit_per_user', 'valid_from', 'valid_until',
            'is_active', 'is_public', 'categories', 'products'
        ]

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Discount value must be positive.")
        return value

    def validate(self, attrs):
        discount_type = attrs.get('discount_type')
        discount_value = attrs.get('discount_value')

        if discount_type == 'percentage' and discount_value > 100:
            raise serializers.ValidationError({
                'discount_value': 'Percentage discount cannot exceed 100%.'
            })

        return attrs


class CouponUsageSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    coupon_name = serializers.CharField(source='coupon.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    order_number = serializers.CharField(
        source='order.order_number', read_only=True)

    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'coupon_code', 'coupon_name', 'user', 'user_email',
            'order', 'order_number', 'discount_amount', 'used_at'
        ]
        read_only_fields = fields


class CustomerCouponSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = CustomerCoupon
        fields = [
            'id', 'coupon', 'user', 'assigned_by', 'assigned_at',
            'expires_at', 'is_used', 'used_at', 'is_valid'
        ]
        read_only_fields = [
            'id', 'assigned_at', 'is_used', 'used_at', 'is_valid'
        ]


class ValidateCouponSerializer(serializers.Serializer):
    """Serializer for coupon validation"""
    code = serializers.CharField(max_length=50)
    order_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    def validate_code(self, value):
        if not value.strip():
            raise serializers.ValidationError("Coupon code is required.")
        return value.strip().upper()


class CouponValidationResponseSerializer(serializers.Serializer):
    """Serializer for coupon validation response"""
    valid = serializers.BooleanField()
    coupon = CouponSerializer(required=False)
    discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class AssignCouponSerializer(serializers.Serializer):
    """Serializer for assigning coupons to customers"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    coupon_id = serializers.UUIDField(required=True)
    expires_at = serializers.DateTimeField(required=False)

    def validate_user_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one user ID is required.")
        return value
