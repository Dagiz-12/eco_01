from .base import BasePaymentGateway


class PayPalGateway(BasePaymentGateway):
    """PayPal payment gateway implementation"""

    def initiate_payment(self, payment, **kwargs):
        """Initiate PayPal payment"""
        paypal_order_id = kwargs.get('paypal_order_id')

        # Simulate PayPal payment processing
        return {
            'success': True,
            'gateway_payment_id': paypal_order_id,
            'response_data': {'status': 'COMPLETED', 'id': paypal_order_id},
            'message': 'PayPal payment completed successfully'
        }

    def verify_payment(self, transaction_id):
        return {'success': True, 'status': 'COMPLETED'}

    def process_refund(self, payment, amount, reason):
        return {'success': True, 'message': 'PayPal refund processed'}

    def handle_webhook(self, payload):
        return {'success': True, 'message': 'PayPal webhook processed'}
