import uuid

from tortoise import fields
from tortoise.models import Model


class Order(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField('models.User', related_name='orders')
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='orders')
    status = fields.CharField(max_length=20, default='in_progress')
    order_mode = fields.CharField(max_length=20, default='dine_in')
    table = fields.ForeignKeyField('models.Table', related_name='orders', null=True)
    subtotal = fields.DecimalField(max_digits=10, decimal_places=2)
    order_fee = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = fields.DecimalField(max_digits=10, decimal_places=2)
    payment_method = fields.ForeignKeyField('models.PaymentMethod', null=True)
    is_reviewed = fields.BooleanField(default=False)
    order_date = fields.DatetimeField(auto_now_add=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "orders"


class OrderItem(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    order = fields.ForeignKeyField('models.Order', related_name='items')
    item = fields.ForeignKeyField('models.MenuItem', related_name='order_items')
    quantity = fields.IntField(default=1)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "order_items"


class OrderItemOption(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    order_item = fields.ForeignKeyField('models.OrderItem', related_name='options')
    option = fields.ForeignKeyField('models.MenuItemOption', related_name='order_item_options')
    quantity = fields.IntField(default=1)
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "order_item_options"


class OrderItemTopping(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    order_item = fields.ForeignKeyField('models.OrderItem', related_name='toppings')
    topping = fields.ForeignKeyField('models.MenuItemTopping', related_name='order_item_toppings')
    quantity = fields.IntField(default=1)
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "order_item_toppings"