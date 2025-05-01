from django.urls import path
from . import views

urlpatterns = [
    path('restaurant/<uuid:restaurant_id>/', views.list_restaurant_testimonials, name='list_restaurant_testimonials'),
    path('user/', views.list_user_testimonials, name='list_user_testimonials'),
    path('', views.create_testimonial, name='create_testimonial'),
    path('<uuid:pk>/', views.update_testimonial, name='update_testimonial'),
    path('<uuid:pk>/delete/', views.delete_testimonial, name='delete_testimonial'),
]