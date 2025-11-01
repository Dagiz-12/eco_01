from rest_framework import serializers
from users.models import User
from products.models import Product, Category
from orders.models import Order, OrderItem
from payments.models import Payment
from reviews.models import Review


class UserManagementSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'email_verified', 'date_joined', 'last_login',
            'order_count', 'total_spent', 'is_active'
        ]

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_total_spent(self, obj):
        total = obj.orders.filter(payment_status='paid').aggregate(
            total=serializers.Sum('grand_total')
        )['total']
        return float(total) if total else 0


class ProductManagementSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True)
    total_sold = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'price',
            'is_active', 'is_featured', 'created_at', 'updated_at',
            'total_sold', 'low_stock'
        ]

    def get_total_sold(self, obj):
        return obj.order_items.aggregate(total=serializers.Sum('quantity'))['total'] or 0

    def get_low_stock(self, obj):
        if hasattr(obj, 'inventory'):
            return obj.inventory.quantity <= 10
        return False


class OrderManagementSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='user.email', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'customer_name', 'customer_email',
            'status', 'payment_status', 'payment_method', 'grand_total',
            'created_at', 'updated_at', 'item_count'
        ]

    def get_customer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_item_count(self, obj):
        return obj.items.count()


class OrderDetailManagementSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='user.email', read_only=True)
    items = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'customer_name', 'customer_email',
            'status', 'payment_status', 'payment_method', 'subtotal',
            'shipping_cost', 'tax_amount', 'grand_total', 'items',
            'shipping_address', 'billing_address', 'status_history',
            'created_at', 'updated_at'
        ]

    def get_customer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_items(self, obj):
        from orders.serializers import OrderItemSerializer
        return OrderItemSerializer(obj.items.all(), many=True).data

    def get_status_history(self, obj):
        from orders.serializers import OrderStatusHistorySerializer
        return OrderStatusHistorySerializer(obj.status_history.all(), many=True).data


class PaymentManagementSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        source='order.order_number', read_only=True)
    customer_email = serializers.CharField(
        source='order.user.email', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'customer_email', 'payment_method',
            'amount', 'status', 'transaction_id', 'gateway_response',
            'created_at', 'updated_at'
        ]


class AnalyticsSerializer(serializers.Serializer):
    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(
        max_digits=10, decimal_places=2)
    top_products = serializers.ListField()
    customer_metrics = serializers.DictField()
