import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

import aiohttp
from tortoise.transactions import atomic

from apps.users.models import OTPVerification, User, Authentication, AuthProvider


class OTPService:
    # Twilio API credentials - store these in environment variables in production
    TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
    TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
    TWILIO_VERIFY_SERVICE_SID = "YOUR_TWILIO_VERIFY_SERVICE_SID"

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a numeric OTP code of specified length"""
        return ''.join(random.choices(string.digits, k=length))

    @classmethod
    async def create_otp_verification(cls, phone_number: str, otp_code: str, expiry_minutes: int = 10):
        """
        Create a new OTP verification record

        Args:
            phone_number: The phone number to verify
            otp_code: The OTP code to store
            expiry_minutes: Number of minutes until the OTP expires

        Returns:
            The newly created OTPVerification object
        """
        expires_at = datetime.now() + timedelta(minutes=expiry_minutes)

        # First invalidate any existing OTP for this phone number
        await OTPVerification.filter(phone_number=phone_number, is_verified=False).update(is_verified=True)

        # Create new OTP record
        return await OTPVerification.create(
            phone_number=phone_number,
            otp_code=otp_code,
            expires_at=expires_at
        )

    @classmethod
    async def send_otp(cls, phone_number: str) -> Tuple[bool, str]:
        """
        Send OTP to phone number using Twilio Verify API

        Args:
            phone_number: The phone number to send OTP to (E.164 format)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate OTP
            otp_code = cls.generate_otp()

            # Store OTP in database
            await cls.create_otp_verification(phone_number, otp_code)

            # Implementation for Twilio Verify API
            # This is a placeholder - in production, use the actual Twilio API call
            url = f"https://verify.twilio.com/v2/Services/{cls.TWILIO_VERIFY_SERVICE_SID}/Verifications"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        auth=aiohttp.BasicAuth(cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN),
                        data={
                            "To": phone_number,
                            "Channel": "sms",
                        }
                ) as response:
                    if response.status == 201:
                        return True, "OTP sent successfully"
                    else:
                        response_data = await response.json()
                        return False, f"Failed to send OTP: {response_data.get('message', 'Unknown error')}"

        except Exception as e:
            # In production, add proper error logging here
            return False, f"Error sending OTP: {str(e)}"

    @classmethod
    async def verify_otp(cls, phone_number: str, otp_code: str) -> Tuple[bool, str]:
        """
        Verify OTP code for a phone number

        Args:
            phone_number: The phone number to verify
            otp_code: The OTP code to check

        Returns:
            Tuple of (success, message)
        """
        try:
            # Find active OTP verification
            otp_verification = await OTPVerification.get_or_none(
                phone_number=phone_number,
                is_verified=False,
                expires_at__gt=datetime.now()
            )

            if not otp_verification:
                return False, "OTP expired or not found"

            # Increment verification attempts
            otp_verification.verification_attempts += 1
            await otp_verification.save()

            # Check attempts limit
            if otp_verification.verification_attempts >= 3:
                otp_verification.is_verified = True  # Mark as used to prevent further attempts
                await otp_verification.save()
                return False, "Maximum verification attempts exceeded"

            # Check OTP code
            if otp_verification.otp_code != otp_code:
                return False, "Invalid OTP code"

            # Mark as verified
            otp_verification.is_verified = True
            await otp_verification.save()

            return True, "OTP verified successfully"

        except Exception as e:
            # In production, add proper error logging here
            return False, f"Error verifying OTP: {str(e)}"

    @classmethod
    async def verify_twilio_otp(cls, phone_number: str, otp_code: str) -> Tuple[bool, str]:
        """
        Verify OTP using Twilio's verification check API

        Args:
            phone_number: The phone number to verify (E.164 format)
            otp_code: The OTP code to check

        Returns:
            Tuple of (success, message)
        """
        try:
            url = f"https://verify.twilio.com/v2/Services/{cls.TWILIO_VERIFY_SERVICE_SID}/VerificationCheck"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        auth=aiohttp.BasicAuth(cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN),
                        data={
                            "To": phone_number,
                            "Code": otp_code
                        }
                ) as response:
                    response_data = await response.json()

                    if response.status == 200 and response_data.get("status") == "approved":
                        return True, "OTP verified successfully"
                    else:
                        return False, f"OTP verification failed: {response_data.get('message', 'Invalid code')}"

        except Exception as e:
            # In production, add proper error logging here
            return False, f"Error verifying OTP with Twilio: {str(e)}"