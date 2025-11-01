from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import DashboardStats, AdminNotification
from users.models import User
from products.models import Product, Category
from orders.models import Order, OrderStatusHistory
from payments.models import Payment
from reviews.models import Review


def admin_required(function=None):
    """Decorator for views that require admin access"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='/admin/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


@admin_required
def dashboard_home(request):
    """Main dashboard homepage"""
    return render(request, 'admin_dashboard/home.html')


@admin_required
def analytics_dashboard(request):
    """Advanced analytics dashboard"""
    return render(request, 'admin_dashboard/analytics.html')


@admin_required
def user_management(request):
    """User management interface"""
    return render(request, 'admin_dashboard/user_management.html')


@admin_required
def product_management(request):
    """Product management interface"""
    return render(request, 'admin_dashboard/product_management.html')


@admin_required
def order_management(request):
    """Order management interface"""
    return render(request, 'admin_dashboard/order_management.html')


@admin_required
def payment_management(request):
    """Payment management interface"""
    return render(request, 'admin_dashboard/payment_management.html')

# API Views


@method_decorator(admin_required, name='dispatch')
class DashboardStatsAPI(APIView):
    def get(self, request):
        # Calculate real-time stats
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(payment_status='paid').aggregate(
            total=Sum('grand_total')
        )['total'] or 0

        total_customers = User.objects.filter(role='customer').count()
        total_products = Product.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()

        # Recent orders (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_orders = Order.objects.filter(created_at__gte=week_ago).count()

        # Revenue this month
        month_start = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = Order.objects.filter(
            created_at__gte=month_start,
            payment_status='paid'
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        stats = {
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'total_customers': total_customers,
            'total_products': total_products,
            'pending_orders': pending_orders,
            'recent_orders': recent_orders,
            'monthly_revenue': float(monthly_revenue),
        }

        return Response(stats)


@method_decorator(admin_required, name='dispatch')
class NotificationListAPI(APIView):
    def get(self, request):
        notifications = AdminNotification.objects.filter(is_read=False)[:10]
        data = [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ]
        return Response(data)


@method_decorator(admin_required, name='dispatch')
class SalesAnalyticsAPI(APIView):
    def get(self, request):
        period = request.GET.get('period', 'week')

        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        else:  # year
            days = 365

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Sales data
        sales_data = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            daily_sales = Order.objects.filter(
                created_at__date=current_date,
                payment_status='paid'
            ).aggregate(total=Sum('grand_total'))['total'] or 0

            sales_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'sales': float(daily_sales),
                'orders': Order.objects.filter(created_at__date=current_date).count()
            })
            current_date = next_date

        # Top products
        top_products = Product.objects.annotate(
            total_sold=Sum('order_items__quantity')
        ).order_by('-total_sold')[:5]

        top_products_data = [
            {
                'name': p.name,
                'sold': p.total_sold or 0,
                'revenue': float(p.price * (p.total_sold or 0))
            }
            for p in top_products
        ]

        return Response({
            'sales_data': sales_data,
            'top_products': top_products_data,
            'period': period
        })


@method_decorator(admin_required, name='dispatch')
class UserAnalyticsAPI(APIView):
    def get(self, request):
        # User growth
        month_ago = timezone.now() - timedelta(days=30)
        new_users = User.objects.filter(date_joined__gte=month_ago).count()

        # User roles
        role_distribution = User.objects.values(
            'role').annotate(count=Count('id'))

        # Active users (ordered in last 30 days)
        active_users = User.objects.filter(
            orders__created_at__gte=month_ago
        ).distinct().count()

        return Response({
            'new_users': new_users,
            'role_distribution': list(role_distribution),
            'active_users': active_users,
            'total_users': User.objects.count()
        })


@method_decorator(admin_required, name='dispatch')
class ProductAnalyticsAPI(APIView):
    def get(self, request):
        # Low stock products
        low_stock_products = Product.objects.filter(
            inventory__quantity__lte=10
        ).count()

        # Top categories
        top_categories = Category.objects.annotate(
            product_count=Count('products'),
            order_count=Count('products__order_items')
        ).order_by('-order_count')[:5]

        category_data = [
            {
                'name': cat.name,
                'products': cat.product_count,
                'orders': cat.order_count
            }
            for cat in top_categories
        ]

        return Response({
            'low_stock_count': low_stock_products,
            'top_categories': category_data,
            'total_products': Product.objects.count(),
            'active_products': Product.objects.filter(is_active=True).count()
        })

# Management Actions


@admin_required
def verify_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.email_verified = True
    user.save()

    # Create notification
    AdminNotification.objects.create(
        title='User Verified',
        message=f'User {user.email} has been verified',
        notification_type='user',
        related_object_id=user_id
    )

    return Response({'success': True, 'message': 'User verified successfully'})


@admin_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')

    if new_status in dict(Order.STATUS_CHOICES):
        old_status = order.status
        order.status = new_status
        order.save()

        # Record status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            note='Status updated by admin',
            created_by=request.user
        )

        return Response({'success': True, 'message': 'Order status updated'})

    return Response({'success': False, 'message': 'Invalid status'}, status=400)


@admin_required
def update_inventory(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    new_quantity = request.POST.get('quantity')

    try:
        quantity = int(new_quantity)
        if quantity >= 0:
            # Update inventory - you might need to adjust based on your inventory model
            if hasattr(product, 'inventory'):
                product.inventory.quantity = quantity
                product.inventory.save()
            else:
                # Fallback if no inventory model
                product.stock_quantity = quantity
                product.save()

            return Response({'success': True, 'message': 'Inventory updated'})
    except ValueError:
        pass

    return Response({'success': False, 'message': 'Invalid quantity'}, status=400)
