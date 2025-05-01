from rest_framework import serializers
from core.serializers import TortoiseSerializer


class PaymentMethodSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    type = serializers.CharField(max_length=20)
    card_number_last4 = serializers.CharField(max_length=4, required=False, allow_null=True)
    card_brand = serializers.CharField(max_length=20, required=False, allow_null=True)
    holder_name = serializers.CharField(max_length=100, required=False, allow_null=True)
    is_default = serializers.BooleanField(default=False)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance)
        return pydantic_model.dict()

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]


class QRCodeSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    payment_id = serializers.UUIDField(read_only=True)
    qr_data = serializers.CharField(read_only=True)
    qr_image_url = serializers.CharField(max_length=255, read_only=True)
    is_downloaded = serializers.BooleanField(read_only=True)
    is_shared = serializers.BooleanField(read_only=True)
    expiry_time = serializers.DateTimeField(read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance)
        return pydantic_model.dict()

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]


class PaymentVerificationSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    payment_id = serializers.UUIDField(read_only=True)
    verification_type = serializers.CharField(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    verification_message = serializers.CharField(read_only=True, allow_null=True)
    cashier_name = serializers.CharField(max_length=100, required=False, allow_null=True)
    table_id = serializers.UUIDField(required=False, allow_null=True)
    verified_at = serializers.DateTimeField(read_only=True, allow_null=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance, exclude={'table'})
        data = pydantic_model.dict()

        # Include table number if available
        if hasattr(instance, 'table') and instance.table_id:
            table = await instance.table
            data['table_number'] = table.table_number

        return data

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]


class PaymentSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField()
    payment_method_id = serializers.UUIDField(required=False, allow_null=True)
    payment_type = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField(read_only=True)
    transaction_id = serializers.CharField(max_length=100, read_only=True, allow_null=True)
    reference_number = serializers.CharField(max_length=100, read_only=True, allow_null=True)
    payment_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    payment_date = serializers.DateTimeField(read_only=True, allow_null=True)
    qr_code = QRCodeSerializer(read_only=True)
    verification = PaymentVerificationSerializer(read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(
            instance,
            exclude={'qr_code', 'verification', 'payment_method', 'order'}
        )
        data = pydantic_model.dict()

        # Include QR code if QRIS payment
        if instance.payment_type == 'qris' and hasattr(instance, 'qr_code'):
            qr_code = await instance.qr_code
            if qr_code:
                data['qr_code'] = await QRCodeSerializer().to_representation(qr_code)

        # Include verification details
        if hasattr(instance, 'verification'):
            verification = await instance.verification
            if verification:
                data['verification'] = await PaymentVerificationSerializer().to_representation(verification)

        # Include order summary
        if hasattr(instance, 'order'):
            order = await instance.order
            data['order_summary'] = {
                'order_id': str(order.id),
                'status': order.status,
                'total_amount': str(order.total_amount)
            }

        # Include payment method details
        if hasattr(instance, 'payment_method') and instance.payment_method_id:
            payment_method = await instance.payment_method
            data['payment_method_details'] = {
                'type': payment_method.type,
                'card_brand': payment_method.card_brand,
                'card_number_last4': payment_method.card_number_last4
            }

        # Calculate time remaining if pending
        if instance.status == 'pending' and instance.payment_deadline:
            import datetime
            now = datetime.datetime.now(instance.payment_deadline.tzinfo)
            if now < instance.payment_deadline:
                time_remaining = instance.payment_deadline - now
                data['time_remaining_seconds'] = time_remaining.total_seconds()
                data[
                    'time_remaining_formatted'] = f"{int(time_remaining.total_seconds() // 60):02d}:{int(time_remaining.total_seconds() % 60):02d}"
            else:
                data['time_remaining_seconds'] = 0
                data['time_remaining_formatted'] = "00:00"

        return data

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]