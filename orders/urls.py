from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

# Router for admin views
router = DefaultRouter()
router.register('admin/orders', views.OrderAdminViewSet,
                basename='admin-order')

urlpatterns = [
    # HTML Pages - REMOVE order detail page from here
    path('checkout/', views.checkout_page, name='checkout'),

    # API Endpoints - KEEP THESE
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/', views.OrderDetailView.as_view(),
         name='order-detail'),  # API endpoint
    path('<int:order_id>/cancel/',
         views.OrderCancelView.as_view(), name='order-cancel'),

    # Admin endpoints
    path('<int:order_id>/update-status/',
         views.OrderStatusUpdateView.as_view(), name='order-update-status'),
    path('stats/', views.OrderStatsView.as_view(), name='order-stats'),

    # Include router URLs
    path('', include(router.urls)),
    path('test-create/', views.TestOrderView.as_view(), name='test-order-create'),
]
