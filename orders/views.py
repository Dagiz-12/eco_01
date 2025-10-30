from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Order, OrderItem, OrderStatusHistory, OrderManager
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderUpdateSerializer, OrderStatusUpdateSerializer
)
from cart.models import CartManager


class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items', 'items__product', 'items__variant', 'status_history'
        )


class OrderCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        print("=== ORDER CREATION STARTED ===")
        print(f"User: {request.user.id} - {request.user.email}")
        print(f"Request data: {request.data}")

        # Get user's cart
        cart = CartManager.get_or_create_cart(request)
        print(f"Cart found: {cart is not None}")
        if cart:
            print(f"Cart items count: {cart.items.count()}")

        if not cart or cart.items.count() == 0:
            print("=== CART IS EMPTY ===")
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderCreateSerializer(
            data=request.data,
            context={'request': request, 'cart': cart}
        )

        if serializer.is_valid():
            print("=== SERIALIZER VALID ===")
            print(f"Validated data: {serializer.validated_data}")

            try:
                # Create order
                order = OrderManager.create_order_from_cart(
                    user=request.user,
                    cart=cart,
                    address_data=serializer.validated_data,
                    payment_method=serializer.validated_data['payment_method']
                )
                print(f"=== ORDER CREATED SUCCESSFULLY ===")
                print(f"Order number: {order.order_number}")
                print(f"Order ID: {order.id}")

                # Return order details
                order_serializer = OrderDetailSerializer(order)
                return Response({
                    'message': 'Order created successfully',
                    'order': order_serializer.data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                print(f"=== ORDER CREATION ERROR ===")
                print(f"Error: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            print("=== SERIALIZER INVALID ===")
            print(f"Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if not order.can_be_cancelled:
            return Response(
                {'error': 'This order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update order status
        old_status = order.status
        order.status = 'cancelled'
        order.payment_status = 'cancelled'
        order.save()

        # Record status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status='cancelled',
            note='Cancelled by user',
            created_by=request.user
        )

        # Restore inventory (simplified - in real app, handle this carefully)
        # This would need proper inventory restoration logic

        order_serializer = OrderDetailSerializer(order)
        return Response({
            'message': 'Order cancelled successfully',
            'order': order_serializer.data
        }, status=status.HTTP_200_OK)


class OrderStatusUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={'order': order}
        )

        if serializer.is_valid():
            old_status = order.status
            new_status = serializer.validated_data['status']
            note = serializer.validated_data.get('note', '')

            # Update order status
            order.status = new_status
            order.save()

            # Record status history
            OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                note=note,
                created_by=request.user
            )

            # Handle specific status updates
            if new_status == 'shipped' and not order.shipped_at:
                from django.utils import timezone
                order.shipped_at = timezone.now()
                order.save()
            elif new_status == 'delivered' and not order.delivered_at:
                from django.utils import timezone
                order.delivered_at = timezone.now()
                order.payment_status = 'paid'  # Mark as paid when delivered
                order.save()

            order_serializer = OrderDetailSerializer(order)
            return Response({
                'message': 'Order status updated successfully',
                'order': order_serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderAdminViewSet(ModelViewSet):
    queryset = Order.objects.all().prefetch_related('items', 'status_history')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        return OrderStatusUpdateView.as_view()(request, order_id=pk)


class OrderStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.db.models import Count, Sum, Avg
        from django.utils import timezone
        from datetime import timedelta

        # Basic stats
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(
            payment_status='paid'
        ).aggregate(Sum('grand_total'))['grand_total__sum'] or 0

        # Recent orders (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = Order.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()

        # Status distribution
        status_distribution = Order.objects.values('status').annotate(
            count=Count('id')
        )

        return Response({
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'recent_orders_30_days': recent_orders,
            'status_distribution': list(status_distribution)
        }, status=status.HTTP_200_OK)


# Add this function to your views.py

def checkout_page(request):
    """Render the checkout page"""
    return render(request, 'orders/checkout.html')


def order_detail_page(request, order_id):
    """Render the order detail page"""
    try:
        # Verify the order exists and user has permission
        order = Order.objects.filter(id=order_id, user=request.user).first()
        if not order:
            return render(request, 'orders/order_not_found.html', status=404)

        return render(request, 'orders/order_detail.html', {
            'order_id': order_id,
            'order_number': order.order_number,
        })
    except Exception as e:
        print(f"Error loading order detail page: {e}")
        return render(request, 'orders/order_error.html', status=500)


class TestOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Simple test endpoint to verify order creation"""
        print("=== TEST ORDER ENDPOINT HIT ===")
        print(f"User: {request.user.id} - {request.user.email}")
        print(f"Request data: {request.data}")

        return Response({
            'message': 'Test endpoint working',
            'user': request.user.email,
            'data_received': request.data,
            'authenticated': True
        }, status=status.HTTP_200_OK)
