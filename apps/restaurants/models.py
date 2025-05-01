import uuid

from tortoise import fields
from tortoise.models import Model


class Restaurant(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    image_url = fields.CharField(max_length=255, null=True)
    rating = fields.DecimalField(max_digits=3, decimal_places=1, null=True)
    location = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "restaurants"


class Table(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='tables')
    table_number = fields.CharField(max_length=10)
    capacity = fields.IntField(null=True)
    is_occupied = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tables"
        unique_together = [("restaurant_id", "table_number")]