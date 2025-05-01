from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import UserSerializer
from apps.users.services import UserService


@api_view(['POST'])
@permission_classes([AllowAny])
async def register(request):
    """Register a new user."""
    serializer = UserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create user using service
        user = await UserService.create_user(serializer.validated_data)

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': await UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
async def login(request):
    """Login with username/email and password."""
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password are required'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Authenticate user
    user = await UserService.authenticate(username, password)

    if not user:
        return Response({'error': 'Invalid credentials'},
                        status=status.HTTP_401_UNAUTHORIZED)

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': await UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
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