from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_vouchers, name='list_vouchers'),
    path('user/', views.list_user_vouchers, name='list_user_vouchers'),
    path('redeem/', views.redeem_voucher, name='redeem_voucher'),
    path('apply/', views.apply_voucher, name='apply_voucher'),
    path('create/', views.create_voucher, name='create_voucher'),
]