from rest_framework import serializers
from .models import NewsletterSubscriber, ContactMessage, FAQ, SiteConfiguration


class NewsletterSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']

    def validate_email(self, value):
        # Basic email validation
        if not value or '@' not in value:
            raise serializers.ValidationError(
                "Please enter a valid email address.")
        return value.lower().strip()


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

    def validate_email(self, value):
        if not value or '@' not in value:
            raise serializers.ValidationError(
                "Please enter a valid email address.")
        return value.lower().strip()

    def validate_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Please enter your name.")
        return value.strip()

    def validate_subject(self, value):
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Please enter a subject with at least 5 characters.")
        return value.strip()

    def validate_message(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Please enter a message with at least 10 characters.")
        return value.strip()


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'order', 'is_active']


class SiteConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfiguration
        fields = '__all__'
