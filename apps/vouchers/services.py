import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from tortoise.transactions import atomic

from apps.orders.models import Order
from apps.users.models import User
from apps.vouchers.models import Voucher, UserVoucher, OrderVoucher


class VoucherService:
    @staticmethod
    async def get_all_vouchers(include_inactive: bool = False) -> List[Voucher]:
        """Get all vouchers, optionally including inactive ones."""
        query = Voucher.all()
        if not include_inactive:
            today = date.today()
            query = query.filter(
                is_active=True,
                expiry_date__gt=today
            )

        return await query

    @staticmethod
    async def get_voucher_by_id(voucher_id: uuid.UUID) -> Optional[Voucher]:
        """Get voucher by ID."""
        return await Voucher.get_or_none(id=voucher_id)

    @staticmethod
    async def get_voucher_by_code(code: str) -> Optional[Voucher]:
        """Get voucher by code."""
        return await Voucher.get_or_none(code=code)

    @staticmethod
    async def get_user_vouchers(
            user_id: uuid.UUID,
            used: Optional[bool] = None
    ) -> List[UserVoucher]:
        """Get vouchers owned by a user, optionally filtering by used status."""
        query = UserVoucher.filter(user_id=user_id)
        if used is not None:
            query = query.filter(is_used=used)

        return await query.prefetch_related('voucher')

    @staticmethod
    async def get_user_voucher_by_id(
            user_voucher_id: uuid.UUID,
            user_id: Optional[uuid.UUID] = None
    ) -> Optional[UserVoucher]:
        """Get user voucher by ID, optionally verifying ownership."""
        query = UserVoucher.get_or_none(id=user_voucher_id)
        if user_id:
            query = UserVoucher.get_or_none(id=user_voucher_id, user_id=user_id)

        return await query.prefetch_related('voucher')

    @staticmethod
    @atomic()
    async def redeem_voucher(user_id: uuid.UUID, voucher_id: uuid.UUID) -> UserVoucher:
        """Redeem a voucher using points."""
        # Get user and voucher
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("User not found")

        voucher = await Voucher.get_or_none(id=voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        # Verify voucher is active and not expired
        today = date.today()
        if not voucher.is_active or (voucher.expiry_date and voucher.expiry_date <= today):
            raise ValueError("Voucher is inactive or expired")

        # Check if user has enough points
        if user.total_points < voucher.points_cost:
            raise ValueError(
                f"Not enough points. Required: {voucher.points_cost}, Available: {user.total_points}"
            )

        # Deduct points
        user.total_points -= voucher.points_cost
        await user.save()

        # Create user voucher
        user_voucher = await UserVoucher.create(
            user_id=user_id,
            voucher_id=voucher_id,
            is_used=False
        )

        # Prefetch voucher for returning
        await user_voucher.fetch_related('voucher')

        return user_voucher

    @staticmethod
    @atomic()
    async def apply_voucher_to_order(
            order_id: uuid.UUID,
            user_voucher_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> OrderVoucher:
        """Apply a voucher to an order."""
        # Verify user voucher belongs to user and is unused
        user_voucher = await UserVoucher.get_or_none(
            id=user_voucher_id,
            user_id=user_id,
            is_used=False
        )

        if not user_voucher:
            raise ValueError("Voucher not found or already used")

        # Verify order belongs to user
        order = await Order.get_or_none(id=order_id, user_id=user_id)
        if not order:
            raise ValueError("Order not found or does not belong to user")

        # Get voucher details
        voucher = await user_voucher.voucher

        # Calculate discount
        discount_amount = Decimal(0)
        if voucher.discount_percentage:
            discount_amount = order.subtotal * (voucher.discount_percentage / 100)
        else:
            discount_amount = voucher.value

        # Cap discount at subtotal
        discount_amount = min(discount_amount, order.subtotal)

        # Create order voucher
        order_voucher = await OrderVoucher.create(
            order_id=order_id,
            voucher_id=voucher.id,
            user_voucher_id=user_voucher_id,
            discount_amount=discount_amount
        )

        # Mark user voucher as used
        user_voucher.is_used = True
        user_voucher.order_id = order_id
        await user_voucher.save()

        # Update order total
        order.discount_amount += discount_amount
        order.total_amount = order.subtotal + order.order_fee - order.discount_amount
        await order.save()

        # Prefetch relations
        await order_voucher.fetch_related('voucher', 'user_voucher')

        return order_voucher

    @staticmethod
    async def create_voucher(data: Dict[str, Any]) -> Voucher:
        """Create a new voucher."""
        voucher = await Voucher.create(**data)
        return voucher