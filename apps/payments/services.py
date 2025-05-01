import base64
import datetime
import io
import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any, cast, Literal

from qrcode.constants import ERROR_CORRECT_L
from qrcode.main import QRCode as QRCodeGenerator
from tortoise.transactions import atomic

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentMethod, QRCode, PaymentVerification


class PaymentService:
    @staticmethod
    async def get_by_id(payment_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[Payment]:
        """Get payment by ID, optionally filtering by user."""
        query = Payment.get_or_none(id=payment_id)
        if user_id:
            query = Payment.get_or_none(id=payment_id, order__user_id=user_id)

        return await query.prefetch_related('qr_code', 'verification')

    @staticmethod
    async def get_user_payments(user_id: uuid.UUID, status: Optional[str] = None) -> List[Payment]:
        """Get all payments for a user, optionally filtering by status."""
        query = Payment.filter(order__user_id=user_id)
        if status:
            query = query.filter(status=status)

        return await query.order_by('-created_at').prefetch_related('qr_code', 'verification')

    @staticmethod
    async def get_user_payment_methods(user_id: uuid.UUID) -> List[PaymentMethod]:
        """Get all payment methods for a user."""
        return await PaymentMethod.filter(user_id=user_id).order_by('-is_default')

    @staticmethod
    @atomic()
    async def create_payment(
            order_id: uuid.UUID,
            payment_type: str,
            amount: Decimal,
            user_id: uuid.UUID,
            payment_method_id: Optional[uuid.UUID] = None,
            table_id: Optional[uuid.UUID] = None
    ) -> Payment:
        """Create a new payment."""
        # Verify order belongs to user
        order = await Order.get_or_none(id=order_id, user_id=user_id)
        if not order:
            raise ValueError("Order not found or does not belong to user")

        # Create payment
        payment = await Payment.create(
            order_id=order_id,
            payment_method_id=payment_method_id,
            payment_type=payment_type,
            amount=amount,
            status="pending",
            payment_deadline=datetime.datetime.now() + datetime.timedelta(minutes=8)
        )

        # Handle payment type specific logic
        if payment_type == "qris":
            # Generate QR code
            await PaymentService.generate_qr_code(payment.id)

            # Create verification record
            await PaymentVerification.create(
                payment_id=payment.id,
                verification_type="qris",
                verification_status="pending"
            )

        elif payment_type in ["debit_card", "credit_card"]:
            # Create verification record
            await PaymentVerification.create(
                payment_id=payment.id,
                verification_type="card",
                verification_status="pending"
            )

        elif payment_type == "cash":
            # Create verification record
            await PaymentVerification.create(
                payment_id=payment.id,
                verification_type="cash",
                verification_status="pending",
                table_id=table_id
            )

        # Return full payment with related objects
        return await PaymentService.get_by_id(payment.id)

    @staticmethod
    async def generate_qr_code(payment_id: uuid.UUID) -> QRCode:
        """Generate QR code for QRIS payment."""
        payment = await Payment.get(id=payment_id)

        # Generate QR code data
        qr_data = f"https://eatsight.com/pay/{payment_id}"

        # Generate QR code image
        qr = QRCodeGenerator(
            version=1,
            error_correction=cast(Literal[0, 1, 2, 3], ERROR_CORRECT_L),
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Save image to buffer
        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)

        # Convert to base64
        base64.b64encode(buffer.getvalue()).decode()

        # Save path
        qr_image_path = f"/media/qrcodes/{payment_id}.png"

        # Create QR code record
        qr_code = await QRCode.create(
            payment_id=payment_id,
            qr_data=qr_data,
            qr_image_url=qr_image_path,
            expiry_time=payment.payment_deadline,
            is_downloaded=False,
            is_shared=False
        )

        return qr_code

    @staticmethod
    async def check_payment_status(payment_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        """Check status of a payment."""
        payment = await PaymentService.get_by_id(payment_id, user_id)
        if not payment:
            return {
                "status": "error",
                "message": "Payment not found"
            }

        # Use the helper method for type hinting
        payment_with_relations = payment.with_relations()
        verification = await payment_with_relations.verification

        return {
            "status": payment.status,
            "verification_status": verification.verification_status if verification else None,
            "message": verification.verification_message if verification else None,
            "timestamp": datetime.datetime.now().isoformat()
        }

    @staticmethod
    async def verify_payment(
            payment_id: uuid.UUID,
            status: str,
            message: Optional[str] = None
    ) -> tuple[bool, None] | tuple[bool, Payment]:
        """Verify a payment (update status)."""
        payment = await Payment.get_or_none(id=payment_id)
        if not payment:
            return False, None

        # Only verify pending payments
        if payment.status != "pending":
            return False, payment

        # Update payment status
        if status == "completed":
            payment.status = "completed"
            payment.payment_date = datetime.datetime.now()

            # Generate transaction ID
            payment.transaction_id = f"{payment.payment_type.upper()}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Mark order as completed
            order = await payment.order
            order.status = "completed"
            await order.save()

        elif status == "failed":
            payment.status = "failed"

        await payment.save()

        # Update verification record
        # Use the helper method for type hinting
        payment_with_relations = payment.with_relations()
        verification = await payment_with_relations.verification

        if verification:
            verification.verification_status = "verified" if status == "completed" else "rejected"
            verification.verification_message = message
            verification.verified_at = datetime.datetime.now()
            await verification.save()

        return True, payment

    @staticmethod
    async def download_qr(payment_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Dict[str, str]]:
        """Mark QR code as downloaded and return its data."""
        payment = await PaymentService.get_by_id(payment_id, user_id)
        if not payment or payment.payment_type != "qris":
            return None

        # Use the helper method for type hinting
        payment_with_relations = payment.with_relations()
        qr_code = await payment_with_relations.qr_code

        if not qr_code:
            return None

        # Mark as downloaded
        qr_code.is_downloaded = True
        await qr_code.save()

        return {
            "qr_data": qr_code.qr_data,
            "qr_image_url": qr_code.qr_image_url
        }

    @staticmethod
    async def share_qr(payment_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Mark QR code as shared."""
        payment = await PaymentService.get_by_id(payment_id, user_id)
        if not payment or payment.payment_type != "qris":
            return False

        # Use the helper method for type hinting
        payment_with_relations = payment.with_relations()
        qr_code = await payment_with_relations.qr_code

        if not qr_code:
            return False

        # Mark as shared
        qr_code.is_shared = True
        await qr_code.save()

        return True