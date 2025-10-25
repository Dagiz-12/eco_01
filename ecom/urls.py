"""
URL configuration for ecom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # API routes only - remove duplicate frontend routes
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/wishlist/', include('wishlist.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/coupons/', include('coupons.urls')),

    # REST Framework auth URLs (for browsable API)
    path('api-auth/', include('rest_framework.urls')),

    # Home app - should be first for root URL
    path('', include('home.urls')),

    # Additional pages
    path('about/', TemplateView.as_view(template_name='home/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='home/contact.html'), name='contact'),
    path('faq/', TemplateView.as_view(template_name='home/faq.html'), name='faq'),
    path('privacy/', TemplateView.as_view(template_name='home/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='home/terms.html'), name='terms'),
    path('shipping/', TemplateView.as_view(template_name='home/shipping.html'), name='shipping'),
    path('returns/', TemplateView.as_view(template_name='home/returns.html'), name='returns'),
]

# Error handlers
handler404 = 'home.views.handler404'
handler500 = 'home.views.handler500'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = 'Hagerbet E-Commerce Administration'
admin.site.site_title = 'Hagerbet Admin'
admin.site.index_title = 'Welcome to Hagerbet Admin Portal'
