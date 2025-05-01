from tortoise import fields
from tortoise.models import Model
import uuid


class Testimonial(Model):
    """Restaurant reviews and ratings."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField('models.User', related_name='testimonials')
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='testimonials')
    order = fields.ForeignKeyField('models.Order', related_name='testimonial', null=True)
    rating = fields.IntField()  # 1-5 stars
    comments = fields.TextField(null=True)
    feedback_categories = fields.JSONField(default=list)  # Store categories as a JSON array
    date = fields.DatetimeField(auto_now_add=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "testimonials"