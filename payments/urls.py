from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment endpoints
    path('', views.PaymentListView.as_view(), name='payment-list'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),

    # Order-specific payment creation
    path('order/<int:order_id>/create/',
         views.PaymentCreateView.as_view(), name='payment-create'),

    # Gateway-specific payment initiation
    path('order/<int:order_id>/cbe/',
         views.CBEPaymentInitiateView.as_view(), name='cbe-payment-initiate'),
    path('order/<int:order_id>/telebirr/',
         views.TeleBirrPaymentInitiateView.as_view(), name='telebirr-payment-initiate'),
    path('order/<int:order_id>/stripe/intent/',
         views.StripePaymentIntentView.as_view(), name='stripe-payment-intent'),

    # Payment verification
    path('cbe/<str:transaction_id>/verify/',
         views.CBEVerifyPaymentView.as_view(), name='cbe-verify-payment'),
    path('telebirr/<str:transaction_id>/verify/',
         views.TeleBirrVerifyPaymentView.as_view(), name='telebirr-verify-payment'),

    # Refund endpoints
    path('refunds/', views.RefundListView.as_view(), name='refund-list'),
    path('refunds/create/', views.RefundCreateView.as_view(), name='refund-create'),

    # Webhook endpoints (no authentication required)
    path('webhooks/stripe/', views.StripeWebhookView.as_view(),
         name='stripe-webhook'),
    path('webhooks/cbe/', views.CBEWebhookView.as_view(), name='cbe-webhook'),
    path('webhooks/telebirr/', views.TeleBirrWebhookView.as_view(),
         name='telebirr-webhook'),
    path('webhooks/paypal/', views.paypal_webhook, name='paypal-webhook'),
]

# Admin router
router = DefaultRouter()
# Add admin views if needed

urlpatterns += router.urls
