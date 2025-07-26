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



