import uuid

from tortoise import fields
from tortoise.models import Model

from enum import Enum

class AuthProvider(str, Enum):
    PHONE = "phone"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"


class User(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True, null=True)
    password = fields.CharField(max_length=128)
    phone_number = fields.CharField(max_length=20, unique=True)
    profile_image = fields.CharField(max_length=255, null=True)
    total_points = fields.IntField(default=0)
    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"


class Authentication(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField('models.User', related_name='authentications')
    auth_provider = fields.CharField(max_length=20)
    auth_token = fields.CharField(max_length=255, null=True)
    last_login = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "authentication"
        unique_together = [("user_id", "auth_provider")]


class OTPVerification(Model):
    """Model for storing OTP verification requests"""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    phone_number = fields.CharField(max_length=20, index=True)
    otp_code = fields.CharField(max_length=6)
    is_verified = fields.BooleanField(default=False)
    verification_attempts = fields.IntField(default=0)
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "otp_verifications"
