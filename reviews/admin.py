from django.contrib import admin
from django.utils.html import format_html
from .models import Review, ReviewImage, ReviewVote, ProductRatingSummary


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1
    readonly_fields = ['created_at']
    fields = ['image', 'alt_text', 'created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'product_name', 'user_email', 'rating_stars', 'title_preview',
        'status', 'is_verified_purchase', 'helpful_votes', 'created_at'
    ]
    list_filter = ['status', 'rating', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__email', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at', 'moderated_at']
    inlines = [ReviewImageInline]
    actions = ['approve_reviews', 'reject_reviews']

    fieldsets = (
        ('Review Information', {
            'fields': ('product', 'user', 'order', 'rating', 'title', 'comment')
        }),
        ('Moderation', {
            'fields': ('status', 'is_verified_purchase', 'helpful_votes')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'moderated_by', 'moderated_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def rating_stars(self, obj):
        return format_html('⭐' * obj.rating)
    rating_stars.short_description = 'Rating'

    def title_preview(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Title'

    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} reviews approved.')
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} reviews rejected.')
    reject_reviews.short_description = "Reject selected reviews"


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'review_product', 'image_preview', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'image_preview']

    def review_product(self, obj):
        return obj.review.product.name
    review_product.short_description = 'Product'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'review_product',
                    'user_email', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['review__product__name', 'user__email']

    def review_product(self, obj):
        return obj.review.product.name
    review_product.short_description = 'Product'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'


@admin.register(ProductRatingSummary)
class ProductRatingSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'product_name', 'average_rating', 'total_reviews',
        'verified_reviews_count', 'updated_at'
    ]
    list_filter = ['updated_at']
    search_fields = ['product__name']
    readonly_fields = ['updated_at']

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

    def has_add_permission(self, request):
        return False  # These are auto-created

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion of rating summaries
