from django.urls import path
from . import views

urlpatterns = [
    # User notification endpoints
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('unread/', views.UnreadNotificationListView.as_view(),
         name='unread-notifications'),
    path('stats/', views.notification_stats, name='notification-stats'),
    path('mark-read/', views.MarkAsReadView.as_view(),
         name='mark-notifications-read'),
    path('preferences/', views.UserNotificationPreferenceView.as_view(),
         name='notification-preferences'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(),
         name='notification-detail'),

    # Admin endpoints
    path('admin/templates/', views.NotificationTemplateListView.as_view(),
         name='notification-templates'),
    path('admin/create/', views.NotificationCreateView.as_view(),
         name='create-notification'),
    path('admin/bulk-create/', views.BulkNotificationCreateView.as_view(),
         name='bulk-create-notification'),
    path('admin/test/', views.send_test_notification, name='test-notification'),

    # Inventory alerts
    path('admin/inventory-alerts/',
         views.InventoryAlertListView.as_view(), name='inventory-alerts'),
    path('admin/inventory-alerts/<uuid:pk>/',
         views.InventoryAlertDetailView.as_view(), name='inventory-alert-detail'),
    path('admin/trigger-alerts/', views.trigger_inventory_alerts,
         name='trigger-inventory-alerts'),

    # Email logs
    path('admin/email-logs/', views.EmailLogListView.as_view(), name='email-logs'),
]
