import course_flow.routing
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

application = ProtocolTypeRouter(
    {
        # http -> django views is added by default
        "websocket": AuthMiddlewareStack(
            URLRouter(course_flow.routing.websocket_urlpatterns)
        ),
    }
)
