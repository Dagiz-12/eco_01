from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from .models import Category, Brand, Product, ProductImage, ProductVariant, InventoryHistory
from .serializers import (
    CategorySerializer, BrandSerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateSerializer, ProductSearchSerializer
)
from .filters import ProductFilter


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class BrandDetailView(generics.RetrieveAPIView):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    lookup_field = 'slug'


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'short_description', 'sku']
    ordering_fields = ['price', 'created_at', 'name', 'quantity']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Product.objects.filter(status='published').select_related(
            'category', 'brand'
        ).prefetch_related('images')

        # Filter by category if provided
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Filter by brand if provided
        brand_slug = self.request.query_params.get('brand')
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter in-stock products
        in_stock = self.request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(quantity__gt=0)

        # Filter featured products
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(status='published').select_related(
            'category', 'brand'
        ).prefetch_related('images', 'variants', 'attributes')


class ProductSearchView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        serializer = ProductSearchSerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data.get('query', '')
            category = serializer.validated_data.get('category')
            brand = serializer.validated_data.get('brand')
            min_price = serializer.validated_data.get('min_price')
            max_price = serializer.validated_data.get('max_price')
            in_stock = serializer.validated_data.get('in_stock')
            featured = serializer.validated_data.get('featured')

            # Build search query
            search_query = Q(status='published')

            if query:
                search_query &= (
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(short_description__icontains=query) |
                    Q(sku__icontains=query) |
                    Q(category__name__icontains=query) |
                    Q(brand__name__icontains=query)
                )

            if category:
                search_query &= Q(category__slug=category)

            if brand:
                search_query &= Q(brand__slug=brand)

            if min_price:
                search_query &= Q(price__gte=min_price)

            if max_price:
                search_query &= Q(price__lte=max_price)

            if in_stock:
                search_query &= Q(quantity__gt=0)

            if featured:
                search_query &= Q(is_featured=True)

            products = Product.objects.filter(search_query).select_related(
                'category', 'brand'
            ).prefetch_related('images')

            serializer = ProductListSerializer(products, many=True)
            return Response({
                'count': products.count(),
                'results': serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeaturedProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Product.objects.filter(
            status='published',
            is_featured=True,
            quantity__gt=0
        ).select_related('category', 'brand').prefetch_related('images')[:12]


class CategoryProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        category_slug = self.kwargs['slug']
        category = get_object_or_404(
            Category, slug=category_slug, is_active=True)

        # Get all products in this category and its subcategories
        categories = [category]
        categories.extend(category.children.filter(is_active=True))

        return Product.objects.filter(
            category__in=categories,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')

# Admin Views


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAdminUser]


class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAdminUser]


class ProductAdminViewSet(ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    @action(detail=True, methods=['post'])
    def update_inventory(self, request, pk=None):
        product = self.get_object()
        quantity_change = request.data.get('quantity_change', 0)
        action_type = request.data.get('action', 'adjustment')
        note = request.data.get('note', '')

        try:
            quantity_change = int(quantity_change)
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid quantity change'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update product quantity
        if product.track_quantity:
            old_quantity = product.quantity
            product.quantity += quantity_change
            product.quantity = max(0, product.quantity)  # Prevent negative
            product.save()

            # Record inventory history
            InventoryHistory.objects.create(
                product=product,
                action=action_type,
                quantity_change=quantity_change,
                new_quantity=product.quantity,
                note=note,
                created_by=request.user
            )

            return Response({
                'message': 'Inventory updated successfully',
                'old_quantity': old_quantity,
                'new_quantity': product.quantity,
                'change': quantity_change
            })

        return Response(
            {'error': 'Inventory tracking is disabled for this product'},
            status=status.HTTP_400_BAD_REQUEST
        )
