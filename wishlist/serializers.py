from rest_framework import serializers
from .models import Wishlist, WishlistItem, WishlistShare
from products.serializers import ProductListSerializer
from users.serializers import UserProfileSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = WishlistItem
        fields = [
            'id', 'product', 'notes', 'priority', 'desired_quantity',
            'line_total', 'added_at', 'updated_at'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at', 'line_total']


class WishlistItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['product', 'notes', 'priority', 'desired_quantity']

    def validate_desired_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    total_value = serializers.ReadOnlyField()
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            'id', 'user', 'name', 'is_public', 'share_token',
            'items', 'item_count', 'total_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'share_token', 'item_count',
            'total_value', 'created_at', 'updated_at'
        ]


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['name', 'is_public']


class WishlistShareSerializer(serializers.ModelSerializer):
    wishlist = WishlistSerializer(read_only=True)
    shared_by = UserProfileSerializer(read_only=True)
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = WishlistShare
        fields = [
            'id', 'wishlist', 'shared_by', 'shared_with_email',
            'message', 'share_url', 'is_active', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'share_url']

    def get_share_url(self, obj):
        request = self.context.get('request')
        if request and obj.wishlist.is_public:
            return obj.wishlist.get_share_url(request)
        return None


class WishlistShareCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistShare
        fields = ['shared_with_email', 'message', 'expires_at']


class PublicWishlistSerializer(serializers.ModelSerializer):
    """Serializer for publicly shared wishlists"""
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    total_value = serializers.ReadOnlyField()
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            'id', 'user', 'name', 'items', 'item_count',
            'total_value', 'created_at'
        ]
        read_only_fields = fields


class MoveToCartSerializer(serializers.Serializer):
    """Serializer for moving wishlist items to cart"""
    item_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )

    def validate_item_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one item ID is required.")
        return value
