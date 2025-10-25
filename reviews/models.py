from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product
from orders.models import Order
import uuid
from django.utils import timezone
from django.db.models import Sum


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star - Poor'),
        (2, '2 Stars - Fair'),
        (3, '3 Stars - Good'),
        (4, '4 Stars - Very Good'),
        (5, '5 Stars - Excellent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('The order this review is associated with')
    )

    # Review content
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('review title'), max_length=200)
    comment = models.TextField(_('review comment'))

    # Moderation
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_verified_purchase = models.BooleanField(
        _('verified purchase'),
        default=False
    )
    helpful_votes = models.PositiveIntegerField(
        _('helpful votes'),
        default=0
    )

    # Metadata
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    moderated_at = models.DateTimeField(
        _('moderated at'), blank=True, null=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        unique_together = ['product', 'user']
        indexes = [
            models.Index(fields=['product', 'status', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email}"

    def save(self, *args, **kwargs):
        # Auto-verify purchase if order is provided
        if self.order and self.order.user == self.user:
            self.is_verified_purchase = True
        super().save(*args, **kwargs)

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_pending(self):
        return self.status == 'pending'

    def mark_as_helpful(self):
        """Increment helpful votes"""
        self.helpful_votes += 1
        self.save(update_fields=['helpful_votes'])

    def approve(self, moderator):
        """Approve the review"""
        self.status = 'approved'
        self.moderated_at = timezone.now()
        self.moderated_by = moderator
        self.save()

    def reject(self, moderator, reason=""):
        """Reject the review"""
        self.status = 'rejected'
        self.moderated_at = timezone.now()
        self.moderated_by = moderator
        self.save()


class ReviewImage(models.Model):
    """Images attached to reviews"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        _('review image'),
        upload_to='review_images/%Y/%m/'
    )
    alt_text = models.CharField(
        _('alt text'),
        max_length=200,
        blank=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('review image')
        verbose_name_plural = _('review images')

    def __str__(self):
        return f"Image for {self.review}"


class ReviewVote(models.Model):
    """Track user votes on reviews (helpful/not helpful)"""
    VOTE_TYPES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_votes'
    )
    vote_type = models.CharField(
        _('vote type'),
        max_length=20,
        choices=VOTE_TYPES
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('review vote')
        verbose_name_plural = _('review votes')
        unique_together = ['review', 'user']

    def __str__(self):
        return f"{self.vote_type} vote by {self.user.email}"


class ProductRatingSummary(models.Model):
    """Pre-calculated rating summary for products"""
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='rating_summary'
    )

    # Rating counts
    total_reviews = models.PositiveIntegerField(_('total reviews'), default=0)
    average_rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        default=0.00
    )

    # Rating distribution
    rating_1_count = models.PositiveIntegerField(_('1 star count'), default=0)
    rating_2_count = models.PositiveIntegerField(_('2 stars count'), default=0)
    rating_3_count = models.PositiveIntegerField(_('3 stars count'), default=0)
    rating_4_count = models.PositiveIntegerField(_('4 stars count'), default=0)
    rating_5_count = models.PositiveIntegerField(_('5 stars count'), default=0)

    # Verified purchases
    verified_reviews_count = models.PositiveIntegerField(
        _('verified reviews count'),
        default=0
    )

    # Helpful metrics
    total_helpful_votes = models.PositiveIntegerField(
        _('total helpful votes'),
        default=0
    )

    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('product rating summary')
        verbose_name_plural = _('product rating summaries')

    def __str__(self):
        return f"Rating summary for {self.product.name}"

    def update_summary(self):
        """Update the rating summary based on current reviews"""
        from django.db.models import Avg, Count, Q

        reviews = self.product.reviews.filter(status='approved')

        # Basic counts
        self.total_reviews = reviews.count()
        self.verified_reviews_count = reviews.filter(
            is_verified_purchase=True
        ).count()

        # Average rating
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        self.average_rating = avg_rating or 0.00

        # Rating distribution
        rating_counts = reviews.values(
            'rating').annotate(count=Count('rating'))
        rating_map = {1: 'rating_1_count', 2: 'rating_2_count',
                      3: 'rating_3_count', 4: 'rating_4_count', 5: 'rating_5_count'}

        # Reset counts
        for count_field in rating_map.values():
            setattr(self, count_field, 0)

        # Update counts
        for item in rating_counts:
            rating = item['rating']
            count = item['count']
            if rating in rating_map:
                setattr(self, rating_map[rating], count)

        # Total helpful votes
        self.total_helpful_votes = reviews.aggregate(
            total=Sum('helpful_votes')
        )['total'] or 0

        self.save()

    def get_rating_percentage(self, rating):
        """Get percentage of reviews for a specific rating"""
        if self.total_reviews == 0:
            return 0
        count = getattr(self, f'rating_{rating}_count', 0)
        return (count / self.total_reviews) * 100
