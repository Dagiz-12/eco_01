from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # Cart management
    path('', views.CartDetailView.as_view(), name='cart-detail'),
    path('summary/', views.CartSummaryView.as_view(), name='cart-summary'),
    path('clear/', views.CartClearView.as_view(), name='cart-clear'),
    path('merge/', views.CartMergeView.as_view(), name='cart-merge'),

    # Cart items
    path('items/', views.CartItemListView.as_view(), name='cart-item-list'),
    path('items/add/', views.CartItemAddView.as_view(), name='cart-item-add'),
    path('items/<int:item_id>/update/',
         views.CartItemUpdateView.as_view(), name='cart-item-update'),
    path('items/<int:item_id>/remove/',
         views.CartItemRemoveView.as_view(), name='cart-item-remove'),
]
