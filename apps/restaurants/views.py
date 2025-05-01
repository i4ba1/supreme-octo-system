from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.restaurants.serializers import RestaurantSerializer, TableSerializer
from apps.restaurants.services import RestaurantService


@api_view(['GET'])
@permission_classes([AllowAny])
async def list_restaurants(request):
    """List all restaurants."""
    restaurants = await RestaurantService.get_all()
    return Response(await RestaurantSerializer(restaurants, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
async def get_restaurant(request, pk):
    """Get restaurant details."""
    restaurant = await RestaurantService.get_by_id(pk)
    if not restaurant:
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(await RestaurantSerializer(restaurant).data)


@api_view(['GET'])
@permission_classes([AllowAny])
async def get_restaurant_tables(request, restaurant_id):
    """Get available tables for a restaurant."""
    tables = await RestaurantService.get_available_tables(restaurant_id)
    return Response(await TableSerializer(tables, many=True).data)