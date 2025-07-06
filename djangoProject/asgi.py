"""
ASGI config for djangoProject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""


import ssl
import certifi

ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
import django

django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns
from django.conf import settings
from django.core.asgi import get_asgi_application
from chat.middleware import JWTAuthMiddleware
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.applications import Starlette




# application = ProtocolTypeRouter({
# 	"http": get_asgi_application(),  # 保持http协议处理同步请求
# 	"websocket": JWTAuthMiddleware(  # 自动将jwt用户绑定到 scope["user"]
# 		# 异步处理websocket协议
# 		URLRouter(
# 			websocket_urlpatterns
# 		)
# 	),
# })


# Django 原始 http 处理器
django_app = get_asgi_application()

# 用 Starlette 包一层，添加 /media 路由支持
http_app = Starlette()
http_app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")
http_app.mount("/", django_app)

# 总入口 application
application = ProtocolTypeRouter({
    "http": http_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    )
})
