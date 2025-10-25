from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Brand, Product, ProductImage
from users.models import User


class CategoryModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic devices and accessories"
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Electronics")
        self.assertEqual(self.category.slug, "electronics")
        self.assertTrue(self.category.is_active)

    def test_category_str(self):
        self.assertEqual(str(self.category), "Electronics")

    def test_category_hierarchy(self):
        subcategory = Category.objects.create(
            name="Smartphones",
            parent=self.category
        )
        self.assertEqual(subcategory.parent, self.category)
        self.assertIn(subcategory, self.category.children.all())


class BrandModelTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Samsung",
            description="South Korean electronics company"
        )

    def test_brand_creation(self):
        self.assertEqual(self.brand.name, "Samsung")
        self.assertEqual(self.brand.slug, "samsung")
        self.assertTrue(self.brand.is_active)


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.brand = Brand.objects.create(name="Samsung")
        self.product = Product.objects.create(
            name="Galaxy S23",
            description="Flagship smartphone",
            category=self.category,
            brand=self.brand,
            price=999.99,
            sku="SAM-GS23-001",
            quantity=50,
            status="published"
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Galaxy S23")
        self.assertEqual(self.product.price, 999.99)
        self.assertEqual(self.product.quantity, 50)
        self.assertEqual(self.product.status, "published")
        self.assertTrue(self.product.is_in_stock)

    def test_product_slug_generation(self):
        self.assertEqual(self.product.slug, "galaxy-s23")

    def test_low_stock_detection(self):
        self.product.quantity = 3
        self.product.low_stock_threshold = 5
        self.assertTrue(self.product.is_low_stock)

    def test_discount_calculation(self):
        self.product.compare_price = 1199.99
        self.assertEqual(self.product.discount_percentage, 16)  # ~16% discount


class ProductAPITests(APITestCase):
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

        self.product_list_url = reverse('products:product-list')
        self.product_detail_url = reverse(
            'products:product-detail', kwargs={'slug': self.product.slug})
        self.category_list_url = reverse('products:category-list')
        self.search_url = reverse('products:product-search')

    def test_product_list(self):
        response = self.client.get(self.product_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_product_detail(self):
        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')

    def test_product_filter_by_category(self):
        response = self.client.get(
            f"{self.product_list_url}?category=electronics")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_search(self):
        search_data = {'query': 'Test Product'}
        response = self.client.post(self.search_url, search_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_featured_products(self):
        self.product.is_featured = True
        self.product.save()

        featured_url = reverse('products:featured-products')
        response = self.client.get(featured_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class CategoryAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.subcategory = Category.objects.create(
            name="Smartphones",
            parent=self.category
        )

    def test_category_list(self):
        url = reverse('products:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only parent categories

    def test_category_detail(self):
        url = reverse('products:category-detail',
                      kwargs={'slug': self.category.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Electronics')


class AdminProductTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='adminpass'
        )
        self.category = Category.objects.create(name="Electronics")
        self.brand = Brand.objects.create(name="Samsung")

        self.client.force_authenticate(user=self.admin_user)

    def test_product_create(self):
        url = reverse('products:product-create')
        data = {
            'name': 'New Product',
            'description': 'New product description',
            'category': self.category.id,
            'brand': self.brand.id,
            'price': 299.99,
            'sku': 'NEW-001',
            'quantity': 100,
            'status': 'draft'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
