from typing import TYPE_CHECKING, Any

from tortoise import fields
from tortoise.models import Model
import uuid


if TYPE_CHECKING:
    from tortoise.queryset import QuerySet
    from apps.menu.models import MenuItemOption, MenuItemTopping


class MenuItem(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='menu_items')
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    image_url = fields.CharField(max_length=255, null=True)
    original_price = fields.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    points_required = fields.IntField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Add type hints that will only be used for IDE recognition
    if TYPE_CHECKING:
        # This creates properties that only exist during type checking
        @property
        def options(self) -> 'QuerySet[MenuItemOption]': ...

        @property
        def toppings(self) -> 'QuerySet[MenuItemTopping]': ...

    class Meta:
        table = "menu_items"


class MenuItemOption(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    item = fields.ForeignKeyField('models.MenuItem', related_name='options')
    option_group = fields.CharField(max_length=50, null=True)
    name = fields.CharField(max_length=100)
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_required = fields.BooleanField(default=False)
    max_selections = fields.IntField(default=1)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "menu_item_options"


class MenuItemTopping(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    item = fields.ForeignKeyField('models.MenuItem', related_name='toppings')
    name = fields.CharField(max_length=100)
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "menu_item_toppings"