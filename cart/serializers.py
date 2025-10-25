from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductListSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    line_total = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'variant', 'quantity', 'price',
            'line_total', 'is_available', 'created_at'
        ]


class CartItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1, min_value=1)

    class Meta:
        model = CartItem
        fields = ['product_id', 'variant_id', 'quantity']

    def validate(self, attrs):
        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id')
        quantity = attrs.get('quantity')

        from products.models import Product, ProductVariant

        try:
            product = Product.objects.get(id=product_id, status='published')
        except Product.DoesNotExist:
            raise serializers.ValidationError({
                'product_id': 'Product not found or not available'
            })

        # Validate variant if provided
        if variant_id:
            try:
                variant = ProductVariant.objects.get(
                    id=variant_id,
                    product=product
                )
                # Check variant stock
                if variant.track_quantity and variant.quantity < quantity:
                    raise serializers.ValidationError({
                        'quantity': f'Only {variant.quantity} items available in stock'
                    })
                attrs['variant'] = variant
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError({
                    'variant_id': 'Variant not found for this product'
                })
        else:
            # Check product stock
            if product.track_quantity and product.quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Only {product.quantity} items available in stock'
                })

        attrs['product'] = product
        return attrs


class CartItemUpdateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, value):
        item = self.instance
        if item.variant:
            if item.variant.track_quantity and item.variant.quantity < value:
                raise serializers.ValidationError(
                    f'Only {item.variant.quantity} items available in stock'
                )
        else:
            if item.product.track_quantity and item.product.quantity < value:
                raise serializers.ValidationError(
                    f'Only {item.product.quantity} items available in stock'
                )
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    total = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items', 'subtotal', 'total',
            'created_at', 'updated_at'
        ]
