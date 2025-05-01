from rest_framework import serializers
from tortoise.contrib.pydantic import pydantic_model_creator


class TortoiseSerializer(serializers.Serializer):
    """Base serializer for Tortoise ORM models."""

    @classmethod
    async def get_pydantic_model(cls, instance, **kwargs):
        """Convert a Tortoise instance to a Pydantic model."""
        pydantic_model = pydantic_model_creator(instance.__class__)
        return await pydantic_model.from_tortoise_orm(instance, **kwargs)

    @classmethod
    async def get_pydantic_models(cls, instances, **kwargs):
        """Convert multiple Tortoise instances to Pydantic models."""
        if not instances:
            return []

        pydantic_model = pydantic_model_creator(instances[0].__class__)
        return [await pydantic_model.from_tortoise_orm(instance, **kwargs) for instance in instances]