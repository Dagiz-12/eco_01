from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Payment, Refund, CBETransaction, TeleBirrTransaction
from orders.models import Order
from users.models import User
from products.models import Product, Category, Brand


class PaymentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass'
        )
        self.order = Order.objects.create(
            user=self.user,
            shipping_address={},
            billing_address={},
            payment_method='stripe',
            subtotal=100.00,
            grand_total=100.00
        )

    def test_payment_creation(self):
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            amount=100.00,
            currency='USD'
        )
        self.assertTrue(payment.payment_id.startswith('pay_'))
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.amount, 100.00)

    def test_payment_successful_property(self):
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            amount=100.00,
            status='completed'
        )
        self.assertTrue(payment.is_successful)

    def test_cbe_transaction_creation(self):
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='cbe',
            amount=100.00
        )
        cbe_transaction = CBETransaction.objects.create(
            payment=payment,
            transaction_id='CBE123456789',
            merchant_id='TEST_MERCHANT',
            terminal_id='TEST_TERMINAL',
            invoice_number=payment.order.order_number
        )
        self.assertEqual(cbe_transaction.transaction_id, 'CBE123456789')
        self.assertEqual(cbe_transaction.status, 'initiated')


class PaymentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass'
        )
        self.order = Order.objects.create(
            user=self.user,
            shipping_address={},
            billing_address={},
            payment_method='stripe',
            subtotal=100.00,
            grand_total=100.00
        )

        self.client.force_authenticate(user=self.user)

        self.payment_list_url = reverse('payments:payment-list')
        self.payment_create_url = reverse(
            'payments:payment-create', kwargs={'order_id': self.order.id})

    def test_payment_list_authenticated(self):
        response = self.client.get(self.payment_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cbe_payment_creation(self):
        cbe_url = reverse('payments:cbe-payment-initiate',
                          kwargs={'order_id': self.order.id})
        data = {'phone_number': '+251911223344'}

        response = self.client.post(cbe_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction', response.data)

    def test_telebirr_payment_creation(self):
        telebirr_url = reverse(
            'payments:telebirr-payment-initiate', kwargs={'order_id': self.order.id})
        data = {'phone_number': '+251911223344'}

        response = self.client.post(telebirr_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction', response.data)


class GatewayTests(TestCase):
    def setUp(self):
        from .gateways import StripeGateway, CBEGateway, TeleBirrGateway

        self.stripe_gateway = StripeGateway()
        self.cbe_gateway = CBEGateway()
        self.telebirr_gateway = TeleBirrGateway()

    def test_gateway_initialization(self):
        self.assertEqual(self.stripe_gateway.name, 'StripeGateway')
        self.assertEqual(self.cbe_gateway.name, 'CBEGateway')
        self.assertEqual(self.telebirr_gateway.name, 'TeleBirrGateway')

    def test_gateway_config_retrieval(self):
        # Test that gateway config methods don't raise errors
        try:
            self.stripe_gateway.get_gateway_config()
            self.cbe_gateway.get_gateway_config()
            self.telebirr_gateway.get_gateway_config()
        except Exception as e:
            self.fail(f"Gateway config retrieval failed: {e}")


class WebhookTests(APITestCase):
    def test_stripe_webhook_endpoint(self):
        url = reverse('payments:stripe-webhook')
        response = self.client.post(url, {})
        # Should return 200 even for invalid webhooks (security measure)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cbe_webhook_endpoint(self):
        url = reverse('payments:cbe-webhook')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_telebirr_webhook_endpoint(self):
        url = reverse('payments:telebirr-webhook')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
