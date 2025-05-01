from rest_framework import serializers

from apps.menu.models import MenuItem, MenuItemOption, MenuItemTopping


class MenuItemToppingSerializer(serializers.Serializer):
    """Serializer for menu item toppings."""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class MenuItemOptionSerializer(serializers.Serializer):
    """Serializer for menu item options."""
    id = serializers.UUIDField(read_only=True)
    option_group = serializers.CharField(max_length=50, allow_null=True)
    name = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_required = serializers.BooleanField(default=False)
    max_selections = serializers.IntegerField(default=1)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class MenuItemSerializer(serializers.Serializer):
    """Serializer for menu items with related options and toppings."""
    id = serializers.UUIDField(read_only=True)
    restaurant_id = serializers.UUIDField()
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(allow_null=True)
    image_url = serializers.CharField(max_length=255, allow_null=True)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    points_required = serializers.IntegerField(allow_null=True)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # Nested serializers for related models
    options = MenuItemOptionSerializer(many=True, read_only=True)
    toppings = MenuItemToppingSerializer(many=True, read_only=True)

    async def create(self, validated_data):
        """Create a new menu item with options and toppings."""
        options_data = self.initial_data.get('options', [])
        toppings_data = self.initial_data.get('toppings', [])

        # Create menu item
        menu_item = await MenuItem.create(**validated_data)

        # Create options
        for option_data in options_data:
            await MenuItemOption.create(item_id=menu_item.id, **option_data)

        # Create toppings
        for topping_data in toppings_data:
            await MenuItemTopping.create(item_id=menu_item.id, **topping_data)

        return menu_item

    async def update(self, instance, validated_data):
        """Update an existing menu item with options and toppings."""
        # Update menu item fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        await instance.save()

        # Handle options if provided
        if 'options' in self.initial_data:
            # Delete existing options
            await MenuItemOption.filter(item_id=instance.id).delete()
            # Create new options
            for option_data in self.initial_data['options']:
                await MenuItemOption.create(item_id=instance.id, **option_data)

        # Handle toppings if provided
        if 'toppings' in self.initial_data:
            # Delete existing toppings
            await MenuItemTopping.filter(item_id=instance.id).delete()
            # Create new toppings
            for topping_data in self.initial_data['toppings']:
                await MenuItemTopping.create(item_id=instance.id, **topping_data)

        return instance


class MenuItemCreateUpdateSerializer(MenuItemSerializer):
    """Extended serializer for creating and updating menu items."""
    # Allow nested writes for options and toppings
    options = MenuItemOptionSerializer(many=True, required=False)
    toppings = MenuItemToppingSerializer(many=True, required=False)