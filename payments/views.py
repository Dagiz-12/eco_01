# payments/views.py - Fix the imports section
from .models import Payment, Refund, CBETransaction, TeleBirrTransaction, PaymentManager
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import Payment, Refund, PaymentGateway, PaymentManager
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, RefundSerializer,
    RefundCreateSerializer, StripePaymentIntentSerializer,
    CBETransactionSerializer, TeleBirrTransactionSerializer  # Added these
)
from orders.models import Order
# Remove this duplicate import: from payments.serializers import CBETransactionSerializer, TeleBirrTransactionSerializer


class PaymentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Check if order already has a payment
        if hasattr(order, 'payment'):
            return Response(
                {'error': 'Order already has a payment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PaymentCreateSerializer(data=request.data)

        if serializer.is_valid():
            payment_method = serializer.validated_data['payment_method']

            # Create payment
            payment = PaymentManager.create_payment(order, payment_method)

            # Process payment based on method
            if payment_method == 'stripe':
                success, message = PaymentManager.process_stripe_payment(
                    payment,
                    serializer.validated_data['stripe_token']
                )
            elif payment_method == 'paypal':
                success, message = PaymentManager.process_paypal_payment(
                    payment,
                    serializer.validated_data['paypal_order_id']
                )
            else:
                # For other methods like bank transfer, COD
                success, message = True, 'Payment initiated successfully'

            if success:
                payment_serializer = PaymentSerializer(payment)
                return Response({
                    'message': message,
                    'payment': payment_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': message,
                    'payment': PaymentSerializer(payment).data
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related('order')


class RefundCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = RefundCreateSerializer(data=request.data)

        if serializer.is_valid():
            payment = serializer.validated_data['payment']
            amount = serializer.validated_data['amount']
            reason = serializer.validated_data['reason']

            success, message = PaymentManager.process_refund(
                payment, amount, reason)

            if success:
                refund = Refund.objects.filter(
                    payment=payment).latest('created_at')
                refund_serializer = RefundSerializer(refund)
                return Response({
                    'message': message,
                    'refund': refund_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': message},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefundListView(generics.ListAPIView):
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Refund.objects.filter(payment__user=self.request.user).select_related('payment')


class StripePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        serializer = StripePaymentIntentSerializer(data={
            'amount': float(order.grand_total),
            'currency': 'usd'
        })

        if serializer.is_valid():
            try:
                import stripe
                from django.conf import settings

                stripe.api_key = settings.STRIPE_SECRET_KEY

                intent = stripe.PaymentIntent.create(
                    amount=int(order.grand_total * 100),  # Convert to cents
                    currency='usd',
                    metadata={
                        'order_number': order.order_number,
                        'user_id': str(request.user.id)
                    }
                )

                return Response({
                    'client_secret': intent.client_secret,
                    'payment_intent_id': intent.id
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response(
                    {'error': f'Failed to create payment intent: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Webhook Views


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = []  # No authentication for webhooks

    def post(self, request):
        import stripe
        from django.conf import settings
        from django.http import HttpResponse

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self.handle_payment_succeeded(payment_intent)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self.handle_payment_failed(payment_intent)

        return HttpResponse(status=200)

    def handle_payment_succeeded(self, payment_intent):
        """Handle successful payment from Stripe"""
        try:
            order_number = payment_intent['metadata'].get('order_number')
            if order_number:
                order = Order.objects.get(order_number=order_number)
                payment = getattr(order, 'payment', None)
                if payment:
                    payment.mark_as_completed(
                        gateway_payment_id=payment_intent['id'],
                        response_data=payment_intent
                    )
        except Exception as e:
            print(f"Error handling successful payment: {e}")

    def handle_payment_failed(self, payment_intent):
        """Handle failed payment from Stripe"""
        try:
            order_number = payment_intent['metadata'].get('order_number')
            if order_number:
                order = Order.objects.get(order_number=order_number)
                payment = getattr(order, 'payment', None)
                if payment:
                    payment.mark_as_failed(response_data=payment_intent)
        except Exception as e:
            print(f"Error handling failed payment: {e}")


@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def paypal_webhook(request):
    """Handle PayPal webhooks"""
    # PayPal webhook implementation would go here
    # This is a simplified version
    try:
        data = json.loads(request.body)
        event_type = data.get('event_type')

        # Handle different PayPal events
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            # Handle completed payment
            pass
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            # Handle denied payment
            pass

        return Response(status=200)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ... previous views remain the same


class CBEPaymentInitiateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Check if order already has a payment
        if hasattr(order, 'payment'):
            return Response(
                {'error': 'Order already has a payment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create payment
        payment = PaymentManager.create_payment(order, 'cbe')
        phone_number = request.data.get('phone_number')

        # Initiate CBE payment
        success, message, response_data = PaymentManager.initiate_cbe_payment(
            payment, phone_number
        )

        if success:
            cbe_transaction = CBETransaction.objects.get(payment=payment)
            transaction_serializer = CBETransactionSerializer(cbe_transaction)

            return Response({
                'message': message,
                'transaction': transaction_serializer.data,
                'payment_details': response_data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )


class TeleBirrPaymentInitiateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Check if order already has a payment
        if hasattr(order, 'payment'):
            return Response(
                {'error': 'Order already has a payment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create payment
        payment = PaymentManager.create_payment(order, 'telebirr')
        phone_number = request.data.get('phone_number')

        # Initiate TeleBirr payment
        success, message, response_data = PaymentManager.initiate_telebirr_payment(
            payment, phone_number
        )

        if success:
            telebirr_transaction = TeleBirrTransaction.objects.get(
                payment=payment)
            transaction_serializer = TeleBirrTransactionSerializer(
                telebirr_transaction)

            return Response({
                'message': message,
                'transaction': transaction_serializer.data,
                'payment_details': response_data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )


class CBEVerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, transaction_id):
        success, message = PaymentManager.verify_cbe_payment(transaction_id)

        if success:
            cbe_transaction = CBETransaction.objects.get(
                transaction_id=transaction_id)
            transaction_serializer = CBETransactionSerializer(cbe_transaction)
            payment_serializer = PaymentSerializer(cbe_transaction.payment)

            return Response({
                'message': message,
                'transaction': transaction_serializer.data,
                'payment': payment_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )


class TeleBirrVerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, transaction_id):
        success, message = PaymentManager.verify_telebirr_payment(
            transaction_id)

        if success:
            telebirr_transaction = TeleBirrTransaction.objects.get(
                transaction_id=transaction_id)
            transaction_serializer = TeleBirrTransactionSerializer(
                telebirr_transaction)
            payment_serializer = PaymentSerializer(
                telebirr_transaction.payment)

            return Response({
                'message': message,
                'transaction': transaction_serializer.data,
                'payment': payment_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

# Webhook Views for CBE and TeleBirr


@method_decorator(csrf_exempt, name='dispatch')
class CBEWebhookView(APIView):
    permission_classes = []  # No authentication for webhooks

    def post(self, request):
        try:
            callback_data = request.data

            # Verify callback signature (in real implementation)
            success, message = PaymentManager.handle_cbe_callback(
                callback_data)

            if success:
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'status': 'error', 'message': message},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class TeleBirrWebhookView(APIView):
    permission_classes = []  # No authentication for webhooks

    def post(self, request):
        try:
            callback_data = request.data

            # Verify callback signature (in real implementation)
            success, message = PaymentManager.handle_telebirr_callback(
                callback_data)

            if success:
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'status': 'error', 'message': message},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
