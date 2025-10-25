from rest_framework import serializers
from .models import (
    Notification, NotificationTemplate, UserNotificationPreference,
    InventoryAlert, EmailLog
)
from users.serializers import UserProfileSerializer


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'category', 'subject',
            'subject_template', 'body_template', 'is_active',
            'variables_help', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    template_name = serializers.CharField(
        source='template.name',
        read_only=True
    )
    related_order_number = serializers.CharField(
        source='related_order.order_number',
        read_only=True
    )
    related_product_name = serializers.CharField(
        source='related_product.name',
        read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'template', 'template_name', 'subject', 'message',
            'notification_type', 'status', 'priority', 'related_order',
            'related_order_number', 'related_product', 'related_product_name',
            'email_sent', 'push_sent', 'sms_sent', 'context_data',
            'scheduled_for', 'sent_at', 'read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'sent_at', 'read_at'
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'user', 'template', 'subject', 'message', 'notification_type',
            'priority', 'related_order', 'related_product', 'context_data',
            'scheduled_for'
        ]


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = UserNotificationPreference
        fields = [
            'id', 'user', 'email_order_updates', 'email_shipping_updates',
            'email_payment_updates', 'email_inventory_alerts', 'email_marketing',
            'push_order_updates', 'push_promotions', 'sms_order_updates',
            'sms_shipping_updates', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class InventoryAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    current_quantity = serializers.IntegerField(
        source='product.quantity',
        read_only=True
    )

    class Meta:
        model = InventoryAlert
        fields = [
            'id', 'product', 'product_name', 'threshold', 'current_quantity',
            'is_active', 'notified_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'notified_at', 'created_at', 'updated_at']


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = [
            'id', 'notification', 'recipient', 'subject', 'body',
            'sent_at', 'status', 'error_message', 'message_id'
        ]
        read_only_fields = fields


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )

    def validate_notification_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one notification ID is required.")
        return value


class BulkNotificationCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple notifications at once"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    template_id = serializers.UUIDField(required=True)
    context_data = serializers.JSONField(required=False)
    scheduled_for = serializers.DateTimeField(required=False)

    def validate_user_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one user ID is required.")
        return value
