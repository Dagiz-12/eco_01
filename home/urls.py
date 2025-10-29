# home/urls.py - CORRECTED VERSION
from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    # HTML Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('shipping/', views.shipping, name='shipping'),
    path('returns/', views.returns, name='returns'),
]
