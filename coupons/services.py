from django.utils import timezone
from .models import Coupon, CouponUsage, CustomerCoupon
from orders.models import Order


class CouponService:
    """Service class for coupon validation and application"""

    def validate_coupon(self, code, user, order_amount=0, cart_items=None):
        """Validate a coupon code for a user and order amount"""
        try:
            coupon = Coupon.objects.get(code=code.upper())
        except Coupon.DoesNotExist:
            return {
                'valid': False,
                'error': 'Invalid coupon code.'
            }

        # Check basic validity
        if not coupon.is_valid:
            return {
                'valid': False,
                'error': 'This coupon is no longer valid.'
            }

        # Check user eligibility
        if not coupon.can_be_used_by_user(user):
            return {
                'valid': False,
                'error': 'You have reached the usage limit for this coupon.'
            }

        # Check minimum order amount
        if order_amount < coupon.minimum_order_amount:
            return {
                'valid': False,
                'error': f'Minimum order amount of ${coupon.minimum_order_amount} required.'
            }

        # Calculate discount
        discount_amount = coupon.calculate_discount(order_amount, cart_items)

        if discount_amount <= 0:
            return {
                'valid': False,
                'error': 'Coupon cannot be applied to this order.'
            }

        return {
            'valid': True,
            'coupon': coupon,
            'discount_amount': discount_amount,
            'message': f'Coupon applied! You save ${discount_amount:.2f}'
        }

    def apply_coupon_to_order(self, coupon, user, order, cart_items=None):
        """Apply coupon to an order and record usage"""
        validation_result = self.validate_coupon(
            code=coupon.code,
            user=user,
            order_amount=order.subtotal,
            cart_items=cart_items
        )

        if not validation_result['valid']:
            return validation_result

        discount_amount = validation_result['discount_amount']

        # Apply discount to order
        order.discount_amount = discount_amount
        order.grand_total = order.subtotal - discount_amount
        order.save()

        # Record coupon usage
        coupon.mark_used(user, order, discount_amount)

        return validation_result

    def check_user_eligibility(self, coupon, user):
        """Check if user is eligible to use a coupon"""
        eligibility = {
            'eligible': True,
            'checks': [],
            'errors': []
        }

        # Basic validity check
        if not coupon.is_valid:
            eligibility['eligible'] = False
            eligibility['errors'].append('Coupon is not valid')

        # User usage limit
        if coupon.usage_limit_per_user:
            user_usage = CouponUsage.objects.filter(
                coupon=coupon,
                user=user
            ).count()
            if user_usage >= coupon.usage_limit_per_user:
                eligibility['eligible'] = False
                eligibility['errors'].append(
                    'You have reached the usage limit for this coupon')
            else:
                eligibility['checks'].append(
                    f'Usage limit: {user_usage}/{coupon.usage_limit_per_user}')

        # Customer-specific coupons
        if hasattr(coupon, 'customer_assignments'):
            assigned_coupon = coupon.customer_assignments.filter(
                user=user,
                is_used=False
            ).first()
            if not assigned_coupon:
                eligibility['eligible'] = False
                eligibility['errors'].append(
                    'This coupon is not assigned to you')
            elif not assigned_coupon.is_valid:
                eligibility['eligible'] = False
                eligibility['errors'].append(
                    'Your assigned coupon has expired')

        return eligibility

    def get_available_coupons_for_user(self, user, order_amount=0):
        """Get all coupons available for a user"""
        # Public active coupons
        public_coupons = Coupon.objects.filter(
            is_active=True,
            is_public=True,
            valid_until__gte=timezone.now()
        )

        # Assigned coupons
        assigned_coupons = Coupon.objects.filter(
            customer_assignments__user=user,
            customer_assignments__is_used=False,
            customer_assignments__expires_at__gte=timezone.now()
        )

        all_coupons = (public_coupons | assigned_coupons).distinct()

        # Filter coupons that meet minimum order amount
        available_coupons = []
        for coupon in all_coupons:
            if (coupon.can_be_used_by_user(user) and
                    order_amount >= coupon.minimum_order_amount):
                available_coupons.append(coupon)

        return available_coupons

    def create_bulk_coupons(self, template, count, prefix=""):
        """Create multiple coupons from a template"""
        created_coupons = []

        for i in range(count):
            coupon = Coupon(
                name=f"{template.name} {i+1}",
                description=template.description,
                discount_type=template.discount_type,
                discount_value=template.discount_value,
                applies_to=template.applies_to,
                minimum_order_amount=template.minimum_order_amount,
                maximum_discount_amount=template.maximum_discount_amount,
                usage_limit=template.usage_limit,
                usage_limit_per_user=template.usage_limit_per_user,
                valid_from=template.valid_from,
                valid_until=template.valid_until,
                is_active=template.is_active,
                is_public=template.is_public,
            )
            coupon.save()

            # Copy categories and products
            coupon.categories.set(template.categories.all())
            coupon.products.set(template.products.all())

            created_coupons.append(coupon)

        return created_coupons
