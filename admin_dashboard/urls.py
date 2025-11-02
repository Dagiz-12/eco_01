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

    path('api/orders/update-status/<int:order_id>/',
         views.update_order_status, name='api-update-order-status'),


    # Mobile API Endpoints (separate namespace)
    path('mobile-api/', include((mobile_api_patterns, 'mobile-api'))),

    # User Management URLs
    path('api/users/', views.UserManagementAPI.as_view(), name='api-users'),
    path('api/users/stats/', views.UserStatsAPI.as_view(), name='api-users-stats'),
    path('api/users/<int:user_id>/',
         views.UserDetailAPI.as_view(), name='api-user-detail'),
    path('api/users/<int:user_id>/action/',
         views.user_action, name='api-user-action'),
    path('api/users/verify/<int:user_id>/',
         views.verify_user, name='api-verify-user'),
    path('api/users/bulk-actions/', views.BulkUserActionsAPI.as_view(),
         name='api-users-bulk-actions'),
    path('api/users/export/', views.export_users_csv, name='api-users-export'),



    # Enhanced Product Management APIs
    path('api/products/stats/', views.ProductStatsAPI.as_view(),
         name='api-products-stats'),
    path('api/products/enhanced/', views.EnhancedProductManagementAPI.as_view(),
         name='api-products-enhanced'),
    path('api/products/<int:product_id>/',
         views.ProductDetailAPI.as_view(), name='api-product-detail'),
    path('api/products/<int:product_id>/quick-edit/',
         views.quick_edit_product, name='api-product-quick-edit'),
    path('api/products/<int:product_id>/inventory/',
         views.update_product_inventory, name='api-product-inventory'),
    path('api/products/bulk-actions/', views.BulkProductActionsAPI.as_view(),
         name='api-products-bulk-actions'),
    path('api/products/export/', views.export_products_csv,
         name='api-products-export'),
]
