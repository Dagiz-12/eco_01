from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegistrationView, UserLoginView, UserProfileView, UserLogoutView
from . import views

app_name = 'users'

# HTML View URLs - SPECIFIC PATHS FIRST
html_patterns = [
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('profile/', views.profile_page, name='profile'),
]

# API URLs - UNDER api/ NAMESPACE
api_patterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]

urlpatterns = [
    # HTML routes first (specific paths)
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('profile/', views.profile_page, name='profile'),

    # API routes under api/ prefix
    path('api/', include(api_patterns)),
]
