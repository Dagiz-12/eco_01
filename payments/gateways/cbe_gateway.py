import time
import hmac
import hashlib
import requests
from django.conf import settings
from .base import BasePaymentGateway


class CBEGateway(BasePaymentGateway):
    """CBE Birr payment gateway implementation"""

    def __init__(self):
        super().__init__()
        self.merchant_id = settings.CBE_MERCHANT_ID
        self.terminal_id = settings.CBE_TERMINAL_ID
        self.secret_key = settings.CBE_SECRET_KEY
        self.api_url = settings.CBE_API_URL

    def initiate_payment(self, payment, **kwargs):
        """Initiate CBE Birr payment"""
        try:
            phone_number = kwargs.get('phone_number')
            transaction_id = f"CBE{int(time.time())}{payment.id:06d}"

            # Prepare payment request
            payment_data = {
                'merchantId': self.merchant_id,
                'terminalId': self.terminal_id,
                'invoiceNo': payment.order.order_number,
                'amount': str(payment.amount),
                'currency': 'ETB',
                'transactionId': transaction_id,
                'customerPhone': phone_number,
                'callbackUrl': f"{settings.BASE_URL}/api/payments/cbe/callback/",
                'timestamp': str(int(time.time()))
            }

            # Generate signature
            signature = self._generate_signature(payment_data)
            payment_data['signature'] = signature

            # Call CBE API (simulated for now)
            # response = requests.post(f"{self.api_url}/initiate", json=payment_data)
            # response_data = response.json()

            # Simulated response
            response_data = {
                'status': 'SUCCESS',
                'transactionId': transaction_id,
                'message': 'Payment initiated successfully',
                'ussdCode': f'*127*1*{transaction_id}#',
                'paymentUrl': f'https://cbe-payment.example.com/pay/{transaction_id}'
            }

            return {
                'success': response_data.get('status') == 'SUCCESS',
                'gateway_payment_id': transaction_id,
                'response_data': response_data,
                'message': response_data.get('message', 'CBE payment initiated')
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'CBE payment initiation failed: {str(e)}'
            }

    def verify_payment(self, transaction_id):
        """Verify CBE payment status"""
        try:
            # Call CBE verification API (simulated)
            # response = requests.get(f"{self.api_url}/verify/{transaction_id}")
            # response_data = response.json()

            # Simulated response
            response_data = {
                'status': 'SUCCESS',
                'transactionId': transaction_id,
                'message': 'Payment verified successfully'
            }

            return {
                'success': response_data.get('status') == 'SUCCESS',
                'status': response_data.get('status'),
                'response_data': response_data,
                'message': response_data.get('message')
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def process_refund(self, payment, amount, reason):
        """Process CBE refund"""
        # CBE refund implementation would go here
        return {
            'success': False,
            'message': 'Refund not yet implemented for CBE'
        }

    def handle_webhook(self, payload):
        """Handle CBE webhook"""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(payload):
                return {'success': False, 'error': 'Invalid signature'}

            transaction_id = payload.get('transactionId')
            status = payload.get('status')

            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': status,
                'message': 'CBE webhook processed successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_signature(self, data):
        """Generate CBE API signature"""
        signature_string = (
            f"{data['merchantId']}{data['terminalId']}"
            f"{data['invoiceNo']}{data['amount']}"
            f"{data['transactionId']}{data['timestamp']}"
        )
        return hmac.new(
            self.secret_key.encode(),
            signature_string.encode(),
            hashlib.sha256
        ).hexdigest()

    def _verify_webhook_signature(self, payload):
        """Verify CBE webhook signature"""
        # Implementation for verifying webhook signature
        return True  # Simplified for now
