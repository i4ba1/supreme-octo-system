from typing import TYPE_CHECKING, Any, List, Optional
from tortoise.queryset import QuerySet

if TYPE_CHECKING:
    from apps.menu.models import MenuItemOption, MenuItemTopping


# Enhance the MenuItem class with proper type hints for its relationships
class MenuItemWithRelations:
    """Type hints for MenuItem relationships to help IDE recognition."""

    # Add type hints for the relationship properties
    @property
    def options(self) -> 'QuerySet[MenuItemOption]':
        """Relationship to menu item options."""
        return Any  # This is just for type checking, not actual implementation

    @property
    def toppings(self) -> 'QuerySet[MenuItemTopping]':
        """Relationship to menu item toppings."""
        return Any  # This is just for type checking, not actual implementation