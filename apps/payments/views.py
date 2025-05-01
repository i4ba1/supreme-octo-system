import uuid
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.payments.serializers import PaymentSerializer
from apps.payments.services import PaymentService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def list_payments(request):
    """List user's payments."""
    status_filter = request.query_params.get('status')
    payments = await PaymentService.get_user_payments(request.user.id, status_filter)
    return Response(await PaymentSerializer(payments, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_payment(request, pk):
    """Get payment details."""
    try:
        payment = await PaymentService.get_by_id(uuid.UUID(pk), request.user.id)
        if not payment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(await PaymentSerializer(payment).data)
    except ValueError:
        return Response({"error": "Invalid payment ID"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def create_payment(request):
    """Create a new payment."""
    try:
        # Extract payment data
        order_id = request.data.get('order')
        payment_type = request.data.get('payment_type')
        amount = Decimal(request.data.get('amount', '0'))
        payment_method_id = request.data.get('payment_method')
        table_id = request.data.get('table')

        # Validate required fields
        if not order_id or not payment_type or amount <= 0:
            return Response({
                'error': 'Order ID, payment type, and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create payment using service
        payment = await PaymentService.create_payment(
            order_id=uuid.UUID(order_id),
            payment_type=payment_type,
            amount=amount,
            user_id=request.user.id,
            payment_method_id=uuid.UUID(payment_method_id) if payment_method_id else None,
            table_id=uuid.UUID(table_id) if table_id else None
        )

        return Response(await PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def check_payment_status(request, pk):
    """Check payment status."""
    try:
        status_info = await PaymentService.check_payment_status(uuid.UUID(pk), request.user.id)
        return Response(status_info)
    except ValueError:
        return Response({"error": "Invalid payment ID"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def download_qr(request, pk):
    """Download QR code for payment."""
    try:
        qr_data = await PaymentService.download_qr(uuid.UUID(pk), request.user.id)
        if not qr_data:
            return Response({'error': 'QR code not available'}, status=status.HTTP_404_NOT_FOUND)

        return Response(qr_data)
    except ValueError:
        return Response({"error": "Invalid payment ID"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def share_qr(request, pk):
    """Share QR code for payment."""
    try:
        success = await PaymentService.share_qr(uuid.UUID(pk), request.user.id)
        if not success:
            return Response({'error': 'QR code not available'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'QR code shared'})
    except ValueError:
        return Response({"error": "Invalid payment ID"}, status=status.HTTP_400_BAD_REQUEST)