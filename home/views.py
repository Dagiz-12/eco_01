# home/views.py - CORRECTED VERSION
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Count, Sum

from .models import HomePageContent, NewsletterSubscriber, ContactMessage, FAQ, SiteConfiguration
from .serializers import NewsletterSubscribeSerializer, ContactMessageSerializer
from products.models import Product, Category
from orders.models import Order

# HTML VIEWS (Function-based)


def home(request):
    """Home page view"""
    # Get site configuration
    try:
        site_config = SiteConfiguration.objects.first()
    except SiteConfiguration.DoesNotExist:
        site_config = None

    # Get home page content
    home_content = {
        section.section: section for section in HomePageContent.objects.filter(is_active=True)
    }

    # Get featured products
    featured_products = Product.objects.filter(
        is_featured=True,
        status='published'
    )[:8]

    # Get categories with product counts
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products')
    ).filter(
        product_count__gt=0
    )[:8]

    context = {
        'site_config': site_config,
        'home_content': home_content,
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'home/home.html', context)


def about(request):
    return render(request, 'home/about.html')


def contact(request):
    return render(request, 'home/contact.html')


def faq(request):
    return render(request, 'home/faq.html')


def privacy(request):
    return render(request, 'home/privacy.html')


def terms(request):
    return render(request, 'home/terms.html')


def shipping(request):
    return render(request, 'home/shipping.html')


def returns(request):
    return render(request, 'home/returns.html')

# API VIEWS


@api_view(['GET'])
@permission_classes([AllowAny])
def categories_api(request):
    """API endpoint for categories"""
    try:
        categories = Category.objects.filter(parent__isnull=True).annotate(
            product_count=Count('products')
        )[:6]

        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'image': category.image.url if category.image else None,
                'product_count': category.product_count
            })

        return Response({
            'success': True,
            'categories': categories_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def featured_products_api(request):
    """API endpoint for featured products"""
    try:
        featured_products = Product.objects.filter(
            is_featured=True,
            status='published'
        )[:8]

        products_data = []
        for product in featured_products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': str(product.price),
                'primary_image': product.primary_image.url if product.primary_image else None,
                'category': product.category.name if product.category else None,
                'is_featured': product.is_featured,
                'is_in_stock': product.is_in_stock
            })

        return Response({
            'success': True,
            'products': products_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def newsletter_subscribe(request):
    """Newsletter subscription API"""
    serializer = NewsletterSubscribeSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']

        # Check if already subscribed
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={
                'user': request.user if request.user.is_authenticated else None
            }
        )

        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.user = request.user if request.user.is_authenticated else None
            subscriber.save()

        return Response({
            'success': True,
            'message': 'Thank you for subscribing to our newsletter!',
            'created': created
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

# Remove duplicate functions - keep only one version of each


def handler404(request, exception):
    return render(request, 'home/404.html', status=404)


def handler500(request):
    return render(request, 'home/500.html', status=500)
