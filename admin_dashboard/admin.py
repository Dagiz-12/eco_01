from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DashboardStats, AdminNotification, SalesReport


@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_orders', 'total_revenue', 'total_customers']
    readonly_fields = ['date', 'total_orders', 'total_revenue',
                       'total_customers', 'total_products', 'pending_orders']


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    readonly_fields = ['created_at']


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'period', 'start_date', 'end_date', 'total_sales']
    readonly_fields = ['generated_at']
