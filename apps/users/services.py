import uuid
import redis
from typing import Optional, Dict, Any

from passlib.hash import bcrypt
from tortoise.transactions import atomic

from apps.users.models import User


class UserService:

    @staticmethod
    async def check_phone_exists(phone_number: str) -> bool:
        """
        Check if a phone number already exists, using Redis cache first.

        Args:
            phone_number: The phone number to check

        Returns:
            True if the phone number exists, False otherwise
        """
        # Get Redis connection
        redis = await UserService.get_redis()

        # Try to get from cache first
        cache_key = f"phone:{phone_number}"
        exists_in_cache = await redis.get(cache_key)

        if exists_in_cache is not None:
            # Return cached result (convert bytes to bool)
            return exists_in_cache == b'1'

        # Not in cache, check database
        user_exists = await User.filter(phone_number=phone_number).exists()

        # Cache the result with expiration of 1 hour (3600 seconds)
        await redis.set(cache_key, '1' if user_exists else '0', expire=3600)

        return user_exists

    @staticmethod
    async def invalidate_phone_cache(phone_number: str) -> None:
        """
        Invalidate phone number cache when a user is created or phone is updated.

        Args:
            phone_number: Phone number to invalidate in cache
        """
        redis = await UserService.get_redis()
        await redis.delete(f"phone:{phone_number}")

    @staticmethod
    async def get_by_id(user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        return await User.get_or_none(id=user_id)

    @staticmethod
    async def get_by_username(username: str) -> Optional[User]:
        """Get user by username."""
        return await User.get_or_none(username=username)

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        return await User.get_or_none(email=email)

    @staticmethod
    async def get_by_phone(phone_number: str) -> Optional[User]:
        """Get user by phone number."""
        return await User.get_or_none(phone_number=phone_number)

    @staticmethod
    async def authenticate(username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password."""
        # Try to find by username or email
        user = await User.get_or_none(username=username)
        if not user:
            user = await User.get_or_none(email=username)

        if not user:
            return None

        # Verify password
        if bcrypt.verify(password, user.password):
            return user

        return None

    @staticmethod
    @atomic()
    async def create_user(data: Dict[str, Any]) -> User:
        """Create a new user."""
        # Hash password
        if 'password' in data:
            data['password'] = bcrypt.hash(data['password'])

        # Create user
        user = await User.create(**data)
        return user

    @staticmethod
    async def update_user(user_id: uuid.UUID, data: Dict[str, Any]) -> Optional[User]:
        """Update user information."""
        user = await User.get_or_none(id=user_id)
        if not user:
            return None

        # Hash password if provided
        if 'password' in data:
            data['password'] = bcrypt.hash(data['password'])

        # Update fields
        for field, value in data.items():
            setattr(user, field, value)

        await user.save()
        return user

    @staticmethod
    async def add_points(user_id: uuid.UUID, points: int) -> Optional[User]:
        """Add points to user account."""
        user = await User.get_or_none(id=user_id)
        if not user:
            return None

        user.total_points += points
        await user.save()
        return user

    @staticmethod
    async def deduct_points(user_id: uuid.UUID, points: int) -> Optional[User]:
        """Deduct points from user account."""
        user = await User.get_or_none(id=user_id)
        if not user or user.total_points < points:
            return None

        user.total_points -= points
        await user.save()
        return user