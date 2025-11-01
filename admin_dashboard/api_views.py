from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json

from .serializers import (
    UserManagementSerializer, ProductManagementSerializer,
    OrderManagementSerializer, OrderDetailManagementSerializer,
    PaymentManagementSerializer, AnalyticsSerializer
)
from users.models import User
from products.models import Product, Category
from orders.models import Order
from payments.models import Payment


class MobileAdminStatsAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Mobile-optimized stats endpoint"""
        # Today's stats
        today = timezone.now().date()
        today_orders = Order.objects.filter(created_at__date=today).count()
        today_revenue = Order.objects.filter(
            created_at__date=today,
            payment_status='paid'
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        # Quick stats
        stats = {
            'today': {
                'orders': today_orders,
                'revenue': float(today_revenue),
            },
            'overall': {
                'total_orders': Order.objects.count(),
                'total_revenue': float(Order.objects.filter(payment_status='paid').aggregate(
                    total=Sum('grand_total')
                )['total'] or 0),
                'pending_orders': Order.objects.filter(status='pending').count(),
                'total_customers': User.objects.filter(role='customer').count(),
            }
        }

        return Response(stats)


class MobileOrderListAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Mobile-optimized order list for admin"""
        status_filter = request.GET.get('status', '')
        page = int(request.GET.get('page', 1))
        page_size = 20

        queryset = Order.objects.all().select_related('user').prefetch_related('items')

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Pagination
        total_count = queryset.count()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        orders = queryset.order_by('-created_at')[start_idx:end_idx]
        serializer = OrderManagementSerializer(orders, many=True)

        return Response({
            'orders': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })


class MobileOrderDetailAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, order_id):
        """Mobile-optimized order detail"""
        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderDetailManagementSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)


class MobileQuickActionsAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """Handle quick actions from mobile app"""
        action = request.data.get('action')
        target_id = request.data.get('target_id')

        if action == 'update_order_status':
            return self.update_order_status(target_id, request.data.get('status'))
        elif action == 'verify_user':
            return self.verify_user(target_id)
        elif action == 'update_inventory':
            return self.update_inventory(target_id, request.data.get('quantity'))

        return Response({'error': 'Invalid action'}, status=400)

    def update_order_status(self, order_id, new_status):
        from orders.models import Order, OrderStatusHistory
        try:
            order = Order.objects.get(id=order_id)
            old_status = order.status
            order.status = new_status
            order.save()

            OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                note='Status updated via mobile admin',
                created_by=self.request.user
            )

            return Response({'success': True, 'message': 'Order status updated'})
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

    def verify_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.email_verified = True
            user.save()
            return Response({'success': True, 'message': 'User verified'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

    def update_inventory(self, product_id, quantity):
        try:
            product = Product.objects.get(id=product_id)
            if hasattr(product, 'inventory'):
                product.inventory.quantity = int(quantity)
                product.inventory.save()
            else:
                product.stock_quantity = int(quantity)
                product.save()
            return Response({'success': True, 'message': 'Inventory updated'})
        except (Product.DoesNotExist, ValueError):
            return Response({'error': 'Invalid product or quantity'}, status=400)
