from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_orders, name='list_orders'),
    path('<uuid:pk>/', views.get_order, name='get_order'),
    path('create/', views.create_order, name='create_order'),
    path('<uuid:pk>/cancel/', views.cancel_order, name='cancel_order'),
]