import uuid
from typing import Optional, Dict, Any

from passlib.hash import bcrypt
from tortoise.transactions import atomic

from apps.users.models import User


class UserService:
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