import uuid
from typing import List, Optional, Dict, Any

from apps.orders.models import Order
from apps.restaurants.models import Restaurant
from apps.reviews.models import Testimonial
from apps.users.models import User


class TestimonialService:
    @staticmethod
    async def get_by_id(testimonial_id: uuid.UUID) -> Optional[Testimonial]:
        """Get testimonial by ID."""
        return await Testimonial.get_or_none(id=testimonial_id).prefetch_related('user', 'restaurant')

    @staticmethod
    async def get_by_restaurant(restaurant_id: uuid.UUID, limit: int = 10) -> List[Testimonial]:
        """Get testimonials for a restaurant."""
        return await Testimonial.filter(
            restaurant_id=restaurant_id
        ).order_by('-date').limit(limit).prefetch_related('user')

    @staticmethod
    async def get_by_user(user_id: uuid.UUID, limit: int = 10) -> List[Testimonial]:
        """Get testimonials written by a user."""
        return await Testimonial.filter(
            user_id=user_id,
            limit=limit
        ).order_by('-date').prefetch_related('restaurant')

    @staticmethod
    async def create_testimonial(
            user_id: uuid.UUID,
            restaurant_id: uuid.UUID,
            rating: int,
            comments: Optional[str] = None,
            feedback_categories: Optional[List[str]] = None,
            order_id: Optional[uuid.UUID] = None
    ) -> Testimonial:
        """Create a new testimonial."""
        # Validate rating
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # Verify restaurant exists
        restaurant = await Restaurant.get_or_none(id=restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")

        # Verify order if provided
        if order_id:
            order = await Order.get_or_none(id=order_id, user_id=user_id)
            if not order:
                raise ValueError("Order not found or does not belong to user")

            # Mark order as reviewed
            order.is_reviewed = True
            await order.save()

        # Create testimonial
        testimonial = await Testimonial.create(
            user_id=user_id,
            restaurant_id=restaurant_id,
            order_id=order_id,
            rating=rating,
            comments=comments,
            feedback_categories=feedback_categories or []
        )

        # Award points to user (500 points per review)
        user = await User.get(id=user_id)
        user.total_points += 500
        await user.save()

        return testimonial

    @staticmethod
    async def update_testimonial(
            testimonial_id: uuid.UUID,
            user_id: uuid.UUID,
            data: Dict[str, Any]
    ) -> Optional[Testimonial]:
        """Update an existing testimonial."""
        testimonial = await Testimonial.get_or_none(id=testimonial_id, user_id=user_id)
        if not testimonial:
            return None

        # Update fields
        if 'rating' in data:
            testimonial.rating = data['rating']
        if 'comments' in data:
            testimonial.comments = data['comments']
        if 'feedback_categories' in data:
            testimonial.feedback_categories = data['feedback_categories']

        await testimonial.save()
        return testimonial

    @staticmethod
    async def delete_testimonial(testimonial_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a testimonial."""
        testimonial = await Testimonial.get_or_none(id=testimonial_id, user_id=user_id)
        if not testimonial:
            return False

        await testimonial.delete()
        return True