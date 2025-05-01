import uuid

from tortoise import fields
from tortoise.models import Model

from apps.payments.types import PaymentWithRelations


class PaymentMethod(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField('models.User', related_name='payment_methods')
    type = fields.CharField(max_length=20)
    card_number_last4 = fields.CharField(max_length=4, null=True)
    card_brand = fields.CharField(max_length=20, null=True)
    holder_name = fields.CharField(max_length=100, null=True)
    is_default = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "payment_methods"


class Payment(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    order = fields.ForeignKeyField('models.Order', related_name='payments')
    payment_method = fields.ForeignKeyField('models.PaymentMethod', related_name='transactions', null=True)
    payment_type = fields.CharField(max_length=20)
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    status = fields.CharField(max_length=20, default='pending')
    transaction_id = fields.CharField(max_length=100, null=True)
    reference_number = fields.CharField(max_length=100, null=True)
    payment_deadline = fields.DatetimeField(null=True)
    payment_date = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def with_relations(self) -> 'PaymentWithRelations':
        """Helper method for type checkers to recognize related attributes."""
        return self

    class Meta:
        table = "payments"


class QRCode(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    payment = fields.OneToOneField('Payment', related_name='qr_code')
    qr_data = fields.TextField()
    qr_image_url = fields.CharField(max_length=255, null=True)
    is_downloaded = fields.BooleanField(default=False)
    is_shared = fields.BooleanField(default=False)
    expiry_time = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "qr_codes"


class PaymentVerification(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    payment = fields.OneToOneField('Payment', related_name='verification')
    verification_type = fields.CharField(max_length=20)
    verification_status = fields.CharField(max_length=20, default='pending')
    verification_message = fields.TextField(null=True)
    cashier_name = fields.CharField(max_length=100, null=True)
    table = fields.ForeignKeyField('models.Table', related_name='payment_verifications', null=True)
    verified_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "payment_verifications"