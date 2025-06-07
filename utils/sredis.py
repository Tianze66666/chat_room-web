# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import redis
from django.conf import settings

redis_client = redis.Redis(
    host=settings.REDIS_CACHE_CONFIG['host'],
    port=settings.REDIS_CACHE_CONFIG['port'],
    db=settings.REDIS_CACHE_CONFIG['db'],
    password=settings.REDIS_CACHE_CONFIG['password'],
    decode_responses=settings.REDIS_CACHE_CONFIG['decode_responses'],
)

class ChangeTokenStatusMixin:
    @staticmethod
    def change_user_token(user_id, refresh_jti=None, access_jti=None):
        key = "user:{}:{}"
        pipe = redis_client.pipeline()

        if not access_jti:
            pipe.delete(key.format('refresh', user_id, ))
            pipe.delete(key.format('access', user_id, ))
            pipe.execute()
            return
        pipe.set(key.format('refresh', user_id, ), refresh_jti, ex=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'])
        pipe.set(key.format('access', user_id, ), access_jti, ex=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'])
        pipe.execute()
