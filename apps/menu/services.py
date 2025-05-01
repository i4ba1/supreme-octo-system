import uuid
from typing import List, Optional, Dict, Any

from apps.menu.models import MenuItem, MenuItemOption, MenuItemTopping


class MenuService:
    @staticmethod
    async def get_all_menu_items(is_active: bool = True) -> List[MenuItem]:
        """
        Retrieve all menu items, optionally filtered by active status.

        Args:
            is_active: Filter only active menu items if True

        Returns:
            List of menu items with their options and toppings
        """
        query = MenuItem.filter(is_active=is_active)
        return await query.prefetch_related('options', 'toppings')

    @staticmethod
    async def get_restaurant_menu_items(restaurant_id: str, is_active: bool = True) -> List[MenuItem]:
        """
        Retrieve menu items for a specific restaurant, optionally filtered by active status.

        Args:
            restaurant_id: UUID of the restaurant
            is_active: Filter only active menu items if True

        Returns:
            List of menu items with their options and toppings
        """
        try:
            restaurant_uuid = uuid.UUID(restaurant_id)
            query = MenuItem.filter(restaurant_id=restaurant_uuid, is_active=is_active)
            return await query.prefetch_related('options', 'toppings')
        except ValueError:
            # Handle invalid UUID
            return []

    @staticmethod
    async def get_menu_item_by_id(item_id: str) -> Optional[MenuItem]:
        """
        Retrieve a specific menu item by ID.

        Args:
            item_id: UUID of the menu item

        Returns:
            Menu item with its options and toppings, or None if not found
        """
        try:
            item_uuid = uuid.UUID(item_id)
            return await MenuItem.get_or_none(id=item_uuid).prefetch_related('options', 'toppings')
        except ValueError:
            # Handle invalid UUID
            return None

    @staticmethod
    async def create_menu_item(restaurant_id: uuid.UUID, menu_item_data: Dict[str, Any]) -> MenuItem:
        """
        Create a new menu item.

        Args:
            restaurant_id: UUID of the restaurant
            menu_item_data: Dictionary containing menu item data

        Returns:
            Created menu item instance
        """
        # Extract options and toppings data if provided
        options_data = menu_item_data.pop('options', [])
        toppings_data = menu_item_data.pop('toppings', [])

        # Create menu item
        menu_item = await MenuItem.create(restaurant_id=restaurant_id, **menu_item_data)

        # Create options if provided
        for option_data in options_data:
            await MenuItemOption.create(item_id=menu_item.id, **option_data)

        # Create toppings if provided
        for topping_data in toppings_data:
            await MenuItemTopping.create(item_id=menu_item.id, **topping_data)

        # Return the menu item with related objects
        return await MenuService.get_menu_item_by_id(str(menu_item.id))

    @staticmethod
    async def update_menu_item(item_id: uuid.UUID, menu_item_data: Dict[str, Any]) -> Optional[MenuItem]:
        """
        Update an existing menu item.

        Args:
            item_id: UUID of the menu item to update
            menu_item_data: Dictionary containing updated menu item data

        Returns:
            Updated menu item instance, or None if not found
        """
        # Get the menu item
        menu_item = await MenuItem.get_or_none(id=item_id)
        if not menu_item:
            return None

        # Extract options and toppings data if provided
        options_data = menu_item_data.pop('options', None)
        toppings_data = menu_item_data.pop('toppings', None)

        # Update menu item fields
        for key, value in menu_item_data.items():
            setattr(menu_item, key, value)
        await menu_item.save()

        # Update options if provided
        if options_data is not None:
            # Delete existing options
            await MenuItemOption.filter(item_id=item_id).delete()
            # Create new options
            for option_data in options_data:
                await MenuItemOption.create(item_id=item_id, **option_data)

        # Update toppings if provided
        if toppings_data is not None:
            # Delete existing toppings
            await MenuItemTopping.filter(item_id=item_id).delete()
            # Create new toppings
            for topping_data in toppings_data:
                await MenuItemTopping.create(item_id=item_id, **topping_data)

        # Return the updated menu item with related objects
        return await MenuService.get_menu_item_by_id(str(item_id))

    @staticmethod
    async def delete_menu_item(item_id: uuid.UUID) -> bool:
        """
        Delete a menu item.

        Args:
            item_id: UUID of the menu item to delete

        Returns:
            True if item was deleted, False otherwise
        """
        # Get the menu item
        menu_item = await MenuItem.get_or_none(id=item_id)
        if not menu_item:
            return False

        # Delete options and toppings first (cascade delete might be configured but just to be safe)
        await MenuItemOption.filter(item_id=item_id).delete()
        await MenuItemTopping.filter(item_id=item_id).delete()

        # Delete the menu item
        await menu_item.delete()
        return True