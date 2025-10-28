from django.urls import path, include
from . import views

app_name = 'home'

urlpatterns = [
    # Main pages
    path('', views.HomeView.as_view(), name='home'),

    # API endpoints - FIX THESE
    path('api/newsletter/subscribe/',
         views.NewsletterSubscribeView.as_view(), name='newsletter-subscribe'),
    path('api/contact/', views.contact_message_view, name='contact-message'),
    path('api/faqs/', views.faq_list_view, name='faq-list'),
    path('api/featured-products/', views.featured_products_view,
         name='featured-products'),
    path('api/categories/', views.categories_view,
         name='categories-list'),  # ✅ THIS EXISTS
    path('api/dashboard/stats/', views.dashboard_stats_view, name='dashboard-stats'),

    # ADD THESE MISSING ENDPOINTS:
    path('api/home/categories/', views.categories_view,
         name='categories-api'),  # ✅ ADD THIS
    path('api/home/featured-products/', views.featured_products_view,
         name='featured-products-api'),  # ✅ ADD THIS
]
