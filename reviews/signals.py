from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review, ReviewVote, ProductRatingSummary


@receiver(post_save, sender=Review)
def update_rating_summary_on_review_save(sender, instance, created, **kwargs):
    """Update product rating summary when review is saved"""
    if instance.status == 'approved' or not created:
        summary, created = ProductRatingSummary.objects.get_or_create(
            product=instance.product
        )
        summary.update_summary()


@receiver(post_delete, sender=Review)
def update_rating_summary_on_review_delete(sender, instance, **kwargs):
    """Update product rating summary when review is deleted"""
    if instance.status == 'approved':
        summary, created = ProductRatingSummary.objects.get_or_create(
            product=instance.product
        )
        summary.update_summary()


@receiver(post_save, sender=ReviewVote)
def update_helpful_votes(sender, instance, created, **kwargs):
    """Update review helpful votes count"""
    if created:
        if instance.vote_type == 'helpful':
            instance.review.helpful_votes += 1
            instance.review.save()
