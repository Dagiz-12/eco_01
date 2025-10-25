from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    # Coupon list and create
    path('', views.CouponListView.as_view(), name='coupon-list'),
    path('create/', views.CouponCreateView.as_view(), name='coupon-create'),

    # Coupon detail, update, delete
    path('<uuid:pk>/', views.CouponDetailView.as_view(), name='coupon-detail'),
    path('<uuid:pk>/update/', views.CouponUpdateView.as_view(), name='coupon-update'),
    path('<uuid:pk>/delete/', views.CouponDeleteView.as_view(), name='coupon-delete'),

    # Coupon validation and application
    path('validate/', views.ValidateCouponView.as_view(), name='validate-coupon'),
    path('apply/', views.ApplyCouponView.as_view(), name='apply-coupon'),
    path('remove/', views.RemoveCouponView.as_view(), name='remove-coupon'),

    # Customer-specific coupons
    path('my-coupons/', views.UserCouponsListView.as_view(), name='user-coupons'),

    # Admin endpoints
    path('assign-customer/', views.AssignCustomerView.as_view(),
         name='assign-customer'),
    path('usage-stats/<uuid:pk>/',
         views.CouponUsageStatsView.as_view(), name='usage-stats'),

    # Additional endpoints
    path('generate-code/', views.generate_coupon_code, name='generate-code'),
    path('usage/', views.CouponUsageListView.as_view(), name='coupon-usage'),
    path('stats/', views.CouponStatsView.as_view(), name='coupon-stats'),
    path('<uuid:coupon_id>/eligibility/',
         views.check_coupon_eligibility, name='check-eligibility'),
]
