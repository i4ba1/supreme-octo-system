from rest_framework import serializers
from core.serializers import TortoiseSerializer


class UserSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False)
    phone_number = serializers.CharField(max_length=20)
    profile_image = serializers.CharField(max_length=255, required=False, allow_null=True)
    total_points = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance)
        data = pydantic_model.dict(exclude={'password'})
        return data


class AuthenticationSerializer(TortoiseSerializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField()
    auth_provider = serializers.CharField(max_length=20)
    last_login = serializers.DateTimeField(read_only=True)

    async def to_representation(self, instance):
        pydantic_model = await self.get_pydantic_model(instance)
        return pydantic_model.dict(exclude={'auth_token'})


class PhoneLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)


class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(max_length=6)


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=['google', 'facebook', 'apple'])
    token = serializers.CharField()
    phone_number = serializers.CharField(max_length=20, required=False, allow_null=True)