from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage, ProductVariant, ProductAttribute


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'image',
            'is_active', 'product_count', 'children', 'created_at'
        ]

    def get_product_count(self, obj):
        return obj.products.count()

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'website',
            'is_active', 'product_count', 'created_at'
        ]

    def get_product_count(self, obj):
        return obj.products.count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'sku', 'price',
                  'compare_price', 'quantity', 'track_quantity']


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'value']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'category', 'brand',
            'price', 'compare_price', 'discount_percentage', 'quantity',
            'is_in_stock', 'is_low_stock', 'primary_image', 'is_featured',
            'status', 'created_at'
        ]

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        first_image = obj.images.first()
        if first_image:
            return ProductImageSerializer(first_image).data
        return None


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'description', 'images', 'variants', 'attributes', 'sku',
            'barcode', 'cost_per_item', 'low_stock_threshold', 'is_digital',
            'meta_title', 'meta_description', 'published_at'
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category', 'brand',
            'price', 'compare_price', 'cost_per_item', 'sku', 'barcode',
            'track_quantity', 'quantity', 'low_stock_threshold', 'status',
            'is_featured', 'is_digital', 'meta_title', 'meta_description'
        ]

    def create(self, validated_data):
        product = Product.objects.create(**validated_data)
        return product


class ProductSearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    brand = serializers.CharField(required=False)
    min_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False)
    in_stock = serializers.BooleanField(required=False)
    featured = serializers.BooleanField(required=False)

    def validate(self, attrs):
        min_price = attrs.get('min_price')
        max_price = attrs.get('max_price')

        if min_price and max_price and min_price > max_price:
            raise serializers.ValidationError({
                'min_price': 'Minimum price cannot be greater than maximum price'
            })

        return attrs
