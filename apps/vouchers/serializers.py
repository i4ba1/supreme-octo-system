from rest_framework import serializers
from core.serializers import TortoiseSerializer


class VoucherSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    code = serializers.CharField(max_length=20)
    description = serializers.CharField(max_length=255)
    points_cost = serializers.IntegerField(min_value=0)
    value = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    expiry_date = serializers.DateField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance)
        return pydantic_model.dict()

    async def to_representation_list(self, instances):
        """Convert multiple instances to representation."""
        return [await self.to_representation(instance) for instance in instances]


class UserVoucherSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    voucher_id = serializers.UUIDField(read_only=True)
    voucher = VoucherSerializer(read_only=True)
    is_used = serializers.BooleanField(read_only=True)
    order_id = serializers.UUIDField(read_only=True, allow_null=True)
    date_acquired = serializers.DateTimeField(read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance, exclude={'voucher'})
        data = pydantic_model.dict()

        # Include voucher details
        if hasattr(instance, 'voucher'):
            voucher = await instance.voucher
            data['voucher'] = await VoucherSerializer().to_representation(voucher)

        return data

    async def to_representation_list(self, instances):
        """Convert multiple instances to representation."""
        return [await self.to_representation(instance) for instance in instances]


class OrderVoucherSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField()
    voucher_id = serializers.UUIDField(read_only=True)
    user_voucher_id = serializers.UUIDField()
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(
            instance,
            exclude={'voucher', 'user_voucher'}
        )
        data = pydantic_model.dict()

        # Include voucher details
        if hasattr(instance, 'voucher'):
            voucher = await instance.voucher
            data['voucher'] = await VoucherSerializer().to_representation(voucher)

        return data

    async def to_representation_list(self, instances):
        """Convert multiple instances to representation."""
        return [await self.to_representation(instance) for instance in instances]