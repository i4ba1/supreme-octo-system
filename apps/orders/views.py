from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import uuid
from decimal import Decimal

from apps.orders.services import OrderService
from apps.orders.serializers import OrderSerializer, OrderItemSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def list_orders(request):
    """List user's orders."""
    status_filter = request.query_params.get('status')
    orders = await OrderService.get_user_orders(request.user.id, status_filter)
    return Response(await OrderSerializer(orders, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_order(request, pk):
    """Get order details."""
    try:
        order = await OrderService.get_by_id(uuid.UUID(pk), request.user.id)
        if not order:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(await OrderSerializer(order).data)
    except ValueError:
        return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def create_order(request):
    """Create a new order."""
    try:
        # Extract basic order data
        restaurant_id = request.data.get('restaurant')
        order_mode = request.data.get('order_mode', 'dine_in')
        table_id = request.data.get('table')
        payment_method_id = request.data.get('payment_method')

        # Extract financial data
        subtotal = Decimal(request.data.get('subtotal', '0'))
        order_fee = Decimal(request.data.get('order_fee', '0'))
        discount_amount = Decimal(request.data.get('discount_amount', '0'))
        total_amount = Decimal(request.data.get('total_amount', '0'))

        # Extract items data
        items_data = request.data.get('items', [])

        # Extract vouchers
        voucher_ids = request.data.get('voucher_ids', [])

        # Validate required fields
        if not restaurant_id or not items_data:
            return Response({
                'error': 'Restaurant ID and items are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create order using service
        order = await OrderService.create_order(
            user_id=request.user.id,
            restaurant_id=uuid.UUID(restaurant_id),
            order_mode=order_mode,
            subtotal=subtotal,
            order_fee=order_fee,
            discount_amount=discount_amount,
            total_amount=total_amount,
            table_id=uuid.UUID(table_id) if table_id else None,
            payment_method_id=uuid.UUID(payment_method_id) if payment_method_id else None,
            items_data=items_data,
            voucher_ids=[uuid.UUID(v_id) for v_id in voucher_ids] if voucher_ids else None
        )

        return Response(await OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def cancel_order(request, pk):
    """Cancel an order."""
    try:
        success = await OrderService.cancel_order(uuid.UUID(pk), request.user.id)
        if success:
            return Response({'status': 'order cancelled'})
        else:
            return Response({'error': 'Cannot cancel order'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"error": "Invalid order ID"}, status=status.HTTP_400_BAD_REQUEST)
