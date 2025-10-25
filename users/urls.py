from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegistrationView, UserLoginView, UserProfileView, UserLogoutView
from . import views

app_name = 'users'

# API URLs
urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Additional user management endpoints
    path('profile/update/', UserProfileView.as_view(), name='user-profile-update'),
]

# For future ViewSet expansion
router = DefaultRouter()
# router.register('addresses', AddressViewSet, basename='address')

urlpatterns += router.urls
