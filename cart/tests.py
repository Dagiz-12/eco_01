from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Cart, CartItem
from products.models import Product, Category, Brand
from users.models import User


class CartModelTests(TestCase):
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
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_creation(self):
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(self.cart.total_items, 0)
        self.assertEqual(self.cart.subtotal, 0)

    def test_cart_item_creation(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.price, 100.00)
        self.assertEqual(cart_item.line_total, 200.00)
        self.assertEqual(self.cart.total_items, 2)
        self.assertEqual(self.cart.subtotal, 200.00)


class CartAPITests(APITestCase):
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

        self.cart_url = reverse('cart:cart-detail')
        self.add_item_url = reverse('cart:cart-item-add')
        self.summary_url = reverse('cart:cart-summary')

    def test_get_cart_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)

    def test_add_item_to_cart(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'product_id': self.product.id,
            'quantity': 2
        }
        response = self.client.post(self.add_item_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cart']['total_items'], 2)
        self.assertEqual(response.data['cart']['subtotal'], '200.00')

    def test_add_item_insufficient_stock(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'product_id': self.product.id,
            'quantity': 15  # More than available stock
        }
        response = self.client.post(self.add_item_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_summary(self):
        self.client.force_authenticate(user=self.user)

        # Add item first
        data = {'product_id': self.product.id, 'quantity': 2}
        self.client.post(self.add_item_url, data)

        # Get summary
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(response.data['subtotal'], 200.00)


class CartSessionTests(APITestCase):
    def setUp(self):
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

        self.cart_url = reverse('cart:cart-detail')
        self.add_item_url = reverse('cart:cart-item-add')

    def test_anonymous_cart_creation(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cart_id', self.client.session)

    def test_add_item_to_anonymous_cart(self):
        data = {
            'product_id': self.product.id,
            'quantity': 1
        }
        response = self.client.post(self.add_item_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cart']['total_items'], 1)
