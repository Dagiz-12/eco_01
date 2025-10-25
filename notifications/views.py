from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import (
    Notification, NotificationTemplate, UserNotificationPreference,
    InventoryAlert, EmailLog
)
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    UserNotificationPreferenceSerializer, InventoryAlertSerializer,
    EmailLogSerializer, MarkAsReadSerializer, BulkNotificationCreateSerializer, NotificationTemplateSerializer
)
from .services import NotificationService
from users.models import User


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'status', 'priority']

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related(
            'template', 'related_order', 'related_product'
        ).order_by('-created_at')


class UnreadNotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            status__in=['pending', 'sent']
        ).select_related(
            'template', 'related_order', 'related_product'
        ).order_by('-created_at')


class NotificationDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkAsReadView(generics.GenericAPIView):
    serializer_class = MarkAsReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data['notification_ids']
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            user=request.user
        )

        updated_count = 0
        for notification in notifications:
            if notification.status in ['pending', 'sent']:
                notification.mark_as_read()
                updated_count += 1

        return Response({
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)


class UserNotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        preference, created = UserNotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference


class NotificationTemplateListView(generics.ListAPIView):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return NotificationTemplate.objects.filter(is_active=True)


class NotificationCreateView(generics.CreateAPIView):
    serializer_class = NotificationCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        notification = serializer.save()
        # Send notification immediately if not scheduled
        if notification.should_send():
            notification_service = NotificationService()
            notification_service.send_notification(notification)


class BulkNotificationCreateView(generics.GenericAPIView):
    serializer_class = BulkNotificationCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data['user_ids']
        template_id = serializer.validated_data['template_id']
        context_data = serializer.validated_data.get('context_data', {})
        scheduled_for = serializer.validated_data.get('scheduled_for')

        template = get_object_or_404(NotificationTemplate, id=template_id)
        users = User.objects.filter(id__in=user_ids)

        notification_service = NotificationService()
        created_count = 0

        for user in users:
            # Check user preferences
            preference, _ = UserNotificationPreference.objects.get_or_create(
                user=user)
            if preference.can_send_email(template.category):
                notification = Notification.objects.create(
                    user=user,
                    template=template,
                    subject=template.render_subject(context_data),
                    message=template.render_body(context_data),
                    notification_type=template.category,
                    context_data=context_data,
                    scheduled_for=scheduled_for
                )
                created_count += 1

        return Response({
            'message': f'Created {created_count} notifications',
            'created_count': created_count
        }, status=status.HTTP_201_CREATED)


class InventoryAlertListView(generics.ListCreateAPIView):
    serializer_class = InventoryAlertSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return InventoryAlert.objects.filter(
            is_active=True
        ).select_related('product').order_by('product__name')


class InventoryAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InventoryAlertSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return InventoryAlert.objects.select_related('product')


class EmailLogListView(generics.ListAPIView):
    serializer_class = EmailLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return EmailLog.objects.select_related('notification').order_by('-sent_at')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """Get notification statistics for the current user"""
    user_notifications = Notification.objects.filter(user=request.user)

    stats = {
        'total': user_notifications.count(),
        'unread': user_notifications.filter(status__in=['pending', 'sent']).count(),
        'read': user_notifications.filter(status='read').count(),
        'failed': user_notifications.filter(status='failed').count(),
    }

    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def send_test_notification(request):
    """Send a test notification to the current user"""
    notification_service = NotificationService()

    test_notification = Notification.objects.create(
        user=request.user,
        subject='Test Notification',
        message='This is a test notification from the system.',
        notification_type='system',
        priority='normal'
    )

    success = notification_service.send_notification(test_notification)

    if success:
        return Response({
            'message': 'Test notification sent successfully',
            'notification_id': str(test_notification.id)
        })
    else:
        return Response({
            'error': 'Failed to send test notification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def trigger_inventory_alerts(request):
    """Manually trigger inventory alerts check"""
    from .tasks import check_inventory_alerts

    alerts_triggered = check_inventory_alerts()

    return Response({
        'message': f'Inventory alerts check completed',
        'alerts_triggered': alerts_triggered
    })
