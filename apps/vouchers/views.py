import uuid

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response

from apps.vouchers.serializers import VoucherSerializer, UserVoucherSerializer, OrderVoucherSerializer
from apps.vouchers.services import VoucherService


@api_view(['GET'])
@permission_classes([AllowAny])
async def list_vouchers(request):
    """List all active vouchers."""
    include_inactive = request.query_params.get('include_inactive', 'false').lower() == 'true'

    # Only admins can see inactive vouchers
    if include_inactive and not request.user.is_staff:
        include_inactive = False

    vouchers = await VoucherService.get_all_vouchers(include_inactive)
    data = await VoucherSerializer().to_representation_list(vouchers)
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def list_user_vouchers(request):
    """List vouchers owned by the current user."""
    used = None
    if 'used' in request.query_params:
        used = request.query_params.get('used').lower() == 'true'

    user_vouchers = await VoucherService.get_user_vouchers(request.user.id, used)
    data = await UserVoucherSerializer().to_representation_list(user_vouchers)
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def redeem_voucher(request):
    """Redeem a voucher using points."""
    try:
        voucher_id = request.data.get('voucher_id')
        if not voucher_id:
            return Response({
                'error': 'Voucher ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Redeem voucher
        user_voucher = await VoucherService.redeem_voucher(
            request.user.id,
            uuid.UUID(voucher_id)
        )

        # Get updated user points
        from apps.users.models import User
        user = await User.get(id=request.user.id)

        # Return response
        data = await UserVoucherSerializer().to_representation(user_voucher)
        data['remaining_points'] = user.total_points

        return Response(data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def apply_voucher(request):
    """Apply a voucher to an order."""
    try:
        order_id = request.data.get('order_id')
        user_voucher_id = request.data.get('user_voucher_id')

        if not order_id or not user_voucher_id:
            return Response({
                'error': 'Order ID and User Voucher ID are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Apply voucher
        order_voucher = await VoucherService.apply_voucher_to_order(
            uuid.UUID(order_id),
            uuid.UUID(user_voucher_id),
            request.user.id
        )

        data = await OrderVoucherSerializer().to_representation(order_voucher)
        return Response(data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
async def create_voucher(request):
    """Create a new voucher (admin only)."""
    try:
        voucher = await VoucherService.create_voucher(request.data)
        data = await VoucherSerializer().to_representation(voucher)
        return Response(data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)