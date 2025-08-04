# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
import functools
from django.http import JsonResponse
from commom.sredis import redis_client



def rate_limit_by_ip(limit_key_prefix="limit_code", seconds=60):
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(self,request, *args, **kwargs):
            # 获取客户端 IP
            ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
            key = f"{limit_key_prefix}:{ip}"
            if redis_client.get(key):
                return JsonResponse(
                    {
                        "code": 1005,
                        "message": "请求过于频繁，请稍后再试"
                    },
                    status=200
                )
            # 设置标记，限流时间为 seconds 秒
            redis_client.set(key, "1", ex=seconds)
            # 正常执行视图
            return view_func(self,request, *args, **kwargs)
        return _wrapped_view
    return decorator