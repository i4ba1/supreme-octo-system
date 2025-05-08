from django.urls import path
from . import views

urlpatterns = [
    path('social/', views.social_login, name='register'),
    path('mobile/', views.send_otp, name='login'),
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
]