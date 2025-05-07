import os

import django
import asyncio
# Import settings after Django setup
from django.conf import settings
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from tortoise import Tortoise


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eatsight.settings')
django.setup()


async def init_tortoise():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    # Only generate schemas in development mode
    if settings.DEBUG:
        await Tortoise.generate_schemas(safe=True)


# Create the ASGI application with Tortoise initialization
async def get_application():
    # Initialize Tortoise first
    await init_tortoise()

    # Then set up the ASGI application
    return ProtocolTypeRouter({
        "http": get_asgi_application(),
        # Uncomment when you're ready to use WebSockets
        # "websocket": AuthMiddlewareStack(
        #     URLRouter(
        #         websocket_urlpatterns
        #     )
        # ),
    })


# This is the ASGI entry point that Uvicorn will use
application = get_application()
