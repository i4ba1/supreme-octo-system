from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.list_menu_items, name='list_menu_items'),
    path('items/<uuid:pk>/', views.get_menu_item, name='get_menu_item'),
]
