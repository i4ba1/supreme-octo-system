from rest_framework import serializers
from core.serializers import TortoiseSerializer


class TableSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    restaurant_id = serializers.UUIDField()
    table_number = serializers.CharField(max_length=10)
    capacity = serializers.IntegerField(required=False, allow_null=True)
    is_occupied = serializers.BooleanField(default=False)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance)
        return pydantic_model.dict()


class RestaurantSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_null=True)
    image_url = serializers.CharField(max_length=255, required=False, allow_null=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=1, required=False, allow_null=True)
    location = serializers.CharField(max_length=255, required=False, allow_null=True)
    tables = TableSerializer(many=True, read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance, exclude={'tables'})
        data = pydantic_model.dict()

        # Add tables
        if hasattr(instance, 'tables'):
            tables = await instance.tables.all()
            data['tables'] = await TableSerializer.get_pydantic_models(tables)

        return data