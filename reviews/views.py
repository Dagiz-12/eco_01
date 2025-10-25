from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Review, ReviewImage, ReviewVote, ProductRatingSummary
from .serializers import (
    ReviewSerializer, ReviewCreateSerializer,
    ReviewVoteSerializer, ProductRatingSummarySerializer
)
from products.models import Product
from orders.models import Order


class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'rating', 'is_verified_purchase']

    def get_queryset(self):
        # Only show approved reviews to regular users
        queryset = Review.objects.filter(status='approved').select_related(
            'user', 'product'
        ).prefetch_related('images')

        # Staff users can see all reviews
        if self.request.user.is_staff:
            queryset = Review.objects.all().select_related(
                'user', 'product'
            ).prefetch_related('images')

        # Filter by product if provided
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset.order_by('-created_at')


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Get client IP address
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')

        review = serializer.save(
            user=self.request.user,
            ip_address=ip
        )

        # Update product rating summary
        self.update_rating_summary(review.product)

    def update_rating_summary(self, product):
        """Update the product's rating summary"""
        summary, created = ProductRatingSummary.objects.get_or_create(
            product=product
        )
        summary.update_summary()


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all().select_related('user', 'product')
        return Review.objects.filter(user=self.request.user).select_related('user', 'product')

    def perform_update(self, serializer):
        review = serializer.save()
        # Update rating summary if rating changed
        if 'rating' in serializer.validated_data:
            self.update_rating_summary(review.product)

    def perform_destroy(self, instance):
        product = instance.product
        instance.delete()
        # Update rating summary after deletion
        self.update_rating_summary(product)

    def update_rating_summary(self, product):
        summary, created = ProductRatingSummary.objects.get_or_create(
            product=product
        )
        summary.update_summary()


class UserReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(
            user=self.request.user
        ).select_related('product').prefetch_related('images').order_by('-created_at')


class ReviewVoteView(generics.CreateAPIView):
    serializer_class = ReviewVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        review_id = kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id, status='approved')

        # Check if user already voted
        existing_vote = ReviewVote.objects.filter(
            review=review,
            user=request.user
        ).first()

        if existing_vote:
            # Update existing vote
            serializer = self.get_serializer(existing_vote, data=request.data)
        else:
            # Create new vote
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        if existing_vote:
            # If vote type changed, update helpful votes count
            if existing_vote.vote_type != serializer.validated_data['vote_type']:
                if existing_vote.vote_type == 'helpful':
                    review.helpful_votes -= 1
                elif serializer.validated_data['vote_type'] == 'helpful':
                    review.helpful_votes += 1
        else:
            # New helpful vote
            if serializer.validated_data['vote_type'] == 'helpful':
                review.helpful_votes += 1

        review.save()
        serializer.save(review=review, user=request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductRatingSummaryView(generics.RetrieveAPIView):
    serializer_class = ProductRatingSummarySerializer
    lookup_field = 'product_id'
    lookup_url_kwarg = 'product_id'

    def get_queryset(self):
        return ProductRatingSummary.objects.select_related('product')


class UserCanReviewView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        """
        Check if user can review a product
        - Has purchased the product
        - Hasn't already reviewed it
        """
        product = get_object_or_404(Product, id=product_id)

        # Check if user has purchased the product
        has_purchased = Order.objects.filter(
            user=request.user,
            items__product=product,
            status__in=['completed', 'delivered']
        ).exists()

        # Check if user has already reviewed the product
        has_reviewed = Review.objects.filter(
            user=request.user,
            product=product
        ).exists()

        can_review = has_purchased and not has_reviewed

        return Response({
            'can_review': can_review,
            'has_purchased': has_purchased,
            'has_reviewed': has_reviewed,
            'product_id': product_id,
            'product_name': product.name
        })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def approve_review(request, review_id):
    """Approve a review (admin only)"""
    review = get_object_or_404(Review, id=review_id)
    review.approve(request.user)

    # Update rating summary
    summary, created = ProductRatingSummary.objects.get_or_create(
        product=review.product
    )
    summary.update_summary()

    return Response({
        'message': 'Review approved successfully',
        'review_id': str(review.id)
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def reject_review(request, review_id):
    """Reject a review (admin only)"""
    review = get_object_or_404(Review, id=review_id)
    review.reject(request.user)
    return Response({
        'message': 'Review rejected successfully',
        'review_id': str(review.id)
    })
