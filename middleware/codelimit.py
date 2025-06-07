# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from utils.aredis import redis_client
from django.http.response import JsonResponse


class AsyncRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response  # 下一步要执行的 view（可能是另一个中间件或视图本身）

    async def __call__(self, request):
        # 这是主逻辑：每次请求进来都会执行这里
        # 获取客户端 IP
        ip = self.get_client_ip(request)
        key = f"ratelimit:{ip}"

        # Redis 限流逻辑：同一个 key 60 秒内只能存在一次
        if await redis_client.exists(key):
            return JsonResponse({"error": "请求频率过高，请稍后再试"}, status=429)
        await redis_client.set(key, 1, ex=60)

        # 如果未限流，继续处理请求
        response = await self.get_response(request)
        return response

    @staticmethod
    def get_client_ip(request):
        # 获取客户端 IP 地址
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')