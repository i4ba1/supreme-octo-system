from rest_framework import serializers
from core.serializers import TortoiseSerializer


class TestimonialSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    restaurant_id = serializers.UUIDField()
    order_id = serializers.UUIDField(required=False, allow_null=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comments = serializers.CharField(required=False, allow_null=True)
    feedback_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    date = serializers.DateTimeField(read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance)
        data = pydantic_model.dict()

        # Include user info
        if hasattr(instance, 'user'):
            user = await instance.user
            data['user'] = {
                'id': str(user.id),
                'username': user.username
            }

        # Include restaurant info
        if hasattr(instance, 'restaurant'):
            restaurant = await instance.restaurant
            data['restaurant'] = {
                'id': str(restaurant.id),
                'name': restaurant.name
            }

        return data

    async def to_representation_list(self, instances):
        """Convert multiple instances to representation."""
        return [await self.to_representation(instance) for instance in instances]