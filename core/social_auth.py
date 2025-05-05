from datetime import datetime
from typing import Optional, Dict, Any, Tuple, Coroutine

import aiohttp
from tortoise.transactions import atomic

from apps.users.models import User, Authentication, AuthProvider


class SocialAuthService:
    # OAuth configuration - store these in environment variables in production
    GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
    GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
    GOOGLE_REDIRECT_URI = "YOUR_GOOGLE_REDIRECT_URI"

    FACEBOOK_APP_ID = "YOUR_FACEBOOK_APP_ID"
    FACEBOOK_APP_SECRET = "YOUR_FACEBOOK_APP_SECRET"
    FACEBOOK_REDIRECT_URI = "YOUR_FACEBOOK_REDIRECT_URI"

    APPLE_CLIENT_ID = "YOUR_APPLE_CLIENT_ID"
    APPLE_TEAM_ID = "YOUR_APPLE_TEAM_ID"
    APPLE_KEY_ID = "YOUR_APPLE_KEY_ID"
    APPLE_PRIVATE_KEY = "YOUR_APPLE_PRIVATE_KEY"  # Path to private key file
    APPLE_REDIRECT_URI = "YOUR_APPLE_REDIRECT_URI"

    @classmethod
    async def verify_google_token(cls, token: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Verify Google OAuth token and extract user information

        Args:
            token: The ID token from Google

        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            # Verify token with Google
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
                ) as response:
                    if response.status != 200:
                        return False, {}, "Invalid Google token"

                    token_info = await response.json()

                    # Verify the audience matches our client ID
                    if token_info.get("aud") != cls.GOOGLE_CLIENT_ID:
                        return False, {}, "Token not intended for this application"

                    # Extract user information
                    user_data = {
                        "auth_id": token_info.get("sub"),
                        "email": token_info.get("email"),
                        "first_name": token_info.get("given_name"),
                        "last_name": token_info.get("family_name"),
                        "profile_image": token_info.get("picture")
                    }

                    return True, user_data, ""

        except Exception as e:
            # In production, add proper error logging here
            return False, {}, f"Error verifying Google token: {str(e)}"

    @classmethod
    async def verify_facebook_token(cls, token: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Verify Facebook OAuth token and extract user information

        Args:
            token: The access token from Facebook

        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            # First, debug the token to verify it
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"https://graph.facebook.com/debug_token?input_token={token}&access_token={cls.FACEBOOK_APP_ID}|{cls.FACEBOOK_APP_SECRET}"
                ) as response:
                    if response.status != 200:
                        return False, {}, "Invalid Facebook token"

                    debug_data = await response.json()
                    if not debug_data.get("data", {}).get("is_valid", False):
                        return False, {}, "Facebook token validation failed"

                # Get user data
                async with session.get(
                        f"https://graph.facebook.com/me?fields=id,email,first_name,last_name,picture&access_token={token}"
                ) as response:
                    if response.status != 200:
                        return False, {}, "Failed to get Facebook user data"

                    fb_user_data = await response.json()

                    # Extract user information
                    user_data = {
                        "auth_id": fb_user_data.get("id"),
                        "email": fb_user_data.get("email"),
                        "first_name": fb_user_data.get("first_name"),
                        "last_name": fb_user_data.get("last_name"),
                        "profile_image": fb_user_data.get("picture", {}).get("data", {}).get("url")
                    }

                    return True, user_data, ""

        except Exception as e:
            # In production, add proper error logging here
            return False, {}, f"Error verifying Facebook token: {str(e)}"

    @classmethod
    async def verify_apple_token(cls, token: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Verify Apple OAuth token and extract user information

        Args:
            token: The ID token from Apple

        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            # Apple's token is a JWT that needs to be decoded and verified
            # In a real implementation, we would use a JWT library to decode and verify the token
            # This is a simplified placeholder

            # For demonstration, we're assuming the token is valid and extracting data
            # In production, implement proper JWT verification

            # Mock user data extraction from Apple token
            user_data = {
                "auth_id": "apple_user_id_123",  # This would come from the decoded token
                "email": "user@example.com",  # This would come from the decoded token
                "first_name": "Apple",  # This might come from additional Apple user data
                "last_name": "User"  # This might come from additional Apple user data
            }

            return True, user_data, ""

        except Exception as e:
            # In production, add proper error logging here
            return False, {}, f"Error verifying Apple token: {str(e)}"

    @classmethod
    @atomic()
    async def authenticate_social_user(
            cls, provider: AuthProvider, auth_token: str, phone_number: Optional[str] = None
    ) -> tuple[None, bool, str] | tuple[User, bool, str] | tuple[Any, bool, str]:
        """
        Authenticate or create a user with social credentials

        Args:
            provider: The authentication provider (google, facebook, apple)
            auth_token: The OAuth token from the provider
            phone_number: Optional phone number for new user creation

        Returns:
            Tuple of (user, is_new_user, error_message)
        """
        try:
            # Verify token based on provider
            if provider == AuthProvider.GOOGLE:
                success, user_data, error = await cls.verify_google_token(auth_token)
            elif provider == AuthProvider.FACEBOOK:
                success, user_data, error = await cls.verify_facebook_token(auth_token)
            elif provider == AuthProvider.APPLE:
                success, user_data, error = await cls.verify_apple_token(auth_token)
            else:
                return None, False, f"Unsupported provider: {provider}"

            if not success:
                return None, False, error

            # Check if we already have this auth provider registered
            auth_id = user_data.get("auth_id")
            auth_record = await Authentication.get_or_none(
                auth_provider=provider,
                auth_id=auth_id
            )

            if auth_record:
                # User exists, update authentication record
                auth_record.auth_token = auth_token
                auth_record.last_login = datetime.now()
                await auth_record.save()

                # Get and return the user
                user = await auth_record.user
                return user, False, ""

            # No existing auth record, check if email exists
            email = user_data.get("email")
            is_new_user = False

            if email:
                user = await User.get_or_none(email=email)
                if user:
                    # User exists with this email, link the new auth provider
                    await Authentication.create(
                        user=user,
                        auth_provider=provider,
                        auth_id=auth_id,
                        auth_token=auth_token,
                        last_login=datetime.now()
                    )
                    return user, False, ""

            # Create new user if we have a phone number or if email is available
            if phone_number or email:
                # Generate a unique username based on provider and ID
                username = f"{provider.value}_{auth_id}"

                # Create the user
                user = await User.create(
                    username=username,
                    email=email,
                    phone_number=phone_number or f"{provider.value}_{auth_id}",  # Placeholder if no phone
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    profile_image=user_data.get("profile_image")
                )

                # Create authentication record
                await Authentication.create(
                    user=user,
                    auth_provider=provider,
                    auth_id=auth_id,
                    auth_token=auth_token,
                    last_login=datetime.now()
                )

                return user, True, ""
            else:
                return None, False, "Phone number required for new account"

        except Exception as e:
            # In production, add proper error logging here
            return None, False, f"Error authenticating with {provider.value}: {str(e)}"