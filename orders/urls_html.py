from django.urls import path
from . import views

app_name = 'orders_html'

urlpatterns = [
    path('checkout/', views.checkout_page, name='checkout'),
    path('<int:order_id>/', views.order_detail_page, name='order-detail-page'),
    path('', views.order_list_page, name='order-list-page'),  # ADD THIS LINE
]
