from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import AuthProvider
from apps.users.serializers import UserSerializer, PhoneLoginSerializer, OTPVerificationSerializer, \
    SocialLoginSerializer
from apps.users.services import UserService
from core.otp_service import OTPService


@api_view(['POST'])
@permission_classes([AllowAny])
async def send_otp(request):
    """Send OTP to phone number for login/registration."""
    serializer = PhoneLoginSerializer(data=request.data)
    if not await serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']

    # Send OTP
    success, message = await OTPService.send_otp(phone_number)

    if success:
        return Response({'message': message}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
async def verify_otp(request):
    """Verify OTP and login/register user."""
    serializer = OTPVerificationSerializer(data=request.data)
    if not await serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    otp_code = serializer.validated_data['otp_code']

    # Verify OTP
    success, message = await OTPService.verify_otp(phone_number, otp_code)

    if not success:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user exists with this phone number
    user = await UserService.get_by_phone(phone_number)
    is_new_user = False

    if not user:
        # Create new user
        try:
            user = await UserService.create_user({
                'phone_number': phone_number
            })
            is_new_user = True
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': await UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'is_new_user': is_new_user
    })


@api_view(['POST'])
@permission_classes([AllowAny])
async def social_login(request):
    """Login/register using social provider."""
    serializer = SocialLoginSerializer(data=request.data)
    if not await serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    provider_name = serializer.validated_data['provider']
    token = serializer.validated_data['token']
    phone_number = serializer.validated_data.get('phone_number')

    # Map string provider to enum
    try:
        provider = AuthProvider(provider_name)
    except ValueError:
        return Response({'error': f"Invalid provider: {provider_name}"},
                        status=status.HTTP_400_BAD_REQUEST)

    # Authenticate with social provider
    user, is_new_user, error = await SocialAuthService.authenticate_social_user(
        provider, token, phone_number
    )

    if not user:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': await UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'is_new_user': is_new_user
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_profile(request):
    """Get current user profile."""
    user = await UserService.get_by_id(request.user.id)
    return Response(await UserSerializer(user).data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
async def update_profile(request):
    """Update user profile."""
    user = await UserService.update_user(request.user.id, request.data)
    return Response(await UserSerializer(user).data)