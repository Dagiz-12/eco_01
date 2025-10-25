import stripe
from django.conf import settings
from .base import BasePaymentGateway


class StripeGateway(BasePaymentGateway):
    """Stripe payment gateway implementation"""

    def __init__(self):
        super().__init__()
        self.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        stripe.api_key = self.api_key

    def initiate_payment(self, payment, **kwargs):
        """Initiate Stripe payment"""
        try:
            token = kwargs.get('token')

            # Create Stripe charge
            charge = stripe.Charge.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency=payment.currency.lower(),
                source=token,
                description=f"Order #{payment.order.order_number}",
                metadata={
                    'order_number': payment.order.order_number,
                    'payment_id': payment.payment_id,
                    'user_id': str(payment.user.id)
                }
            )

            if charge.status == 'succeeded':
                return {
                    'success': True,
                    'gateway_payment_id': charge.id,
                    'response_data': charge,
                    'message': 'Payment successful'
                }
            else:
                return {
                    'success': False,
                    'response_data': charge,
                    'message': f'Payment failed: {charge.failure_message}'
                }

        except stripe.error.CardError as e:
            return {
                'success': False,
                'response_data': {'error': str(e)},
                'message': f'Card error: {e.user_message}'
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'response_data': {'error': str(e)},
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'response_data': {'error': str(e)},
                'message': f'Unexpected error: {str(e)}'
            }

    def verify_payment(self, transaction_id):
        """Verify Stripe payment"""
        try:
            charge = stripe.Charge.retrieve(transaction_id)
            return {
                'success': charge.status == 'succeeded',
                'status': charge.status,
                'response_data': charge
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def process_refund(self, payment, amount, reason):
        """Process Stripe refund"""
        try:
            refund = stripe.Refund.create(
                charge=payment.gateway_payment_id,
                amount=int(amount * 100),  # Convert to cents
                reason='requested_by_customer'
            )

            return {
                'success': refund.status == 'succeeded',
                'gateway_refund_id': refund.id,
                'response_data': refund,
                'message': 'Refund processed successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Refund failed: {str(e)}'
            }

    def handle_webhook(self, payload, signature):
        """Handle Stripe webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            return {
                'success': True,
                'event_type': event['type'],
                'event_data': event['data']['object'],
                'message': 'Webhook processed successfully'
            }

        except ValueError as e:
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError as e:
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
