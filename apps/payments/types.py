from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from apps.payments.models import Payment, QRCode, PaymentVerification

    # Extend the Payment class with explicit type annotations
    class PaymentWithRelations(Payment):
        verification: Optional['PaymentVerification']
        qr_code: Optional['QRCode']