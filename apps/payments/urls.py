from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_payments, name='list_payments'),
    path('<uuid:pk>/', views.get_payment, name='get_payment'),
    path('create/', views.create_payment, name='create_payment'),
    path('<uuid:pk>/check_status/', views.check_payment_status, name='check_payment_status'),
    path('<uuid:pk>/download_qr/', views.download_qr, name='download_qr'),
    path('<uuid:pk>/share_qr/', views.share_qr, name='share_qr'),
]
