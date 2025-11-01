from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.core.exceptions import PermissionDenied


def admin_required(function=None, permissions=[]):
    """
    Decorator for views that require admin/staff access with specific permissions
    """
    def check_admin(user):
        if not user.is_authenticated:
            return False
        if not user.is_staff and not user.is_superuser:
            return False

        # Check specific permissions if provided
        if permissions:
            user_perms = user.get_all_permissions()
            if not any(perm in user_perms for perm in permissions):
                return False

        return True

    actual_decorator = user_passes_test(check_admin, login_url='/admin/login/')

    if function:
        return actual_decorator(function)
    return actual_decorator


def role_required(roles=[]):
    """
    Decorator for views that require specific user roles
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")

            if not any(role == request.user.role for role in roles):
                return HttpResponseForbidden("Insufficient permissions")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Specific permission decorators


def can_manage_orders(function=None):
    return admin_required(function, permissions=['admin_dashboard.manage_orders'])


def can_manage_products(function=None):
    return admin_required(function, permissions=['admin_dashboard.manage_products'])


def can_manage_users(function=None):
    return admin_required(function, permissions=['admin_dashboard.manage_users'])


def can_view_analytics(function=None):
    return admin_required(function, permissions=['admin_dashboard.view_analytics'])
