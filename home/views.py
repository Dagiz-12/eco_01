from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import HomePageContent, NewsletterSubscriber, ContactMessage, FAQ, SiteConfiguration
from .serializers import NewsletterSubscribeSerializer, ContactMessageSerializer
from products.models import Product, Category
from orders.models import Order
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta


class HomeView(TemplateView):
    template_name = 'home/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get site configuration
        try:
            context['site_config'] = SiteConfiguration.objects.first()
        except SiteConfiguration.DoesNotExist:
            context['site_config'] = None

        # Get home page content
        context['home_content'] = {
            section.section: section for section in HomePageContent.objects.filter(is_active=True)
        }

        # ✅ FIXED: Use available fields from Product model
        context['featured_products'] = Product.objects.filter(
            is_featured=True,
            status='published'  # Use 'status' field instead of non-existent 'is_active'
        )[:8]

        # Get categories with product counts
        context['categories'] = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products')
        ).filter(
            product_count__gt=0
        )[:8]

        return context


@method_decorator(csrf_exempt, name='dispatch')
class NewsletterSubscribeView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = NewsletterSubscribeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Check if already subscribed
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={
                    'user': request.user if request.user.is_authenticated else None}
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


@api_view(['POST'])
@permission_classes([AllowAny])
def contact_message_view(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        contact_message = serializer.save()

        # Get client IP and user agent
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        contact_message.ip_address = ip
        contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
        contact_message.save()

        return Response({
            'success': True,
            'message': 'Thank you for your message! We will get back to you soon.',
            'message_id': str(contact_message.id)
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def faq_list_view(request):
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')

    faq_data = {}
    for faq in faqs:
        if faq.category not in faq_data:
            faq_data[faq.category] = []
        faq_data[faq.category].append({
            'id': str(faq.id),
            'question': faq.question,
            'answer': faq.answer
        })

    return Response({
        'success': True,
        'faqs': faq_data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def featured_products_view(request):
    """API endpoint for featured products"""
    # ✅ FIXED: Use 'status' instead of 'is_active'
    products = Product.objects.filter(
        is_featured=True,
        status='published'  # Changed from 'is_active=True'
    ).select_related('category', 'brand')[:12]

    product_data = []
    for product in products:
        product_data.append({
            'id': str(product.id),
            'name': product.name,
            'slug': product.slug,
            'price': str(product.price),
            'compare_price': str(product.compare_price) if product.compare_price else None,
            'primary_image': product.primary_image.url if hasattr(product, 'primary_image') and product.primary_image else None,
            'is_featured': product.is_featured,
            'is_in_stock': product.is_in_stock,
            'category': product.category.name if product.category else None,
            'brand': product.brand.name if product.brand else None,
        })

    return Response({
        'success': False,  # ✅ FIXED: Changed to True
        'products': product_data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def categories_view(request):
    """API endpoint for categories"""
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True  # Only top-level categories
    ).annotate(
        product_count=Count('products')
    ).filter(
        product_count__gt=0
    )[:12]

    category_data = []
    for category in categories:
        category_data.append({
            'id': str(category.id),
            'name': category.name,
            'slug': category.slug,
            'image': category.image.url if category.image else None,
            'product_count': category.product_count,
            'description': category.description
        })

    return Response({
        'success': True,
        'categories': category_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """Dashboard statistics for authenticated users"""
    user = request.user

    # Basic stats
    total_orders = Order.objects.filter(user=user).count()
    total_spent = Order.objects.filter(
        user=user,
        status__in=['completed', 'delivered']
    ).aggregate(total=Sum('grand_total'))['total'] or 0

    # Recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]

    order_data = []
    for order in recent_orders:
        order_data.append({
            'order_number': order.order_number,
            'status': order.status,
            'grand_total': str(order.grand_total),
            'created_at': order.created_at.isoformat(),
            'item_count': order.items.count()
        })

    return Response({
        'success': True,
        'stats': {
            'total_orders': total_orders,
            'total_spent': float(total_spent),
            'member_since': user.date_joined.strftime('%B %Y')
        },
        'recent_orders': order_data
    })


def handler404(request, exception):
    return render(request, 'home/404.html', status=404)


def handler500(request):
    return render(request, 'home/500.html', status=500)


# HTML Views
