from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, CartManager
from .serializers import (
    CartSerializer, CartItemSerializer,
    CartItemCreateSerializer, CartItemUpdateSerializer
)
from products.models import Product, ProductVariant


class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        return CartManager.get_or_create_cart(self.request)


class CartItemAddView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        cart = CartManager.get_or_create_cart(request)
        serializer = CartItemCreateSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.validated_data['product']
            variant = serializer.validated_data.get('variant')
            quantity = serializer.validated_data['quantity']

            # Check if item already exists in cart
            existing_item = cart.items.filter(
                product=product,
                variant=variant
            ).first()

            if existing_item:
                # Update quantity if item exists
                existing_item.quantity += quantity
                existing_item.save()
                item_serializer = CartItemSerializer(existing_item)
            else:
                # Create new cart item
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    quantity=quantity
                )
                item_serializer = CartItemSerializer(cart_item)

            # Return updated cart
            cart_serializer = CartSerializer(cart)
            return Response({
                'message': 'Item added to cart successfully',
                'item': item_serializer.data,
                'cart': cart_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemUpdateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def put(self, request, item_id):
        cart = CartManager.get_or_create_cart(request)

        try:
            cart_item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CartItemUpdateSerializer(cart_item, data=request.data)

        if serializer.is_valid():
            serializer.save()

            # Return updated cart
            cart_serializer = CartSerializer(cart)
            return Response({
                'message': 'Cart item updated successfully',
                'cart': cart_serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemRemoveView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request, item_id):
        cart = CartManager.get_or_create_cart(request)

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()

            # Return updated cart
            cart_serializer = CartSerializer(cart)
            return Response({
                'message': 'Item removed from cart successfully',
                'cart': cart_serializer.data
            }, status=status.HTTP_200_OK)

        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CartClearView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        cart = CartManager.get_or_create_cart(request)
        cart.clear()

        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart cleared successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class CartItemListView(generics.ListAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        cart = CartManager.get_or_create_cart(self.request)
        return cart.items.select_related('product', 'variant').all()


class CartSummaryView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        cart = CartManager.get_or_create_cart(request)

        summary = {
            'total_items': cart.total_items,
            'subtotal': float(cart.subtotal),
            'total': float(cart.total),
            'items_count': cart.items.count(),
            'is_empty': cart.items.count() == 0
        }

        return Response(summary, status=status.HTTP_200_OK)


class CartMergeView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        """
        Merge anonymous cart with user cart after login
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'User must be authenticated'},
                status=status.HTTP_400_BAD_REQUEST
            )

        session_cart_id = request.session.get('cart_id')
        if not session_cart_id:
            return Response(
                {'message': 'No session cart to merge'},
                status=status.HTTP_200_OK
            )

        try:
            user_cart = Cart.objects.get(user=request.user)
            session_cart = Cart.objects.get(
                id=session_cart_id, user__isnull=True)

            user_cart.merge_with_session_cart(session_cart)
            del request.session['cart_id']

            cart_serializer = CartSerializer(user_cart)
            return Response({
                'message': 'Cart merged successfully',
                'cart': cart_serializer.data
            }, status=status.HTTP_200_OK)

        except Cart.DoesNotExist:
            return Response(
                {'error': 'Session cart not found'},
                status=status.HTTP_404_NOT_FOUND
            )
