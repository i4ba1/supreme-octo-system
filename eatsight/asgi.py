import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from tortoise.contrib.django import register_tortoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eatsight.settings')
django.setup()

# Import settings after Django setup
from django.conf import settings

# Initialize Tortoise ORM
register_tortoise(
    config=settings.TORTOISE_ORM,
    generate_schemas=True,
)

# Import routing after Tortoise initialization
# from apps.payments.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # "websocket": AuthMiddlewareStack(
    #     URLRouter(
    #         websocket_urlpatterns
    #     )
    # ),
})