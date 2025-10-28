from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Wishlist, WishlistItem, WishlistShare
from .serializers import (
    WishlistSerializer, WishlistItemSerializer, WishlistItemCreateSerializer,
    WishlistShareSerializer, WishlistShareCreateSerializer,
    PublicWishlistSerializer, MoveToCartSerializer
)
from cart.models import Cart


class WishlistDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get or create user's wishlist"""
        wishlist, created = Wishlist.objects.get_or_create(
            user=self.request.user
        )
        return wishlist


class WishlistItemListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WishlistItemCreateSerializer
        return WishlistItemSerializer

    def get_queryset(self):
        wishlist = get_object_or_404(Wishlist, user=self.request.user)
        return WishlistItem.objects.filter(wishlist=wishlist).select_related('product')

    def perform_create(self, serializer):
        wishlist = get_object_or_404(Wishlist, user=self.request.user)
        serializer.save(wishlist=wishlist)


class WishlistItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        wishlist = get_object_or_404(Wishlist, user=self.request.user)
        return WishlistItem.objects.filter(wishlist=wishlist)


class AddToWishlistView(generics.CreateAPIView):
    serializer_class = WishlistItemCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        wishlist = get_object_or_404(Wishlist, user=request.user)

        # Check if product already in wishlist
        existing_item = WishlistItem.objects.filter(
            wishlist=wishlist,
            product_id=product_id
        ).first()

        if existing_item:
            # Update existing item
            serializer = self.get_serializer(existing_item, data=request.data)
        else:
            # Create new item
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        if existing_item:
            serializer.save()
            message = 'Wishlist item updated'
        else:
            serializer.save(wishlist=wishlist, product_id=product_id)
            message = 'Product added to wishlist'

        return Response(
            {'message': message, 'data': serializer.data},
            status=status.HTTP_200_OK
        )


class RemoveFromWishlistView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        wishlist = get_object_or_404(Wishlist, user=request.user)

        deleted_count, _ = WishlistItem.objects.filter(
            wishlist=wishlist,
            product_id=product_id
        ).delete()

        if deleted_count > 0:
            return Response(
                {'message': 'Product removed from wishlist'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Product not found in wishlist'},
                status=status.HTTP_404_NOT_FOUND
            )


class MoveToCartView(generics.GenericAPIView):
    serializer_class = MoveToCartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item_ids = serializer.validated_data['item_ids']
        wishlist = get_object_or_404(Wishlist, user=request.user)
        cart, created = Cart.objects.get_or_create(user=request.user)

        moved_items = []
        failed_items = []

        with transaction.atomic():
            for item_id in item_ids:
                try:
                    wishlist_item = WishlistItem.objects.get(
                        id=item_id,
                        wishlist=wishlist
                    )
                    cart_item, created = wishlist_item.move_to_cart(cart)
                    moved_items.append(str(item_id))
                except WishlistItem.DoesNotExist:
                    failed_items.append(str(item_id))

        response_data = {
            'moved_items': moved_items,
            'failed_items': failed_items,
            'message': f'Successfully moved {len(moved_items)} items to cart'
        }

        return Response(response_data, status=status.HTTP_200_OK)


class WishlistShareView(generics.CreateAPIView):
    serializer_class = WishlistShareCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        wishlist = get_object_or_404(Wishlist, user=request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create share record
        share = WishlistShare.objects.create(
            wishlist=wishlist,
            shared_by=request.user,
            **serializer.validated_data
        )

        # Make wishlist public if it's not already
        if not wishlist.is_public:
            wishlist.is_public = True
            wishlist.save()

        share_serializer = WishlistShareSerializer(
            share,
            context={'request': request}
        )

        return Response(
            {
                'message': 'Wishlist shared successfully',
                'share_url': share_serializer.data['share_url'],
                'data': share_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class PublicWishlistDetailView(generics.RetrieveAPIView):
    serializer_class = PublicWishlistSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'share_token'
    lookup_url_kwarg = 'share_token'

    def get_queryset(self):
        return Wishlist.objects.filter(is_public=True)


class CheckProductInWishlistView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        wishlist = get_object_or_404(Wishlist, user=request.user)
        is_in_wishlist = wishlist.contains_product(product_id)

        return Response({
            'product_id': product_id,
            'is_in_wishlist': is_in_wishlist
        })


# Add to wishlist/views.py


def wishlist_page(request):
    return render(request, 'wishlist/wishlist_detail.html')


def wishlist_share_page(request, share_token):
    return render(request, 'wishlist/public_wishlist.html')
