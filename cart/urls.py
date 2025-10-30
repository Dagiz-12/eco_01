# cart/urls.py - CORRECTED VERSION
from django.urls import path
from . import views

app_name = 'cart'

# CORRECTED cart/urls.py
# CORRECTED cart/urls.py
urlpatterns = [
    # HTML Pages
    path('', views.cart_page, name='cart-detail-page'),
    path('summary/', views.cart_summary_page, name='cart-summary-page'),

    # API Endpoints - FIXED PATHS
    path('api/detail/', views.CartDetailView.as_view(), name='cart-detail'),
    path('api/summary/', views.CartSummaryView.as_view(), name='cart-summary'),
    path('api/clear/', views.CartClearView.as_view(), name='cart-clear'),
    path('api/merge/', views.CartMergeView.as_view(), name='cart-merge'),
    path('api/items/', views.CartItemListView.as_view(), name='cart-item-list'),
    path('api/items/add/', views.CartItemAddView.as_view(), name='cart-item-add'),
    path('api/items/<int:item_id>/update/',
         views.CartItemUpdateView.as_view(), name='cart-item-update'),
    path('api/items/<int:item_id>/remove/',
         views.CartItemRemoveView.as_view(), name='cart-item-remove'),
]
