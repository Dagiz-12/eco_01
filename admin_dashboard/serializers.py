from rest_framework import serializers
from django.db.models import Sum
from users.models import User
from products.models import Product, Category
from orders.models import Order, OrderItem, OrderStatusHistory
from payments.models import Payment


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
            total=Sum('grand_total')
        )['total']
        return float(total) if total else 0


class ProductManagementSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True)
    total_sold = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'price',
            'is_active', 'is_featured', 'created_at', 'updated_at',
            'total_sold', 'low_stock', 'primary_image', 'quantity', 'status'
        ]

    def get_is_active(self, obj):
        return obj.status == 'published'

    def get_total_sold(self, obj):
        result = obj.order_items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    def get_low_stock(self, obj):
        return obj.quantity <= obj.low_stock_threshold

    def get_primary_image(self, obj):
        return obj.primary_image


class ProductStatsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    published_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_brands = serializers.IntegerField()


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    total_sold = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'category_name', 'brand', 'brand_name',
            'price', 'compare_price', 'cost_per_item', 'sku', 'barcode',
            'quantity', 'low_stock_threshold', 'track_quantity',
            'status', 'is_featured', 'is_digital', 'meta_title', 'meta_description',
            'created_at', 'updated_at', 'published_at',
            'total_sold', 'low_stock', 'primary_image', 'images', 'variants'
        ]

    def get_total_sold(self, obj):
        from django.db.models import Sum
        result = obj.order_items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    def get_low_stock(self, obj):
        return obj.quantity <= obj.low_stock_threshold

    def get_primary_image(self, obj):
        return obj.primary_image

    def get_images(self, obj):
        from products.serializers import ProductImageSerializer
        images = obj.images.all()
        return ProductImageSerializer(images, many=True).data

    def get_variants(self, obj):
        from products.serializers import ProductVariantSerializer
        variants = obj.variants.all()
        return ProductVariantSerializer(variants, many=True).data


class EnhancedProductManagementSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    total_sold = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'brand', 'brand_name',
            'price', 'compare_price', 'quantity', 'low_stock_threshold',
            'status', 'is_featured', 'created_at', 'updated_at',
            'total_sold', 'low_stock', 'primary_image'
        ]

    def get_total_sold(self, obj):
        from django.db.models import Sum
        result = obj.order_items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    def get_low_stock(self, obj):
        return obj.quantity <= obj.low_stock_threshold

    def get_primary_image(self, obj):
        return obj.primary_image


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

# ADD THESE MISSING SERIALIZERS:


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name',
                  'variant', 'quantity', 'price', 'line_total']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.username', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'old_status', 'new_status',
                  'note', 'created_by_name', 'created_at']


class OrderDetailManagementSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='user.email', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

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


class UserDetailSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'email_verified', 'date_joined', 'last_login',
            'order_count', 'total_spent', 'is_active', 'addresses'
        ]

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_total_spent(self, obj):
        from django.db.models import Sum
        total = obj.orders.filter(payment_status='paid').aggregate(
            total=Sum('grand_total')
        )['total']
        return float(total) if total else 0

    def get_addresses(self, obj):
        from users.serializers import AddressSerializer
        addresses = obj.addresses.all()
        return AddressSerializer(addresses, many=True).data
