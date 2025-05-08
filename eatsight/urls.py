from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API authentication
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # REST API endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/restaurants/', include('apps.restaurants.urls')),
    path('api/menu/', include('apps.menu.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/vouchers/', include('apps.vouchers.urls')),
    path('api/reviews/', include('apps.reviews.urls')),

    # GraphQL endpoint (will implement async version later)
    # path('graphql/', include('graphql_api.urls')),
]