# products/urls.py - CORRECTED VERSION
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'products'

# Router for admin views
router = DefaultRouter()
router.register('admin/products', views.ProductAdminViewSet,
                basename='admin-product')

urlpatterns = [
    # HTML Pages - Frontend (User-facing)
    path('', views.ProductListView.as_view(), name='product_list'),
    path('search/', views.product_search, name='product_search'),
    path('category/<slug:slug>/',
         views.CategoryDetailView.as_view(), name='category_detail'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # API Endpoints - Backend (JSON responses)
    path('api/categories/', views.CategoryListView.as_view(),
         name='category-api-list'),
    path('api/categories/<slug:slug>/',
         views.CategoryDetailView.as_view(), name='category-api-detail'),
    path('api/brands/', views.BrandListView.as_view(), name='brand-api-list'),
    path('api/brands/<slug:slug>/',
         views.BrandDetailView.as_view(), name='brand-api-detail'),
    path('api/featured/', views.FeaturedProductsView.as_view(),
         name='featured-api-products'),
    path('api/search/', views.ProductSearchView.as_view(),
         name='product-api-search'),

    # Admin endpoints
    path('api/admin/create/', views.ProductCreateView.as_view(),
         name='product-create'),
    path('api/admin/<int:pk>/update/',
         views.ProductUpdateView.as_view(), name='product-update'),

    # Include router URLs
    path('api/', include(router.urls)),
]
