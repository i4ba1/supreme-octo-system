from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import uuid

from apps.reviews.services import TestimonialService
from apps.reviews.serializers import TestimonialSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
async def list_restaurant_testimonials(request, restaurant_id):
    """List testimonials for a restaurant."""
    try:
        testimonials = await TestimonialService.get_by_restaurant(
            uuid.UUID(restaurant_id),
            limit=int(request.query_params.get('limit', 10))
        )
        data = await TestimonialSerializer().to_representation_list(testimonials)
        return Response(data)
    except ValueError:
        return Response({"error": "Invalid restaurant ID"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def list_user_testimonials(request):
    """List testimonials written by the current user."""
    testimonials = await TestimonialService.get_by_user(
        request.user.id,
        limit=int(request.query_params.get('limit', 10))
    )
    data = await TestimonialSerializer().to_representation_list(testimonials)
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def create_testimonial(request):
    """Create a new testimonial."""
    try:
        # Extract data
        restaurant_id = request.data.get('restaurant_id')
        rating = int(request.data.get('rating', 0))
        comments = request.data.get('comments')
        feedback_categories = request.data.get('feedback_categories', [])
        order_id = request.data.get('order_id')

        # Validate required fields
        if not restaurant_id or not rating:
            return Response({
                'error': 'Restaurant ID and rating are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create testimonial
        testimonial = await TestimonialService.create_testimonial(
            user_id=request.user.id,
            restaurant_id=uuid.UUID(restaurant_id),
            rating=rating,
            comments=comments,
            feedback_categories=feedback_categories,
            order_id=uuid.UUID(order_id) if order_id else None
        )

        # Return response with points awarded
        data = await TestimonialSerializer().to_representation(testimonial)
        data['points_awarded'] = 500  # Add points awarded info

        return Response(data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
async def update_testimonial(request, pk):
    """Update an existing testimonial."""
    try:
        testimonial = await TestimonialService.update_testimonial(
            uuid.UUID(pk),
            request.user.id,
            request.data
        )

        if not testimonial:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = await TestimonialSerializer().to_representation(testimonial)
        return Response(data)
    except ValueError:
        return Response({"error": "Invalid testimonial ID"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
async def delete_testimonial(request, pk):
    """Delete a testimonial."""
    try:
        success = await TestimonialService.delete_testimonial(uuid.UUID(pk), request.user.id)

        if not success:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
    except ValueError:
        return Response({"error": "Invalid testimonial ID"}, status=status.HTTP_400_BAD_REQUEST)