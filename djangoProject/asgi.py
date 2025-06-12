"""
ASGI config for djangoProject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# import os
#
# from django.core.asgi import get_asgi_application
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
#
# application = get_asgi_application()

import ssl
import certifi

ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())


import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

import django

django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
	"http": get_asgi_application(),  # 保持http协议处理同步请求
	"websocket": AuthMiddlewareStack(  # 自动将 session/cookie 用户绑定到 scope["user"]
		# 异步处理websocket协议
		URLRouter(
			websocket_urlpatterns
		)
	),
})
