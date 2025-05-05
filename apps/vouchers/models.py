import uuid

from tortoise import fields
from tortoise.models import Model


class Voucher(Model):
    """Vouchers that can be redeemed with points."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    code = fields.CharField(max_length=20, unique=True)
    description = fields.CharField(max_length=255)
    points_cost = fields.IntField()
    value = fields.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    expiry_date = fields.DateField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "vouchers"


class UserVoucher(Model):
    """Vouchers acquired by users."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField('models.User', related_name='vouchers')
    voucher = fields.ForeignKeyField('models.Voucher', related_name='user_vouchers')
    is_used = fields.BooleanField(default=False)
    order = fields.ForeignKeyField('models.Order', related_name='redeemed_vouchers', null=True)
    date_acquired = fields.DatetimeField(auto_now_add=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_vouchers"


class OrderVoucher(Model):
    """Vouchers applied to orders."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    order = fields.ForeignKeyField('models.Order', related_name='applied_vouchers')
    voucher = fields.ForeignKeyField('models.Voucher', related_name='order_applications')
    user_voucher = fields.ForeignKeyField('models.UserVoucher', related_name='order_application', null=True)
    discount_amount = fields.DecimalField(max_digits=10, decimal_places=2)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "order_vouchers"