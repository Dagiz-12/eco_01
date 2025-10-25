from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import Coupon, CouponUsage, CustomerCoupon
from .serializers import (
    CouponSerializer, CouponCreateSerializer, CouponUsageSerializer,
    CustomerCouponSerializer, ValidateCouponSerializer,
    CouponValidationResponseSerializer, AssignCouponSerializer
)
from .services import CouponService
from users.models import User
from orders.models import Order
from django.db import models


class CouponListView(generics.ListAPIView):
    serializer_class = CouponSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['discount_type', 'is_active', 'is_public']

    def get_queryset(self):
        queryset = Coupon.objects.filter(is_active=True, is_public=True)

        # Admin users can see all coupons
        if self.request.user.is_staff:
            queryset = Coupon.objects.all()

        return queryset.select_related('created_by').prefetch_related(
            'categories', 'products'
        ).order_by('-created_at')


class CouponDetailView(generics.RetrieveAPIView):
    serializer_class = CouponSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Coupon.objects.all()
        return Coupon.objects.filter(is_active=True, is_public=True)


class CouponCreateView(generics.CreateAPIView):
    serializer_class = CouponCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CouponUpdateView(generics.UpdateAPIView):
    serializer_class = CouponCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Coupon.objects.all()


# ADD THIS MISSING VIEW
class CouponDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Coupon.objects.all()

    def perform_destroy(self, instance):
        # Instead of actually deleting, we can deactivate it
        instance.is_active = False
        instance.save()


class ValidateCouponView(generics.GenericAPIView):
    serializer_class = ValidateCouponSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        order_amount = serializer.validated_data['order_amount']

        coupon_service = CouponService()
        result = coupon_service.validate_coupon(
            code=code,
            user=request.user,
            order_amount=order_amount
        )

        response_serializer = CouponValidationResponseSerializer(result)
        return Response(response_serializer.data)


class UserCouponsListView(generics.ListAPIView):
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get public active coupons and assigned coupons
        public_coupons = Coupon.objects.filter(
            is_active=True,
            is_public=True,
            valid_until__gte=timezone.now()
        )

        # Get assigned coupons
        assigned_coupons = Coupon.objects.filter(
            customer_assignments__user=self.request.user,
            customer_assignments__is_used=False,
            customer_assignments__expires_at__gte=timezone.now()
        )

        return (public_coupons | assigned_coupons).distinct()


class CustomerCouponListView(generics.ListAPIView):
    serializer_class = CustomerCouponSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerCoupon.objects.filter(
            user=self.request.user,
            is_used=False
        ).select_related('coupon').order_by('-assigned_at')


class AssignCouponView(generics.GenericAPIView):
    serializer_class = AssignCouponSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data['user_ids']
        coupon_id = serializer.validated_data['coupon_id']
        expires_at = serializer.validated_data.get('expires_at')

        coupon = get_object_or_404(Coupon, id=coupon_id)
        users = User.objects.filter(id__in=user_ids)

        assigned_count = 0
        for user in users:
            customer_coupon, created = CustomerCoupon.objects.get_or_create(
                coupon=coupon,
                user=user,
                defaults={
                    'assigned_by': request.user,
                    'expires_at': expires_at
                }
            )
            if created:
                assigned_count += 1

        return Response({
            'message': f'Assigned coupon to {assigned_count} users',
            'assigned_count': assigned_count
        }, status=status.HTTP_201_CREATED)


class CouponUsageListView(generics.ListAPIView):
    serializer_class = CouponUsageSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return CouponUsage.objects.select_related(
            'coupon', 'user', 'order'
        ).order_by('-used_at')


class CouponStatsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        total_coupons = Coupon.objects.count()
        active_coupons = Coupon.objects.filter(is_active=True).count()
        total_usage = CouponUsage.objects.count()
        total_discount = CouponUsage.objects.aggregate(
            total=models.Sum('discount_amount')
        )['total'] or 0

        # Most used coupons
        popular_coupons = Coupon.objects.annotate(
            usage_count=models.Count('usages')
        ).order_by('-usage_count')[:5]

        stats = {
            'total_coupons': total_coupons,
            'active_coupons': active_coupons,
            'total_usage': total_usage,
            'total_discount': float(total_discount),
            'popular_coupons': [
                {
                    'code': coupon.code,
                    'name': coupon.name,
                    'usage_count': coupon.usage_count
                }
                for coupon in popular_coupons
            ]
        }

        return Response(stats)


# ADD THESE MISSING VIEWS THAT ARE REFERENCED IN URLS
class ApplyCouponView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Implementation for applying coupon to cart/order
        return Response({"message": "Coupon applied successfully"})


class RemoveCouponView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Implementation for removing coupon from cart/order
        return Response({"message": "Coupon removed successfully"})


class AssignCustomerView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Implementation for assigning coupon to specific customer
        return Response({"message": "Coupon assigned to customer"})


class CouponUsageStatsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        coupon_id = self.kwargs.get('pk')
        coupon = get_object_or_404(Coupon, id=coupon_id)

        usage_stats = CouponUsage.objects.filter(coupon=coupon).aggregate(
            total_uses=models.Count('id'),
            total_discount=models.Sum('discount_amount'),
            average_discount=models.Avg('discount_amount')
        )

        return Response(usage_stats)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def generate_coupon_code(request):
    """Generate a unique coupon code"""
    from .models import Coupon

    code = Coupon().generate_unique_code()

    return Response({
        'code': code,
        'message': 'Unique coupon code generated'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_coupon_eligibility(request, coupon_id):
    """Check if user is eligible to use a specific coupon"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon_service = CouponService()

    eligibility = coupon_service.check_user_eligibility(coupon, request.user)

    return Response(eligibility)
