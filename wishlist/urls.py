# wishlist/urls.py - CORRECTED VERSION
from django.urls import path
from . import views

app_name = 'wishlist'

# CORRECTED wishlist/urls.py
# CORRECTED wishlist/urls.py
urlpatterns = [
    # HTML Pages
    path('', views.wishlist_page, name='wishlist-detail-page'),
    path('shared/<uuid:share_token>/',
         views.wishlist_share_page, name='public-wishlist-page'),

    # API Endpoints - FIXED PATHS
    path('api/detail/', views.WishlistDetailView.as_view(), name='wishlist-detail'),
    path('api/items/', views.WishlistItemListView.as_view(), name='wishlist-items'),
    path('api/items/<int:pk>/', views.WishlistItemDetailView.as_view(),
         name='wishlist-item-detail'),
    # ✅ FIX: Match the URL pattern JavaScript is using
    path('api/add/<int:product_id>/',
         views.AddToWishlistView.as_view(), name='add-to-wishlist'),
    path('api/remove/<int:product_id>/',
         views.RemoveFromWishlistView.as_view(), name='remove-from-wishlist'),
    path('api/check/<int:product_id>/',
         views.CheckProductInWishlistView.as_view(), name='check-in-wishlist'),
    path('api/move-to-cart/', views.MoveToCartView.as_view(), name='move-to-cart'),
    path('api/share/', views.WishlistShareView.as_view(), name='wishlist-share'),
    path('api/shared/<uuid:share_token>/',
         views.PublicWishlistDetailView.as_view(), name='public-wishlist'),
]
