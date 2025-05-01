import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any

from tortoise.transactions import atomic

from apps.orders.models import Order, OrderItem, OrderItemOption, OrderItemTopping
from apps.vouchers.models import Voucher, UserVoucher, OrderVoucher


class OrderService:
    @staticmethod
    async def get_by_id(order_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[Order]:
        """Get order by ID, optionally filtering by user."""
        query = Order.get_or_none(id=order_id)
        if user_id:
            query = Order.get_or_none(id=order_id, user_id=user_id)

        return await query.prefetch_related(
            'items__options__option',
            'items__toppings__topping',
            'items__item'
        )

    @staticmethod
    async def get_user_orders(user_id: uuid.UUID, status: Optional[str] = None) -> List[Order]:
        """Get all orders for a user, optionally filtering by status."""
        query = Order.filter(user_id=user_id)
        if status:
            query = query.filter(status=status)

        return await query.order_by('-created_at').prefetch_related(
            'restaurant',
            'items__item'
        )

    @staticmethod
    @atomic()
    async def create_order(
            user_id: uuid.UUID,
            restaurant_id: uuid.UUID,
            order_mode: str,
            subtotal: Decimal,
            order_fee: Decimal,
            discount_amount: Decimal,
            total_amount: Decimal,
            table_id: Optional[uuid.UUID] = None,
            payment_method_id: Optional[uuid.UUID] = None,
            items_data: Optional[List[Dict[str, Any]]] = None,
            voucher_ids: Optional[List[uuid.UUID]] = None
    ) -> Order:
        """Create a new order with items, options, and toppings."""
        # Create order
        order = await Order.create(
            user_id=user_id,
            restaurant_id=restaurant_id,
            status="in_progress",
            order_mode=order_mode,
            table_id=table_id,
            subtotal=subtotal,
            order_fee=order_fee,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_method_id=payment_method_id
        )

        # Add items
        if items_data:
            for item_data in items_data:
                # Create order item
                order_item = await OrderItem.create(
                    order_id=order.id,
                    item_id=item_data['item_id'],
                    quantity=item_data.get('quantity', 1),
                    price=item_data['price'],
                    special_instructions=item_data.get('special_instructions')
                )

                # Add options
                if 'options' in item_data:
                    for option_data in item_data['options']:
                        await OrderItemOption.create(
                            order_item_id=order_item.id,
                            option_id=option_data['option_id'],
                            quantity=option_data.get('quantity', 1),
                            price=option_data.get('price', 0)
                        )

                # Add toppings
                if 'toppings' in item_data:
                    for topping_data in item_data['toppings']:
                        await OrderItemTopping.create(
                            order_item_id=order_item.id,
                            topping_id=topping_data['topping_id'],
                            quantity=topping_data.get('quantity', 1),
                            price=topping_data.get('price', 0)
                        )

        # Apply vouchers
        if voucher_ids:
            for voucher_id in voucher_ids:
                user_voucher = await UserVoucher.get_or_none(
                    user_id=user_id,
                    voucher_id=voucher_id,
                    is_used=False
                )

                if user_voucher:
                    # Mark voucher as used
                    user_voucher.is_used = True
                    user_voucher.order_id = order.id
                    await user_voucher.save()

                    # Create order voucher
                    voucher = await Voucher.get(id=voucher_id)

                    # Calculate discount amount
                    Decimal(0)
                    if voucher.discount_percentage:
                        discount = subtotal * (voucher.discount_percentage / 100)
                    else:
                        discount = voucher.value

                    await OrderVoucher.create(
                        order_id=order.id,
                        voucher_id=voucher_id,
                        user_voucher_id=user_voucher.id,
                        discount_amount=discount
                    )

        # Return the full order
        return await OrderService.get_by_id(order.id)

    @staticmethod
    async def cancel_order(order_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Cancel an order if it's in progress and belongs to the user."""
        order = await Order.get_or_none(id=order_id, user_id=user_id)

        if not order or order.status != "in_progress":
            return False

        order.status = "cancelled"
        await order.save()
        return True

    @staticmethod
    async def complete_order(order_id: uuid.UUID) -> bool:
        """Mark an order as completed."""
        order = await Order.get_or_none(id=order_id)

        if not order or order.status != "in_progress":
            return False

        order.status = "completed"
        await order.save()
        return True