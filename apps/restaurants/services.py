import uuid
from typing import List, Optional, Dict, Any

from tortoise.functions import Avg

from apps.restaurants.models import Restaurant, Table
from apps.reviews.models import Testimonial


class RestaurantService:
    @staticmethod
    async def get_all() -> List[Restaurant]:
        """Get all restaurants."""
        return await Restaurant.all().prefetch_related('tables')

    @staticmethod
    async def get_by_id(restaurant_id: uuid.UUID) -> Optional[Restaurant]:
        """Get restaurant by ID."""
        return await Restaurant.get_or_none(id=restaurant_id).prefetch_related('tables')

    @staticmethod
    async def create_restaurant(data: Dict[str, Any]) -> Restaurant:
        """Create a new restaurant."""
        return await Restaurant.create(**data)

    @staticmethod
    async def update_restaurant(restaurant_id: uuid.UUID, data: Dict[str, Any]) -> Optional[Restaurant]:
        """Update restaurant information."""
        restaurant = await Restaurant.get_or_none(id=restaurant_id)
        if not restaurant:
            return None

        for field, value in data.items():
            setattr(restaurant, field, value)

        await restaurant.save()
        return restaurant

    @staticmethod
    async def get_average_rating(restaurant_id: uuid.UUID) -> float:
        """Get average rating for a restaurant."""
        # Using values_list to get just the average value directly
        result = await Testimonial.filter(restaurant_id=restaurant_id).annotate(
            avg_rating=Avg('rating')
        ).values_list('avg_rating', flat=True)

        if result and result[0] is not None:
            return float(result[0])
        return 0.0

    @staticmethod
    async def get_available_tables(restaurant_id: uuid.UUID) -> List[Table]:
        """Get available tables for a restaurant."""
        return await Table.filter(restaurant_id=restaurant_id, is_occupied=False)