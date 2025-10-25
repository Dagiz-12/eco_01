from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class UserModelTests(TestCase):
    def test_create_user(self):
        """Test creating a new user"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            phone='+251911223344'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'customer')
        self.assertFalse(user.email_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        self.assertEqual(admin_user.role, 'admin')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class UserAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('users:user-register')
        self.login_url = reverse('users:user-login')
        self.profile_url = reverse('users:user-profile')

    def test_user_registration(self):
        """Test user registration API"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'phone': '+251911223355',
            'role': 'customer'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_user_login(self):
        """Test user login API"""
        # First create a user
        user = User.objects.create_user(
            email='login@example.com',
            username='loginuser',
            password='loginpass123'
        )

        # Then test login
        data = {
            'email': 'login@example.com',
            'password': 'loginpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'wrong@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
