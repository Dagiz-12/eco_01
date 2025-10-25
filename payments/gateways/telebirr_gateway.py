import time
import hashlib
import requests
from django.conf import settings
from .base import BasePaymentGateway


class TeleBirrGateway(BasePaymentGateway):
    """TeleBirr payment gateway implementation"""

    def __init__(self):
        super().__init__()
        self.short_code = settings.TELEBIRR_SHORT_CODE
        self.app_id = settings.TELEBIRR_APP_ID
        self.app_key = settings.TELEBIRR_APP_KEY
        self.app_secret = settings.TELEBIRR_APP_SECRET
        self.api_url = settings.TELEBIRR_API_URL

    def initiate_payment(self, payment, **kwargs):
        """Initiate TeleBirr payment"""
        try:
            phone_number = kwargs.get('phone_number')
            transaction_id = f"TBR{int(time.time())}{payment.id:06d}"

            # Prepare payment request
            payment_data = {
                'outTradeNo': transaction_id,
                'subject': f"Order #{payment.order.order_number}",
                'totalAmount': str(payment.amount),
                'shortCode': self.short_code,
                'notifyUrl': f"{settings.BASE_URL}/api/payments/telebirr/callback/",
                'returnUrl': f"{settings.BASE_URL}/orders/{payment.order.id}/",
                'receiveName': "Hagerbet E-Commerce",
                'appId': self.app_id,
                'timeoutExpress': '30m',
                'nonce': str(int(time.time())),
                'timestamp': str(int(time.time() * 1000))
            }

            # Generate signature
            signature = self._generate_signature(payment_data)
            payment_data['sign'] = signature

            # Call TeleBirr API (simulated for now)
            # response = requests.post(f"{self.api_url}/unifiedorder", json=payment_data)
            # response_data = response.json()

            # Simulated response
            response_data = {
                'code': '200',
                'msg': 'success',
                'outTradeNo': transaction_id,
                'qrCode': f'https://telebirr.qr.example.com/{transaction_id}',
                'ussd': f'*806*{transaction_id}#',
                'deepLink': f'telebirr://payment/{transaction_id}'
            }

            return {
                'success': response_data.get('code') == '200',
                'gateway_payment_id': transaction_id,
                'response_data': response_data,
                'message': response_data.get('msg', 'TeleBirr payment initiated')
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'TeleBirr payment initiation failed: {str(e)}'
            }

    def verify_payment(self, transaction_id):
        """Verify TeleBirr payment status"""
        try:
            # Call TeleBirr verification API (simulated)
            # response = requests.get(f"{self.api_url}/orderquery/{transaction_id}")
            # response_data = response.json()

            # Simulated response
            response_data = {
                'code': '200',
                'msg': 'success',
                'tradeStatus': 'SUCCESS'
            }

            return {
                'success': response_data.get('code') == '200',
                'status': response_data.get('tradeStatus'),
                'response_data': response_data,
                'message': response_data.get('msg')
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def process_refund(self, payment, amount, reason):
        """Process TeleBirr refund"""
        # TeleBirr refund implementation would go here
        return {
            'success': False,
            'message': 'Refund not yet implemented for TeleBirr'
        }

    def handle_webhook(self, payload):
        """Handle TeleBirr webhook"""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(payload):
                return {'success': False, 'error': 'Invalid signature'}

            transaction_id = payload.get('outTradeNo')
            status = payload.get('tradeStatus')

            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': status,
                'message': 'TeleBirr webhook processed successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_signature(self, data):
        """Generate TeleBirr API signature"""
        sorted_params = sorted(data.items())
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_string += self.app_secret
        return hashlib.sha256(sign_string.encode()).hexdigest()

    def _verify_webhook_signature(self, payload):
        """Verify TeleBirr webhook signature"""
        # Implementation for verifying webhook signature
        return True  # Simplified for now
