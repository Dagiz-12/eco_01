from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid


class HomePageContent(models.Model):
    """Manage home page content and sections"""
    SECTION_CHOICES = [
        ('hero', 'Hero Section'),
        ('features', 'Features Section'),
        ('testimonials', 'Testimonials Section'),
        ('newsletter', 'Newsletter Section'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.CharField(
        _('section'), max_length=20, choices=SECTION_CHOICES, unique=True)
    title = models.CharField(_('title'), max_length=200, blank=True)
    subtitle = models.TextField(_('subtitle'), blank=True)
    content = models.JSONField(_('content'), blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    order = models.PositiveIntegerField(_('order'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('home page content')
        verbose_name_plural = _('home page contents')
        ordering = ['order', 'section']

    def __str__(self):
        return f"{self.get_section_display()} - {self.title}"


class NewsletterSubscriber(models.Model):
    """Newsletter subscription management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email'), unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletter_subscriptions'
    )
    is_active = models.BooleanField(_('is active'), default=True)
    subscribed_at = models.DateTimeField(_('subscribed at'), auto_now_add=True)
    unsubscribed_at = models.DateTimeField(
        _('unsubscribed at'), blank=True, null=True)

    class Meta:
        verbose_name = _('newsletter subscriber')
        verbose_name_plural = _('newsletter subscribers')
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email

    def unsubscribe(self):
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()


class SiteConfiguration(models.Model):
    """Site-wide configuration settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site_name = models.CharField(
        _('site name'), max_length=100, default='HagerBet')
    site_description = models.TextField(_('site description'), blank=True)
    contact_email = models.EmailField(
        _('contact email'), default='contact@hagerbet.com')
    phone_number = models.CharField(
        _('phone number'), max_length=20, blank=True)
    address = models.TextField(_('address'), blank=True)

    # Social Media
    facebook_url = models.URLField(_('facebook url'), blank=True)
    twitter_url = models.URLField(_('twitter url'), blank=True)
    instagram_url = models.URLField(_('instagram url'), blank=True)
    linkedin_url = models.URLField(_('linkedin url'), blank=True)

    # SEO
    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)
    meta_keywords = models.TextField(_('meta keywords'), blank=True)

    # Features
    enable_registration = models.BooleanField(
        _('enable registration'), default=True)
    enable_reviews = models.BooleanField(_('enable reviews'), default=True)
    enable_wishlist = models.BooleanField(_('enable wishlist'), default=True)

    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('site configuration')
        verbose_name_plural = _('site configuration')

    def __str__(self):
        return "Site Configuration"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValidationError(
                'There can be only one SiteConfiguration instance')
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    """Contact form submissions"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100)
    email = models.EmailField(_('email'))
    subject = models.CharField(_('subject'), max_length=200)
    message = models.TextField(_('message'))
    status = models.CharField(
        _('status'), max_length=20, choices=STATUS_CHOICES, default='new')
    ip_address = models.GenericIPAddressField(
        _('IP address'), blank=True, null=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('contact message')
        verbose_name_plural = _('contact messages')
        ordering = ['-created_at']

    def __str__(self):
        return f"Contact from {self.name} - {self.subject}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('ordering', 'Ordering'),
        ('shipping', 'Shipping'),
        ('payments', 'Payments'),
        ('returns', 'Returns & Refunds'),
        ('account', 'Account'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(_('question'), max_length=200)
    answer = models.TextField(_('answer'))
    category = models.CharField(
        _('category'), max_length=20, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(_('order'), default=0)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['category', 'order', 'question']

    def __str__(self):
        return self.question
