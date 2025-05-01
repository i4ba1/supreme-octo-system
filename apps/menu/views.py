from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.menu.services import MenuService
from apps.menu.serializers import MenuItemSerializer, MenuItemCreateUpdateSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
async def list_menu_items(request):
    """List menu items, optionally filtered by restaurant."""
    restaurant_id = request.query_params.get('restaurant')
    is_active = request.query_params.get('is_active', 'true').lower() == 'true'

    if restaurant_id:
        menu_items = await MenuService.get_restaurant_menu_items(restaurant_id, is_active)
    else:
        menu_items = await MenuService.get_all_menu_items(is_active)

    return Response(await MenuItemSerializer(menu_items, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
async def get_menu_item(request, pk):
    """Get menu item details."""
    menu_item = await MenuService.get_menu_item_by_id(pk)
    if not menu_item:
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(await MenuItemSerializer(menu_item).data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
async def create_menu_item(request):
    """Create a new menu item."""
    serializer = MenuItemCreateUpdateSerializer(data=request.data)
    if await serializer.is_valid(raise_exception=True):
        restaurant_id = request.data.get('restaurant_id')
        menu_item = await MenuService.create_menu_item(restaurant_id, serializer.validated_data)
        return Response(await MenuItemSerializer(menu_item).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
async def update_menu_item(request, pk):
    """Update an existing menu item."""
    menu_item = await MenuService.get_menu_item_by_id(pk)
    if not menu_item:
        return Response({"detail": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = MenuItemCreateUpdateSerializer(data=request.data)
    if await serializer.is_valid(raise_exception=True):
        updated_item = await MenuService.update_menu_item(menu_item.id, serializer.validated_data)
        return Response(await MenuItemSerializer(updated_item).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
async def delete_menu_item(request, pk):
    """Delete a menu item."""
    menu_item = await MenuService.get_menu_item_by_id(pk)
    if not menu_item:
        return Response({"detail": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

    success = await MenuService.delete_menu_item(menu_item.id)
    if success:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({"detail": "Failed to delete menu item"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
async def list_menu_item_options(request, item_id):
    """List all options for a specific menu item."""
    menu_item = await MenuService.get_menu_item_by_id(item_id)
    if not menu_item:
        return Response({"detail": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

    options = await menu_item.options.all()
    from apps.menu.serializers import MenuItemOptionSerializer
    return Response(await MenuItemOptionSerializer(options, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
async def list_menu_item_toppings(request, item_id):
    """List all toppings for a specific menu item."""
    menu_item = await MenuService.get_menu_item_by_id(item_id)
    if not menu_item:
        return Response({"detail": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

    toppings = await menu_item.toppings.all()
    from apps.menu.serializers import MenuItemToppingSerializer
    return Response(await MenuItemToppingSerializer(toppings, many=True).data)