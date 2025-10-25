from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Order, OrderItem
from users.models import User, Address
from products.models import Product, Category, Brand
from cart.models import Cart, CartItem


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass'
        )
        self.category = Category.objects.create(name="Electronics")
        self.brand = Brand.objects.create(name="Samsung")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            category=self.category,
            brand=self.brand,
            price=100.00,
            sku="TEST-001",
            quantity=10,
            status="published"
        )
        self.shipping_address = Address.objects.create(
            user=self.user,
            address_type='shipping',
            street="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country",
            zip_code="12345"
        )
        self.billing_address = Address.objects.create(
            user=self.user,
            address_type='billing',
            street="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country",
            zip_code="12345"
        )

    def test_order_creation(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address={},
            billing_address={},
            payment_method='stripe',
            subtotal=100.00,
            grand_total=100.00
        )
        self.assertTrue(order.order_number.startswith('ORD-'))
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.payment_status, 'pending')

    def test_order_item_creation(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address={},
            billing_address={},
            payment_method='stripe',
            subtotal=200.00,
            grand_total=200.00
        )
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=100.00
        )
        self.assertEqual(order_item.line_total, 200.00)
        self.assertEqual(order.items.count(), 1)


class OrderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass'
        )
        self.category = Category.objects.create(name="Electronics")
        self.brand = Brand.objects.create(name="Samsung")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            category=self.category,
            brand=self.brand,
            price=100.00,
            sku="TEST-001",
            quantity=10,
            status="published"
        )
        self.shipping_address = Address.objects.create(
            user=self.user,
            address_type='shipping',
            street="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country",
            zip_code="12345"
        )
        self.billing_address = Address.objects.create(
            user=self.user,
            address_type='billing',
            street="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country",
            zip_code="12345"
        )

        # Create cart with items
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=100.00
        )

        self.client.force_authenticate(user=self.user)

        self.order_list_url = reverse('orders:order-list')
        self.order_create_url = reverse('orders:order-create')

    def test_create_order(self):
        data = {
            'shipping_address_id': self.shipping_address.id,
            'billing_address_id': self.billing_address.id,
            'payment_method': 'stripe'
        }
        response = self.client.post(self.order_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.grand_total, 200.00)

    def test_order_list(self):
        # Create an order first
        order = Order.objects.create(
            user=self.user,
            shipping_address={},
            billing_address={},
            payment_method='stripe',
            subtotal=100.00,
            grand_total=100.00
        )

        response = self.client.get(self.order_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_order_empty_cart(self):
        # Clear cart
        self.cart.clear()

        data = {
            'shipping_address_id': self.shipping_address.id,
            'billing_address_id': self.billing_address.id,
            'payment_method': 'stripe'
        }
        response = self.client.post(self.order_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
