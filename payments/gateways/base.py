from abc import ABC, abstractmethod
from django.conf import settings


class BasePaymentGateway(ABC):
    """Abstract base class for all payment gateways"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.test_mode = getattr(settings, 'DEBUG', True)

    @abstractmethod
    def initiate_payment(self, payment, **kwargs):
        """Initiate payment with the gateway"""
        pass

    @abstractmethod
    def verify_payment(self, transaction_id):
        """Verify payment status"""
        pass

    @abstractmethod
    def process_refund(self, payment, amount, reason):
        """Process refund"""
        pass

    @abstractmethod
    def handle_webhook(self, payload):
        """Handle webhook callbacks"""
        pass

    def get_gateway_config(self):
        """Get gateway-specific configuration"""
        gateway_name = self.__class__.__name__.replace('Gateway', '').upper()
        return getattr(settings, f'{gateway_name}_CONFIG', {})

    def validate_amount(self, amount):
        """Validate payment amount"""
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        return True
