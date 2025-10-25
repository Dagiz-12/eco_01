from django.urls import path
from . import views

urlpatterns = [
    # Wishlist management
    path('', views.WishlistDetailView.as_view(), name='wishlist-detail'),
    path('items/', views.WishlistItemListView.as_view(), name='wishlist-items'),
    path('items/<uuid:pk>/', views.WishlistItemDetailView.as_view(),
         name='wishlist-item-detail'),

    # Product operations
    path('add/<uuid:product_id>/',
         views.AddToWishlistView.as_view(), name='add-to-wishlist'),
    path('remove/<uuid:product_id>/',
         views.RemoveFromWishlistView.as_view(), name='remove-from-wishlist'),
    path('check/<uuid:product_id>/',
         views.CheckProductInWishlistView.as_view(), name='check-in-wishlist'),

    # Cart operations
    path('move-to-cart/', views.MoveToCartView.as_view(), name='move-to-cart'),

    # Sharing
    path('share/', views.WishlistShareView.as_view(), name='wishlist-share'),
    path('shared/<uuid:share_token>/',
         views.PublicWishlistDetailView.as_view(), name='public-wishlist'),
]
