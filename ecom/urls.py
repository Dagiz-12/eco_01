from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from home import views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # Home app - HTML pages
    path('', include('home.urls')),

    path('admin-dashboard/', include('admin_dashboard.urls')),

    # Home API endpoints
    path('api/home/', include([
        path('categories/', views.categories_api, name='categories-api'),
        path('featured-products/', views.featured_products_api,
             name='featured-products-api'),
        path('newsletter/subscribe/', views.newsletter_subscribe,
             name='newsletter-subscribe'),
    ])),

    # Other API routes
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/cart/', include('cart.urls')),


    # HTML routes for orders - SEPARATE NAMESPACE
    # HTML pages - NOTE: Different path structure
    path('orders/', include('orders.urls_html')),

    # Other API routes
    path('api/payments/', include('payments.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/wishlist/', include('wishlist.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/coupons/', include('coupons.urls')),
    path('api/orders/', include('orders.urls')),  # API endpoints

    # REST Framework auth URLs
    path('api-auth/', include('rest_framework.urls')),
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
