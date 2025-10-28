from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    # HTML Pages
    path('', views.wishlist_page, name='wishlist-detail-page'),
    path('shared/<uuid:share_token>/',
         views.wishlist_share_page, name='public-wishlist-page'),

    # API Endpoints
    path('api/', views.WishlistDetailView.as_view(), name='wishlist-detail'),
    path('api/items/', views.WishlistItemListView.as_view(), name='wishlist-items'),
    path('api/items/<uuid:pk>/', views.WishlistItemDetailView.as_view(),
         name='wishlist-item-detail'),
    path('api/add/<uuid:product_id>/',
         views.AddToWishlistView.as_view(), name='add-to-wishlist'),
    path('api/remove/<uuid:product_id>/',
         views.RemoveFromWishlistView.as_view(), name='remove-from-wishlist'),
    path('api/check/<uuid:product_id>/',
         views.CheckProductInWishlistView.as_view(), name='check-in-wishlist'),
    path('api/move-to-cart/', views.MoveToCartView.as_view(), name='move-to-cart'),
    path('api/share/', views.WishlistShareView.as_view(), name='wishlist-share'),
    path('api/shared/<uuid:share_token>/',
         views.PublicWishlistDetailView.as_view(), name='public-wishlist'),
]
