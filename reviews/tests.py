from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order
from .models import Review, ReviewVote

User = get_user_model()


class ReviewModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=100.00
        )

    def test_create_review(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.status, 'pending')

    def test_verified_purchase(self):
        # Test verified purchase logic
        order = Order.objects.create(user=self.user, total_amount=100.00)
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            order=order,
            rating=5,
            title='Verified review',
            comment='Purchased and reviewed'
        )
        self.assertTrue(review.is_verified_purchase)
