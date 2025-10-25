from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reviews'

router = DefaultRouter()

urlpatterns = [
    # Public endpoints
    path('', views.ReviewListView.as_view(), name='review-list'),
    path('products/<uuid:product_id>/summary/',
         views.ProductRatingSummaryView.as_view(),
         name='product-rating-summary'),

    # Authenticated user endpoints
    path('my-reviews/', views.UserReviewListView.as_view(), name='user-reviews'),
    path('create/', views.ReviewCreateView.as_view(), name='review-create'),
    path('can-review/<uuid:product_id>/',
         views.UserCanReviewView.as_view(),
         name='can-review'),

    # Review management
    path('<uuid:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('<uuid:review_id>/vote/',
         views.ReviewVoteView.as_view(), name='review-vote'),

    # Admin endpoints
    path('<uuid:review_id>/approve/', views.approve_review, name='approve-review'),
    path('<uuid:review_id>/reject/', views.reject_review, name='reject-review'),
]
