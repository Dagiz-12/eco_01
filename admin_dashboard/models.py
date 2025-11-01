from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order
from users.models import User
from payments.models import Payment

User = get_user_model()


class DashboardStats(models.Model):
    """Store aggregated dashboard statistics for performance"""
    date = models.DateField(unique=True)
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    total_customers = models.IntegerField(default=0)
    total_products = models.IntegerField(default=0)
    pending_orders = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Dashboard Statistics'
        verbose_name_plural = 'Dashboard Statistics'


class AdminNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'New Order'),
        ('payment', 'Payment Issue'),
        ('inventory', 'Low Inventory'),
        ('user', 'User Verification'),
        ('system', 'System Alert'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    related_object_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class SalesReport(models.Model):
    REPORT_PERIODS = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    title = models.CharField(max_length=200)
    period = models.CharField(max_length=20, choices=REPORT_PERIODS)
    start_date = models.DateField()
    end_date = models.DateField()
    total_sales = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    average_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.period}"
