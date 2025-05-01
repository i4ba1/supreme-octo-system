from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_restaurants, name='list_restaurants'),
    path('<uuid:pk>/', views.get_restaurant, name='get_restaurant'),
    path('<uuid:restaurant_id>/tables/', views.get_restaurant_tables, name='get_restaurant_tables'),
]