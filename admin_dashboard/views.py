

from payments.models import Payment, Refund
from django.http import HttpResponse, JsonResponse
import csv


# Add these imports at the top

from datetime import datetime, timedelta

import traceback
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from .models import DashboardStats, AdminNotification
import json

from .models import DashboardStats, AdminNotification
from users.models import User
from products.models import Product, Category, Brand
from orders.models import Order, OrderStatusHistory
from payments.models import Payment
from reviews.models import Review
from .serializers import (
    UserManagementSerializer,
    ProductManagementSerializer,
    OrderManagementSerializer,
    OrderDetailManagementSerializer,  # This should work now
    PaymentManagementSerializer,
    AnalyticsSerializer, UserDetailSerializer, ProductDetailSerializer, EnhancedProductManagementSerializer
)


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


@admin_required
def show_add_product_form(request):
    """Render the add product form"""
    return render(request, 'admin_dashboard/add_product.html')


# admin payment views

# Add to admin_dashboard/views.py


@admin_required
def get_order_payments(request, order_id):
    """Get payment information for an order"""
    try:
        order = get_object_or_404(Order, id=order_id)

        # Get payments for this order
        payments = Payment.objects.filter(order=order).order_by('-created_at')

        payments_data = []
        for payment in payments:
            payment_data = {
                'id': payment.id,
                'payment_id': str(payment.payment_id),
                'payment_method': payment.payment_method,
                'status': payment.status,
                'amount': str(payment.amount),
                'currency': payment.currency,
                'gateway_payment_id': payment.gateway_payment_id,
                'created_at': payment.created_at.isoformat(),
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                'failed_at': payment.failed_at.isoformat() if payment.failed_at else None,
                'is_successful': payment.is_successful,
                'can_be_refunded': payment.can_be_refunded,
            }

            # Add gateway-specific information
            if hasattr(payment, 'cbe_transaction'):
                cbe = payment.cbe_transaction
                payment_data['gateway_details'] = {
                    'type': 'cbe',
                    'transaction_id': cbe.transaction_id,
                    'status': cbe.status,
                    'ussd_code': f'*127*1*{cbe.transaction_id}#' if cbe.transaction_id else None,
                }
            elif hasattr(payment, 'telebirr_transaction'):
                telebirr = payment.telebirr_transaction
                payment_data['gateway_details'] = {
                    'type': 'telebirr',
                    'transaction_id': telebirr.transaction_id,
                    'status': telebirr.status,
                    'ussd_code': f'*806*{telebirr.transaction_id}#' if telebirr.transaction_id else None,
                    'qr_code_url': telebirr.qr_code_url,
                }
            elif payment.payment_method in ['stripe', 'paypal']:
                payment_data['gateway_details'] = {
                    'type': payment.payment_method,
                    'transaction_id': payment.gateway_payment_id,
                }

            payments_data.append(payment_data)

        return JsonResponse({
            'success': True,
            'order_id': order_id,
            'payments': payments_data,
            'total_payments': len(payments_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to fetch payment data: {str(e)}'
        }, status=500)


@admin_required
def verify_payment(request, payment_id):
    """Manually verify a payment"""
    try:
        payment = get_object_or_404(Payment, id=payment_id)

        # Check if payment can be verified
        if payment.status in ['completed', 'refunded', 'partially_refunded']:
            return JsonResponse({
                'success': False,
                'message': f'Payment is already {payment.status}'
            }, status=400)

        # Simulate payment verification
        # In production, this would call the actual gateway API
        if payment.payment_method == 'cbe' and hasattr(payment, 'cbe_transaction'):
            # Simulate CBE verification
            from payments.models import PaymentManager
            success, message = PaymentManager.verify_cbe_payment(
                payment.cbe_transaction.transaction_id
            )

        elif payment.payment_method == 'telebirr' and hasattr(payment, 'telebirr_transaction'):
            # Simulate TeleBirr verification
            from payments.models import PaymentManager
            success, message = PaymentManager.verify_telebirr_payment(
                payment.telebirr_transaction.transaction_id
            )

        else:
            # For other payment methods, mark as completed for demo
            payment.mark_as_completed()
            success, message = True, f'{payment.get_payment_method_display()} payment verified successfully'

        if success:
            # Update order payment status if payment is completed
            if payment.status == 'completed':
                payment.order.payment_status = 'paid'
                payment.order.save()

            return JsonResponse({
                'success': True,
                'message': message,
                'payment_status': payment.status,
                'order_payment_status': payment.order.payment_status
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Payment verification failed: {str(e)}'
        }, status=500)


@admin_required
def get_payment_details(request, payment_id):
    """Get detailed payment information"""
    try:
        payment = get_object_or_404(Payment, id=payment_id)

        payment_data = {
            'id': payment.id,
            'payment_id': str(payment.payment_id),
            'order_number': payment.order.order_number,
            'customer_name': f"{payment.user.first_name} {payment.user.last_name}",
            'customer_email': payment.user.email,
            'payment_method': payment.payment_method,
            'payment_method_display': payment.get_payment_method_display(),
            'status': payment.status,
            'status_display': payment.get_status_display(),
            'amount': str(payment.amount),
            'currency': payment.currency,
            'gateway_payment_id': payment.gateway_payment_id,
            'gateway_response': payment.gateway_response,
            'created_at': payment.created_at.isoformat(),
            'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
            'failed_at': payment.failed_at.isoformat() if payment.failed_at else None,
            'is_successful': payment.is_successful,
            'can_be_refunded': payment.can_be_refunded,
        }

        # Add refund information
        refunds = Refund.objects.filter(payment=payment)
        payment_data['refunds'] = [
            {
                'refund_id': str(refund.refund_id),
                'amount': str(refund.amount),
                'reason': refund.reason,
                'status': refund.status,
                'created_at': refund.created_at.isoformat(),
                'processed_at': refund.processed_at.isoformat() if refund.processed_at else None,
            }
            for refund in refunds
        ]

        return JsonResponse({
            'success': True,
            'payment': payment_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to fetch payment details: {str(e)}'
        }, status=500)


@method_decorator(admin_required, name='dispatch')
class AddProductAPI(APIView):
    def post(self, request):
        """Handle new product creation"""
        try:
            data = request.data

            # Create new product
            product = Product.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                price=float(data['price']),
                quantity=int(data.get('quantity', 0)),
                status=data.get('status', 'draft'),
                category_id=data.get('category'),
                brand_id=data.get('brand'),
                sku=data.get('sku', ''),
                is_featured=bool(data.get('is_featured', False))
            )

            return Response({
                'success': True,
                'message': 'Product created successfully',
                'product_id': product.id
            })
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=500)


@admin_required
def user_action(request, user_id):
    """Handle single user actions (toggle active, etc.)"""
    try:
        user = User.objects.get(id=user_id)

        if request.method == 'POST':
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'toggle_active':
                user.is_active = not user.is_active
                user.save()
                return JsonResponse({
                    'success': True,
                    'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
                })
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'}, status=400)

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# Add these API views to your views.py


@method_decorator(admin_required, name='dispatch')
class ProductStatsAPI(APIView):
    def get(self, request):
        """Get product statistics for the dashboard"""
        try:
            # Total products
            total_products = Product.objects.count()

            # Published products
            published_products = Product.objects.filter(
                status='published').count()

            # Low stock products (quantity <= low_stock_threshold)
            low_stock_products = Product.objects.filter(
                quantity__lte=10,  # Default low stock threshold
                track_quantity=True
            ).count()

            # Out of stock products
            out_of_stock_products = Product.objects.filter(
                quantity=0,
                track_quantity=True
            ).count()

            # Total categories and brands
            total_categories = Category.objects.count()
            total_brands = Brand.objects.count()

            return Response({
                'total_products': total_products,
                'published_products': published_products,
                'low_stock_products': low_stock_products,
                'out_of_stock_products': out_of_stock_products,
                'total_categories': total_categories,
                'total_brands': total_brands
            })
        except Exception as e:
            print(f"DEBUG: Error in ProductStatsAPI: {str(e)}")
            return Response({'error': str(e)}, status=500)


@method_decorator(admin_required, name='dispatch')
class ProductDetailAPI(APIView):
    def get(self, request, product_id):
        """Get detailed product information"""
        try:
            product = Product.objects.select_related('category', 'brand').prefetch_related(
                'images', 'variants', 'order_items'
            ).get(id=product_id)

            serializer = ProductDetailSerializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


@method_decorator(admin_required, name='dispatch')
class EnhancedProductManagementAPI(APIView):
    def get(self, request):
        """Enhanced product listing with advanced filtering"""
        try:
            # Get filter parameters
            search = request.GET.get('search', '')
            category = request.GET.get('category', '')
            brand = request.GET.get('brand', '')
            status = request.GET.get('status', '')
            stock = request.GET.get('stock', '')
            price = request.GET.get('price', '')
            sort = request.GET.get('sort', 'newest')
            page = int(request.GET.get('page', 1))
            page_size = 20

            # Build queryset
            queryset = Product.objects.select_related(
                'category', 'brand').prefetch_related('images')

            # Apply filters
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(sku__icontains=search) |
                    Q(description__icontains=search)
                )

            if category:
                queryset = queryset.filter(category_id=category)

            if brand:
                queryset = queryset.filter(brand_id=brand)

            if status:
                queryset = queryset.filter(status=status)

            if stock:
                if stock == 'in_stock':
                    queryset = queryset.filter(quantity__gt=0)
                elif stock == 'low_stock':
                    queryset = queryset.filter(
                        quantity__lte=models.F('low_stock_threshold'),
                        quantity__gt=0
                    )
                elif stock == 'out_of_stock':
                    queryset = queryset.filter(quantity=0)

            if price:
                if price == '0-50':
                    queryset = queryset.filter(price__range=(0, 50))
                elif price == '50-100':
                    queryset = queryset.filter(price__range=(50, 100))
                elif price == '100-500':
                    queryset = queryset.filter(price__range=(100, 500))
                elif price == '500+':
                    queryset = queryset.filter(price__gte=500)

            # Apply sorting
            if sort == 'newest':
                queryset = queryset.order_by('-created_at')
            elif sort == 'oldest':
                queryset = queryset.order_by('created_at')
            elif sort == 'name_asc':
                queryset = queryset.order_by('name')
            elif sort == 'name_desc':
                queryset = queryset.order_by('-name')
            elif sort == 'price_asc':
                queryset = queryset.order_by('price')
            elif sort == 'price_desc':
                queryset = queryset.order_by('-price')
            elif sort == 'stock_asc':
                queryset = queryset.order_by('quantity')
            elif sort == 'stock_desc':
                queryset = queryset.order_by('-quantity')

            # Pagination
            total_count = queryset.count()
            start_idx = (page - 1) * page_size
            products = queryset[start_idx:start_idx + page_size]

            serializer = EnhancedProductManagementSerializer(
                products, many=True)

            return Response({
                'products': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


@method_decorator(admin_required, name='dispatch')
class BulkProductActionsAPI(APIView):
    def post(self, request):
        """Handle bulk product actions (publish, unpublish, delete, etc.)"""
        try:
            action = request.data.get('action')
            product_ids = request.data.get('product_ids', [])

            if not product_ids:
                return Response({'error': 'No products selected'}, status=400)

            products = Product.objects.filter(id__in=product_ids)

            if action == 'publish':
                products.update(status='published')
                message = f'{products.count()} products published successfully'
            elif action == 'unpublish':
                products.update(status='draft')
                message = f'{products.count()} products unpublished successfully'
            elif action == 'delete':
                count = products.count()
                products.delete()
                message = f'{count} products deleted successfully'
            elif action == 'feature':
                products.update(is_featured=True)
                message = f'{products.count()} products featured successfully'
            elif action == 'unfeature':
                products.update(is_featured=False)
                message = f'{products.count()} products unfeatured successfully'
            else:
                return Response({'error': 'Invalid action'}, status=400)

            return Response({'success': True, 'message': message})

        except Exception as e:
            return Response({'error': str(e)}, status=500)


@admin_required
def export_products_csv(request):
    """Export products to CSV"""
    try:
        # Get filter parameters
        search = request.GET.get('search', '')
        category = request.GET.get('category', '')
        brand = request.GET.get('brand', '')
        status = request.GET.get('status', '')
        stock = request.GET.get('stock', '')
        price = request.GET.get('price', '')

        # Build queryset
        queryset = Product.objects.select_related('category', 'brand')

        # Apply the same filters as the listing
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if brand:
            queryset = queryset.filter(brand_id=brand)
        if status:
            queryset = queryset.filter(status=status)
        if stock:
            if stock == 'in_stock':
                queryset = queryset.filter(quantity__gt=0)
            elif stock == 'low_stock':
                queryset = queryset.filter(
                    quantity__lte=models.F('low_stock_threshold'),
                    quantity__gt=0
                )
            elif stock == 'out_of_stock':
                queryset = queryset.filter(quantity=0)
        if price:
            if price == '0-50':
                queryset = queryset.filter(price__range=(0, 50))
            elif price == '50-100':
                queryset = queryset.filter(price__range=(50, 100))
            elif price == '100-500':
                queryset = queryset.filter(price__range=(100, 500))
            elif price == '500+':
                queryset = queryset.filter(price__gte=500)

        # Create HTTP response with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products_export.csv"'

        # Create CSV writer
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'SKU', 'Category', 'Brand', 'Price',
            'Compare Price', 'Cost Price', 'Quantity', 'Low Stock Threshold',
            'Status', 'Featured', 'Digital', 'Description', 'Created At', 'Updated At'
        ])

        # Write product data
        for product in queryset:
            writer.writerow([
                product.id,
                product.name,
                product.sku,
                product.category.name if product.category else '',
                product.brand.name if product.brand else '',
                float(product.price),
                float(product.compare_price) if product.compare_price else '',
                float(product.cost_per_item) if product.cost_per_item else '',
                product.quantity,
                product.low_stock_threshold,
                product.status,
                'Yes' if product.is_featured else 'No',
                'Yes' if product.is_digital else 'No',
                product.description.replace('\n', ' ').replace(
                    '\r', ' ')[:100],  # Truncate long descriptions
                product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                product.updated_at.strftime(
                    '%Y-%m-%d %H:%M:%S') if product.updated_at else ''
            ])

        return response

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@admin_required
def quick_edit_product(request, product_id):
    """Handle quick edits to product fields"""
    try:
        product = Product.objects.get(id=product_id)

        if request.method == 'POST':
            import json
            data = json.loads(request.body)

            # Update allowed fields
            allowed_fields = ['name', 'price', 'compare_price',
                              'quantity', 'status', 'is_featured']
            for field in allowed_fields:
                if field in data:
                    # Handle different data types
                    if field in ['price', 'compare_price']:
                        setattr(product, field, float(
                            data[field]) if data[field] else None)
                    elif field == 'quantity':
                        setattr(product, field, int(data[field]))
                    elif field == 'is_featured':
                        setattr(product, field, bool(data[field]))
                    else:
                        setattr(product, field, data[field])

            product.save()

            return JsonResponse({
                'success': True,
                'message': 'Product updated successfully',
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'quantity': product.quantity,
                    'status': product.status,
                    'is_featured': product.is_featured
                }
            })

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        print(f"DEBUG: Error in quick_edit_product: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@admin_required
def update_product_inventory(request, product_id):
    """Update product inventory with enhanced functionality"""
    try:
        product = Product.objects.get(id=product_id)

        if request.method == 'POST':
            data = json.loads(request.body)

            # Handle status updates
            if data.get('action') == 'update_status':
                new_status = data.get('status')
                if new_status in ['draft', 'published', 'archived']:
                    product.status = new_status
                    product.save()
                    return JsonResponse({'success': True, 'message': 'Product status updated'})

            # Handle quantity updates
            new_quantity = data.get('quantity')
            if new_quantity is not None:
                try:
                    quantity = int(new_quantity)
                    if quantity >= 0:
                        old_quantity = product.quantity
                        product.quantity = quantity
                        product.save()

                        # Record inventory history if quantity changed
                        if old_quantity != quantity:
                            from products.models import InventoryHistory
                            InventoryHistory.objects.create(
                                product=product,
                                action='adjustment',
                                quantity_change=quantity - old_quantity,
                                new_quantity=quantity,
                                note='Inventory adjusted by admin',
                                created_by=request.user
                            )

                        return JsonResponse({'success': True, 'message': 'Inventory updated'})
                except ValueError:
                    return JsonResponse({'success': False, 'message': 'Invalid quantity'}, status=400)

            # Handle featured status
            if 'is_featured' in data:
                product.is_featured = data['is_featured']
                product.save()
                return JsonResponse({'success': True, 'message': 'Featured status updated'})

        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# new


# Add these API views to your views.py

@method_decorator(admin_required, name='dispatch')
class UserStatsAPI(APIView):
    def get(self, request):
        """Get user statistics for the dashboard"""
        try:
            # Total users
            total_users = User.objects.count()

            # Pending verification
            pending_verification = User.objects.filter(
                email_verified=False).count()

            # Active today (users who logged in today)
            today = timezone.now().date()
            active_today = User.objects.filter(
                last_login__date=today
            ).count()

            # Seller count
            seller_count = User.objects.filter(role='seller').count()

            # New users this week
            week_ago = timezone.now() - timedelta(days=7)
            new_users_week = User.objects.filter(
                date_joined__gte=week_ago).count()

            return Response({
                'total_users': total_users,
                'pending_verification': pending_verification,
                'active_today': active_today,
                'seller_count': seller_count,
                'new_users_week': new_users_week
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


@method_decorator(admin_required, name='dispatch')
class UserDetailAPI(APIView):
    def get(self, request, user_id):
        """Get detailed user information"""
        try:
            user = User.objects.get(id=user_id)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


@method_decorator(admin_required, name='dispatch')
class BulkUserActionsAPI(APIView):
    def post(self, request):
        """Handle bulk user actions (verify, activate, deactivate)"""
        try:
            action = request.data.get('action')
            user_ids = request.data.get('user_ids', [])

            if not user_ids:
                return Response({'error': 'No users selected'}, status=400)

            users = User.objects.filter(id__in=user_ids)

            if action == 'verify':
                users.update(email_verified=True)
                message = f'{users.count()} users verified successfully'
            elif action == 'activate':
                users.update(is_active=True)
                message = f'{users.count()} users activated successfully'
            elif action == 'deactivate':
                users.update(is_active=False)
                message = f'{users.count()} users deactivated successfully'
            else:
                return Response({'error': 'Invalid action'}, status=400)

            return Response({'success': True, 'message': message})

        except Exception as e:
            return Response({'error': str(e)}, status=500)


@admin_required
def export_users_csv(request):
    """Export users to CSV"""
    try:
        # Get filter parameters
        role_filter = request.GET.get('role', '')
        verification_filter = request.GET.get('verification', '')
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # Build queryset
        queryset = User.objects.all()

        if role_filter:
            queryset = queryset.filter(role=role_filter)
        if verification_filter == 'pending':
            queryset = queryset.filter(email_verified=False)
        elif verification_filter == 'verified':
            queryset = queryset.filter(email_verified=True)
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        if date_from:
            queryset = queryset.filter(date_joined__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_joined__lte=date_to)

        # Create HTTP response with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

        # Create CSV writer
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Email', 'First Name', 'Last Name', 'Username', 'Role',
            'Email Verified', 'Account Active', 'Date Joined', 'Last Login',
            'Order Count', 'Total Spent'
        ])

        # Write user data
        for user in queryset:
            # Calculate order count and total spent
            order_count = user.orders.count()
            total_spent = user.orders.filter(payment_status='paid').aggregate(
                total=Sum('grand_total')
            )['total'] or 0

            writer.writerow([
                user.id,
                user.email,
                user.first_name or '',
                user.last_name or '',
                user.username,
                user.role,
                'Yes' if user.email_verified else 'No',
                'Yes' if user.is_active else 'No',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime(
                    '%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                order_count,
                float(total_spent)
            ])

        return response

    except Exception as e:
        return Response({'error': str(e)}, status=500)


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
        try:
            # FIX: Use quantity instead of inventory
            low_stock_products = Product.objects.filter(
                quantity__lte=10,  # FIX: Use quantity field directly
                track_quantity=True
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
                # FIX: Use status instead of is_active
                'active_products': Product.objects.filter(status='published').count()
            })
        except Exception as e:
            print(f"DEBUG: Error in ProductAnalyticsAPI: {str(e)}")
            return Response({'error': str(e)}, status=500)
# Management Actions


@admin_required
def verify_user(request, user_id):
    """Verify a user's email"""
    try:
        user = User.objects.get(id=user_id)
        user.email_verified = True
        user.save()

        # Create notification
        AdminNotification.objects.create(
            title='User Verified',
            message=f'User {user.email} has been verified',
            notification_type='user',
            related_object_id=user_id
        )

        return JsonResponse({'success': True, 'message': 'User verified successfully'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@admin_required
def update_order_status(request, order_id):
    """Update order status with payment validation"""
    try:
        order = get_object_or_404(Order, id=order_id)

        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            new_status = data.get('status')
            notes = data.get('notes', '')

            # 🚨 PAYMENT VALIDATION: Prevent confirming unpaid orders
            if new_status == 'confirmed' and order.payment_status != 'paid':
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot confirm order #{order.order_number}: Payment not received. Current payment status: {order.payment_status}'
                }, status=400)

            if new_status in dict(Order.STATUS_CHOICES):
                old_status = order.status
                order.status = new_status
                order.save()

                # Record status history
                OrderStatusHistory.objects.create(
                    order=order,
                    old_status=old_status,
                    new_status=new_status,
                    note=notes,
                    created_by=request.user
                )

                return JsonResponse({
                    'success': True,
                    'message': f'Order status updated from {old_status} to {new_status}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid status'
                }, status=400)

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
    except Exception as e:
        print(f"DEBUG: Error in update_order_status: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@admin_required
def update_inventory(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        data = json.loads(request.body)

        # Handle status updates
        if data.get('action') == 'update_status':
            new_status = data.get('status')
            if new_status in ['draft', 'published', 'archived']:
                product.status = new_status
                product.save()
                return JsonResponse({'success': True, 'message': 'Product status updated'})

        # Handle quantity updates
        new_quantity = data.get('quantity')
        if new_quantity is not None:
            try:
                quantity = int(new_quantity)
                if quantity >= 0:
                    product.quantity = quantity
                    product.save()
                    return JsonResponse({'success': True, 'message': 'Inventory updated'})
            except ValueError:
                pass

    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


# Add these to your existing views.py

@method_decorator(admin_required, name='dispatch')
class UserManagementAPI(APIView):
    def get(self, request):
        try:
            role_filter = request.GET.get('role', '')
            verification_filter = request.GET.get('verification', '')
            status_filter = request.GET.get('status', '')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            page = int(request.GET.get('page', 1))
            page_size = 20

            queryset = User.objects.all()

            # Apply filters
            if role_filter:
                queryset = queryset.filter(role=role_filter)
            if verification_filter == 'pending':
                queryset = queryset.filter(email_verified=False)
            elif verification_filter == 'verified':
                queryset = queryset.filter(email_verified=True)
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
            if date_from:
                queryset = queryset.filter(date_joined__gte=date_from)
            if date_to:
                queryset = queryset.filter(date_joined__lte=date_to)

            total_count = queryset.count()
            start_idx = (page - 1) * page_size
            users = queryset.order_by(
                '-date_joined')[start_idx:start_idx + page_size]

            serializer = UserManagementSerializer(users, many=True)

            return Response({
                'users': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            })
        except Exception as e:
            print(f"DEBUG: Error in UserManagementAPI: {str(e)}")
            return Response({'error': str(e)}, status=500)


@method_decorator(admin_required, name='dispatch')
class ProductManagementAPI(APIView):
    def get(self, request):
        try:
            print("DEBUG: ProductManagementAPI called")
            products = Product.objects.all()[:50]
            print(f"DEBUG: Found {len(products)} products")

            # Check if serializer exists
            from .serializers import ProductManagementSerializer
            print("DEBUG: Serializer imported successfully")

            serializer = ProductManagementSerializer(products, many=True)
            print("DEBUG: Serialization successful")

            return Response(serializer.data)
        except Exception as e:
            print(f"DEBUG: Error in ProductManagementAPI: {str(e)}")
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=500)
# Add to urls.py


# Add payment stats endpoint


@method_decorator(admin_required, name='dispatch')
class PaymentStatsAPI(APIView):
    def get(self, request):
        from payments.models import Payment
        stats = {
            'total': Payment.objects.count(),
            'pending': Payment.objects.filter(status='pending').count(),
            'completed': Payment.objects.filter(status='completed').count(),
            'failed': Payment.objects.filter(status='failed').count(),
        }
        return Response(stats)


# Add this to your admin_dashboard/views.py

@method_decorator(admin_required, name='dispatch')
class OrderManagementAPI(APIView):
    def get(self, request):
        try:
            status_filter = request.GET.get('status', '')
            payment_status_filter = request.GET.get('payment_status', '')
            payment_status_detailed_filter = request.GET.get(
                'payment_status_detailed', '')
            search = request.GET.get('search', '')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 20))
            sort = request.GET.get('sort', 'newest')

            queryset = Order.objects.all().select_related('user')

            # Apply filters
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if payment_status_filter:
                queryset = queryset.filter(
                    payment_status=payment_status_filter)
            if payment_status_detailed_filter:
                if payment_status_detailed_filter == 'no_payment':
                    queryset = queryset.filter(payments__isnull=True)
                else:
                    queryset = queryset.filter(
                        payments__status=payment_status_detailed_filter)
            if search:
                queryset = queryset.filter(
                    Q(order_number__icontains=search) |
                    Q(user__email__icontains=search) |
                    Q(user__first_name__icontains=search) |
                    Q(user__last_name__icontains=search)
                )
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)

            # Apply sorting
            if sort == 'newest':
                queryset = queryset.order_by('-created_at')
            elif sort == 'oldest':
                queryset = queryset.order_by('created_at')
            elif sort == 'total_asc':
                queryset = queryset.order_by('grand_total')
            elif sort == 'total_desc':
                queryset = queryset.order_by('-grand_total')

            # Pagination
            total = queryset.count()
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit

            orders = list(queryset[start_idx:end_idx])

            # Enhanced serialization with payment info
            orders_data = []
            for order in orders:
                # Get the latest payment for this order
                latest_payment = Payment.objects.filter(
                    order=order).order_by('-created_at').first()

                order_data = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': f"{order.user.first_name} {order.user.last_name}",
                    'customer_email': order.user.email,
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'payment_method': order.payment_method,
                    'grand_total': str(order.grand_total),
                    'subtotal': str(order.subtotal),
                    'shipping_cost': str(order.shipping_cost),
                    'tax_amount': str(order.tax_amount),
                    'item_count': order.items.count(),
                    'created_at': order.created_at.isoformat(),
                    'updated_at': order.updated_at.isoformat(),

                    # FIXED: Enhanced payment information
                    'has_payment': latest_payment is not None,
                    'payment_status_detailed': latest_payment.status if latest_payment else 'no_payment',
                    'payment_amount': str(latest_payment.amount) if latest_payment else '0.00',
                    'payment_currency': latest_payment.currency if latest_payment else 'ETB',
                    'payment_created_at': latest_payment.created_at.isoformat() if latest_payment else None,
                    'payment_completed_at': latest_payment.completed_at.isoformat() if latest_payment and latest_payment.completed_at else None,
                }
                orders_data.append(order_data)

            return Response({
                'orders': orders_data,  # Use enhanced data instead of serializer
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total
                }
            })
        except Exception as e:
            print(f"DEBUG: Error in OrderManagementAPI: {str(e)}")
            return Response({'error': str(e)}, status=500)


@method_decorator(admin_required, name='dispatch')
class OrderDetailAPI(APIView):
    def get(self, request, order_id):
        """Get detailed order information"""
        try:
            order = Order.objects.select_related('user').prefetch_related(
                'items', 'items__product', 'status_history'
            ).get(id=order_id)

            serializer = OrderDetailManagementSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)
        except Exception as e:
            print(f"DEBUG: Error in OrderDetailAPI: {str(e)}")
            return Response({'error': str(e)}, status=500)


class CategoryListAPI(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class BrandListAPI(APIView):
    def get(self, request):
        brands = Brand.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)
