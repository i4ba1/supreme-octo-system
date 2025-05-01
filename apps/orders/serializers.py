from rest_framework import serializers
from core.serializers import TortoiseSerializer
from apps.menu.serializers import MenuItemSerializer


class OrderItemToppingSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    order_item_id = serializers.UUIDField()
    topping_id = serializers.UUIDField()
    topping_name = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(default=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance, exclude={'topping'})
        data = pydantic_model.dict()

        # Include topping name
        if hasattr(instance, 'topping'):
            topping = await instance.topping
            data['topping_name'] = topping.name

        return data

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]


class OrderItemOptionSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    order_item_id = serializers.UUIDField()
    option_id = serializers.UUIDField()
    option_name = serializers.CharField(read_only=True)
    option_group = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(default=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance, exclude={'option'})
        data = pydantic_model.dict()

        # Include option details
        if hasattr(instance, 'option'):
            option = await instance.option
            data['option_name'] = option.name
            data['option_group'] = option.option_group

        return data

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]


class OrderItemSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField()
    item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(default=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = serializers.CharField(required=False, allow_null=True)
    options = OrderItemOptionSerializer(many=True, read_only=True)
    toppings = OrderItemToppingSerializer(many=True, read_only=True)
    item_details = serializers.DictField(read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(
            instance,
            exclude={'options', 'toppings', 'item'}
        )
        data = pydantic_model.dict()

        # Include item details
        if hasattr(instance, 'item'):
            item = await instance.item
            data['item_details'] = {
                'id': str(item.id),
                'name': item.name,
                'image_url': item.image_url
            }

        # Include options
        if hasattr(instance, 'options'):
            options = await instance.options.all().prefetch_related('option')
            data['options'] = await OrderItemOptionSerializer().to_representation_list(options)

        # Include toppings
        if hasattr(instance, 'toppings'):
            toppings = await instance.toppings.all().prefetch_related('topping')
            data['toppings'] = await OrderItemToppingSerializer().to_representation_list(toppings)

        # Calculate total price
        item_total = data['price'] * data['quantity']
        options_total = sum(option['price'] * option['quantity'] for option in data.get('options', []))
        toppings_total = sum(topping['price'] * topping['quantity'] for topping in data.get('toppings', []))

        data['total_price'] = item_total + options_total + toppings_total

        return data

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]


class OrderSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    restaurant_id = serializers.UUIDField()
    restaurant_name = serializers.CharField(read_only=True)
    status = serializers.CharField(default='in_progress')
    order_mode = serializers.CharField(default='dine_in')
    table_id = serializers.UUIDField(required=False, allow_null=True)
    table_number = serializers.CharField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    order_fee = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method_id = serializers.UUIDField(required=False, allow_null=True)
    is_reviewed = serializers.BooleanField(default=False)
    order_date = serializers.DateTimeField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(
            instance,
            exclude={'items', 'restaurant', 'table', 'payment_method'}
        )
        data = pydantic_model.dict()

        # Include restaurant details
        if hasattr(instance, 'restaurant'):
            restaurant = await instance.restaurant
            data['restaurant_name'] = restaurant.name

        # Include table details
        if hasattr(instance, 'table') and instance.table_id:
            table = await instance.table
            data['table_number'] = table.table_number

        # Include items
        if hasattr(instance, 'items'):
            items = await instance.items.all().prefetch_related('item', 'options', 'toppings')
            data['items'] = await OrderItemSerializer().to_representation_list(items)

        # Include payments status if any
        if hasattr(instance, 'payments'):
            payments = await instance.payments.all()
            if payments:
                latest_payment = payments[0]  # Assuming the first is the latest
                data['payment_status'] = latest_payment.status

        return data

    async def to_representation_list(self, instances):
        return [await self.to_representation(instance) for instance in instances]