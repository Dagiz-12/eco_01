from django.urls import path, include
from . import views
from . import api_views

app_name = 'admin_dashboard'

# Mobile API Routes (for Flutter app)
mobile_api_patterns = [
    path('stats/', api_views.MobileAdminStatsAPI.as_view(), name='mobile-stats'),
    path('orders/', api_views.MobileOrderListAPI.as_view(), name='mobile-orders'),
    path('orders/<int:order_id>/',
         api_views.MobileOrderDetailAPI.as_view(), name='mobile-order-detail'),
    path('quick-actions/', api_views.MobileQuickActionsAPI.as_view(),
         name='mobile-quick-actions'),
]

urlpatterns = [
    # Dashboard Pages
    path('', views.dashboard_home, name='dashboard-home'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('users/', views.user_management, name='user-management'),
    path('products/', views.product_management, name='product-management'),
    path('orders/', views.order_management, name='order-management'),
    path('payments/', views.payment_management, name='payment-management'),

    # Web API Endpoints
    path('api/stats/', views.DashboardStatsAPI.as_view(), name='api-stats'),
    path('api/notifications/', views.NotificationListAPI.as_view(),
         name='api-notifications'),
    path('api/analytics/sales/', views.SalesAnalyticsAPI.as_view(),
         name='api-sales-analytics'),
    path('api/analytics/users/', views.UserAnalyticsAPI.as_view(),
         name='api-user-analytics'),
    path('api/analytics/products/', views.ProductAnalyticsAPI.as_view(),
         name='api-product-analytics'),

    # Management APIs - ADD THESE
    path('api/orders/', views.OrderManagementAPI.as_view(), name='api-orders'),
    path('api/products/', views.ProductManagementAPI.as_view(), name='api-products'),
    path('api/users/', views.UserManagementAPI.as_view(), name='api-users'),

    # Existing management actions
    path('api/users/verify/<int:user_id>/',
         views.verify_user, name='api-verify-user'),
    path('api/orders/update-status/<int:order_id>/',
         views.update_order_status, name='api-update-order-status'),
    path('api/products/update-inventory/<int:product_id>/',
         views.update_inventory, name='api-update-inventory'),

    # Mobile API Endpoints (separate namespace)
    path('mobile-api/', include((mobile_api_patterns, 'mobile-api'))),
]
