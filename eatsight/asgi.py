import os

import django
from channels.routing import ProtocolTypeRouter
# Import settings after Django setup
from django.conf import settings
from django.core.asgi import get_asgi_application
from tortoise import Tortoise


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eatsight.settings.development')
django.setup()


# Define Tortoise initialization function
async def init_tortoise():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    if settings.DEBUG:
        await Tortoise.generate_schemas(safe=True)


# Create a proper ASGI application with lifecycle events
class TortoiseInitASGI:
    def __init__(self, app):
        self.app = app


    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            message = await receive()
            if message["type"] == "lifespan.startup":
                # Initialize Tortoise on startup
                await init_tortoise()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                # Close Tortoise connections on shutdown
                await Tortoise.close_connections()
                await send({"type": "lifespan.shutdown.complete"})
        else:
            # Handle regular requests
            await self.app(scope, receive, send)


# Create the Django ASGI application
django_application = get_asgi_application()

# Define the main application
application = ProtocolTypeRouter({
    "http": django_application,
    # Uncomment when ready for websockets
    # "websocket": AuthMiddlewareStack(
    #     URLRouter(websocket_urlpatterns)
    # ),
})

# Wrap the application with Tortoise initialization middleware
application = TortoiseInitASGI(application)
