from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'products'

# Router for admin views
router = DefaultRouter()
router.register('admin/products', views.ProductAdminViewSet,
                basename='admin-product')

urlpatterns = [
    # Public endpoints
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/',
         views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<slug:slug>/products/',
         views.CategoryProductsView.as_view(), name='category-products'),

    path('brands/', views.BrandListView.as_view(), name='brand-list'),
    path('brands/<slug:slug>/', views.BrandDetailView.as_view(), name='brand-detail'),

    path('', views.ProductListView.as_view(), name='product-list'),
    path('featured/', views.FeaturedProductsView.as_view(),
         name='featured-products'),
    path('search/', views.ProductSearchView.as_view(), name='product-search'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),

    # Admin endpoints
    path('admin/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('admin/<int:pk>/update/',
         views.ProductUpdateView.as_view(), name='product-update'),

    # Include router URLs
    path('', include(router.urls)),
]
