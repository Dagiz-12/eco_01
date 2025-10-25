from rest_framework import serializers
from .models import Review, ReviewImage, ReviewVote, ProductRatingSummary
from users.serializers import UserProfileSerializer


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'alt_text', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    user_has_voted = serializers.SerializerMethodField()
    user_vote_type = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 'order', 'rating',
            'title', 'comment', 'status', 'is_verified_purchase',
            'helpful_votes', 'images', 'user_has_voted', 'user_vote_type',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'is_verified_purchase', 'helpful_votes',
            'created_at', 'updated_at', 'user_has_voted', 'user_vote_type'
        ]

    def get_user_has_voted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.votes.filter(user=request.user).exists()
        return False

    def get_user_vote_type(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            return vote.vote_type if vote else None
        return None

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        # Check if user has already reviewed this product
        request = self.context.get('request')
        product = attrs.get('product')

        if request and request.user.is_authenticated and product:
            existing_review = Review.objects.filter(
                product=product,
                user=request.user
            ).exists()

            if existing_review and not self.instance:
                raise serializers.ValidationError({
                    'product': 'You have already reviewed this product.'
                })

        return attrs


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['product', 'order', 'rating', 'title', 'comment']

    def validate_order(self, value):
        """Validate that the order belongs to the user and contains the product"""
        request = self.context.get('request')
        if value and value.user != request.user:
            raise serializers.ValidationError("Order does not belong to you.")
        return value


class ReviewVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewVote
        fields = ['id', 'review', 'vote_type', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        review = attrs.get('review')

        # User cannot vote on their own review
        if review.user == request.user:
            raise serializers.ValidationError(
                "You cannot vote on your own review.")

        return attrs


class ProductRatingSummarySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    rating_distribution = serializers.SerializerMethodField()

    class Meta:
        model = ProductRatingSummary
        fields = [
            'product', 'product_name', 'total_reviews', 'average_rating',
            'rating_1_count', 'rating_2_count', 'rating_3_count',
            'rating_4_count', 'rating_5_count', 'verified_reviews_count',
            'total_helpful_votes', 'rating_distribution', 'updated_at'
        ]
        read_only_fields = fields

    def get_rating_distribution(self, obj):
        """Get rating distribution as percentages"""
        if obj.total_reviews == 0:
            return {str(i): 0 for i in range(1, 6)}

        distribution = {}
        for rating in range(1, 6):
            count = getattr(obj, f'rating_{rating}_count')
            percentage = (count / obj.total_reviews) * 100
            distribution[str(rating)] = round(percentage, 1)

        return distribution
